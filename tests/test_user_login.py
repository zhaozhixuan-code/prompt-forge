import json
from typing import Any

import pytest
from fastapi import Request, Response

from app.api.user import login, logout
from app.core.exceptions import BusinessException, ErrorCode
from app.core.security import SESSION_KEY_PREFIX, build_session_key
from app.models.user import User
from app.schemas.user import UserLoginRequest
from app.services import user_service


class FakeRedis:
    # 单测只关心是否写入 Redis Session，不依赖真实 Redis 服务。
    def __init__(self) -> None:
        self.setex_calls: list[tuple[str, int, str]] = []
        self.delete_calls: list[str] = []

    def setex(self, key: str, time: int, value: str) -> None:
        self.setex_calls.append((key, time, value))

    def delete(self, key: str) -> None:
        self.delete_calls.append(key)


def _make_user(password: str) -> User:
    user = User(
        id=1,
        userAccount="testuser",
        userPassword=user_service.encrypt_password(password),
        userName="testuser",
        userRole="user",
    )
    return user


def test_login_user_creates_session_and_returns_user_vo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _make_user("password123")
    redis_client = FakeRedis()

    def fake_get_user_by_account(db: Any, user_account: str) -> User | None:
        assert user_account == "testuser"
        return user

    monkeypatch.setattr(user_service, "get_user_by_account", fake_get_user_by_account)

    result = user_service.login_user(
        db=object(),
        redis_client=redis_client,  # type: ignore[arg-type]
        request=UserLoginRequest(
            userAccount=" testuser ",
            userPassword="password123",
        ),
    )

    assert result.user.id == 1
    assert result.user.userAccount == "testuser"
    assert result.session_id
    assert len(redis_client.setex_calls) == 1

    session_key, ttl, payload = redis_client.setex_calls[0]
    assert session_key.startswith(SESSION_KEY_PREFIX)
    assert ttl == user_service.get_settings().session_expire_seconds
    assert json.loads(payload) == {"userId": 1}


def test_login_user_rejects_wrong_password(monkeypatch: pytest.MonkeyPatch) -> None:
    user = _make_user("password123")
    monkeypatch.setattr(user_service, "get_user_by_account", lambda db, account: user)

    with pytest.raises(BusinessException) as exc_info:
        user_service.login_user(
            db=object(),
            redis_client=FakeRedis(),  # type: ignore[arg-type]
            request=UserLoginRequest(
                userAccount="testuser",
                userPassword="wrongpass",
            ),
        )

    assert exc_info.value.error_code is ErrorCode.PARAMS_ERROR
    assert exc_info.value.message == "用户不存在或密码错误"


def test_login_route_returns_user_and_sets_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 直接调用路由函数验证 Set-Cookie；避免为 TestClient 额外引入 httpx 依赖。
    user = _make_user("password123")
    redis_client = FakeRedis()
    monkeypatch.setattr(user_service, "get_user_by_account", lambda db, account: user)

    response = Response()
    result = login(
        request=UserLoginRequest(
            userAccount="testuser",
            userPassword="password123",
        ),
        response=response,
        db=object(),  # type: ignore[arg-type]
        redis_client=redis_client,  # type: ignore[arg-type]
    )

    assert result.code == 0
    assert result.data is not None
    assert result.data.userAccount == "testuser"
    assert "PF_SESSION=" in response.headers["set-cookie"]
    assert len(redis_client.setex_calls) == 1


def test_logout_user_deletes_session() -> None:
    redis_client = FakeRedis()

    result = user_service.logout_user(
        redis_client=redis_client,  # type: ignore[arg-type]
        session_id="session-token",
    )

    assert result is True
    assert redis_client.delete_calls == [build_session_key("session-token")]


def test_logout_route_deletes_session_and_clears_cookie() -> None:
    redis_client = FakeRedis()
    request = Request(
        {
            "type": "http",
            "headers": [(b"cookie", b"PF_SESSION=session-token")],
        }
    )
    response = Response()

    result = logout(
        request=request,
        response=response,
        redis_client=redis_client,  # type: ignore[arg-type]
    )

    assert result.code == 0
    assert result.data is True
    assert redis_client.delete_calls == [build_session_key("session-token")]
    assert "PF_SESSION=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_logout_route_without_cookie_is_idempotent() -> None:
    redis_client = FakeRedis()
    request = Request({"type": "http", "headers": []})
    response = Response()

    result = logout(
        request=request,
        response=response,
        redis_client=redis_client,  # type: ignore[arg-type]
    )

    assert result.code == 0
    assert result.data is True
    assert redis_client.delete_calls == []
