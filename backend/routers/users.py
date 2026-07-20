from fastapi import APIRouter, Header
from database import get_db
from models import TagsRequest, CardRequest, ChatRequest, ok, error
from routers.auth import get_current_user_id
from services.ai_service import chat_with_ai
from pydantic import BaseModel
import json

router = APIRouter(prefix="/api", tags=["users"])


class UpdateUserRequest(BaseModel):
    nickname: str = ""
    bio: str = ""
    card_image: str = ""
    avatar: str = ""


@router.post("/users/me/tags")
def save_tags(req: TagsRequest, authorization: str | None = Header(None)):
    """保存显性标签（6维度）"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        db.execute(
            """UPDATE users SET personality=?, interests=?, topics=?,
               consumption=?, life_rhythm=?, distance=? WHERE id=?""",
            [req.personality, req.interests, req.topics,
             req.consumption, req.life_rhythm, req.distance, user_id]
        )
        db.commit()
        return ok(None)
    except Exception as e:
        db.rollback()
        return error(f"保存失败: {str(e)}")
    finally:
        db.close()


@router.get("/users/me")
def get_me(authorization: str | None = Header(None)):
    """获取当前用户完整信息"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        user = db.execute("SELECT * FROM users WHERE id=?", [user_id]).fetchone()
        if not user:
            return error("用户不存在")
        return ok(dict(user))
    finally:
        db.close()


@router.put("/users/me")
def update_me(req: UpdateUserRequest, authorization: str | None = Header(None)):
    """更新用户信息（昵称、卡片等）"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        if req.nickname:
            db.execute("UPDATE users SET nickname=? WHERE id=?", [req.nickname, user_id])
        if req.bio or req.card_image or req.avatar:
            db.execute(
                "UPDATE users SET bio=?, card_image=?, avatar=? WHERE id=?",
                [req.bio, req.card_image, req.avatar, user_id]
            )
        db.commit()
        return ok(None)
    except Exception as e:
        db.rollback()
        return error(f"更新失败: {str(e)}")
    finally:
        db.close()


@router.get("/users/me/events")
def get_my_events(authorization: str | None = Header(None)):
    """获取我的事件（我发起的 + 我申请的）"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        # 我发起的
        created = db.execute("""
            SELECT e.*, 'created' as role FROM events e WHERE e.creator_id = ?
            ORDER BY e.created_at DESC
        """, [user_id]).fetchall()

        # 我申请的
        joined = db.execute("""
            SELECT e.*, ep.status as role FROM events e
            JOIN event_participants ep ON e.id = ep.event_id
            WHERE ep.user_id = ?
            ORDER BY ep.created_at DESC
        """, [user_id]).fetchall()

        result = []
        for r in created:
            result.append({
                "id": r["id"], "title": r["title"], "location": r["location"],
                "event_date": r["event_date"], "event_duration": r["event_duration"],
                "category": r["category"], "role": "发起的"
            })
        for r in joined:
            role_label = {"pending": "待审批", "accepted": "已通过", "rejected": "已拒绝"}.get(r["role"], r["role"])
            result.append({
                "id": r["id"], "title": r["title"], "location": r["location"],
                "event_date": r["event_date"], "event_duration": r["event_duration"],
                "category": r["category"], "role": role_label
            })
        return ok(result)
    finally:
        db.close()


@router.post("/users/me/card")
def save_card(req: CardRequest, authorization: str | None = Header(None)):
    """保存人格卡片"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        db.execute(
            "UPDATE users SET bio=?, card_image=?, avatar=? WHERE id=?",
            [req.bio, req.card_image, req.avatar, user_id]
        )
        db.commit()
        return ok(None)
    except Exception as e:
        db.rollback()
        return error(f"保存失败: {str(e)}")
    finally:
        db.close()


@router.post("/chat")
def chat(req: ChatRequest, authorization: str | None = Header(None)):
    """AI 对话：返回 AI 回复 + 隐性量表"""
    user_id = get_current_user_id(authorization)
    result = chat_with_ai(req.message)

    if not result:
        return error("AI 服务暂时不可用")

    traits = result.get("traits", {})
    if traits:
        db = get_db()
        try:
            db.execute(
                """UPDATE users SET empathy=?, agency=?, energy=?,
                   sensitivity=?, openness=? WHERE id=?""",
                [traits.get("empathy", 50), traits.get("agency", 50),
                 traits.get("energy", 50), traits.get("sensitivity", 50),
                 traits.get("openness", 50), user_id]
            )
            db.commit()
        finally:
            db.close()

    return ok({
        "reply": result.get("reply", ""),
        "traits": traits
    })