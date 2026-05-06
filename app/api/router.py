from fastapi import APIRouter

from app.api.health import router as health_router

# 所有 /api 下的业务路由统一汇总到这里。
# 后续用户、应用、聊天等模块会继续 include_router 到 api_router。
api_router = APIRouter()
api_router.include_router(health_router)
