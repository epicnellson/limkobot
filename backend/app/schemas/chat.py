from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatAsk(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+\d{10,15}$")
    message_text: str = Field(..., min_length=1, max_length=4000)


class ChatMessage(BaseModel):
    log_id: str
    student_id: str
    sender: Literal["user", "bot"]
    message_text: str
    intent_type: str | None = None
    sentiment_score: float | None = None
    timestamp: datetime


class Source(BaseModel):
    id: str
    title: str
    category: str | None = None
    source_url: str | None = None
    score: float | None = None


class ChatReply(BaseModel):
    user_message: ChatMessage
    bot_message: ChatMessage
    sources: list[Source]
    routing: Literal["rule", "rag"]