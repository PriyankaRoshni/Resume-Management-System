from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    # OAuth tokens (basic, single-provider storage suitable for this mini‑project)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Unknown")
    profession: Mapped[str] = mapped_column(String(64), nullable=False, default="Unclassified")
    experience: Mapped[str] = mapped_column(String(128), nullable=False, default="")

    # Extra structured fields used by domain views / Excel reports
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain: Mapped[str] = mapped_column(String(64), nullable=False, default="Others")
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    education: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)


class EmailSource(str, Enum):
    GMAIL = "Gmail"
    OUTLOOK = "Outlook"
    OTHER = "Other"


class EmailStatus(str, Enum):
    PROCESSED = "Processed"
    PENDING = "Pending"
    UNPROCESSED = "Unprocessed"


class EmailAttachmentType(str, Enum):
    PDF = "PDF"
    DOCX = "DOCX"


class EmailMessage(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)

    source: Mapped[EmailSource] = mapped_column(String(32), nullable=False, default=EmailSource.GMAIL.value)
    attachment_type: Mapped[EmailAttachmentType] = mapped_column(
        String(16), nullable=False, default=EmailAttachmentType.PDF.value
    )
    status: Mapped[EmailStatus] = mapped_column(String(16), nullable=False, default=EmailStatus.UNPROCESSED.value)

    # Optional ownership – who this email belongs to (for multi‑user support)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    user: Mapped["User"] = relationship("User", backref="emails")




