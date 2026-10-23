from fastapi import APIRouter, HTTPException

from app.schemas import ConversationIn, ConversationListItem, ConversationOut
from app.services import conversation_service as svc

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationOut, status_code=201)
def create(body: ConversationIn):
    return svc.create_conversation(body.title, [m.model_dump() for m in body.messages])


@router.get("", response_model=list[ConversationListItem])
def list_all():
    """목록 응답에는 messages를 포함하지 않는다. 전체 메시지는 GET /{id}로 조회."""
    return svc.list_conversations()


@router.get("/{conv_id}", response_model=ConversationOut)
def get_one(conv_id: str):
    c = svc.get_conversation(conv_id)
    if not c:
        raise HTTPException(404, "대화를 찾을 수 없습니다.")
    return c


@router.delete("/{conv_id}")
def delete(conv_id: str):
    if not svc.delete_conversation(conv_id):
        raise HTTPException(404, "대화를 찾을 수 없습니다.")
    return {"deleted": conv_id}
