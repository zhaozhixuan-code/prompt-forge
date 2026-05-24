import json
from typing import Any

import pytest
from fastapi import Request

from app.api import deps
from app.core.exceptions import BusinessException, ErrorCode
from app.core.security import build_session_key
from app.models.user import User
from app.services import user_service


class FakeRedis:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self.values = values or {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)


def _make_request(cookie: str | None = None) -> Request:
    headers = []
    if cookie is not None:
        headers.append((b"cookie", cookie.encode("utf-8")))
    return Request({"type": "http", "headers": headers})


def _make_user(user_role: str = "user") -> User:
    return User(
        id=1,
        userAccount="testuser",
        userPassword=user_service.encrypt_password("password123"),
        userName="testuser",
        userRole=user_role,
    )


def test_get_current_user_reads_cookie_session_and_loads_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedis(
        {
            build_session_key("session-token"): json.dumps({"userId": 1}),
        }
    )
    user = _make_user()

    def fake_get_user_by_id(db: Any, user_id: int) -> User | None:
        assert user_id == 1
        return user

    monkeypatch.setattr(deps, "get_user_by_id", fake_get_user_by_id)

    current_user = deps.get_current_user(
        request=_make_request("PF_SESSION=session-token"),
        db=object(),
        redis_client=redis_client,  # type: ignore[arg-type]
    )

    assert current_user.id == 1
    assert current_user.userAccount == "testuser"


def test_get_current_user_rejects_missing_cookie() -> None:
    with pytest.raises(BusinessException) as exc_info:
        deps.get_current_user(
            request=_make_request(),
            db=object(),
            redis_client=FakeRedis(),  # type: ignore[arg-type]
        )

    assert exc_info.value.error_code is ErrorCode.NOT_LOGIN_ERROR


def test_get_current_user_rejects_malformed_session_payload() -> None:
    redis_client = FakeRedis({build_session_key("session-token"): "not-json"})

    with pytest.raises(BusinessException) as exc_info:
        deps.get_current_user(
            request=_make_request("PF_SESSION=session-token"),
            db=object(),
            redis_client=redis_client,  # type: ignore[arg-type]
        )

    assert exc_info.value.error_code is ErrorCode.NOT_LOGIN_ERROR


def test_get_current_user_rejects_string_user_id_session() -> None:
    redis_client = FakeRedis(
        {
            build_session_key("session-token"): json.dumps({"userId": "1"}),
        }
    )

    with pytest.raises(BusinessException) as exc_info:
        deps.get_current_user(
            request=_make_request("PF_SESSION=session-token"),
            db=object(),
            redis_client=redis_client,  # type: ignore[arg-type]
        )

    assert exc_info.value.error_code is ErrorCode.NOT_LOGIN_ERROR


def test_get_current_user_rejects_missing_database_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedis(
        {
            build_session_key("session-token"): json.dumps({"userId": 1}),
        }
    )
    monkeypatch.setattr(deps, "get_user_by_id", lambda db, user_id: None)

    with pytest.raises(BusinessException) as exc_info:
        deps.get_current_user(
            request=_make_request("PF_SESSION=session-token"),
            db=object(),
            redis_client=redis_client,  # type: ignore[arg-type]
        )

    assert exc_info.value.error_code is ErrorCode.NOT_LOGIN_ERROR


def test_require_admin_accepts_admin_user() -> None:
    admin_user = _make_user(user_role="admin")

    assert deps.require_admin(admin_user) is admin_user


def test_require_admin_rejects_normal_user() -> None:
    with pytest.raises(BusinessException) as exc_info:
        deps.get_current_admin_user(_make_user(user_role="user"))

    assert exc_info.value.error_code is ErrorCode.NO_AUTH_ERROR
