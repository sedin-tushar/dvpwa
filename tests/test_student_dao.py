import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

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

    await Student.create(conn, name="O'Reilly")

    # The query must NOT contain the literal name value
    assert "O'Reilly" not in cursor.executed_query, (
        "SQL injection risk: name was interpolated directly into the query string"
    )
    # The query must use a placeholder
    assert "%(name)s" in cursor.executed_query
    # The name must be passed as a parameter
    assert cursor.executed_params == {'name': "O'Reilly"}


@pytest.mark.asyncio
async def test_create_passes_name_as_parameter():
    """Ensure the name value is passed via params, not baked into the SQL."""
    cursor = FakeCursor()
    conn = FakeConn(cursor)

    await Student.create(conn, name="Alice")

    assert cursor.executed_params is not None
    assert cursor.executed_params.get('name') == "Alice"
