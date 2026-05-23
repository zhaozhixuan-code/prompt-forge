from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    # 对齐 sql/zzx_ai_code.sql 中的 user 表，字段名暂时沿用原 Java 项目的驼峰列名。
    __tablename__ = "user"

    # 主键 ID 使用 MySQL bigint 自增，兼容原 Java 后端的用户 id 类型。
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 登录账号和加密后的密码；userAccount 在数据库中有唯一索引。
    userAccount: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    userPassword: Mapped[str] = mapped_column(String(512), nullable=False)

    # 用户资料字段，注册时先默认把 userName 设置为账号，其他资料后续由用户补充。
    userName: Mapped[str | None] = mapped_column(String(256), nullable=True)
    userAvatar: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    userProfile: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # 用户角色沿用原项目约定：普通用户为 user，管理员为 admin。
    userRole: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        default="user",
        server_default=text("'user'"),
    )

    # editTime 表示业务编辑时间，当前先交给数据库默认写入创建时刻。
    editTime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # createTime 记录创建时间，由数据库默认值生成。
    createTime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # updateTime 对齐表结构中的 ON UPDATE CURRENT_TIMESTAMP，记录最后更新时间。
    updateTime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    # 逻辑删除标记：0 表示正常，1 表示已删除；查询时通常需要过滤 isDelete == 0。
    isDelete: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
