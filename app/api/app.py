from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, require_login
from app.core.response import BaseResponse
from app.db.session import get_db
from app.models.user import User
from app.schemas.app import (
    AppAddRequest,
    AppAdminUpdateRequest,
    AppAdminVO,
    AppDeleteRequest,
    AppPageVO,
    AppQueryRequest,
    AppUpdateRequest,
    AppVO,
)
from app.services.app_service import (
    add_app_by_user,
    delete_app_by_admin,
    delete_app_by_user,
    get_app_vo_by_id,
    get_app_vo_by_id_by_admin,
    list_app_vo_by_page_by_admin,
    list_good_app_vo_by_page,
    list_my_app_vo_by_page,
    update_app_by_admin,
    update_app_by_user,
)

router = APIRouter(prefix="/app", tags=["app"])


@router.post("/add", response_model=BaseResponse[str])
def add_app(
    request: AppAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
) -> BaseResponse[str]:
    """创建应用。"""
    app_id = add_app_by_user(db, request, current_user)
    return BaseResponse.ok(str(app_id))


@router.post("/update", response_model=BaseResponse[bool])
def update_app(
    request: AppUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
) -> BaseResponse[bool]:
    """登录用户更新自己的应用名称。"""
    result = update_app_by_user(db, request, current_user)
    return BaseResponse.ok(result)


@router.post("/delete", response_model=BaseResponse[bool])
def delete_app(
    request: AppDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
) -> BaseResponse[bool]:
    """登录用户删除自己的应用。"""
    result = delete_app_by_user(db, request, current_user)
    return BaseResponse.ok(result)


@router.get("/get/vo", response_model=BaseResponse[AppVO])
def get_app_vo(
    id: int,
    db: Session = Depends(get_db),
) -> BaseResponse[AppVO]:
    """按 ID 获取应用公开详情。"""
    app = get_app_vo_by_id(db, id)
    return BaseResponse.ok(app)


@router.post("/my/list/page/vo", response_model=BaseResponse[AppPageVO])
def list_my_app_vo(
    request: AppQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
) -> BaseResponse[AppPageVO]:
    """分页获取当前用户创建的应用。"""
    page = list_my_app_vo_by_page(db, request, current_user)
    return BaseResponse.ok(page)


@router.post("/good/list/page/vo", response_model=BaseResponse[AppPageVO])
def list_good_app_vo(
    request: AppQueryRequest,
    db: Session = Depends(get_db),
) -> BaseResponse[AppPageVO]:
    """分页获取精选应用。"""
    page = list_good_app_vo_by_page(db, request)
    return BaseResponse.ok(page)


@router.post("/admin/delete", response_model=BaseResponse[bool])
def delete_app_admin(
    request: AppDeleteRequest,
    db: Session = Depends(get_db),
    current_admin_user: User = Depends(get_current_admin_user),
) -> BaseResponse[bool]:
    """管理员删除应用。"""
    _ = current_admin_user
    result = delete_app_by_admin(db, request)
    return BaseResponse.ok(result)


@router.post("/admin/update", response_model=BaseResponse[bool])
def update_app_admin(
    request: AppAdminUpdateRequest,
    db: Session = Depends(get_db),
    current_admin_user: User = Depends(get_current_admin_user),
) -> BaseResponse[bool]:
    """管理员更新应用。"""
    _ = current_admin_user
    result = update_app_by_admin(db, request)
    return BaseResponse.ok(result)


@router.post("/admin/list/page/vo", response_model=BaseResponse[AppPageVO])
def list_app_vo_admin(
    request: AppQueryRequest,
    db: Session = Depends(get_db),
    current_admin_user: User = Depends(get_current_admin_user),
) -> BaseResponse[AppPageVO]:
    """管理员分页获取应用列表。"""
    _ = current_admin_user
    page = list_app_vo_by_page_by_admin(db, request)
    return BaseResponse.ok(page)


@router.get("/admin/get/vo", response_model=BaseResponse[AppAdminVO])
def get_app_vo_admin(
    id: int,
    db: Session = Depends(get_db),
    current_admin_user: User = Depends(get_current_admin_user),
) -> BaseResponse[AppAdminVO]:
    """管理员按 ID 获取应用详情。"""
    _ = current_admin_user
    app = get_app_vo_by_id_by_admin(db, id)
    return BaseResponse.ok(app)
