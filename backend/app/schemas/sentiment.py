from datetime import datetime

from pydantic import BaseModel


class SentimentFlagOut(BaseModel):
    flag_id: str
    log_id: str
    severity: str
    reviewed_by: str | None = None
    resolved: bool
    message_text: str | None = None
    timestamp: datetime | None = None