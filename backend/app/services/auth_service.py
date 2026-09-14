import datetime
import random

from jose import JWTError, jwt

from app.config import settings

STUDENT_TOKEN_EXPIRE_MINUTES = 24 * 60


def generate_otp(length: int = 6) -> str:
    return "".join(random.choices("0123456789", k=length))


def create_access_token(user_id: str, phone: str, role: str) -> str:
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "phone": phone,
        "role": role,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return {}


def create_student_access_token(student_id: str) -> str:
    """24-hour JWT for a WhatsApp/OTP-verified student. Payload: {"student_id": ...}."""
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=STUDENT_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "student_id": str(student_id),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_student_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return {}