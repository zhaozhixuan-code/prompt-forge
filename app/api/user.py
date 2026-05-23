from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import BaseResponse
from app.db.session import get_db
from app.schemas.user import UserRegisterRequest
from app.services.user_service import register_user

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/register", response_model=BaseResponse[int])
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> BaseResponse[int]:
    # 路由层只负责参数接收、依赖注入和统一响应包装，注册规则放到 service 层。
    user_id = register_user(db, request)
    return BaseResponse.ok(user_id)
