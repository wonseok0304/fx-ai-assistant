"""저장소 계층. 기본은 Firestore, USE_MEMORY_DB=true면 로컬 테스트용 메모리 DB."""
import json
import uuid
from functools import lru_cache
from typing import Optional

from app import config


class MemoryStore:
    def __init__(self):
        self._cols: dict[str, dict[str, dict]] = {}

    def _col(self, name):
        return self._cols.setdefault(name, {})

    def add(self, col, data):
        doc_id = uuid.uuid4().hex[:20]
        self._col(col)[doc_id] = dict(data)
        return doc_id

    def list(self, col):
        return [{"id": i, **d} for i, d in self._col(col).items()]

    def get(self, col, doc_id) -> Optional[dict]:
        d = self._col(col).get(doc_id)
        return {"id": doc_id, **d} if d is not None else None

    def update(self, col, doc_id, data) -> bool:
        if doc_id not in self._col(col):
            return False
        self._col(col)[doc_id].update(data)
        return True

    def delete(self, col, doc_id) -> bool:
        return self._col(col).pop(doc_id, None) is not None


class FirestoreStore:
    def __init__(self):
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            if config.FIREBASE_SERVICE_ACCOUNT_JSON:
                cred = credentials.Certificate(json.loads(config.FIREBASE_SERVICE_ACCOUNT_JSON))
            elif config.FIREBASE_SERVICE_ACCOUNT_PATH:
                cred = credentials.Certificate(config.FIREBASE_SERVICE_ACCOUNT_PATH)
            else:
                raise RuntimeError(
                    "FIREBASE_SERVICE_ACCOUNT_JSON 또는 FIREBASE_SERVICE_ACCOUNT_PATH 환경변수가 필요합니다."
                )
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def add(self, col, data):
        _, ref = self.db.collection(col).add(data)
        return ref.id

    def list(self, col):
        return [{"id": d.id, **d.to_dict()} for d in self.db.collection(col).stream()]

    def get(self, col, doc_id) -> Optional[dict]:
        d = self.db.collection(col).document(doc_id).get()
        return {"id": d.id, **d.to_dict()} if d.exists else None

    def update(self, col, doc_id, data) -> bool:
        ref = self.db.collection(col).document(doc_id)
        if not ref.get().exists:
            return False
        ref.update(data)
        return True

    def delete(self, col, doc_id) -> bool:
        ref = self.db.collection(col).document(doc_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True


@lru_cache(maxsize=1)
def get_store():
    return MemoryStore() if config.USE_MEMORY_DB else FirestoreStore()
