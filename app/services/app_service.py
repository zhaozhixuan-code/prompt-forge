from sqlalchemy.orm import Session

from app.ai.routing_service import route_code_gen_type
from app.core.exceptions import ErrorCode, throw_if
from app.models.app import App
from app.models.user import User
from app.repositories.app_repository import (
    create_app,
    get_app_by_id,
    list_apps_by_page,
    list_good_apps_by_page,
    list_user_apps_by_page,
    soft_delete_app_by_id,
    update_app_by_id,
)
from app.repositories.user_repository import get_user_by_id
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
from app.schemas.user import UserVO

MAX_USER_PAGE_SIZE = 20


def _build_default_app_name(init_prompt: str) -> str:
    # Java 端创建应用时默认取 initPrompt 前 12 位作为应用名。
    return init_prompt[:12]


def _check_app_owner_or_admin(app: App, current_user: User) -> None:
    # 普通用户只能操作自己的应用，管理员可删除任意应用。
    is_owner = app.userId == current_user.id
    is_admin = current_user.userRole == "admin"
    throw_if(not is_owner and not is_admin, ErrorCode.NO_AUTH_ERROR)


def _build_app_vo(db: Session, app: App) -> AppVO:
    app_vo = AppVO.model_validate(app)
    user = get_user_by_id(db, app.userId)
    app_vo.user = UserVO.model_validate(user) if user is not None else None
    return app_vo


def _build_app_admin_vo(db: Session, app: App) -> AppAdminVO:
    app_vo = AppAdminVO.model_validate(app)
    user = get_user_by_id(db, app.userId)
    app_vo.user = UserVO.model_validate(user) if user is not None else None
    return app_vo


def _build_app_page_vo(db: Session, records: list[App], total: int, request: AppQueryRequest) -> AppPageVO:
    pages = (total + request.pageSize - 1) // request.pageSize
    return AppPageVO(
        records=[_build_app_vo(db, app) for app in records],
        total=total,
        size=request.pageSize,
        current=request.current,
        pages=pages,
        pageNum=request.current,
        pageSize=request.pageSize,
        totalRow=total,
    )


def add_app_by_user(db: Session, request: AppAddRequest, current_user: User) -> int:
    """登录用户创建应用。

    先校验初始 prompt，再交给 AI 路由判断生成类型。
    路由结果会随应用一起写入 code_gen_type，后续生成链路直接按这个类型执行。
    """
    init_prompt = request.initPrompt.strip()
    throw_if(not init_prompt, ErrorCode.PARAMS_ERROR, "初始化 prompt 不能为空")

    # 创建时就确定生成模式，避免后续生成阶段再去猜测用户意图。
    app = create_app(
        db,
        app_name=_build_default_app_name(init_prompt),
        init_prompt=init_prompt,
        # 这里不再写死 html，而是由智能路由决定应用的生成类型。
        code_gen_type=route_code_gen_type(init_prompt).codeGenType,
        user_id=current_user.id,
    )
    return app.id


def update_app_by_user(db: Session, request: AppUpdateRequest, current_user: User) -> bool:
    """登录用户更新自己的应用名称。"""
    throw_if(request.id <= 0, ErrorCode.PARAMS_ERROR, "invalid app id")
    app = get_app_by_id(db, request.id)
    throw_if(app is None, ErrorCode.NOT_FOUND_ERROR, "app not found")
    throw_if(app.userId != current_user.id, ErrorCode.NO_AUTH_ERROR)

    update_values: dict[str, object] = {}
    if request.appName is not None:
        app_name = request.appName.strip()
        throw_if(not app_name, ErrorCode.PARAMS_ERROR, "app name cannot be empty")
        update_values["appName"] = app_name

    if not update_values:
        return True

    update_app_by_id(db, app, update_values)
    return True


def delete_app_by_user(db: Session, request: AppDeleteRequest, current_user: User) -> bool:
    """登录用户删除自己的应用，管理员也允许走该接口删除。"""
    throw_if(request.id <= 0, ErrorCode.PARAMS_ERROR, "invalid app id")
    app = get_app_by_id(db, request.id)
    throw_if(app is None, ErrorCode.NOT_FOUND_ERROR, "app not found")
    _check_app_owner_or_admin(app, current_user)
    soft_delete_app_by_id(db, app)
    return True


def get_app_vo_by_id(db: Session, app_id: int) -> AppVO:
    """按 ID 获取应用公开详情。"""
    throw_if(app_id <= 0, ErrorCode.PARAMS_ERROR, "invalid app id")
    app = get_app_by_id(db, app_id)
    throw_if(app is None, ErrorCode.NOT_FOUND_ERROR, "app not found")
    return _build_app_vo(db, app)


def list_my_app_vo_by_page(db: Session, request: AppQueryRequest, current_user: User) -> AppPageVO:
    """分页获取当前登录用户创建的应用。"""
    throw_if(request.pageSize > MAX_USER_PAGE_SIZE, ErrorCode.PARAMS_ERROR, "每页最多查询 20 个应用")
    records, total = list_user_apps_by_page(db, current_user.id, request)
    return _build_app_page_vo(db, records, total, request)


def list_good_app_vo_by_page(db: Session, request: AppQueryRequest) -> AppPageVO:
    """分页获取精选应用。"""
    throw_if(request.pageSize > MAX_USER_PAGE_SIZE, ErrorCode.PARAMS_ERROR, "每页最多查询 20 个应用")
    records, total = list_good_apps_by_page(db, request)
    return _build_app_page_vo(db, records, total, request)


def delete_app_by_admin(db: Session, request: AppDeleteRequest) -> bool:
    """管理员删除任意应用。"""
    throw_if(request.id <= 0, ErrorCode.PARAMS_ERROR, "invalid app id")
    app = get_app_by_id(db, request.id)
    throw_if(app is None, ErrorCode.NOT_FOUND_ERROR, "app not found")
    soft_delete_app_by_id(db, app)
    return True


def update_app_by_admin(db: Session, request: AppAdminUpdateRequest) -> bool:
    """管理员更新应用名称、封面和精选优先级。"""
    throw_if(request.id <= 0, ErrorCode.PARAMS_ERROR, "invalid app id")
    app = get_app_by_id(db, request.id)
    throw_if(app is None, ErrorCode.NOT_FOUND_ERROR, "app not found")

    update_values: dict[str, object] = {}
    if request.appName is not None:
        app_name = request.appName.strip()
        throw_if(not app_name, ErrorCode.PARAMS_ERROR, "app name cannot be empty")
        update_values["appName"] = app_name
    if request.cover is not None:
        update_values["cover"] = request.cover
    if request.priority is not None:
        throw_if(request.priority < 0, ErrorCode.PARAMS_ERROR, "priority cannot be negative")
        update_values["priority"] = request.priority

    if not update_values:
        return True

    update_app_by_id(db, app, update_values)
    return True


def list_app_vo_by_page_by_admin(db: Session, request: AppQueryRequest) -> AppPageVO:
    """管理员分页获取应用列表。"""
    records, total = list_apps_by_page(db, request)
    return _build_app_page_vo(db, records, total, request)


def get_app_vo_by_id_by_admin(db: Session, app_id: int) -> AppAdminVO:
    """管理员按 ID 获取应用详情。"""
    throw_if(app_id <= 0, ErrorCode.PARAMS_ERROR, "invalid app id")
    app = get_app_by_id(db, app_id)
    throw_if(app is None, ErrorCode.NOT_FOUND_ERROR, "app not found")
    return _build_app_admin_vo(db, app)
