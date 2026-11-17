from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SentimentFlag(Base):
    """Escalated message from the spec schema (SYSTEM_SPECS.md 3.6)."""

    __tablename__ = "sentiment_flags"

    flag_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    log_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("conversation_logs.log_id", ondelete="CASCADE"),
        index=True,
    )
    severity: Mapped[str | None] = mapped_column(String(20))
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("admin_users.admin_id"),
    )
    resolved: Mapped[bool | None] = mapped_column(
        Boolean, server_default=text("false")
    )
