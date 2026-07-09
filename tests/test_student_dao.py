import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from sqli.dao.student import Student


class AsyncContextManagerMock:
    def __init__(self, cursor_mock):
        self.cursor_mock = cursor_mock

    async def __aenter__(self):
        return self.cursor_mock

    async def __aexit__(self, *args):
        pass


def make_conn_mock(cursor_mock):
    conn = MagicMock()
    conn.cursor.return_value = AsyncContextManagerMock(cursor_mock)
    return conn


@pytest.mark.asyncio
async def test_create_uses_parameterized_query():
    """Ensure Student.create uses parameterized query, not string formatting."""
    cursor_mock = AsyncMock()
    conn = make_conn_mock(cursor_mock)

    await Student.create(conn, name="test_user")

    cursor_mock.execute.assert_called_once()
    call_args = cursor_mock.execute.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    # The query should NOT contain the literal name embedded in it
    assert 'test_user' not in query, "SQL injection: name was embedded directly in query string"
    # The query should use a placeholder
    assert '%(name)s' in query
    # The params should contain the name
    assert params == {'name': 'test_user'}


@pytest.mark.asyncio
async def test_create_sql_injection_safe():
    """Ensure malicious input is not embedded in the query string."""
    cursor_mock = AsyncMock()
    conn = make_conn_mock(cursor_mock)

    malicious_name = "Robert'); DROP TABLE students;--"
    await Student.create(conn, name=malicious_name)

    cursor_mock.execute.assert_called_once()
    call_args = cursor_mock.execute.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    # The malicious string must NOT appear in the query itself
    assert malicious_name not in query
    assert 'DROP' not in query
    # It should be safely passed as a parameter
    assert params == {'name': malicious_name}


@pytest.mark.asyncio
async def test_from_raw_none():
    assert Student.from_raw(None) is None


@pytest.mark.asyncio
async def test_from_raw_valid():
    s = Student.from_raw((1, 'Alice'))
    assert s.id == 1
    assert s.name == 'Alice'
