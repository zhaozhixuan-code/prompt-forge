from sqlalchemy import text

from app.db.session import SessionLocal


class TestMySQLConnection:
    test_key = "promptforge_mysql_connection_test"
    test_value = "mysql test message"

    @staticmethod
    def _ensure_test_table() -> None:
        # Use an isolated table so the connection test does not depend on business tables.
        create_table_sql = text(
            """
            CREATE TABLE IF NOT EXISTS promptforge_connection_test (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                test_key VARCHAR(128) NOT NULL UNIQUE,
                test_value VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )

        with SessionLocal() as session:
            session.execute(create_table_sql)
            session.commit()

    @staticmethod
    def _drop_test_table() -> None:
        # Remove the table created only for this connection test.
        with SessionLocal() as session:
            session.execute(text("DROP TABLE IF EXISTS promptforge_connection_test"))
            session.commit()

    def test_insert_and_query_test_message(self) -> None:
        self._ensure_test_table()

        insert_sql = text(
            """
            INSERT INTO promptforge_connection_test (test_key, test_value)
            VALUES (:test_key, :test_value)
            ON DUPLICATE KEY UPDATE test_value = :test_value
            """
        )
        query_sql = text(
            """
            SELECT test_value
            FROM promptforge_connection_test
            WHERE test_key = :test_key
            """
        )

        try:
            with SessionLocal() as session:
                # Insert a stable test row, then query it back to verify MySQL writes and reads.
                session.execute(
                    insert_sql,
                    {"test_key": self.test_key, "test_value": self.test_value},
                )
                session.commit()

                saved_value = session.execute(
                    query_sql,
                    {"test_key": self.test_key},
                ).scalar_one_or_none()

            assert saved_value == self.test_value
        finally:
            self._drop_test_table()
