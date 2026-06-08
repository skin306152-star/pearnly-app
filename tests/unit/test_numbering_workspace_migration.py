# -*- coding: utf-8 -*-
"""PO-7b 迁移守门:连号按主体的 ensure(建索引 + 回填 + 守门式 drop 旧 PK)。

证明:总是建 uq_dns_ws;仅当全表零 NULL 主体时才 DROP 旧 PK(否则保留,兼容路径仍安全)。
内存假游标拦 SQL · 不触真库。
"""

import unittest

import services.db_migrations.numbering_workspace_key as mig


class _Cur:
    def __init__(self, null_count):
        self._null = null_count
        self.sql = []

    def execute(self, sql, params=None):
        self.sql.append(" ".join(sql.split()))

    def fetchone(self):
        last = self.sql[-1]
        if "information_schema.tables" in last:
            return {"exists": 1}  # 表存在
        if "count(*)" in last and "workspace_client_id IS NULL" in last:
            return {"c": self._null}
        return {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _DB:
    def __init__(self, cur):
        self._cur = cur

    def get_cursor(self, commit=False):
        return self._cur


class NumberingMigrationTests(unittest.TestCase):
    def _run(self, null_count):
        cur = _Cur(null_count)
        orig = mig.db
        mig.db = _DB(cur)
        try:
            mig.ensure_numbering_workspace_key()
        finally:
            mig.db = orig
        return " || ".join(cur.sql)

    def test_creates_unique_index_always(self):
        joined = self._run(null_count=0)
        self.assertIn("CREATE UNIQUE INDEX IF NOT EXISTS uq_dns_ws", joined)
        self.assertIn("ADD COLUMN IF NOT EXISTS workspace_client_id", joined)

    def test_drops_old_pk_when_no_null_subjects(self):
        joined = self._run(null_count=0)
        self.assertIn("DROP CONSTRAINT IF EXISTS document_number_sequences_pkey", joined)

    def test_keeps_old_pk_when_null_subjects_remain(self):
        joined = self._run(null_count=3)
        self.assertNotIn("DROP CONSTRAINT", joined)


if __name__ == "__main__":
    unittest.main()
