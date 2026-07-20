import json
import math
from database import get_db


def calculate_match_score(user_a: dict, user_b: dict) -> float:
    """
    计算两个用户的匹配得分。
    显性维度 60% + 隐性维度 40%
    """
    explicit_score = _calculate_explicit_match(user_a, user_b)
    implicit_score = _calculate_implicit_match(user_a, user_b)
    return round(explicit_score * 0.6 + implicit_score * 0.4, 2)


def _calculate_explicit_match(a: dict, b: dict) -> float:
    """显性维度匹配（人格气质、兴趣活动、聊天话题、消费观、生活节奏）"""
    scores = []

    # 1. 人格气质：相同=1，不同=0
    if a.get("personality") and b.get("personality"):
        scores.append(1.0 if a["personality"] == b["personality"] else 0.0)

    # 2. 兴趣活动：Jaccard 相似度
    scores.append(_jaccard(a.get("interests"), b.get("interests")))

    # 3. 聊天话题：Jaccard 相似度
    scores.append(_jaccard(a.get("topics"), b.get("topics")))

    # 4. 消费观：相同=1，不同=0
    if a.get("consumption") and b.get("consumption"):
        scores.append(1.0 if a["consumption"] == b["consumption"] else 0.0)

    # 5. 生活节奏：相同=1，不同=0
    if a.get("life_rhythm") and b.get("life_rhythm"):
        scores.append(1.0 if a["life_rhythm"] == b["life_rhythm"] else 0.0)

    if not scores:
        return 0.5
    return sum(scores) / len(scores)


def _calculate_implicit_match(a: dict, b: dict) -> float:
    """隐性维度匹配：5个维度的余弦相似度"""
    dims = ["empathy", "agency", "energy", "sensitivity", "openness"]
    vec_a = [a.get(d, 50) or 50 for d in dims]
    vec_b = [b.get(d, 50) or 50 for d in dims]

    dot = sum(va * vb for va, vb in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(v * v for v in vec_a))
    norm_b = math.sqrt(sum(v * v for v in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.5

    cosine = dot / (norm_a * norm_b)
    # 余弦相似度范围 [-1, 1]，映射到 [0, 1]
    return (cosine + 1) / 2


def _jaccard(a_str: str | None, b_str: str | None) -> float:
    """计算两个 JSON 数组字符串的 Jaccard 相似度"""
    try:
        set_a = set(json.loads(a_str)) if a_str else set()
        set_b = set(json.loads(b_str)) if b_str else set()
    except (json.JSONDecodeError, TypeError):
        return 0.5

    if not set_a and not set_b:
        return 0.5
    if not set_a or not set_b:
        return 0.0

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def get_recommended_persons(user_id: int, limit: int = 20) -> list:
    """返回按匹配度降序排列的推荐用户列表"""
    db = get_db()
    try:
        # 获取当前用户
        current = db.execute("SELECT * FROM users WHERE id=?", [user_id]).fetchone()
        if not current:
            return []

        current_dict = dict(current)

        # 获取所有其他用户
        others = db.execute("SELECT * FROM users WHERE id != ?", [user_id]).fetchall()

        # 计算匹配度
        scored = []
        for other in others:
            other_dict = dict(other)
            score = calculate_match_score(current_dict, other_dict)
            scored.append({
                "id": other_dict["id"],
                "nickname": other_dict["nickname"],
                "avatar": other_dict["avatar"],
                "bio": other_dict["bio"],
                "card_image": other_dict["card_image"],
                "personality": other_dict["personality"],
                "interests": other_dict["interests"],
                "topics": other_dict["topics"],
                "consumption": other_dict["consumption"],
                "life_rhythm": other_dict["life_rhythm"],
                "birth_date": other_dict.get("birth_date", ""),
                "match_score": score
            })

        # 按匹配度降序
        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored[:limit]
    finally:
        db.close()


def get_recommended_events(user_id: int, sort_by: str = "recommend") -> list:
    """返回按指定排序方式的事件列表"""
    db = get_db()
    try:
        current = db.execute("SELECT * FROM users WHERE id=?", [user_id]).fetchone()
        if not current:
            return []

        events = db.execute("""
            SELECT e.*, u.nickname as creator_nickname, u.avatar as creator_avatar,
                   u.personality, u.interests, u.topics, u.consumption, u.life_rhythm,
                   u.empathy, u.agency, u.energy, u.sensitivity, u.openness
            FROM events e
            JOIN users u ON e.creator_id = u.id
        """).fetchall()

        current_dict = dict(current)
        result = []

        for e in events:
            creator_dict = {
                "personality": e["personality"],
                "interests": e["interests"],
                "topics": e["topics"],
                "consumption": e["consumption"],
                "life_rhythm": e["life_rhythm"],
                "empathy": e["empathy"],
                "agency": e["agency"],
                "energy": e["energy"],
                "sensitivity": e["sensitivity"],
                "openness": e["openness"]
            }
            match_score = calculate_match_score(current_dict, creator_dict)

            result.append({
                "id": e["id"],
                "creator_id": e["creator_id"],
                "creator_nickname": e["creator_nickname"],
                "creator_avatar": e["creator_avatar"],
                "title": e["title"],
                "description": e["description"],
                "location": e["location"],
                "event_date": e["event_date"], "event_duration": e["event_duration"],
                "max_participants": e["max_participants"],
                "category": e["category"],
                "match_score": match_score,
                "created_at": e["created_at"]
            })

        if sort_by == "recommend":
            result.sort(key=lambda x: x["match_score"], reverse=True)
        elif sort_by == "distance":
            # 暂无真实距离，按创建时间
            result.sort(key=lambda x: x["created_at"], reverse=True)
        elif sort_by == "match":
            result.sort(key=lambda x: x["match_score"], reverse=True)

        return result
    finally:
        db.close()