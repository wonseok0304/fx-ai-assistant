from datetime import date as Date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DataIn(BaseModel):
    date: Date = Field(..., description="YYYY-MM-DD")
    value: float = Field(..., gt=0, lt=1_000_000, description="USD/KRW 환율")
    memo: str = Field("", max_length=200)

    @field_validator("memo")
    @classmethod
    def strip_memo(cls, v):
        return v.strip()


class DataOut(BaseModel):
    id: str
    date: str
    value: float
    memo: str = ""


class SummaryOut(BaseModel):
    period: Optional[str]
    count: int
    metrics: dict
    trend: str


class MessageIn(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ConversationIn(BaseModel):
    title: str = Field("", max_length=100)
    messages: list[MessageIn] = Field(..., min_length=1, max_length=200)


class ConversationListItem(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str


class ConversationOut(ConversationListItem):
    messages: list[dict]


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = None


class ChatOut(BaseModel):
    reply: str
    conversation_id: str
    tools_used: list[dict] = []
