from pydantic import BaseModel
from typing import Optional


# ── 认证 ──

class RegisterRequest(BaseModel):
    nickname: str
    password: str
    birth_date: str = ""


class LoginRequest(BaseModel):
    nickname: str
    password: str


# ── 用户 ──

class TagsRequest(BaseModel):
    personality: str
    interests: str
    topics: str
    consumption: str
    life_rhythm: str
    distance: str = "city"


class CardRequest(BaseModel):
    bio: str = ""
    card_image: str = ""
    avatar: str = ""


# ── AI 对话 ──

class ChatRequest(BaseModel):
    message: str


# ── 事件 ──

class EventCreateRequest(BaseModel):
    title: str
    description: str = ""
    location: str
    event_date: str
    event_duration: str = "2小时"
    max_participants: int = 5
    category: str = ""


# ── 消息 ──

class MessageSendRequest(BaseModel):
    to_user_id: int
    content: str
    context_type: str = "person"
    context_id: Optional[int] = None


# ── 通用响应 ──

def ok(data=None):
    return {"ok": True, "data": data}


def error(msg: str):
    return {"ok": False, "error": msg}