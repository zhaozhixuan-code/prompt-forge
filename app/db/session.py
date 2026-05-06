from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# SQLAlchemy 数据库引擎，负责管理 MySQL 连接池。
engine = create_engine(
    settings.database_url,
    echo=settings.mysql_echo,
    pool_pre_ping=True,
    pool_recycle=settings.mysql_pool_recycle,
    pool_size=settings.mysql_pool_size,
    max_overflow=settings.mysql_max_overflow,
)

# 数据库 Session 工厂；一次请求通常使用一个 Session。
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    # FastAPI 依赖函数：接口里 Depends(get_db) 即可拿到数据库 Session。
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
