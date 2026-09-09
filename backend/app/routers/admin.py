from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import Conversation, Document, Feedback, Message, User
from app.schemas.auth import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_ROLES = ("student", "admin")


@router.get("/dashboard/stats", response_model=dict)
def dashboard_stats(
    _admin: User = Depends(require_admin), db: Session = Depends(get_db)
) -> dict:
    return {
        "users": db.query(func.count(User.id)).scalar() or 0,
        "conversations": db.query(func.count(Conversation.id)).scalar() or 0,
        "messages": db.query(func.count(Message.id)).scalar() or 0,
        "documents": db.query(func.count(Document.id)).scalar() or 0,
    }


@router.get("/users", response_model=list[UserOut])
def list_users(
    _admin: User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/role", response_model=UserOut)
def set_user_role(
    user_id: UUID,
    role: str,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="role must be 'student' or 'admin'",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    user.role = role
    db.commit()
    db.refresh(user)
    return user


@router.get("/conversations", response_model=list[dict])
def list_all_conversations(
    _admin: User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.query(Conversation).order_by(Conversation.started_at.desc()).all()
    return [
        {
            "id": str(conversation.id),
            "user_id": str(conversation.user_id),
            "channel": conversation.channel,
            "status": conversation.status,
            "started_at": conversation.started_at.isoformat(),
        }
        for conversation in rows
    ]


@router.get("/analytics/messages", response_model=dict)
def message_analytics(
    _admin: User = Depends(require_admin), db: Session = Depends(get_db)
) -> dict:
    rows = (
        db.query(Message.sender, func.count(Message.id))
        .group_by(Message.sender)
        .all()
    )
    return {"by_sender": {sender: count for sender, count in rows}}


@router.get("/analytics/feedback", response_model=dict)
def feedback_analytics(
    _admin: User = Depends(require_admin), db: Session = Depends(get_db)
) -> dict:
    rows = (
        db.query(Feedback.rating, func.count(Feedback.id))
        .group_by(Feedback.rating)
        .all()
    )
    return {"by_rating": {str(rating): count for rating, count in rows}}