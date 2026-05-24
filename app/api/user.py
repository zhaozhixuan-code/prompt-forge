from fastapi import APIRouter, Depends, Request, Response
from redis import Redis
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, require_login
from app.core.config import get_settings
from app.core.response import BaseResponse
from app.db.redis import get_redis_client
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserAddRequest,
    UserAdminVO,
    UserDeleteRequest,
    UserLoginRequest,
    UserPageVO,
    UserQueryRequest,
    UserRegisterRequest,
    UserUpdateRequest,
    UserVO,
)
from app.services.user_service import (
    add_user_by_admin,
    delete_user_by_admin,
    get_user_by_admin,
    get_user_vo_by_id,
    list_user_vo_by_page,
    login_user,
    logout_user,
    register_user,
    update_user_by_admin,
)

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


@router.post("/logout", response_model=BaseResponse[bool])
def logout(
    request: Request,
    response: Response,
    redis_client: Redis = Depends(get_redis_client),
) -> BaseResponse[bool]:
    """
    用户注销。

    Args:
        request: HTTP 请求对象，用于读取登录 Cookie。
        response: HTTP 响应对象，用于清理浏览器登录 Cookie。
        redis_client: Redis 客户端，用于删除登录 Session。

    Returns:
        是否退出登录成功。
    """
    settings = get_settings()
    session_id = request.cookies.get(settings.session_cookie_name)
    result = logout_user(redis_client, session_id)

    # 删除浏览器端 Cookie；Redis Session 删除后，服务端登录态也随之失效。
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=settings.session_cookie_httponly,
        samesite=settings.session_cookie_samesite,
    )
    return BaseResponse.ok(result)


@router.get("/get/login", response_model=BaseResponse[UserVO])
def get_login_user(
    current_user: User = Depends(require_login),
) -> BaseResponse[UserVO]:
    """
    获取当前登录用户。

    Args:
        current_user: 已通过登录态校验的当前用户。

    Returns:
        当前登录用户信息。
    """
    return BaseResponse.ok(UserVO.model_validate(current_user))


@router.post("/add", response_model=BaseResponse[int])
def add_user(
    request: UserAddRequest,
    db: Session = Depends(get_db),
    current_admin_user: User = Depends(get_current_admin_user),
) -> BaseResponse[int]:
    """管理员创建用户。"""
    _ = current_admin_user
    user_id = add_user_by_admin(db, request)
    return BaseResponse.ok(user_id)


@router.get("/get", response_model=BaseResponse[UserAdminVO])
def get_user(
    id: int,
    db: Session = Depends(get_db),
    current_admin_user: User = Depends(get_current_admin_user),
) -> BaseResponse[UserAdminVO]:
    """管理员按 ID 获取用户详情。"""
    _ = current_admin_user
    user = get_user_by_admin(db, id)
    return BaseResponse.ok(user)


@router.get("/get/vo", response_model=BaseResponse[UserVO])
def get_user_vo(
    id: int,
    db: Session = Depends(get_db),
) -> BaseResponse[UserVO]:
    """按 ID 获取用户包装类；该接口允许非管理员访问。"""
    user = get_user_vo_by_id(db, id)
    return BaseResponse.ok(user)


@router.post("/delete", response_model=BaseResponse[bool])
def delete_user(
    request: UserDeleteRequest,
    db: Session = Depends(get_db),
    current_admin_user: User = Depends(get_current_admin_user),
) -> BaseResponse[bool]:
    """管理员按 ID 删除用户。"""
    _ = current_admin_user
    result = delete_user_by_admin(db, request)
    return BaseResponse.ok(result)


@router.post("/update", response_model=BaseResponse[bool])
def update_user(
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_admin_user: User = Depends(get_current_admin_user),
) -> BaseResponse[bool]:
    """管理员更新用户资料。"""
    _ = current_admin_user
    result = update_user_by_admin(db, request)
    return BaseResponse.ok(result)


@router.post("/list/page/vo", response_model=BaseResponse[UserPageVO])
def list_user_vo(
    request: UserQueryRequest,
    db: Session = Depends(get_db),
    current_admin_user: User = Depends(get_current_admin_user),
) -> BaseResponse[UserPageVO]:
    """管理员分页获取用户包装类列表。"""
    _ = current_admin_user
    page = list_user_vo_by_page(db, request)
    return BaseResponse.ok(page)
