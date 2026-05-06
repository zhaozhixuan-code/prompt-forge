from functools import lru_cache

from redis import Redis

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    # Redis 连接全局复用，后续 Session、缓存、限流都会从这里拿客户端。
    settings = get_settings()
    return Redis.from_url(
        settings.redis_url,
        decode_responses=settings.redis_decode_responses,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


def close_redis_client() -> None:
    # 应用关闭时释放 Redis 连接。
    get_redis_client().close()
