from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_account(db: Session, user_account: str) -> User | None:
    # 注册前按账号查重，并过滤逻辑删除的数据。
    stmt = select(User).where(
        User.userAccount == user_account,
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
