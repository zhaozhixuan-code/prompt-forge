from fastapi import APIRouter

from app.api.app import router as app_router
from app.api.health import router as health_router
from app.api.user import router as user_router

api_router = APIRouter()
api_router.include_router(health_router)
# 用户模块路由：当前先接入注册接口，后续登录、登出等接口继续挂在这里。
api_router.include_router(user_router)
api_router.include_router(app_router)
