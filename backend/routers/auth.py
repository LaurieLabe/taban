import hashlib
import secrets
from fastapi import APIRouter, HTTPException
from database import get_db
from models import RegisterRequest, LoginRequest, ok, error

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 简单内存 token 存储: {token: user_id}
tokens = {}


def hash_password(password: str) -> str:
    salt = "taban_salt_2026"
    return hashlib.sha256((password + salt).encode()).hexdigest()


def generate_token() -> str:
    return secrets.token_hex(32)


@router.post("/register")
def register(req: RegisterRequest):
    """注册：昵称 + 密码"""
    if not req.nickname or not req.password:
        return error("昵称和密码不能为空")
    if len(req.nickname) < 2:
        return error("昵称至少2个字符")
    if len(req.password) < 4:
        return error("密码至少4个字符")

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (nickname, password_hash, birth_date) VALUES (?, ?, ?)",
            [req.nickname, hash_password(req.password), req.birth_date]
        )
        db.commit()
        user_id = cursor.lastrowid
        return ok({"user_id": user_id})
    except Exception as e:
        db.rollback()
        # 昵称重复
        if "UNIQUE" in str(e).upper():
            return error("该昵称已被注册")
        return error(f"注册失败: {str(e)}")
    finally:
        db.close()


@router.post("/login")
def login(req: LoginRequest):
    """登录：昵称 + 密码，返回 token"""
    db = get_db()
    try:
        user = db.execute(
            "SELECT id, password_hash FROM users WHERE nickname = ?",
            [req.nickname]
        ).fetchone()

        if not user:
            return error("用户不存在")

        if user["password_hash"] != hash_password(req.password):
            return error("密码错误")

        token = generate_token()
        tokens[token] = user["id"]
        return ok({"token": token, "user_id": user["id"]})
    finally:
        db.close()


def get_current_user_id(authorization: str | None) -> int:
    """从 Authorization header 提取当前用户 ID"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    user_id = tokens.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    return user_id