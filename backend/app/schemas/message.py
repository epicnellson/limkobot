from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    conversation_id: UUID
    body: str = Field(..., min_length=1, max_length=4000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: UUID
    sender: str
    body: str
    intent: str | None = None
    confidence: float | None = None
    is_answered: bool
    created_at: datetime


class BotReply(BaseModel):
    user_message: MessageOut
    bot_message: MessageOut


class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None