from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_student
from app.schemas.chat import ChatAsk, ChatReply
from app.services import stub_data

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatReply)
def ask(payload: ChatAsk, student: dict = Depends(get_current_student)) -> dict:
    if payload.phone_number != student["phone_number"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only send messages for your own number",
        )

    result = stub_data.ask(student["phone_number"], payload.message_text)
    result["user_message"]["sender"] = "user"
    result["bot_message"]["sender"] = "bot"
    return result
