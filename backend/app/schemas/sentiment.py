from datetime import datetime

from pydantic import BaseModel


class SentimentFlagOut(BaseModel):
    flag_id: str
    log_id: str | None = None
    severity: str | None = None
    reviewed_by: str | None = None
    resolved: bool = False
    message_text: str | None = None
    timestamp: datetime | None = None
