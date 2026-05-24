from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.app import App
from app.schemas.app import AppQueryRequest

APP_SORT_FIELDS = {
    "id": App.id,
    "appName": App.appName,
    "priority": App.priority,
    "createTime": App.createTime,
    "updateTime": App.updateTime,
    "editTime": App.editTime,
}


def get_app_by_id(db: Session, app_id: int) -> App | None:
    # 默认过滤逻辑删除数据，保持和 Java 逻辑删除行为一致。
    stmt = select(App).where(App.id == app_id, App.isDelete == 0)
    return db.execute(stmt).scalar_one_or_none()


def create_app(
    db: Session,
    *,
    app_name: str,
    init_prompt: str,
    code_gen_type: str,
    user_id: int,
) -> App:
    # 只负责落库，参数校验和默认值策略放在 service 层。
    app = App(
        appName=app_name,
        initPrompt=init_prompt,
        codeGenType=code_gen_type,
        userId=user_id,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def update_app_by_id(db: Session, app: App, values: Mapping[str, Any]) -> App:
    # 只更新 service 明确传入的字段，避免 None 误覆盖。
    for field, value in values.items():
        setattr(app, field, value)
    app.editTime = datetime.now()

    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def soft_delete_app_by_id(db: Session, app: App) -> None:
    # 对齐 app 表 isDelete 字段，仅做逻辑删除。
    app.isDelete = 1
    db.add(app)
    db.commit()


def _build_app_query(request: AppQueryRequest):
    # 查询条件对齐 Java getQueryWrapper：id 精确，其余文本字段模糊或精确匹配。
    stmt = select(App).where(App.isDelete == 0)

    if request.id is not None:
        stmt = stmt.where(App.id == request.id)
    if request.appName:
        stmt = stmt.where(App.appName.like(f"%{request.appName.strip()}%"))
    if request.cover:
        stmt = stmt.where(App.cover.like(f"%{request.cover.strip()}%"))
    if request.initPrompt:
        stmt = stmt.where(App.initPrompt.like(f"%{request.initPrompt.strip()}%"))
    if request.codeGenType:
        stmt = stmt.where(App.codeGenType == request.codeGenType.strip())
    if request.deployKey:
        stmt = stmt.where(App.deployKey == request.deployKey.strip())
    if request.priority is not None:
        stmt = stmt.where(App.priority == request.priority)
    if request.userId is not None:
        stmt = stmt.where(App.userId == request.userId)

    return stmt


def _apply_order(stmt, request: AppQueryRequest):
    sort_column = APP_SORT_FIELDS.get(request.sortField or "")
    if sort_column is None:
        return stmt.order_by(App.createTime.desc(), App.id.desc())
    if request.sortOrder == "ascend":
        return stmt.order_by(sort_column.asc(), App.id.desc())
    return stmt.order_by(sort_column.desc(), App.id.desc())


def list_apps_by_page(db: Session, request: AppQueryRequest) -> tuple[list[App], int]:
    # total 和 records 分开查询，返回结果由 service 封装成前端兼容 Page VO。
    base_stmt = _build_app_query(request)
    total_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = db.execute(total_stmt).scalar_one()

    offset = (request.current - 1) * request.pageSize
    data_stmt = _apply_order(base_stmt, request).offset(offset).limit(request.pageSize)
    records = list(db.execute(data_stmt).scalars().all())
    return records, int(total)


def list_user_apps_by_page(
    db: Session,
    user_id: int,
    request: AppQueryRequest,
) -> tuple[list[App], int]:
    # 我的应用列表强制按当前登录用户过滤。
    request.userId = user_id
    return list_apps_by_page(db, request)


def list_good_apps_by_page(
    db: Session,
    request: AppQueryRequest,
) -> tuple[list[App], int]:
    # 精选应用沿用 Java 常量 priority=99。
    request.priority = 99
    return list_apps_by_page(db, request)
