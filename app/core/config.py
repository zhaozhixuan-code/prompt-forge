from functools import lru_cache
from typing import Annotated
from urllib.parse import quote_plus

from fastapi import Depends
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 从环境变量和 .env 文件读取配置；没有配置时使用下面的默认值。
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "PromptForge"
    api_prefix: str = "/api"
    debug: bool = False

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "zzx_ai_code"
    mysql_charset: str = "utf8mb4"
    mysql_echo: bool = False
    mysql_pool_size: int = 5
    mysql_max_overflow: int = 10
    mysql_pool_recycle: int = 3600

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_db: int = 0
    redis_decode_responses: bool = True

    # Python 端使用自定义 Redis Session；这些配置控制浏览器 Cookie 行为和 Session TTL。
    session_cookie_name: str = "PF_SESSION"
    session_expire_seconds: int = 60 * 60 * 24 * 30
    session_cookie_httponly: bool = True
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"

    @computed_field
    @property
    def database_url(self) -> str:
        # SQLAlchemy 使用的 MySQL 连接串。
        # quote_plus 用来处理密码里可能出现的 @、#、: 等特殊字符。
        user = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset={self.mysql_charset}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        # Redis 客户端使用的连接串，密码为空时不拼接认证信息。
        auth = f":{quote_plus(self.redis_password)}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    # 配置对象全局复用，避免每次请求都重复解析环境变量。
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
