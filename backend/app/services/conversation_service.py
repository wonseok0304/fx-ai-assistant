from datetime import datetime, timezone

from app import config
from app.store import get_store

COL = config.CONVERSATION_COLLECTION


def _now():
    return datetime.now(timezone.utc).isoformat()


def _brief(c: dict) -> dict:
    return {
        "id": c["id"],
        "title": c.get("title", ""),
        "message_count": len(c.get("messages", [])),
        "created_at": c["created_at"],
        "updated_at": c["updated_at"],
    }


def list_conversations() -> list[dict]:
    rows = sorted(get_store().list(COL), key=lambda c: c["updated_at"], reverse=True)
    return [_brief(c) for c in rows]


def get_conversation(conv_id: str):
    c = get_store().get(COL, conv_id)
    return {**_brief(c), "messages": c["messages"]} if c else None


def create_conversation(title: str, messages: list[dict]) -> dict:
    now = _now()
    title = title or messages[0]["content"][:30]
    doc = {"title": title, "messages": messages, "created_at": now, "updated_at": now}
    return {**_brief({"id": get_store().add(COL, doc), **doc}), "messages": messages}


def append_messages(conv_id: str, new_messages: list[dict]):
    c = get_store().get(COL, conv_id)
    if not c:
        return None
    msgs = c["messages"] + new_messages
    get_store().update(COL, conv_id, {"messages": msgs, "updated_at": _now()})
    return msgs


def delete_conversation(conv_id: str) -> bool:
    return get_store().delete(COL, conv_id)
