from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DocType = Literal[
    "prospectus",
    "fee_schedule",
    "transcript",
    "student_handbook",
    "academic_calendar",
    "other",
]


class DocumentRequestCreate(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+\d{10,15}$")
    doc_type: DocType


class DocumentRequestOut(BaseModel):
    request_id: str
    student_id: str
    doc_type: str
    status: str
    generated_at: datetime | None = None