from django.test import TestCase

from .base import DataSourceExecutor
from .presto import PrestoExecutor
from .sqlite import SqliteExecutor


class _FakeCursor:
    def __init__(self, rows=None, description=None, execute_error=None):
        self.rows = rows or []
        self.description = description or []
        self.executed_sql = None
        self.executed_params = None
        self.execute_error = execute_error

    def execute(self, sql, params=None):
        if self.execute_error is not None:
            raise self.execute_error
        self.executed_sql = sql
        self.executed_params = params

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        return None


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True


class _CursorFactoryConn:
    def __init__(self, cursors):
        self._cursors = list(cursors)

    def cursor(self):
        if not self._cursors:
            raise AssertionError('No cursor prepared for test')
        return self._cursors.pop(0)


class _TestExecutor(DataSourceExecutor):
    def __init__(self, cursor):
        super().__init__({})
        self.conn = _FakeConn(cursor)

    def connect(self):
        return None

    def build_pagination_sql(self, sql, page_size, offset):
        return f"{sql} LIMIT {int(page_size)} OFFSET {int(offset)}"


class DataSourceExecutorTests(TestCase):
    def test_show_with_leading_comment_should_not_paginate(self):
        cursor = _FakeCursor(rows=[("users",)], description=[("table",)])
        executor = _TestExecutor(cursor)

        original_sql = "-- just a comment\nSHOW TABLES"
        result = executor.execute_query(original_sql, page_size=10, offset=0)

        self.assertEqual(cursor.executed_sql, original_sql)
        self.assertNotIn("next", result)

    def test_select_without_pagination_should_keep_original_sql(self):
        cursor = _FakeCursor(rows=[(1,)], description=[("id",)])
        executor = _TestExecutor(cursor)

        original_sql = "-- line1\nSELECT 1"
        executor.execute_query(original_sql)

        self.assertEqual(cursor.executed_sql, original_sql)

    def test_with_write_sql_should_be_rejected(self):
        cursor = _FakeCursor()
        executor = _TestExecutor(cursor)

        with self.assertRaises(ValueError):
            executor.execute_query(
                "WITH t AS (INSERT INTO logs(msg) VALUES ('x') RETURNING *) SELECT * FROM t"
            )

    def test_pagination_fetch_plus_one_should_set_next(self):
        cursor = _FakeCursor(
            rows=[(1, "a"), (2, "b"), (3, "c")],
            description=[("id",), ("name",)],
        )
        executor = _TestExecutor(cursor)

        result = executor.execute_query("SELECT id, name FROM t", page_size=2, offset=0)

        self.assertIn("LIMIT 3 OFFSET 0", cursor.executed_sql)
        self.assertEqual(len(result["rows"]), 2)
        self.assertEqual(result["next"], {"offset": 2, "pageSize": 2})

    def test_pagination_last_page_should_not_have_next(self):
        cursor = _FakeCursor(
            rows=[(21, "u21"), (22, "u22")],
            description=[("id",), ("name",)],
        )
        executor = _TestExecutor(cursor)

        result = executor.execute_query("SELECT id, name FROM t", page_size=2, offset=20)

        self.assertIn("LIMIT 3 OFFSET 20", cursor.executed_sql)
        self.assertEqual(len(result["rows"]), 2)
        self.assertIsNone(result["next"])

    def test_check_sql_trailing_semicolon_should_pass(self):
        cursor = _FakeCursor()
        executor = _TestExecutor(cursor)

        normalized = executor._check_and_normalized_sql("SELECT 1;")

        self.assertEqual(normalized, "SELECT 1")

    def test_check_sql_multi_statement_should_fail(self):
        cursor = _FakeCursor()
        executor = _TestExecutor(cursor)

        with self.assertRaises(ValueError):
            executor._check_and_normalized_sql("SELECT 1; SELECT 2")

    def test_check_sql_semicolon_in_string_should_pass(self):
        cursor = _FakeCursor()
        executor = _TestExecutor(cursor)

        normalized = executor._check_and_normalized_sql("SELECT 'a;b' AS value")

        self.assertEqual(normalized, "SELECT 'a;b' AS value")

    def test_check_sql_mysql_hash_comment_should_pass(self):
        cursor = _FakeCursor()
        executor = _TestExecutor(cursor)

        normalized = executor._check_and_normalized_sql("# mysql comment\nSELECT 1")

        self.assertEqual(normalized, "SELECT 1")

    def test_strip_trailing_semicolon_should_check_last_non_comment_line(self):
        cursor = _FakeCursor()
        executor = _TestExecutor(cursor)

        sql = "SELECT 1;\n-- trailing comment"
        stripped = executor._strip_trailing_semicolon(sql)

        self.assertEqual(stripped, "SELECT 1\n-- trailing comment")

    def test_strip_trailing_semicolon_should_keep_when_no_semicolon(self):
        cursor = _FakeCursor()
        executor = _TestExecutor(cursor)

        sql = "SELECT 1\n-- trailing comment"
        stripped = executor._strip_trailing_semicolon(sql)

        self.assertEqual(stripped, sql)


class PrestoExecutorTests(TestCase):
    def test_build_show_create_table_sql_should_quote_identifiers(self):
        executor = PrestoExecutor({})

        sql = executor._build_show_create_table_sql('ods', 'user_orders')

        self.assertEqual(sql, 'SHOW CREATE TABLE "ods"."user_orders"')

    def test_quote_identifier_should_escape_double_quotes(self):
        executor = PrestoExecutor({})

        quoted = executor._quote_identifier('ods"prod')

        self.assertEqual(quoted, '"ods""prod"')

    def test_get_table_comment_should_use_quoted_show_create_sql(self):
        first_cursor = _FakeCursor(execute_error=RuntimeError('metadata unavailable'))
        second_cursor = _FakeCursor(rows=[("CREATE TABLE x COMMENT 'safe comment'",)])
        executor = PrestoExecutor({})
        executor.conn = _CursorFactoryConn([first_cursor, second_cursor])

        comment = executor._get_table_comment('ods;drop', 'table--name')

        self.assertEqual(comment, 'safe comment')
        self.assertEqual(
            second_cursor.executed_sql,
            'SHOW CREATE TABLE "ods;drop"."table--name"',
        )


class SqliteExecutorTests(TestCase):
    def test_quote_identifier_should_wrap_table_name(self):
        executor = SqliteExecutor({})

        quoted = executor._quote_identifier('user_orders')

        self.assertEqual(quoted, '"user_orders"')

    def test_quote_identifier_should_escape_double_quotes(self):
        executor = SqliteExecutor({})

        quoted = executor._quote_identifier('user"orders')

        self.assertEqual(quoted, '"user""orders"')
