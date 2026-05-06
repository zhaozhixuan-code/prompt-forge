from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.db.redis import close_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # FastAPI 生命周期钩子；当前只在应用关闭时释放 Redis 连接。
    yield
    close_redis_client()


def create_app() -> FastAPI:
    # 创建 FastAPI 应用实例，并集中注册中间件和路由。
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # 允许前端跨域请求 Python 后端。开发阶段默认放开，后续可在 .env 中收紧。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 统一挂载 /api 前缀，保持和原前端请求路径兼容。
    app.include_router(api_router, prefix=settings.api_prefix)
    register_exception_handlers(app)
    return app


app = create_app()
