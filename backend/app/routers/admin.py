from datetime import timezone
from io import BytesIO
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import (
    Conversation,
    ConversationLog,
    Document,
    Feedback,
    Message,
    SentimentFlag,
    User,
)
from app.schemas.auth import UserOut
from app.schemas.sentiment import SentimentFlagOut
from app.services import voice_service

router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_ROLES = ("student", "admin")
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".html", ".htm"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _extract_text(filename: str, content: bytes) -> tuple[str, str]:
    """Return (source_type, text) for a supported knowledge-base file."""
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported file type. Use PDF, TXT, MD or HTML.",
        )

    source_type = suffix.lstrip(".")
    if source_type == "htm":
        source_type = "html"
    elif source_type == "markdown":
        source_type = "md"

    if source_type == "pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - dependency is pinned
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PDF extraction is not available on this server.",
            ) from exc

        try:
            reader = PdfReader(BytesIO(content))
            text = "\n\n".join(
                (page.extract_text() or "").strip() for page in reader.pages
            ).strip()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not read this PDF.",
            ) from exc
    else:
        text = content.decode("utf-8", errors="replace").strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text found in this file.",
        )

    return source_type, text


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


@router.post("/knowledge-base", response_model=dict, status_code=201)
async def upload_knowledge_base(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str | None = Form(default=None),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 10 MB limit",
        )

    clean_title = title.strip()
    if not clean_title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title is required",
        )
    if len(clean_title) > 255:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title must be 255 characters or fewer",
        )

    clean_category = category.strip() if category else None
    if clean_category and len(clean_category) > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category must be 50 characters or fewer",
        )

    source_type, text = _extract_text(file.filename or "", content)

    document = Document(
        title=clean_title,
        source_type=source_type,
        category=clean_category,
        content=text,
        chunked=False,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "doc_id": str(document.id),
        "title": document.title,
        "category": document.category,
        "embedded": document.chunked,
        "updated_at": (
            document.updated_at.isoformat() if document.updated_at else None
        ),
    }


@router.get("/flags", response_model=list[SentimentFlagOut])
def list_sentiment_flags(
    resolved: bool | None = None,
    severity: str | None = None,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(SentimentFlag, ConversationLog).outerjoin(
        ConversationLog, SentimentFlag.log_id == ConversationLog.log_id
    )
    if resolved is not None:
        query = query.filter(SentimentFlag.resolved == resolved)
    if severity is not None:
        query = query.filter(SentimentFlag.severity == severity)

    rows = query.order_by(ConversationLog.timestamp.desc().nullslast()).all()
    flags = []
    for flag, log in rows:
        timestamp = log.timestamp if log else None
        if timestamp is not None and timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        flags.append(
            {
                "flag_id": str(flag.flag_id),
                "log_id": str(flag.log_id) if flag.log_id else None,
                "severity": flag.severity,
                "reviewed_by": str(flag.reviewed_by) if flag.reviewed_by else None,
                "resolved": bool(flag.resolved),
                "message_text": log.message_text if log else None,
                "timestamp": timestamp,
            }
        )
    return flags


@router.get("/diagnostics/voice", response_model=dict)
def voice_diagnostics(_admin: User = Depends(require_admin)) -> dict:
    return voice_service.diagnostics()


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
