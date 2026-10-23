from fastapi import APIRouter

from app.schemas import ChatIn, ChatOut
from app.services import chat_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    return chat_service.chat(body.message, body.conversation_id)
