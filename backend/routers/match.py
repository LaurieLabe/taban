from fastapi import APIRouter, Header
from models import ok
from routers.auth import get_current_user_id
from services.match_service import get_recommended_persons

router = APIRouter(prefix="/api", tags=["match"])


@router.get("/match/persons")
def list_persons(authorization: str | None = Header(None)):
    """推荐的人列表，按匹配度降序"""
    user_id = get_current_user_id(authorization)
    persons = get_recommended_persons(user_id)
    return ok(persons)