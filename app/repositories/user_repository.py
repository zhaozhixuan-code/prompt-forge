from collections.abc import Mapping
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserQueryRequest


def get_user_by_account(db: Session, user_account: str) -> User | None:
    # 注册前按账号查重，并过滤逻辑删除的数据。
    stmt = select(User).where(
        User.userAccount == user_account,
        User.isDelete == 0,
    )
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    # 所有按 ID 查询默认过滤逻辑删除数据，避免管理接口误操作已删除用户。
    stmt = select(User).where(
        User.id == user_id,
        User.isDelete == 0,
    )
    return db.execute(stmt).scalar_one_or_none()


def create_user(db: Session, user_account: str, user_password: str) -> User:
    # 只负责落库；账号规则、密码校验和加密由 service 层完成。
    user = User(
        userAccount=user_account,
        userPassword=user_password,
        userName=user_account,
        userRole="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_admin_user(
    db: Session,
    *,
    user_account: str,
    user_password: str,
    user_name: str | None,
    user_avatar: str | None,
    user_profile: str | None,
    user_role: str,
) -> User:
    # 管理员创建用户允许指定资料和角色，密码加密与参数校验由 service 层负责。
    user = User(
        userAccount=user_account,
        userPassword=user_password,
        userName=user_name or user_account,
        userAvatar=user_avatar,
        userProfile=user_profile,
        userRole=user_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_by_id(db: Session, user: User, values: Mapping[str, Any]) -> User:
    # 只更新 service 层明确传入的字段，避免 None 请求值误覆盖已有资料。
    for field, value in values.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def soft_delete_user_by_id(db: Session, user: User) -> None:
    # 对齐 user 表 isDelete 字段，删除用户时只做逻辑删除。
    user.isDelete = 1
    db.add(user)
    db.commit()


def _build_user_query(request: UserQueryRequest):
    # 分页查询支持精确账号/角色查询，以及昵称、简介的模糊搜索。
    stmt = select(User).where(User.isDelete == 0)

    if request.id is not None:
        stmt = stmt.where(User.id == request.id)
    if request.userAccount:
        stmt = stmt.where(User.userAccount == request.userAccount.strip())
    if request.userName:
        stmt = stmt.where(User.userName.like(f"%{request.userName.strip()}%"))
    if request.userProfile:
        stmt = stmt.where(User.userProfile.like(f"%{request.userProfile.strip()}%"))
    if request.userRole:
        stmt = stmt.where(User.userRole == request.userRole.strip())

    return stmt


def list_users_by_page(db: Session, request: UserQueryRequest) -> tuple[list[User], int]:
    # total 和 records 分开查询，返回结构由 service 层封装成前端兼容的 Page VO。
    base_stmt = _build_user_query(request)
    total_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = db.execute(total_stmt).scalar_one()

    offset = (request.current - 1) * request.pageSize
    data_stmt = (
        base_stmt.order_by(User.createTime.desc(), User.id.desc())
        .offset(offset)
        .limit(request.pageSize)
    )
    records = list(db.execute(data_stmt).scalars().all())
    return records, int(total)
