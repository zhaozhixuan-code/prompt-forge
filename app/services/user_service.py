import hashlib
from dataclasses import dataclass

from redis import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import BusinessException, ErrorCode, throw_if
from app.core.security import create_user_session
from app.repositories.user_repository import create_user, get_user_by_account
from app.schemas.user import UserLoginRequest, UserRegisterRequest, UserVO

SALT = "zhaozhixuan"


@dataclass(frozen=True)
class UserLoginResult:
    # 登录接口既要返回用户 VO，也要把 session_id 交给路由层写入 Cookie。
    user: UserVO
    session_id: str


def encrypt_password(password: str) -> str:
    # 兼容原 Java 后端 getEncryptPassword：md5(SALT + userPassword)。
    # 后续如切换 bcrypt，需要兼顾旧用户密码迁移。
    return hashlib.md5(f"{SALT}{password}".encode("utf-8")).hexdigest()


def register_user(db: Session, request: UserRegisterRequest) -> int:
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
