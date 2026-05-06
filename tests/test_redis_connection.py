from app.db.redis import get_redis_client


class TestRedisConnection:
    test_key = "promptforge:redis:connection:test"
    test_value = "redis test message"

    def test_set_and_get_test_message(self) -> None:
        redis_client = get_redis_client()

        # Ping first so connection failures point clearly to Redis availability/configuration.
        assert redis_client.ping() is True

        try:
            # Write a stable test key, then read it back to verify Redis writes and reads.
            redis_client.set(self.test_key, self.test_value)
            saved_value = redis_client.get(self.test_key)

            assert saved_value == self.test_value
        finally:
            redis_client.delete(self.test_key)
