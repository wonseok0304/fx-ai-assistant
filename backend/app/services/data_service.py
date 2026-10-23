from app import config
from app.store import get_store

COL = config.DATA_COLLECTION


def list_data(limit: int | None = None, order: str = "asc") -> list[dict]:
    rows = sorted(get_store().list(COL), key=lambda r: r["date"], reverse=(order == "desc"))
    return rows[:limit] if limit else rows


def create_data(payload: dict) -> dict:
    payload = {**payload, "date": payload["date"].isoformat()}
    return {"id": get_store().add(COL, payload), **payload}


def update_data(doc_id: str, payload: dict):
    payload = {**payload, "date": payload["date"].isoformat()}
    if not get_store().update(COL, doc_id, payload):
        return None
    return {"id": doc_id, **payload}


def delete_data(doc_id: str) -> bool:
    return get_store().delete(COL, doc_id)
