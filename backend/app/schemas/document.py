from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    title: str
    source_type: str
    source_url: str | None = None
    category: str | None = None
    content: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    source_type: str
    source_url: str | None = None
    category: str | None = None
    chunked: bool
    created_at: datetime
    updated_at: datetime