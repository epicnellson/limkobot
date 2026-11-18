from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConversationLog(Base):
    """Message log used by the sentiment review queue (SYSTEM_SPECS.md 3.4)."""

    __tablename__ = "conversation_logs"

    log_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    student_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("students.student_id", ondelete="CASCADE"),
        index=True,
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent_type: Mapped[str | None] = mapped_column(String(50))
    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(), server_default=text("now()")
    )
