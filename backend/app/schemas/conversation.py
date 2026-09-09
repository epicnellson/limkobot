from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    channel: str = "whatsapp"


class ConversationUpdate(BaseModel):
    status: str | None = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    channel: str
    status: str
    started_at: datetime
    last_message_at: datetime | None = None


class ConversationDetail(ConversationOut):
    pass