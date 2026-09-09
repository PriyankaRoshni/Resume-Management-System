from __future__ import annotations

import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from .db import get_db
from .models import User

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

OAUTH_SCOPE = "openid email https://www.googleapis.com/auth/gmail.readonly"

SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


def _get_serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("SESSION_SECRET", "dev-session-secret")
    return URLSafeTimedSerializer(secret_key=secret, salt="resume-session")


def _encode_state() -> str:
    # Simple random state; cryptographic strength is not critical here
    raw = os.urandom(16)
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def get_oauth_config() -> tuple[str, str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    if not client_id or not client_secret:
        raise RuntimeError("GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET not configured in environment")
    return client_id, client_secret, redirect_uri


def create_session(response: Response, user_id: int) -> None:
    s = _get_serializer()
    token = s.dumps({"uid": user_id})
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


def _load_user_from_token(token: str, db: Session) -> User:
    s = _get_serializer()
    try:
        data = s.loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="Session expired")
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid session")

    uid = data.get("uid")
    if uid is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        # Also allow Authorization: Bearer for future flexibility
        auth_scheme = HTTPBearer(auto_error=False)
        credentials: HTTPAuthorizationCredentials | None = auth_scheme(request)  # type: ignore[arg-type]
        if credentials and credentials.scheme.lower() == "bearer":
            token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _load_user_from_token(token, db)


CurrentUser = Annotated[User, Depends(get_current_user)]


async def exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
    client_id, client_secret, _ = get_oauth_config()
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to exchange code: {resp.text}")
        return resp.json()


async def fetch_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch userinfo: {resp.text}")
        return resp.json()


def update_user_tokens(user: User, token_data: dict) -> None:
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token") or user.refresh_token
    expires_in = token_data.get("expires_in")

    user.access_token = access_token
    user.refresh_token = refresh_token
    if expires_in:
        user.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

