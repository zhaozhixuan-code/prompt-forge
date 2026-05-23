from fastapi import Depends, Request
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import BusinessException, ErrorCode
from app.core.security import get_user_id_from_session
from app.db.redis import get_redis_client
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import get_user_by_id


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis_client),
) -> User:
    """从 Cookie Session 中解析当前登录用户。"""
    settings = get_settings()
    session_id = request.cookies.get(settings.session_cookie_name)
    user_id = get_user_id_from_session(redis_client, session_id)
    if user_id is None:
        raise BusinessException(ErrorCode.NOT_LOGIN_ERROR)

    # Session 只保存 userId，真实用户信息每次从数据库读取，避免角色等信息在 Redis 中长期过期。
    user = get_user_by_id(db, user_id)
    if user is None:
        raise BusinessException(ErrorCode.NOT_LOGIN_ERROR)
    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """校验当前登录用户是否为管理员。"""
    if current_user.userRole != "admin":
        raise BusinessException(ErrorCode.NO_AUTH_ERROR)
    return current_user
