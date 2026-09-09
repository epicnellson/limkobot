from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Conversation, Feedback, Message, User
from app.schemas.message import BotReply, FeedbackCreate, MessageCreate
from app.services.rag_service import answer

router = APIRouter(prefix="/messages", tags=["messages"])


def _get_owned_conversation(conversation_id, user: User, db: Session) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return conversation


@router.post("", response_model=BotReply, status_code=201)
def send_message(
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BotReply:
    conversation = _get_owned_conversation(payload.conversation_id, user, db)

    user_message = Message(
        conversation_id=conversation.id, sender="user", body=payload.body
    )
    db.add(user_message)

    reply_text = answer(payload.body, str(conversation.id))
    bot_message = Message(
        conversation_id=conversation.id,
        sender="bot",
        body=reply_text,
        is_answered=True,
    )
    db.add(bot_message)

    conversation.last_message_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_message)
    db.refresh(bot_message)

    return BotReply(user_message=user_message, bot_message=bot_message)


@router.post("/{message_id}/feedback", response_model=dict)
def submit_feedback(
    message_id: int,
    payload: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    message = db.get(Message, message_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )

    conversation = db.get(Conversation, message.conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to rate this message",
        )

    feedback = Feedback(
        message_id=message.id,
        conversation_id=conversation.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    return {"detail": "Feedback recorded"}