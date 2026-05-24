from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class App(Base):
    # 对齐 sql/zzx_ai_code.sql 中的 app 表，字段名沿用 Java 项目的驼峰列名。
    __tablename__ = "app"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    appName: Mapped[str | None] = mapped_column(String(256), nullable=True)
    cover: Mapped[str | None] = mapped_column(String(512), nullable=True)
    initPrompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    codeGenType: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deployKey: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    deployedTime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    userId: Mapped[int] = mapped_column(BigInteger, nullable=False)

    editTime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    createTime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updateTime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )
    isDelete: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
