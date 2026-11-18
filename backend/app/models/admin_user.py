from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AdminUser(Base):
    """Dashboard reviewer from the spec schema (SYSTEM_SPECS.md 3.2)."""

    __tablename__ = "admin_users"

    admin_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
