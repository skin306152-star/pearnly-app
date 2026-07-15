# -*- coding: utf-8 -*-
"""IN-0d 验收断言 3 · 客户名录导入 commit 真库全链(docker pearnly-db)。

导入 5 行(3 valid + 1 dup + 1 error)→ 建 3 行、dup 行落 skip、error 行诚实点名原因;
同文件重导 → 已建的 3 行这次全落 skip(税号已在库,commit 幂等 · 零新建),原本的
dup 行仍 skip,结构性 error 行(缺 name)结构没变仍 error——三态如实反映当次真实状态,
不是靠"记住上次结果"硬凑成全绿。

照 tests/unit/test_workorder_crypto_db_chain.py 的门(库不可用 skip 不 fail,自带
_require_db,不 import tests.integration._helpers 避免全量 discovery 时的 env 副作用)。
本地跑:

    PEARNLY_INTEGRATION_DB=1 PGSSLMODE=disable \
    DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly \
    python -m unittest tests.integration.test_client_import_commit_real_db -v
"""

from __future__ import annotations

import os
import unittest
import uuid


def _require_db() -> None:
    if not os.environ.get("PEARNLY_INTEGRATION_DB", "").strip():
        raise unittest.SkipTest("真库测试需要 PEARNLY_INTEGRATION_DB=1 + DATABASE_URL 才跑")
    if not os.environ.get("DATABASE_URL", "").strip():
        raise unittest.SkipTest("真库测试需要 env DATABASE_URL")


class ClientImportCommitRealDbTests(unittest.TestCase):
    def setUp(self):
        _require_db()
        os.environ.setdefault("PGSSLMODE", "disable")

        from core import db
        from routes import client_import_routes as r
        from services.workspace import store

        self.db, self.r = db, r
        store.ensure_workspace_tables()

        self.tenant_id = str(uuid.uuid4())
        self.user = {"id": str(uuid.uuid4())}
        self.addCleanup(self._cleanup)

        # 预置一个已存在的账套主体(模拟"税号已在库"的重复行)。M1 泰文名闸现网默认全开
        # (2026-07 拍板"测完没问题就全开"),名字必须含泰文字符才能过校验——同真实事务所
        # 客户名录场景一致(泰国注册公司名本就是泰文)。
        self.dup_tax_id = "0105551000019"
        wid = db.create_workspace_client(
            self.user["id"], self.tenant_id, "บริษัท เดิม จำกัด", tax_id=self.dup_tax_id
        )
        self.assertIsNotNone(wid)

    def _cleanup(self):
        with self.db.get_cursor_rls(tenant_id=self.tenant_id, commit=True) as cur:
            cur.execute("DELETE FROM workspace_clients WHERE tenant_id = %s", (self.tenant_id,))

    def _rows(self):
        r = self.r
        return [
            r.ClientImportRow(row_index=0, name="บริษัท อัลฟ่า จำกัด", tax_id="0105551000027"),
            r.ClientImportRow(row_index=1, name="บริษัท เบต้า จำกัด", tax_id="0105551000035"),
            r.ClientImportRow(row_index=2, name="บริษัท แกมม่า จำกัด", tax_id="0105551000043"),
            r.ClientImportRow(row_index=3, name="บริษัท ซ้ำ จำกัด", tax_id=self.dup_tax_id),
            r.ClientImportRow(row_index=4, name=""),  # 缺 name → 结构性 error
        ]

    def _commit(self, rows):
        return [self.r._judge_row(row, self.user, self.tenant_id, dry_run=False) for row in rows]

    def test_first_commit_three_valid_one_dup_one_error(self):
        results = self._commit(self._rows())
        by_idx = {r["row_index"]: r for r in results}
        self.assertEqual(by_idx[0]["status"], "created")
        self.assertEqual(by_idx[1]["status"], "created")
        self.assertEqual(by_idx[2]["status"], "created")
        self.assertEqual(by_idx[3]["status"], "skip")
        self.assertEqual(by_idx[3]["reason"], "workspace.tax_id_duplicate")
        self.assertEqual(by_idx[4]["status"], "error")
        self.assertEqual(by_idx[4]["reason"], "client_import.err_missing_name")
        created = sum(1 for r in results if r["status"] == "created")
        self.assertEqual(created, 3)

    def test_reimport_same_file_creates_zero_new_rows(self):
        first = self._commit(self._rows())
        self.assertEqual(sum(1 for r in first if r["status"] == "created"), 3)

        second = self._commit(self._rows())
        by_idx = {r["row_index"]: r for r in second}
        # 命门:commit 幂等——已建的行(0/1/2)这次全落 skip,零新建。
        self.assertEqual(by_idx[0]["status"], "skip")
        self.assertEqual(by_idx[1]["status"], "skip")
        self.assertEqual(by_idx[2]["status"], "skip")
        # 本就存在的重复行仍 skip(结构没变)。
        self.assertEqual(by_idx[3]["status"], "skip")
        # 结构性错误行结构没变,如实仍报同一个错(不是靠"记结果"硬凑成全 skip)。
        self.assertEqual(by_idx[4]["status"], "error")
        created = sum(1 for r in second if r["status"] == "created")
        self.assertEqual(created, 0, "重导不得二次创建")


if __name__ == "__main__":
    unittest.main()
