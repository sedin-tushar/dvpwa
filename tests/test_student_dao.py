import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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
async def test_student_create_uses_parameterized_query():
    """Ensure Student.create uses parameterized queries, not string formatting."""
    cursor_mock = MagicMock()
    cursor_mock.execute = AsyncMock()
    conn = make_conn_mock(cursor_mock)

    await Student.create(conn, name="test_user")

    cursor_mock.execute.assert_called_once()
    call_args = cursor_mock.execute.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    # The query should contain a placeholder, not the literal name
    assert 'test_user' not in query, "SQL injection risk: name was interpolated into query string"
    assert '%(name)s' in query or '%s' in query, "Query should use parameterized placeholder"
    assert params == {'name': 'test_user'}, "Parameters should be passed separately"


@pytest.mark.asyncio
async def test_student_create_sql_injection_safe():
    """Ensure malicious input is not interpolated into the SQL string."""
    cursor_mock = MagicMock()
    cursor_mock.execute = AsyncMock()
    conn = make_conn_mock(cursor_mock)

    malicious_name = "'; DROP TABLE students; --"
    await Student.create(conn, name=malicious_name)

    call_args = cursor_mock.execute.call_args
    query = call_args[0][0]

    # The malicious string must NOT appear in the query itself
    assert malicious_name not in query, "SQL injection vulnerability detected"


def test_student_from_raw():
    raw = (1, 'Alice')
    student = Student.from_raw(raw)
    assert student.id == 1
    assert student.name == 'Alice'


def test_student_from_raw_none():
    assert Student.from_raw(None) is None
