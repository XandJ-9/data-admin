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

    def execute_query(self, sql, params=None):
        self.connect()
        cur = self.conn.cursor()
        try:
            cur.execute(sql, params or [])
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                return {"columns": cols, "rows": rows}
            else:
                self.conn.commit()
                return {"columns": [], "rows": []}
        finally:
            cur.close()

    def list_tables(self):
        raise NotImplementedError

    def get_table_schema(self, table):
        raise NotImplementedError

