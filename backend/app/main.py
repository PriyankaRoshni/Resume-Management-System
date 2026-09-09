from __future__ import annotations

import os
import shutil
from pathlib import Path

from collections import Counter, defaultdict
from datetime import datetime
from io import BytesIO

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session

# Reuse your existing Gemini pipeline as-is
from system import fetch_emails as pipeline

from .auth import (
    CurrentUser,
    GOOGLE_AUTH_URL,
    OAUTH_SCOPE,
    clear_session,
    create_session,
    exchange_code_for_tokens,
    fetch_userinfo,
    get_oauth_config,
    update_user_tokens,
)
from .db import Base, engine, get_db
from .gmail_sync import fetch_gmail_messages
from .models import EmailAttachmentType, EmailMessage, EmailSource, EmailStatus, Resume, User
from .schemas import DashboardOverview, DomainCount, EmailOut, MeOut, ResumeOut, TrendPoint, UploadResponse


UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_SUFFIXES = {".pdf", ".docx"}

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Classifier API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/auth/google/start")
def auth_google_start() -> RedirectResponse:
    client_id, _, redirect_uri = get_oauth_config()
    state = os.urandom(16).hex()
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": OAUTH_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    from urllib.parse import urlencode

    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url, status_code=302)


@app.get("/auth/google/callback")
async def auth_google_callback(code: str, state: str, db: Session = Depends(get_db)) -> RedirectResponse:
    # In a production app we would validate state; for this mini project we keep it simple.
    _, _, redirect_uri = get_oauth_config()
    token_data = await exchange_code_for_tokens(code, redirect_uri)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token in response")

    info = await fetch_userinfo(access_token)
    email = info.get("email")
    sub = info.get("sub")
    if not email or not sub:
        raise HTTPException(status_code=400, detail="Failed to fetch user email")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, google_sub=sub)
        db.add(user)

    user.google_sub = sub
    update_user_tokens(user, token_data)
    db.commit()
    db.refresh(user)

    response = RedirectResponse(url="/dashboard", status_code=302)
    create_session(response, user.id)
    return response


@app.post("/auth/logout")
def auth_logout() -> RedirectResponse:
    response = RedirectResponse(url="/login", status_code=302)
    clear_session(response)
    return response


@app.get("/me", response_model=MeOut)
def me(current_user: CurrentUser) -> MeOut:
    return MeOut(id=current_user.id, email=current_user.email)


@app.post("/emails/sync")
async def sync_emails(current_user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    created = await fetch_gmail_messages(current_user, db)
    return {"synced": created}


def infer_domain(profession: str) -> str:
    text = (profession or "").lower()
    if any(k in text for k in ["software", "developer", "data", "ml", "ai", "cs", "computer"]):
        return "Computer Science"
    if any(k in text for k in ["electronics", "embedded", "vlsi", "fpga"]):
        return "Electronics"
    if any(k in text for k in ["mechanical", "automotive", "thermal"]):
        return "Mechanical"
    return "Others"


@app.post("/resumes/upload", response_model=UploadResponse)
def upload_and_classify_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResponse:
    try:
        pipeline.require_api_key()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only .pdf and .docx files are supported.")

    stored_name = f"{os.urandom(8).hex()}_{Path(file.filename).name}"
    stored_path = (UPLOAD_DIR / stored_name).resolve()

    try:
        with stored_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    text = pipeline.extract_text(stored_path)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the uploaded file.")

    parsed = pipeline.parse_resume_with_gemini(text)

    profession = parsed.get("Profession", "Unclassified") or "Unclassified"
    domain = parsed.get("Domain") or infer_domain(profession)

    resume = Resume(
        original_filename=file.filename or stored_name,
        stored_path=str(stored_path),
        full_name=parsed.get("Full Name", "Unknown") or "Unknown",
        profession=profession,
        experience=parsed.get("Experience", "") or "",
        email=parsed.get("Email"),
        domain=domain,
        skills=parsed.get("Skills"),
        education=parsed.get("Education"),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return UploadResponse(id=resume.id, message="Uploaded and classified.")


@app.get("/resumes", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db)) -> list[ResumeOut]:
    return db.query(Resume).order_by(Resume.created_at.desc()).all()


@app.get("/resumes/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db)) -> ResumeOut:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return resume


@app.get("/emails", response_model=list[EmailOut])
def list_emails(
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    source: EmailSource | None = None,
    attachment: EmailAttachmentType | None = None,
    current_user: CurrentUser | None = None,
    db: Session = Depends(get_db),
) -> list[EmailOut]:
    q = db.query(EmailMessage)

    if current_user is not None:
        q = q.filter(EmailMessage.user_id == current_user.id)

    if from_date is not None:
        q = q.filter(EmailMessage.received_at >= from_date)
    if to_date is not None:
        q = q.filter(EmailMessage.received_at <= to_date)
    if source is not None:
        q = q.filter(EmailMessage.source == source)
    if attachment is not None:
        q = q.filter(EmailMessage.attachment_type == attachment)

    items = q.order_by(EmailMessage.received_at.desc()).all()

    return items


@app.get("/dashboard/overview", response_model=DashboardOverview)
def dashboard_overview(db: Session = Depends(get_db)) -> DashboardOverview:
    total_resumes = db.query(Resume).count()
    pending_resumes = 0  # placeholder – would be driven by a status field if added later

    total_emails_processed = db.query(EmailMessage).filter(EmailMessage.status == EmailStatus.PROCESSED).count()

    domain_counter: Counter[str] = Counter()
    for (domain,) in db.query(Resume.domain).all():
        if domain:
            domain_counter[domain] += 1

    domain_counts = [DomainCount(name=name, value=value) for name, value in domain_counter.most_common()]
    domains_identified = len(domain_counts)

    # Very simple trend: count resumes per month (last 6 distinct months present in data)
    trend_counter: dict[str, int] = defaultdict(int)
    for (created_at,) in db.query(Resume.created_at).all():
        if created_at:
            key = created_at.strftime("%b %Y")
            trend_counter[key] += 1

    # Sort by datetime representation for stable ordering
    trend_points = sorted(
        (datetime.strptime(k, "%b %Y"), v) for k, v in trend_counter.items()
    )
    trend = [
        TrendPoint(month=dt.strftime("%b"), value=value) for dt, value in trend_points[-6:]
    ]

    return DashboardOverview(
        total_emails_processed=total_emails_processed,
        total_resumes_extracted=total_resumes,
        domains_identified=domains_identified,
        pending_resumes=pending_resumes,
        domain_counts=domain_counts,
        trend=trend,
    )


@app.get("/reports/excel")
def export_domain_excel(
    domain: str = Query(..., description="Domain name, e.g. 'Computer Science'"),
    db: Session = Depends(get_db),
):
    try:
        import pandas as pd
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"pandas is required for Excel export: {e}")

    q = db.query(Resume)
    if domain and domain.lower() != "all":
        q = q.filter(Resume.domain == domain)
    rows = q.order_by(Resume.created_at.desc()).all()

    data = [
        {
            "Candidate Name": r.full_name,
            "Email ID": r.email or "",
            "Domain": r.domain,
            "Skills Extracted": r.skills or "",
            "Education": r.education or "",
            "Experience": r.experience or "",
            "Resume File": r.original_filename,
        }
        for r in rows
    ]

    df = pd.DataFrame(data)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resumes")
    buf.seek(0)

    safe = domain.replace(" ", "_")
    filename = f"{safe}_Resumes.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )

