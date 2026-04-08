from datetime import datetime, date, time
from decimal import Decimal
import re


class DataSourceExecutor:

    username = None
    password = None
    database = None
    params = None
    host = None
    port = None

    def __init__(self, info):
        self.info = info or {}
        self.conn = None

    def connect(self):
        raise NotImplementedError

    def close(self):
        try:
            if self.conn:
                self.conn.close()
        finally:
            self.conn = None

    def test_connection(self):
        self.connect()
        return True

    def execute_query(self, sql, params=None, page_size=None, offset=None):
        self.connect()
        original_sql = (sql or '').strip()
        # 基础校验：仅允许查询类语句，禁止执行非查询（如 INSERT/UPDATE/DELETE/DDL）
        normalized_sql = self._check_and_normalized_sql(original_sql)
        normalized_sql_lower = normalized_sql.lower()
        execute_sql = original_sql
        paginated = False
        query_page_size = None
        if isinstance(page_size, int) and page_size > 0 and isinstance(offset, int) and offset >= 0:
            if not normalized_sql_lower.startswith(('show', 'describe', 'explain')):
                # 通过多取 1 条判断是否存在下一页，避免总数整除时误判
                query_page_size = int(page_size)
                fetch_size = query_page_size + 1
                execute_sql = self.build_pagination_sql(
                    self._strip_trailing_semicolon(original_sql),
                    fetch_size,
                    int(offset),
                )
                paginated = True
        cur = self.conn.cursor()
        try:
            cur.execute(execute_sql, params)
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                has_more = False
                if paginated and query_page_size is not None:
                    has_more = len(rows) > query_page_size
                    rows = rows[:query_page_size]
                # 对返回结果进行时间戳/日期/时间等类型的格式化，遵循统一字符串输出规范
                fmt_rows = [
                    tuple(self._format_cell(v) for v in r)
                    for r in rows
                ]
                data = {"columns": cols, "rows": fmt_rows}
                if paginated:
                    data["next"] = {"offset": int(offset) + int(page_size), "pageSize": int(page_size)} if has_more else None
                return data
            else:
                self.conn.commit()
                return {"columns": [], "rows": []}
        finally:
            cur.close()

    def build_pagination_sql(self, sql, page_size, offset):
        return sql

    def list_tables(self):
        raise NotImplementedError

    def get_table_schema(self, table):
        raise NotImplementedError

    def get_table_info(self, table):
        raise NotImplementedError

    def list_tables_info(self):
        raise NotImplementedError

    def get_databases(self):
        return None

    def _format_cell(self, v):
        # 统一时间戳/日期/时间格式化为字符串；数值保留原样，Decimal 转为 float
        if isinstance(v, datetime):
            return v.strftime('%Y-%m-%d %H:%M:%S')
        # 避免 datetime 命中 date 分支，需先判断 datetime
        if isinstance(v, date):
            return v.strftime('%Y-%m-%d')
        if isinstance(v, time):
            return v.strftime('%H:%M:%S')
        if isinstance(v, Decimal):
            return float(v)
        return v

    def _check_and_normalized_sql(self, sql):
        s_raw = (sql or '').strip()
        if not s_raw:
            raise ValueError('SQL不能为空')

        # 先移除块注释，再移除行注释，避免注释干扰前缀判定
        s_no_block = re.sub(r'/\*.*?\*/', ' ', s_raw, flags=re.DOTALL)
        lines = []
        for line in s_no_block.split('\n'):
            stripped = line.lstrip()
            if stripped.startswith('--') or stripped.startswith('#'):
                continue
            line = re.sub(r'\s--.*$', '', line)
            if line.strip():
                lines.append(line)
        s = '\n'.join(lines).strip()

        allowed_prefixes = ('select', 'with', 'show', 'describe', 'explain')
        if s == '':
            raise ValueError('SQL不能为空')

        # 仅允许单条语句；仅在字符串字面量外识别分号
        if self._has_multiple_statements(s):
            raise ValueError('仅允许执行单条查询语句，禁止多语句执行')
        s = s.rstrip()
        if s.endswith(';'):
            s = s[:-1].rstrip()

        s_lower = s.lower()
        if not s_lower.startswith(allowed_prefixes):
            raise ValueError('仅允许执行查询语句（SELECT/WITH/SHOW/DESCRIBE/EXPLAIN），禁止执行其他语句')

        if s_lower.startswith('with'):
            # WITH 语句存在写操作绕过风险，显式拦截常见写/DDL关键词
            if re.search(r'\b(insert|update|delete|merge|create|drop|alter|truncate|grant|revoke|replace)\b', s_lower):
                raise ValueError('仅允许执行查询语句，WITH 语句中禁止包含写操作或DDL')
            if 'select' not in s_lower:
                raise ValueError('WITH 语句仅允许用于查询（SELECT）')

        return s

    def _has_multiple_statements(self, sql):
        parts = []
        current = []
        in_single = False
        in_double = False
        i = 0

        while i < len(sql):
            ch = sql[i]
            if in_single:
                current.append(ch)
                if ch == "'":
                    # SQL 单引号转义：''
                    if i + 1 < len(sql) and sql[i + 1] == "'":
                        current.append(sql[i + 1])
                        i += 1
                    else:
                        in_single = False
                i += 1
                continue

            if in_double:
                current.append(ch)
                if ch == '"':
                    # 双引号转义：""
                    if i + 1 < len(sql) and sql[i + 1] == '"':
                        current.append(sql[i + 1])
                        i += 1
                    else:
                        in_double = False
                i += 1
                continue

            if ch == "'":
                in_single = True
                current.append(ch)
                i += 1
                continue

            if ch == '"':
                in_double = True
                current.append(ch)
                i += 1
                continue

            if ch == ';':
                part = ''.join(current).strip()
                if part:
                    parts.append(part)
                current = []
                i += 1
                continue

            current.append(ch)
            i += 1

        tail = ''.join(current).strip()
        if tail:
            parts.append(tail)

        return len(parts) > 1

    def _strip_trailing_semicolon(self, sql):
        lines = (sql or '').split('\n')
        if not lines:
            return sql

        for idx in range(len(lines) - 1, -1, -1):
            line = lines[idx]
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('--') or stripped.startswith('#'):
                continue

            code = re.sub(r'\s--.*$', '', line)
            code = re.sub(r'\s#.*$', '', code)
            if code.rstrip().endswith(';'):
                semicolon_index = code.rfind(';')
                code_without_semicolon = code[:semicolon_index] + code[semicolon_index + 1:]
                lines[idx] = line.replace(code, code_without_semicolon, 1)
                return '\n'.join(lines)
            return '\n'.join(lines)

        return '\n'.join(lines)
