import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from sqli.dao.student import Student


class FakeCursor:
    def __init__(self):
        self.execute = AsyncMock()
        self.fetchone = AsyncMock(return_value=None)
        self.fetchall = AsyncMock(return_value=[])

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeConn:
    def __init__(self, cursor: FakeCursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


@pytest.mark.asyncio
async def test_create_uses_parameterized_query():
    """Ensure Student.create uses parameterized query, not string formatting."""
    cursor = FakeCursor()
    conn = FakeConn(cursor)

    await Student.create(conn, name="Alice")

    cursor.execute.assert_called_once()
    args = cursor.execute.call_args

    # First positional arg is the SQL string
    sql = args[0][0]
    # Second positional arg is the params dict
    params = args[0][1]

    # The name must NOT be embedded in the SQL string
    assert "Alice" not in sql, "Name should not be interpolated into SQL string"
    # The name must be passed as a parameter
    assert params == {"name": "Alice"}, f"Expected params dict with name, got {params}"
    # The SQL should use a placeholder
    assert "%(name)s" in sql


@pytest.mark.asyncio
async def test_create_sql_injection_safe():
    """Ensure malicious input is not interpolated into the SQL string."""
    cursor = FakeCursor()
    conn = FakeConn(cursor)

    malicious_name = "Robert'); DROP TABLE students;--"
    await Student.create(conn, name=malicious_name)

    args = cursor.execute.call_args
    sql = args[0][0]

    # Malicious input must not appear in the SQL string itself
    assert malicious_name not in sql, "SQL injection payload must not be in query string"
