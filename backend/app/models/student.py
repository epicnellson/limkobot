from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Student(Base):
    """WhatsApp student profile from the spec schema (SYSTEM_SPECS.md 3.1)."""

    __tablename__ = "students"

    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )
    programme: Mapped[str | None] = mapped_column(String(100))
    otp_verified: Mapped[bool | None] = mapped_column(
        Boolean, server_default=text("false")
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(), server_default=text("now()")
    )
