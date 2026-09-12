import re

from pydantic import BaseModel, ConfigDict, Field

PHONE_PATTERN = re.compile(r"^\+\d{10,15}$")


class OTPRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+\d{10,15}$")


class OTPVerify(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+\d{10,15}$")
    code: str = Field(..., min_length=6, max_length=6)


class OTPRequestSent(BaseModel):
    status: str
    expires_in_minutes: int


class OTPVerified(BaseModel):
    status: str
    token: str
    expires_in: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    phone: str
    full_name: str | None = None
    student_id: str | None = None
    email: str | None = None
    role: str
    is_verified: bool