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
    """Ensure Student.create uses parameterized query, not string interpolation."""
    cursor = MagicMock()
    cursor.execute = AsyncMock()
    conn = make_conn_mock(cursor)

    await Student.create(conn, name="Alice")

    cursor.execute.assert_called_once()
    args = cursor.execute.call_args
    query = args[0][0]
    params = args[0][1]

    # The query must NOT contain the literal name value
    assert "Alice" not in query, "Name should not be interpolated into the SQL string"
    # The query must use a placeholder
    assert "%(name)s" in query or "%s" in query
    # The params must contain the name
    assert params == {"name": "Alice"} or params == ("Alice",)


@pytest.mark.asyncio
async def test_create_sql_injection_safe():
    """Ensure SQL injection payload is passed as parameter, not in query string."""
    cursor = MagicMock()
    cursor.execute = AsyncMock()
    conn = make_conn_mock(cursor)

    malicious_name = "'; DROP TABLE students; --"
    await Student.create(conn, name=malicious_name)

    cursor.execute.assert_called_once()
    args = cursor.execute.call_args
    query = args[0][0]
    params = args[0][1]

    # The malicious payload must NOT appear in the query string
    assert malicious_name not in query, (
        "SQL injection payload must not be interpolated into the query string"
    )
    # It should appear in the params
    assert malicious_name in params.values() or malicious_name in params
