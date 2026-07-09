import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from sqli.dao.student import Student


class TestStudentFromRaw:
    def test_from_raw_with_data(self):
        raw = (1, "Alice")
        student = Student.from_raw(raw)
        assert student == Student(id=1, name="Alice")

    def test_from_raw_with_none(self):
        result = Student.from_raw(None)
        assert result is None


class TestStudentCreate:
    @pytest.mark.asyncio
    async def test_create_uses_parameterized_query(self):
        """Ensure create() uses parameterized query, not string interpolation."""
        mock_cursor = AsyncMock()
        mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor.__aexit__ = AsyncMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor = MagicMock(return_value=mock_cursor)

        await Student.create(mock_conn, name="Alice")

        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        # The query should NOT contain the literal name value
        assert "Alice" not in query
        # The query should use a placeholder
        assert "%(name)s" in query
        # The name should be passed as a parameter
        assert params == {'name': "Alice"}

    @pytest.mark.asyncio
    async def test_create_sql_injection_safe(self):
        """Ensure SQL injection attempts are passed as parameters, not interpolated."""
        mock_cursor = AsyncMock()
        mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor.__aexit__ = AsyncMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor = MagicMock(return_value=mock_cursor)

        malicious_name = "Robert'); DROP TABLE students;--"
        await Student.create(mock_conn, name=malicious_name)

        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        # The malicious string should NOT be in the query itself
        assert malicious_name not in query
        # It should be safely passed as a parameter
        assert params == {'name': malicious_name}
