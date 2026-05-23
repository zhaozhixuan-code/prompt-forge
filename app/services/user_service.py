import hashlib
from dataclasses import dataclass

from redis import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import BusinessException, ErrorCode, throw_if
from app.core.security import create_user_session, delete_user_session
from app.repositories.user_repository import (
    create_admin_user,
    create_user,
    get_user_by_account,
    get_user_by_id,
    list_users_by_page,
    soft_delete_user_by_id,
    update_user_by_id,
)
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

SALT = "zhaozhixuan"
DEFAULT_ADMIN_CREATE_PASSWORD = "12345678"
USER_ROLES = {"user", "admin"}


@dataclass(frozen=True)
class UserLoginResult:
    # 登录接口既要返回用户 VO，也要把 session_id 交给路由层写入 Cookie。
    user: UserVO
    session_id: str


def encrypt_password(password: str) -> str:
    """
    加密用户密码。

    Args:
        password: 用户提交的明文密码。

    Returns:
        兼容原 Java 后端的 MD5 加密密码。
    """
    # 兼容原 Java 后端 getEncryptPassword：md5(SALT + userPassword)。
    # 后续如切换 bcrypt，需要兼顾旧用户密码迁移。
    return hashlib.md5(f"{SALT}{password}".encode("utf-8")).hexdigest()


def register_user(db: Session, request: UserRegisterRequest) -> int:
    """
    用户注册。

    Args:
        db: 数据库会话，用于账号查重和创建用户。
        request: 用户注册请求，包含账号、密码和确认密码。

    Returns:
        注册成功后的用户 ID。

    Raises:
        BusinessException: 当账号格式不合法、密码不合法、两次密码不一致或账号已存在时抛出。
    """
    # 统一在业务层处理注册校验，避免路由层掺入业务规则。
    user_account = request.userAccount.strip()
    user_password = request.userPassword
    check_password = request.checkPassword

    # 基础参数校验需要尽量保持和原 Java 后端一致，减少前端兼容成本。
    throw_if(len(user_account) < 4, ErrorCode.PARAMS_ERROR, "账号长度不能小于 4 位")
    throw_if(len(user_password) < 8, ErrorCode.PARAMS_ERROR, "密码长度不能小于 8 位")
    throw_if(user_password != check_password, ErrorCode.PARAMS_ERROR, "两次输入的密码不一致")

    # 先做显式查重，给前端返回明确的业务错误。
    existing_user = get_user_by_account(db, user_account)
    throw_if(existing_user is not None, ErrorCode.PARAMS_ERROR, "账号已存在")

    try:
        user = create_user(db, user_account, encrypt_password(user_password))
    except IntegrityError as exc:
        # 并发注册同一账号时，数据库唯一索引仍可能抛错，这里转换为业务异常。
        db.rollback()
        raise BusinessException(ErrorCode.PARAMS_ERROR, "账号已存在") from exc

    return user.id


def login_user(
    db: Session,
    redis_client: Redis,
    request: UserLoginRequest,
) -> UserLoginResult:
    """
    用户登录。

    Args:
        db: 数据库会话，用于按账号查询用户。
        redis_client: Redis 客户端，用于写入登录 Session。
        request: 用户登录请求，包含账号和密码。

    Returns:
        登录用户信息和需要写入 Cookie 的 session_id。

    Raises:
        BusinessException: 当账号密码格式不合法、用户不存在或密码错误时抛出。
    """
    # 账号允许前后有空格，进入业务逻辑前统一裁剪，和注册逻辑保持一致。
    user_account = request.userAccount.strip()
    user_password = request.userPassword

    # 登录参数规则沿用注册阶段的最低长度校验，避免明显无效请求继续查库。
    throw_if(len(user_account) < 4, ErrorCode.PARAMS_ERROR, "账号长度不能小于 4 位")
    throw_if(len(user_password) < 8, ErrorCode.PARAMS_ERROR, "密码长度不能小于 8 位")

    # 密码加密方式必须兼容旧 Java 后端，否则历史用户无法登录。
    user = get_user_by_account(db, user_account)
    throw_if(
        user is None or user.userPassword != encrypt_password(user_password),
        ErrorCode.PARAMS_ERROR,
        "用户不存在或密码错误",
    )

    # Python 端不复刻 Spring Session 的 Redis Hash 结构，只保证 Cookie + Redis 登录态行为一致。
    settings = get_settings()
    session_id = create_user_session(
        redis_client,
        user.id,
        settings.session_expire_seconds,
    )

    # 对外仍返回前端熟悉的 UserVO，不暴露 userPassword、isDelete 等内部字段。
    return UserLoginResult(
        user=UserVO.model_validate(user),
        session_id=session_id,
    )


def logout_user(redis_client: Redis, session_id: str | None) -> bool:
    """
    用户注销。

    Args:
        redis_client: Redis 客户端，用于删除登录 Session。
        session_id: 当前请求 Cookie 中携带的登录 Session ID。

    Returns:
        退出登录是否成功。
    """
    # 和 Java 的 request.getSession().removeAttribute(...) 类似，
    # Python 端删除 Redis Session 后，后续请求就无法再通过该 Cookie 获取登录用户。
    delete_user_session(redis_client, session_id)
    return True


def add_user_by_admin(db: Session, request: UserAddRequest) -> int:
    """管理员创建用户。"""
    user_account = request.userAccount.strip()
    user_password = request.userPassword or DEFAULT_ADMIN_CREATE_PASSWORD
    user_role = request.userRole.strip()

    # 管理端创建也复用用户账号、密码和角色的基础约束，避免写入前端无法处理的数据。
    throw_if(len(user_account) < 4, ErrorCode.PARAMS_ERROR, "user account is too short")
    throw_if(len(user_password) < 8, ErrorCode.PARAMS_ERROR, "password is too short")
    throw_if(user_role not in USER_ROLES, ErrorCode.PARAMS_ERROR, "invalid user role")
    throw_if(
        get_user_by_account(db, user_account) is not None,
        ErrorCode.PARAMS_ERROR,
        "user account already exists",
    )

    try:
        user = create_admin_user(
            db,
            user_account=user_account,
            user_password=encrypt_password(user_password),
            user_name=request.userName,
            user_avatar=request.userAvatar,
            user_profile=request.userProfile,
            user_role=user_role,
        )
    except IntegrityError as exc:
        db.rollback()
        raise BusinessException(ErrorCode.PARAMS_ERROR, "user account already exists") from exc

    return user.id


def get_user_by_admin(db: Session, user_id: int) -> UserAdminVO:
    """管理员按 ID 获取用户详情。"""
    throw_if(user_id <= 0, ErrorCode.PARAMS_ERROR, "invalid user id")
    user = get_user_by_id(db, user_id)
    throw_if(user is None, ErrorCode.NOT_FOUND_ERROR, "user not found")
    return UserAdminVO.model_validate(user)


def get_user_vo_by_id(db: Session, user_id: int) -> UserVO:
    """按 ID 获取安全的用户包装类。"""
    throw_if(user_id <= 0, ErrorCode.PARAMS_ERROR, "invalid user id")
    user = get_user_by_id(db, user_id)
    throw_if(user is None, ErrorCode.NOT_FOUND_ERROR, "user not found")
    return UserVO.model_validate(user)


def delete_user_by_admin(db: Session, request: UserDeleteRequest) -> bool:
    """管理员逻辑删除用户。"""
    throw_if(request.id <= 0, ErrorCode.PARAMS_ERROR, "invalid user id")
    user = get_user_by_id(db, request.id)
    throw_if(user is None, ErrorCode.NOT_FOUND_ERROR, "user not found")
    soft_delete_user_by_id(db, user)
    return True


def update_user_by_admin(db: Session, request: UserUpdateRequest) -> bool:
    """管理员更新用户资料。"""
    throw_if(request.id <= 0, ErrorCode.PARAMS_ERROR, "invalid user id")
    user = get_user_by_id(db, request.id)
    throw_if(user is None, ErrorCode.NOT_FOUND_ERROR, "user not found")

    update_values: dict[str, object] = {}
    if request.userAccount is not None:
        # 修改账号时需要排除当前用户自身，否则保持原账号也会被误判为重复。
        user_account = request.userAccount.strip()
        throw_if(len(user_account) < 4, ErrorCode.PARAMS_ERROR, "user account is too short")
        existing_user = get_user_by_account(db, user_account)
        throw_if(
            existing_user is not None and existing_user.id != request.id,
            ErrorCode.PARAMS_ERROR,
            "user account already exists",
        )
        update_values["userAccount"] = user_account
    if request.userPassword is not None:
        # 数据库只保存加密后的密码，避免管理端更新时绕过统一加密规则。
        throw_if(len(request.userPassword) < 8, ErrorCode.PARAMS_ERROR, "password is too short")
        update_values["userPassword"] = encrypt_password(request.userPassword)
    if request.userName is not None:
        update_values["userName"] = request.userName
    if request.userAvatar is not None:
        update_values["userAvatar"] = request.userAvatar
    if request.userProfile is not None:
        update_values["userProfile"] = request.userProfile
    if request.userRole is not None:
        user_role = request.userRole.strip()
        throw_if(user_role not in USER_ROLES, ErrorCode.PARAMS_ERROR, "invalid user role")
        update_values["userRole"] = user_role

    if not update_values:
        # 空更新请求视为成功，和多数 Java 管理端接口行为保持一致。
        return True

    try:
        update_user_by_id(db, user, update_values)
    except IntegrityError as exc:
        db.rollback()
        raise BusinessException(ErrorCode.PARAMS_ERROR, "user account already exists") from exc
    return True


def list_user_vo_by_page(db: Session, request: UserQueryRequest) -> UserPageVO:
    """分页获取安全的用户包装类列表。"""
    records, total = list_users_by_page(db, request)
    pages = (total + request.pageSize - 1) // request.pageSize
    return UserPageVO(
        records=[UserVO.model_validate(user) for user in records],
        total=total,
        size=request.pageSize,
        current=request.current,
        pages=pages,
    )
