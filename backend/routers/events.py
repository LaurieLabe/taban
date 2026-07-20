from fastapi import APIRouter, Header, Query
from database import get_db
from models import EventCreateRequest, ok, error
from routers.auth import get_current_user_id
from services.match_service import get_recommended_events

router = APIRouter(prefix="/api", tags=["events"])


@router.post("/events")
def create_event(req: EventCreateRequest, authorization: str | None = Header(None)):
    """发布事件"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        cursor = db.execute(
            """INSERT INTO events (creator_id, title, description, location, event_date, event_duration, max_participants, category)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [user_id, req.title, req.description, req.location, req.event_date, req.event_duration,
             req.max_participants, req.category]
        )
        db.commit()
        return ok({"event_id": cursor.lastrowid})
    except Exception as e:
        db.rollback()
        return error(f"发布失败: {str(e)}")
    finally:
        db.close()


@router.get("/events")
def list_events(
    authorization: str | None = Header(None),
    sort: str = Query("recommend")
):
    """事件列表，支持排序：recommend / distance / match"""
    user_id = get_current_user_id(authorization)
    events = get_recommended_events(user_id, sort)
    return ok(events)


@router.get("/events/{event_id}")
def get_event(event_id: int, authorization: str | None = Header(None)):
    """事件详情"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        row = db.execute("""
            SELECT e.*, u.nickname as creator_nickname, u.avatar as creator_avatar,
                   u.bio as creator_bio, u.personality, u.interests, u.topics,
                   u.consumption, u.life_rhythm, u.card_image
            FROM events e
            JOIN users u ON e.creator_id = u.id
            WHERE e.id = ?
        """, [event_id]).fetchone()

        if not row:
            return error("事件不存在")

        return ok({
            "id": row["id"],
            "creator_id": row["creator_id"],
            "creator_nickname": row["creator_nickname"],
            "creator_avatar": row["creator_avatar"],
            "creator_bio": row["creator_bio"],
            "creator_card_image": row["card_image"],
            "creator_tags": {
                "personality": row["personality"],
                "interests": row["interests"],
                "topics": row["topics"],
                "consumption": row["consumption"],
                "life_rhythm": row["life_rhythm"]
            },
            "title": row["title"],
            "description": row["description"],
            "location": row["location"],
            "event_date": row["event_date"],
            "event_duration": row["event_duration"],
            "max_participants": row["max_participants"],
            "category": row["category"],
            "created_at": row["created_at"]
        })
    finally:
        db.close()


@router.post("/events/{event_id}/join")
def join_event(event_id: int, authorization: str | None = Header(None)):
    """申请加入事件"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        event = db.execute("SELECT id, creator_id FROM events WHERE id=?", [event_id]).fetchone()
        if not event:
            return error("事件不存在")
        if event["creator_id"] == user_id:
            return error("不能加入自己发布的事件")

        existing = db.execute(
            "SELECT id FROM event_participants WHERE event_id=? AND user_id=?",
            [event_id, user_id]
        ).fetchone()
        if existing:
            return error("已经申请过了")

        db.execute(
            "INSERT INTO event_participants (event_id, user_id) VALUES (?, ?)",
            [event_id, user_id]
        )
        db.commit()
        return ok(None)
    except Exception as e:
        db.rollback()
        return error(f"申请失败: {str(e)}")
    finally:
        db.close()


# ── 审批相关 ──

@router.get("/events/{event_id}/applicants")
def list_applicants(event_id: int, authorization: str | None = Header(None)):
    """查看事件申请者列表（仅发起人可查看）"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        event = db.execute("SELECT creator_id FROM events WHERE id=?", [event_id]).fetchone()
        if not event:
            return error("事件不存在")
        if event["creator_id"] != user_id:
            return error("仅发起人可查看申请列表")

        rows = db.execute("""
            SELECT ep.*, u.nickname, u.avatar, u.bio, u.personality, u.interests
            FROM event_participants ep
            JOIN users u ON ep.user_id = u.id
            WHERE ep.event_id = ?
            ORDER BY ep.created_at DESC
        """, [event_id]).fetchall()

        applicants = []
        for r in rows:
            applicants.append({
                "id": r["id"],
                "user_id": r["user_id"],
                "nickname": r["nickname"],
                "avatar": r["avatar"],
                "bio": r["bio"],
                "personality": r["personality"],
                "interests": r["interests"],
                "status": r["status"],
                "created_at": r["created_at"]
            })
        return ok(applicants)
    finally:
        db.close()


@router.post("/events/{event_id}/applicants/{applicant_user_id}/accept")
def accept_applicant(event_id: int, applicant_user_id: int, authorization: str | None = Header(None)):
    """通过申请"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        event = db.execute("SELECT creator_id FROM events WHERE id=?", [event_id]).fetchone()
        if not event or event["creator_id"] != user_id:
            return error("无权限")
        db.execute(
            "UPDATE event_participants SET status='accepted' WHERE event_id=? AND user_id=?",
            [event_id, applicant_user_id]
        )
        db.commit()
        return ok(None)
    except Exception as e:
        db.rollback()
        return error(f"操作失败: {str(e)}")
    finally:
        db.close()


@router.post("/events/{event_id}/applicants/{applicant_user_id}/reject")
def reject_applicant(event_id: int, applicant_user_id: int, authorization: str | None = Header(None)):
    """拒绝申请"""
    user_id = get_current_user_id(authorization)
    db = get_db()
    try:
        event = db.execute("SELECT creator_id FROM events WHERE id=?", [event_id]).fetchone()
        if not event or event["creator_id"] != user_id:
            return error("无权限")
        db.execute(
            "UPDATE event_participants SET status='rejected' WHERE event_id=? AND user_id=?",
            [event_id, applicant_user_id]
        )
        db.commit()
        return ok(None)
    except Exception as e:
        db.rollback()
        return error(f"操作失败: {str(e)}")
    finally:
        db.close()