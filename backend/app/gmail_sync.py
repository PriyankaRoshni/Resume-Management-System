from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .auth import GOOGLE_TOKEN_URL, get_oauth_config, update_user_tokens
from .models import EmailAttachmentType, EmailMessage, EmailSource, EmailStatus, User


GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"


async def _refresh_access_token(user: User, db: Session) -> str:
    if user.access_token and user.token_expiry and user.token_expiry > datetime.now(timezone.utc):
        return user.access_token

    if not user.refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token stored for user")

    client_id, client_secret, redirect_uri = get_oauth_config()
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": user.refresh_token,
                "grant_type": "refresh_token",
                "redirect_uri": redirect_uri,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail=f"Failed to refresh token: {resp.text}")
        data = resp.json()
        update_user_tokens(user, data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.access_token or ""


async def _gmail_get(client: httpx.AsyncClient, access_token: str, path: str, params: dict[str, Any] | None = None) -> dict:
    resp = await client.get(
        f"{GMAIL_API_BASE}{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params or {},
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Gmail API error: {resp.text}")
    return resp.json()


def _parse_header(headers: list[dict[str, str]], name: str) -> str | None:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value")
    return None


async def fetch_gmail_messages(user: User, db: Session, max_messages: int = 50) -> int:
    """
    Fetch recent Gmail messages with attachments and store basic metadata in EmailMessage.
    """
    access_token = await _refresh_access_token(user, db)

    async with httpx.AsyncClient(timeout=20) as client:
        lst = await _gmail_get(
            client,
            access_token,
            f"/users/{'me'}/messages",
            params={"maxResults": max_messages, "q": "has:attachment"},
        )
        ids = [m["id"] for m in lst.get("messages", [])]
        if not ids:
            return 0

        created = 0
        for mid in ids:
            full = await _gmail_get(
                client,
                access_token,
                f"/users/me/messages/{mid}",
                params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]},
            )
            headers = full.get("payload", {}).get("headers", [])
            sender = _parse_header(headers, "From") or "unknown"
            subject = _parse_header(headers, "Subject") or "(no subject)"
            date_raw = _parse_header(headers, "Date")

            received_at = datetime.now(timezone.utc)
            if date_raw:
                try:
                    from email.utils import parsedate_to_datetime

                    received_at = parsedate_to_datetime(date_raw)
                except Exception:
                    pass

            # For now we only track that there was an attachment and approximate type
            attachment_type = EmailAttachmentType.PDF

            exists = (
                db.query(EmailMessage)
                .filter(
                    EmailMessage.user_id == user.id,
                    EmailMessage.sender == sender,
                    EmailMessage.subject == subject,
                    EmailMessage.received_at == received_at,
                )
                .first()
            )
            if exists:
                continue

            email = EmailMessage(
                sender=sender,
                subject=subject,
                received_at=received_at,
                source=EmailSource.GMAIL.value,
                attachment_type=attachment_type.value,
                status=EmailStatus.UNPROCESSED.value,
                user_id=user.id,
            )
            db.add(email)
            created += 1

        db.commit()
        return created

