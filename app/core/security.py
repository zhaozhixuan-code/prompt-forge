import json
import secrets

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
