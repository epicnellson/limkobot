from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models import User
from app.schemas.auth import OTPRequest, OTPRequestSent, OTPVerify, OTPVerified, UserOut
from app.services import auth_service, stub_data
from app.services.whatsapp_service import send_message

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_TTL_MINUTES = 5


@router.post("/otp/request", response_model=OTPRequestSent)
def request_otp(payload: OTPRequest) -> OTPRequestSent:
    result = stub_data.request_otp(payload.phone_number)
    student, code = result["student"], result["code"]

    message = (
        f"Your LimkoBot verification code is {code}. "
        f"It expires in {OTP_TTL_MINUTES} minutes."
    )
    send_message(student["phone_number"], message)

    return OTPRequestSent(status="sent", expires_in_minutes=OTP_TTL_MINUTES)


@router.post("/otp/verify", response_model=OTPVerified)
def verify_otp(payload: OTPVerify) -> OTPVerified:
    student = stub_data.verify_otp(payload.phone_number, payload.code)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification code",
        )

    token = auth_service.create_student_access_token(student["student_id"])
    return OTPVerified(
        status="verified",
        token=token,
        expires_in=auth_service.STUDENT_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)) -> User:
    return user