from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.auth import OTPRequest, OTPVerify, Token, UserOut
from app.services import auth_service
from app.services.email_service import send_email
from app.services.twilio_service import send_whatsapp_message

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_TTL_MINUTES = 5


@router.post("/otp/request", status_code=200)
def request_otp(payload: OTPRequest, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.phone == payload.phone).first()
    if user is None:
        user = User(phone=payload.phone, email=payload.email)
        db.add(user)

    user.otp_code = auth_service.generate_otp()
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Phone number already exists"
        )

    message = (
        f"Your LimkoBot verification code is {user.otp_code}. "
        f"It expires in {OTP_TTL_MINUTES} minutes."
    )
    if user.email:
        send_email(user.email, "Your LimkoBot verification code", message)
    else:
        send_whatsapp_message(user.phone, message)

    return {"detail": "OTP sent", "expires_in_minutes": OTP_TTL_MINUTES}


@router.post("/otp/verify", response_model=Token)
def verify_otp(payload: OTPVerify, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.phone == payload.phone).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not user.otp_code or user.otp_code != payload.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    if not user.otp_expires_at or user.otp_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification code expired")

    user.otp_code = None
    user.otp_expires_at = None
    user.is_verified = True
    db.commit()

    token = auth_service.create_access_token(str(user.id), user.phone, user.role)
    return Token(
        access_token=token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)) -> User:
    return user