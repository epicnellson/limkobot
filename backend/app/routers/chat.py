from fastapi import APIRouter

from app.schemas.chat import ChatAsk, ChatReply
from app.services import stub_data

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatReply)
def ask(payload: ChatAsk) -> dict:
    result = stub_data.ask(payload.phone_number, payload.message_text)
    result["user_message"]["sender"] = "user"
    result["bot_message"]["sender"] = "bot"
    return result