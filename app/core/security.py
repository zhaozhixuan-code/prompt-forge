import json
import secrets
from typing import Any

from redis import Redis

SESSION_KEY_PREFIX = "promptforge:session:"


def build_session_key(session_id: str) -> str:
    # Redis key 统一加业务前缀，避免和缓存、限流等其他 Redis 数据混在一起。
    return f"{SESSION_KEY_PREFIX}{session_id}"


def create_user_session(
    redis_client: Redis,
    user_id: int,
    expire_seconds: int,
) -> str:
    # session_id 必须是不可预测随机值；Cookie 中只放这个随机值，不放用户 ID。
    session_id = secrets.token_urlsafe(32)

    # 第一阶段只保存 userId，后续如需角色、权限版本等字段可以兼容性扩展 JSON。
    payload = json.dumps({"userId": user_id}, separators=(",", ":"))

    # setex 同时写入值和过期时间，对应 Spring Session 中会话自动过期的行为。
    redis_client.setex(build_session_key(session_id), expire_seconds, payload)
    return session_id


def get_user_id_from_session(redis_client: Redis, session_id: str | None) -> int | None:
    """从 Redis Session 中读取当前登录用户 ID。"""
    # 没有 Cookie 或 Redis 中不存在对应 key，都按未登录处理。
    if not session_id:
        return None

    payload = redis_client.get(build_session_key(session_id))
    if payload is None:
        return None
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    try:
        session_data: Any = json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        # Session 内容异常时不抛系统错误，按登录态失效处理更符合前端预期。
        return None

    user_id = session_data.get("userId") if isinstance(session_data, dict) else None
    return user_id if isinstance(user_id, int) else None


def delete_user_session(redis_client: Redis, session_id: str | None) -> None:
    """
    删除 Redis 中的用户登录 Session。

    Args:
        redis_client: Redis 客户端。
        session_id: Cookie 中携带的登录 Session ID。
    """
    # 退出登录允许重复调用；没有 Cookie 时无需访问 Redis，直接视为已经退出。
    if not session_id:
        return

    redis_client.delete(build_session_key(session_id))
