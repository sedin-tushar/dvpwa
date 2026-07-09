import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqli.dao.student import Student


class FakeCursor:
    def __init__(self):
        self.executed_query = None
        self.executed_params = None
        self._rows = []

    async def execute(self, query: str, params=None):
        self.executed_query = query
        self.executed_params = params

    async def fetchone(self):
        return self._rows[0] if self._rows else None

    async def fetchall(self):
        return self._rows

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

    malicious_name = "Robert'); DROP TABLE students;--"
    await Student.create(conn, malicious_name)

    # The raw SQL should NOT contain the malicious string
    assert malicious_name not in cursor.executed_query, (
        "SQL injection: user input was interpolated directly into the query"
    )
    # The params should carry the value safely
    assert cursor.executed_params == {'name': malicious_name}
    # The query should use a placeholder
    assert '%(name)s' in cursor.executed_query


@pytest.mark.asyncio
async def test_create_normal_name():
    """Ensure Student.create works correctly for a normal name."""
    cursor = FakeCursor()
    conn = FakeConn(cursor)

    await Student.create(conn, 'Alice')

    assert cursor.executed_params == {'name': 'Alice'}
    assert 'INSERT INTO students' in cursor.executed_query
