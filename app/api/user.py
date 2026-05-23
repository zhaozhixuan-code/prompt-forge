from fastapi import APIRouter, Depends, Response
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.response import BaseResponse
from app.db.redis import get_redis_client
from app.db.session import get_db
from app.schemas.user import UserLoginRequest, UserRegisterRequest, UserVO
from app.services.user_service import login_user, register_user

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/register", response_model=BaseResponse[int])
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> BaseResponse[int]:
    """
    用户注册。

    Args:
        request: 用户注册请求，包含账号、密码和确认密码。
        db: 数据库会话，用于查询账号和创建用户。

    Returns:
        注册成功后的用户 ID。
    """
    # 路由层只负责参数接收、依赖注入和统一响应包装，注册规则放到 service 层。
    user_id = register_user(db, request)
    return BaseResponse.ok(user_id)


@router.post("/login", response_model=BaseResponse[UserVO])
def login(
    request: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis_client),
) -> BaseResponse[UserVO]:
    """
    用户登录。

    Args:
        request: 用户登录请求，包含账号和密码。
        response: HTTP 响应对象，用于写入登录 Cookie。
        db: 数据库会话，用于查询用户信息。
        redis_client: Redis 客户端，用于保存登录 Session。

    Returns:
        登录成功后的用户信息。
    """
    # 登录成功后 service 会生成 Redis Session，并把随机 session_id 返回给路由层。
    result = login_user(db, redis_client, request)
    settings = get_settings()

    # Cookie 只保存 session_id，真实登录用户信息保存在 Redis，前端无需感知内部结构。
    # path="/" 保证后续 /api 下的接口都会自动携带该 Cookie。
    response.set_cookie(
        key=settings.session_cookie_name,
        value=result.session_id,
        max_age=settings.session_expire_seconds,
        httponly=settings.session_cookie_httponly,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    return BaseResponse.ok(result.user)
