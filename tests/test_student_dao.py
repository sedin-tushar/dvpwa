import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from sqli.dao.student import Student


class AsyncContextManagerMock:
    def __init__(self, cursor_mock):
        self._cursor = cursor_mock

    async def __aenter__(self):
        return self._cursor

    async def __aexit__(self, *args):
        pass


def make_conn_mock(cursor_mock):
    conn = MagicMock()
    conn.cursor.return_value = AsyncContextManagerMock(cursor_mock)
    return conn


@pytest.mark.asyncio
async def test_create_uses_parameterized_query():
    """Ensure Student.create uses a parameterized query, not string formatting."""
    cursor = MagicMock()
    cursor.execute = AsyncMock()
    conn = make_conn_mock(cursor)

    await Student.create(conn, name="Alice")

    cursor.execute.assert_called_once()
    args = cursor.execute.call_args
    query = args[0][0]
    params = args[0][1]

    # The query must NOT contain the literal name embedded in it
    assert "Alice" not in query, "Name should not be embedded in the SQL string"
    # The query must use a placeholder
    assert "%(name)s" in query or "%s" in query
    # The params must contain the name
    assert params == {"name": "Alice"}


@pytest.mark.asyncio
async def test_create_sql_injection_safe():
    """Ensure SQL injection attempts are passed as parameters, not interpolated."""
    cursor = MagicMock()
    cursor.execute = AsyncMock()
    conn = make_conn_mock(cursor)

    malicious_name = "Robert'); DROP TABLE students;--"
    await Student.create(conn, name=malicious_name)

    cursor.execute.assert_called_once()
    args = cursor.execute.call_args
    query = args[0][0]
    params = args[0][1]

    # The malicious string must NOT be in the query itself
    assert "DROP TABLE" not in query
    # It must be safely passed as a parameter
    assert params == {"name": malicious_name}


@pytest.mark.asyncio
async def test_from_raw_none():
    assert Student.from_raw(None) is None


@pytest.mark.asyncio
async def test_from_raw_valid():
    s = Student.from_raw((1, "Alice"))
    assert s.id == 1
    assert s.name == "Alice"
