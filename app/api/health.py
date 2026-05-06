from fastapi import APIRouter

from app.core.response import BaseResponse

# 健康检查路由，用来确认 Python 后端服务是否正常启动。
router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=BaseResponse[dict[str, str]])
def health() -> BaseResponse[dict[str, str]]:
    # 按项目约定统一返回 {code, data, message} 结构，便于前端兼容。
    return BaseResponse.ok({"status": "ok"})
