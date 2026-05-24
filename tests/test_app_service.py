from datetime import datetime
from typing import Any

import pytest

from app.core.exceptions import BusinessException, ErrorCode
from app.models.app import App
from app.models.user import User
from app.schemas.app import (
    AppAddRequest,
    AppAdminUpdateRequest,
    AppDeleteRequest,
    AppVO,
    AppQueryRequest,
    AppUpdateRequest,
)
from app.services import app_service, user_service


def _make_user(*, user_id: int = 1, user_role: str = "user") -> User:
    return User(
        id=user_id,
        userAccount=f"user{user_id}",
        userPassword=user_service.encrypt_password("password123"),
        userName=f"user{user_id}",
        userRole=user_role,
    )


def _make_app(*, app_id: int = 1, user_id: int = 1, priority: int = 0) -> App:
    now = datetime.now()
    return App(
        id=app_id,
        appName="old app",
        cover=None,
        initPrompt="make a todo app",
        codeGenType="html",
        deployKey=None,
        deployedTime=None,
        priority=priority,
        userId=user_id,
        editTime=now,
        createTime=now,
        updateTime=now,
        isDelete=0,
    )


def test_add_app_by_user_sets_owner_and_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_create_app(db: Any, **kwargs: Any) -> App:
        captured.update(kwargs)
        return _make_app(app_id=10, user_id=kwargs["user_id"])

    monkeypatch.setattr(app_service, "create_app", fake_create_app)

    app_id = app_service.add_app_by_user(
        db=object(),
        request=AppAddRequest(initPrompt=" build a landing page "),
        current_user=_make_user(user_id=7),
    )

    assert app_id == 10
    assert captured["user_id"] == 7
    assert captured["init_prompt"] == "build a landing page"
    assert captured["app_name"] == "build a land"
    assert captured["code_gen_type"] == app_service.DEFAULT_CODE_GEN_TYPE


def test_update_app_by_user_rejects_non_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(app_service, "get_app_by_id", lambda db, app_id: _make_app(user_id=2))

    with pytest.raises(BusinessException) as exc_info:
        app_service.update_app_by_user(
            db=object(),
            request=AppUpdateRequest(id=1, appName="new name"),
            current_user=_make_user(user_id=1),
        )

    assert exc_info.value.error_code is ErrorCode.NO_AUTH_ERROR


def test_update_app_by_user_only_updates_app_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _make_app(user_id=1)
    captured: dict[str, Any] = {}

    monkeypatch.setattr(app_service, "get_app_by_id", lambda db, app_id: app)

    def fake_update_app_by_id(db: Any, app: App, values: dict[str, Any]) -> App:
        captured.update(values)
        return app

    monkeypatch.setattr(app_service, "update_app_by_id", fake_update_app_by_id)

    result = app_service.update_app_by_user(
        db=object(),
        request=AppUpdateRequest(id=1, appName=" new name "),
        current_user=_make_user(user_id=1),
    )

    assert result is True
    assert captured == {"appName": "new name"}


def test_delete_app_by_user_soft_deletes_owned_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _make_app(user_id=1)
    deleted: list[int] = []

    monkeypatch.setattr(app_service, "get_app_by_id", lambda db, app_id: app)
    monkeypatch.setattr(app_service, "soft_delete_app_by_id", lambda db, app: deleted.append(app.id))

    result = app_service.delete_app_by_user(
        db=object(),
        request=AppDeleteRequest(id=1),
        current_user=_make_user(user_id=1),
    )

    assert result is True
    assert deleted == [1]


def test_delete_app_by_user_allows_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _make_app(user_id=2)
    deleted: list[int] = []

    monkeypatch.setattr(app_service, "get_app_by_id", lambda db, app_id: app)
    monkeypatch.setattr(app_service, "soft_delete_app_by_id", lambda db, app: deleted.append(app.id))

    result = app_service.delete_app_by_user(
        db=object(),
        request=AppDeleteRequest(id=1),
        current_user=_make_user(user_id=1, user_role="admin"),
    )

    assert result is True
    assert deleted == [1]


def test_admin_update_app_allows_cover_and_priority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _make_app(user_id=2)
    captured: dict[str, Any] = {}

    monkeypatch.setattr(app_service, "get_app_by_id", lambda db, app_id: app)

    def fake_update_app_by_id(db: Any, app: App, values: dict[str, Any]) -> App:
        captured.update(values)
        return app

    monkeypatch.setattr(app_service, "update_app_by_id", fake_update_app_by_id)

    result = app_service.update_app_by_admin(
        db=object(),
        request=AppAdminUpdateRequest(
            id=1,
            appName=" featured ",
            cover="https://example.com/cover.png",
            priority=99,
        ),
    )

    assert result is True
    assert captured == {
        "appName": "featured",
        "cover": "https://example.com/cover.png",
        "priority": 99,
    }


def test_list_my_app_vo_by_page_returns_page_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    apps = [_make_app(app_id=1, user_id=1), _make_app(app_id=2, user_id=1)]
    user = _make_user(user_id=1)

    def fake_list_user_apps_by_page(db: Any, user_id: int, request: AppQueryRequest):
        assert user_id == 1
        assert request.current == 2
        assert request.pageSize == 5
        return apps, 12

    monkeypatch.setattr(app_service, "list_user_apps_by_page", fake_list_user_apps_by_page)
    monkeypatch.setattr(app_service, "get_user_by_id", lambda db, user_id: user)

    page = app_service.list_my_app_vo_by_page(
        db=object(),
        request=AppQueryRequest(pageNum=2, pageSize=5),
        current_user=user,
    )

    assert page.total == 12
    assert page.current == 2
    assert page.size == 5
    assert page.pages == 3
    assert page.pageNum == 2
    assert page.pageSize == 5
    assert page.totalRow == 12
    assert [record.id for record in page.records] == [1, 2]
    assert page.records[0].user is not None


def test_list_good_app_vo_by_page_limits_page_size() -> None:
    with pytest.raises(BusinessException) as exc_info:
        app_service.list_good_app_vo_by_page(
            db=object(),
            request=AppQueryRequest(pageSize=21),
        )

    assert exc_info.value.error_code is ErrorCode.PARAMS_ERROR


def test_app_vo_serializes_bigint_ids_as_string() -> None:
    app = _make_app(
        app_id=390402563977154561,
        user_id=1991139811048484869,
    )

    app_vo = AppVO.model_validate(app)
    dumped = app_vo.model_dump(mode="json")

    assert app_vo.id == 390402563977154561
    assert app_vo.userId == 1991139811048484869
    assert dumped["id"] == "390402563977154561"
    assert dumped["userId"] == "1991139811048484869"
