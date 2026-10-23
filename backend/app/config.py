import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# 비워 두면 OpenAI 기본 주소. Groq/Gemini 같은 OpenAI 호환 API를 쓰려면 주소를 지정한다.
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "") or None
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))

FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
USE_MEMORY_DB = os.getenv("USE_MEMORY_DB", "false").lower() == "true"

ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5500").split(",") if o.strip()
]

DATA_COLLECTION = "data"
CONVERSATION_COLLECTION = "conversations"
