from typing import Any

import pytest

from app.api.deps import get_current_admin_user
from app.core.exceptions import BusinessException, ErrorCode
from app.models.user import User
from app.schemas.user import UserAddRequest, UserQueryRequest, UserUpdateRequest
from app.services import user_service


def _make_user(
    *,
    user_id: int = 1,
    user_account: str = "testuser",
    user_role: str = "user",
) -> User:
    return User(
        id=user_id,
        userAccount=user_account,
        userPassword=user_service.encrypt_password("password123"),
        userName=user_account,
        userRole=user_role,
    )


def test_add_user_by_admin_uses_default_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(user_service, "get_user_by_account", lambda db, account: None)

    def fake_create_admin_user(db: Any, **kwargs: Any) -> User:
        captured.update(kwargs)
        return _make_user(user_id=2, user_account=kwargs["user_account"])

    monkeypatch.setattr(user_service, "create_admin_user", fake_create_admin_user)

    user_id = user_service.add_user_by_admin(
        db=object(),
        request=UserAddRequest(
            userAccount=" adminuser ",
            userPassword="requestpass123",
            userRole="admin",
        ),
    )

    assert user_id == 2
    assert captured["user_account"] == "adminuser"
    assert captured["user_role"] == "admin"
    assert captured["user_password"] == user_service.encrypt_password(
        user_service.DEFAULT_ADMIN_CREATE_PASSWORD
    )


def test_update_user_by_admin_encrypts_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _make_user()
    captured: dict[str, Any] = {}

    monkeypatch.setattr(user_service, "get_user_by_id", lambda db, user_id: user)
    monkeypatch.setattr(user_service, "get_user_by_account", lambda db, account: user)

    def fake_update_user_by_id(db: Any, user: User, values: dict[str, Any]) -> User:
        captured.update(values)
        return user

    monkeypatch.setattr(user_service, "update_user_by_id", fake_update_user_by_id)

    result = user_service.update_user_by_admin(
        db=object(),
        request=UserUpdateRequest(
            id=1,
            userAccount="testuser",
            userPassword="newpass123",
            userRole="admin",
        ),
    )

    assert result is True
    assert captured["userPassword"] == user_service.encrypt_password("newpass123")
    assert captured["userRole"] == "admin"


def test_list_user_vo_by_page_returns_page_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    users = [_make_user(user_id=1), _make_user(user_id=2, user_account="otheruser")]

    def fake_list_users_by_page(db: Any, request: UserQueryRequest):
        assert request.current == 2
        assert request.pageSize == 5
        return users, 12

    monkeypatch.setattr(user_service, "list_users_by_page", fake_list_users_by_page)

    page = user_service.list_user_vo_by_page(
        db=object(),
        request=UserQueryRequest(pageNum=2, pageSize=5),
    )

    assert page.total == 12
    assert page.current == 2
    assert page.size == 5
    assert page.pages == 3
    assert page.pageNum == 2
    assert page.pageSize == 5
    assert page.totalRow == 12
    assert [record.id for record in page.records] == [1, 2]


def test_get_current_admin_user_rejects_normal_user() -> None:
    with pytest.raises(BusinessException) as exc_info:
        get_current_admin_user(_make_user(user_role="user"))

    assert exc_info.value.error_code is ErrorCode.NO_AUTH_ERROR
