from fastapi import APIRouter, Header
from database import get_db
from models import MessageSendRequest, ok, error
from routers.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=["messages"])


@router.post("/messages")
def send_message(req: MessageSendRequest, authorization: str | None = Header(None)):
    """发送消息"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        # 检查接收者是否存在
        receiver = db.execute("SELECT id FROM users WHERE id=?", [req.to_user_id]).fetchone()
        if not receiver:
            return error("接收者不存在")
        if req.to_user_id == user_id:
            return error("不能给自己发消息")

        cursor = db.execute(
            """INSERT INTO messages (from_user_id, to_user_id, content, context_type, context_id)
               VALUES (?, ?, ?, ?, ?)""",
            [user_id, req.to_user_id, req.content, req.context_type, req.context_id]
        )
        db.commit()
        return ok({"message_id": cursor.lastrowid})
    except Exception as e:
        db.rollback()
        return error(f"发送失败: {str(e)}")
    finally:
        db.close()


@router.get("/messages")
def list_messages(authorization: str | None = Header(None)):
    """消息列表：按会话聚合，返回每个会话的最新一条消息"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        # 找出所有与当前用户有关的会话对方
        rows = db.execute("""
            SELECT
                CASE WHEN m.from_user_id = ? THEN m.to_user_id ELSE m.from_user_id END as partner_id,
                u.nickname as partner_nickname,
                u.avatar as partner_avatar,
                m.content as last_message,
                m.context_type,
                m.is_read,
                m.created_at,
                m.from_user_id
            FROM messages m
            JOIN users u ON u.id = CASE WHEN m.from_user_id = ? THEN m.to_user_id ELSE m.from_user_id END
            WHERE m.id IN (
                SELECT MAX(id) FROM messages
                WHERE from_user_id = ? OR to_user_id = ?
                GROUP BY CASE WHEN from_user_id = ? THEN to_user_id ELSE from_user_id END
            )
            ORDER BY m.created_at DESC
        """, [user_id, user_id, user_id, user_id, user_id]).fetchall()

        conversations = []
        for row in rows:
            conversations.append({
                "partner_id": row["partner_id"],
                "partner_nickname": row["partner_nickname"],
                "partner_avatar": row["partner_avatar"],
                "last_message": row["last_message"],
                "context_type": row["context_type"],
                "is_read": bool(row["is_read"]),
                "is_from_me": row["from_user_id"] == user_id,
                "created_at": row["created_at"]
            })

        return ok(conversations)
    finally:
        db.close()


@router.get("/messages/{partner_id}")
def get_chat_history(partner_id: int, authorization: str | None = Header(None)):
    """与某人的聊天记录"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        rows = db.execute("""
            SELECT m.*, u.nickname as from_nickname, u.avatar as from_avatar
            FROM messages m
            JOIN users u ON m.from_user_id = u.id
            WHERE (m.from_user_id = ? AND m.to_user_id = ?)
               OR (m.from_user_id = ? AND m.to_user_id = ?)
            ORDER BY m.created_at ASC
        """, [user_id, partner_id, partner_id, user_id]).fetchall()

        # 标记对方发来的消息为已读
        db.execute(
            "UPDATE messages SET is_read=1 WHERE from_user_id=? AND to_user_id=? AND is_read=0",
            [partner_id, user_id]
        )
        db.commit()

        messages = []
        for row in rows:
            messages.append({
                "id": row["id"],
                "from_user_id": row["from_user_id"],
                "from_nickname": row["from_nickname"],
                "from_avatar": row["from_avatar"],
                "to_user_id": row["to_user_id"],
                "content": row["content"],
                "context_type": row["context_type"],
                "is_read": bool(row["is_read"]),
                "is_from_me": row["from_user_id"] == user_id,
                "created_at": row["created_at"]
            })

        return ok(messages)
    finally:
        db.close()