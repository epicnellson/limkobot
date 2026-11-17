from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal, get_db
from app.models import User
from app.schemas.auth import UserOut
from app.services import stub_data
from app.services.auth_service import decode_access_token, decode_student_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        phone=user.phone,
        full_name=user.full_name,
        student_id=user.student_id,
        email=user.email,
        role=user.role,
        is_verified=user.is_verified,
    )


def _student_out(student: dict) -> UserOut:
    return UserOut(
        id=UUID(student["student_id"]),
        phone=student["phone_number"],
        full_name=student.get("full_name"),
        student_id=student["student_id"],
        role="student",
        is_verified=bool(student.get("otp_verified")),
    )


def get_current_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserOut:
    """Resolve a staff JWT (``sub``) or a student JWT (``student_id``) for /auth/me."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    subject = payload.get("sub")
    if subject:
        if SessionLocal is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is not configured",
            )
        try:
            user_id = UUID(str(subject))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        with SessionLocal() as db:
            user = db.get(User, user_id)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
                )
            return _user_out(user)

    student_id = payload.get("student_id")
    if student_id:
        student = stub_data.get_student_by_id(str(student_id))
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Student not found"
            )
        return _student_out(student)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    try:
        user = db.get(User, UUID(user_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return user


def get_current_student(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """Resolve the JWT issued on /auth/otp/verify to the owning student record.

    Protects WhatsApp-facing endpoints such as /documents/request.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = decode_student_access_token(credentials.credentials)
    student_id = payload.get("student_id")
    if not student_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    student = stub_data.get_student_by_id(str(student_id))
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Student not found"
        )
    return student