"""应用配置集中管理模块。

本文件只负责声明配置项、默认值和派生连接串，不放业务逻辑。
配置优先从环境变量和项目根目录的 .env 文件读取，字段名不区分大小写，
例如 app_name 可以通过 APP_NAME 或 app_name 覆盖。
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated
from urllib.parse import quote_plus

from fastapi import Depends
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """PromptForge 运行时配置。

    默认值主要服务本地开发；生产环境应通过环境变量或 .env 覆盖敏感信息。
    这里的字段会被 FastAPI、数据库、Redis、Session 和 AI 路由模块复用。
    """

    # Pydantic Settings 的读取规则：
    # - env_file 指定从项目根目录 .env 加载配置。
    # - env_file_encoding 保证中文和特殊字符按 UTF-8 读取。
    # - case_sensitive=False 允许 APP_NAME / app_name 等大小写写法。
    # - extra="ignore" 允许 .env 存在暂未迁移的旧配置，避免启动失败。
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用展示名称，会用于 FastAPI 文档标题等非业务场景。
    app_name: str = "PromptForge"
    # 统一接口前缀，保持与现有前端和 Java 后端兼容。
    api_prefix: str = "/api"
    # FastAPI 调试开关；生产环境建议保持 False，避免暴露调试细节。
    debug: bool = False

    # CORS 允许的前端来源；本地迁移阶段默认放开，生产环境应改为明确域名。
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    # MySQL 主机地址，沿用原项目数据库服务。
    mysql_host: str = "127.0.0.1"
    # MySQL 端口，默认使用标准端口 3306。
    mysql_port: int = 3306
    # MySQL 登录用户名。
    mysql_user: str = "root"
    # MySQL 登录密码；不要在代码中写生产密码，应通过 .env 注入。
    mysql_password: str = ""
    # 当前 Python 后端默认连接的数据库名称。
    mysql_database: str = "zzx_ai_code"
    # 数据库字符集，utf8mb4 可正确保存中文和表情等完整 Unicode 字符。
    mysql_charset: str = "utf8mb4"
    # 是否打印 SQLAlchemy 执行的 SQL；排查 SQL 时开启，平时保持关闭。
    mysql_echo: bool = False
    # SQLAlchemy 连接池常驻连接数，用于复用数据库连接。
    mysql_pool_size: int = 5
    # 连接池满时允许临时创建的额外连接数。
    mysql_max_overflow: int = 10
    # 连接回收时间，避免 MySQL 长连接空闲过久后被服务端断开。
    mysql_pool_recycle: int = 3600

    # Redis 主机地址，用于 Session、缓存和后续限流等能力。
    redis_host: str = "127.0.0.1"
    # Redis 端口，默认使用标准端口 6379。
    redis_port: int = 6379
    # Redis 密码；为空时按无密码 Redis 连接。
    redis_password: str | None = None
    # Redis 数据库编号，默认使用 0 号库。
    redis_db: int = 0
    # 是否把 Redis 返回值解码为字符串，业务代码通常更适合直接处理 str。
    redis_decode_responses: bool = True

    # 通用 OpenAI-compatible 模型配置，当前由 langchain-openai 统一接入。
    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_model: str | None = None
    # AI 路由温度；0 表示更稳定、可复现的分类结果。
    ai_routing_temperature: float = 0
    # AI 路由最大尝试次数，用于处理模型返回格式不合法等情况。
    ai_routing_max_attempts: int = 3
    # 单次 AI 请求超时时间，避免接口长时间挂起。
    ai_request_timeout_seconds: float = 30
    # AI SDK 层面的重试次数；外层业务已有重试时可保持为 0，避免重复重试。
    ai_max_retries: int = 0

    # 浏览器保存的 Session Cookie 名称，前端通过 Cookie 维持登录态。
    session_cookie_name: str = "PF_SESSION"
    # Session 过期时间，默认 30 天；Redis 中的 Session TTL 与它保持一致。
    session_expire_seconds: int = 60 * 60 * 24 * 30
    # 禁止前端脚本读取 Cookie，降低 XSS 窃取登录态的风险。
    session_cookie_httponly: bool = True
    # 是否仅通过 HTTPS 发送 Cookie；本地 HTTP 开发环境默认关闭。
    session_cookie_secure: bool = False
    # Cookie 跨站策略；lax 兼顾安全性和常见页面跳转场景。
    session_cookie_samesite: str = "lax"

    @computed_field
    @property
    def database_url(self) -> str:
        """生成 SQLAlchemy 使用的 MySQL 连接串。"""

        # 用户名和密码可能包含 @、#、: 等特殊字符，必须 URL 编码后再拼接。
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
        """生成 Redis 客户端使用的连接串。"""

        # Redis 密码为空时不拼接认证段，兼容本地无密码 Redis。
        auth = f":{quote_plus(self.redis_password)}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def resolved_ai_api_key(self) -> str | None:
        """返回当前实际使用的模型 API Key。"""

        return self.ai_api_key

    @property
    def resolved_ai_base_url(self) -> str:
        """返回当前实际使用的 OpenAI-compatible 地址。"""

        return self.ai_base_url or "https://api.deepseek.com"

    @property
    def resolved_ai_model(self) -> str:
        """返回当前实际使用的聊天模型名称。"""

        return self.ai_model or "deepseek-chat"


@lru_cache
def get_settings() -> Settings:
    """返回全局复用的配置对象。"""

    # BaseSettings 会解析环境变量和 .env，缓存后可避免每次请求重复解析。
    return Settings()


# FastAPI 依赖注入别名，接口层可直接声明 settings: SettingsDep。
SettingsDep = Annotated[Settings, Depends(get_settings)]
