from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .models import EmailAttachmentType, EmailSource, EmailStatus


class MeOut(BaseModel):
  id: int
  email: str


class ResumeOut(BaseModel):
    id: int
    original_filename: str
    stored_path: str
    full_name: str
    profession: str
    experience: str
    email: str | None = None
    domain: str
    skills: str | None = None
    education: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    id: int
    message: str


class EmailOut(BaseModel):
    id: int
    sender: str
    subject: str
    received_at: datetime
    source: EmailSource
    attachment_type: EmailAttachmentType
    status: EmailStatus

    class Config:
        from_attributes = True


class DomainCount(BaseModel):
    name: str
    value: int


class TrendPoint(BaseModel):
    month: str
    value: int


class DashboardOverview(BaseModel):
    total_emails_processed: int
    total_resumes_extracted: int
    domains_identified: int
    pending_resumes: int
    domain_counts: list[DomainCount]
    trend: list[TrendPoint]


