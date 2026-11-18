"""Database-backed conversation store for WhatsApp messages.

Persists students, users, conversations, messages, conversation logs and
sentiment flags so the dashboard reflects live activity. Falls back to the
in-memory stub store when no database is configured or a write fails, so a
student still receives a reply.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Conversation,
    ConversationLog,
    Message,
    SentimentFlag,
    Student,
    User,
)
from app.services import reply_engine, stub_data

logger = logging.getLogger(__name__)


def database_available() -> bool:
    return SessionLocal is not None


def answer_message(phone_number: str, message_text: str) -> dict:
    if not database_available():
        result = stub_data.ask(phone_number, message_text)
        result["persisted"] = False
        return result

    db = SessionLocal()
    try:
        result = _answer_in_db(db, phone_number, message_text)
        db.commit()
        return result
    except Exception:  # noqa: BLE001 - never leave the student without a reply
        db.rollback()
        logger.exception("Database reply failed for %s; using in-memory store", phone_number)
        result = stub_data.ask(phone_number, message_text)
        result["persisted"] = False
        return result
    finally:
        db.close()


def _answer_in_db(db: Session, phone_number: str, message_text: str) -> dict:
    user, user_created = _get_or_create_user(db, phone_number)
    student, student_created = _get_or_create_student(db, phone_number)
    conversation = _active_conversation(db, user)

    if student_created:
        reply, intent_type, routing = reply_engine.WELCOME_TEXT, "welcome", "welcome"
    else:
        reply, intent_type, routing = reply_engine.select_reply(message_text)

    user_message = Message(
        conversation_id=conversation.id,
        sender="user",
        body=message_text,
        message_type="text",
    )
    db.add(user_message)

    log = ConversationLog(
        student_id=student.student_id,
        message_text=message_text,
        intent_type=intent_type,
    )
    db.add(log)
    db.flush()

    flagged = reply_engine.is_negative(message_text)
    if flagged:
        log.sentiment_score = Decimal(str(reply_engine.NEGATIVE_SCORE))
        db.add(
            SentimentFlag(
                log_id=log.log_id,
                severity=reply_engine.FLAG_SEVERITY,
                resolved=False,
            )
        )

    bot_message = Message(
        conversation_id=conversation.id,
        sender="bot",
        body=reply,
        message_type="text",
        intent=intent_type,
        is_answered=True,
    )
    db.add(bot_message)

    conversation.last_message_at = datetime.now(timezone.utc)
    db.flush()

    return {
        "reply": reply,
        "intent": intent_type,
        "routing": routing,
        "persisted": True,
        "is_new_student": student_created,
        "new_user": user_created,
        "conversation_id": str(conversation.id),
        "log_id": str(log.log_id),
        "flagged": flagged,
    }


def _get_or_create_user(db: Session, phone_number: str) -> tuple[User, bool]:
    user = db.query(User).filter(User.phone == phone_number).one_or_none()
    if user is not None:
        return user, False

    user = User(phone=phone_number, full_name=f"WhatsApp {phone_number}", role="student")
    db.add(user)
    db.flush()
    return user, True


def _get_or_create_student(db: Session, phone_number: str) -> tuple[Student, bool]:
    student = db.query(Student).filter(Student.phone_number == phone_number).one_or_none()
    if student is not None:
        return student, False

    student = Student(phone_number=phone_number, full_name=f"WhatsApp {phone_number}")
    db.add(student)
    db.flush()
    return student, True


def _active_conversation(db: Session, user: User) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id, Conversation.status == "active")
        .order_by(Conversation.started_at.desc())
        .first()
    )
    if conversation is not None:
        return conversation

    conversation = Conversation(user_id=user.id, channel="whatsapp", status="active")
    db.add(conversation)
    db.flush()
    return conversation
