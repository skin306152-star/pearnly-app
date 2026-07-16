# -*- coding: utf-8 -*-
"""前门合同真表全链 + 幂等 + RLS 隔离(FD-0a 验收断言①②④ · 照 test_workorder_rls_real_tables 配方)。

真 postgres 上验:①draft→confirm 全链跑通,confirm 后 work_order_items 出现 N 条且 dedupe_key
= file:sha256 与上传逐字节一致;②重复 confirm 幂等(同工单不重建、附件不重复入料);④跨租户
读 ai_goal_contracts 0 行。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_front_desk_rls_real_tables -v
"""

import hashlib
import os
import tempfile
import unittest

from tests.integration._helpers import require_db

TA = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TB = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
_FD_TABLES = ("ai_contract_files", "ai_goal_contracts")
_WO_TABLES = ("work_orders", "work_order_events", "work_order_items", "work_order_deliverables")


class FrontDeskRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"
        cls._tmp = tempfile.mkdtemp()
        os.environ["WORKORDER_STORAGE_DIR"] = cls._tmp

        from core import db, rls
        from services.front_desk import contract_store
        from services.workorder import store

        from tests.integration._workorder_schema import build_workorder_schema

        cls.db, cls.store, cls.contract_store = db, store, contract_store

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(
                "DROP TABLE IF EXISTS ai_contract_files, ai_goal_contracts, "
                "work_order_deliverables, work_order_items, work_order_events, "
                "work_orders CASCADE"
            )
        build_workorder_schema()  # 工单 4 表(confirm 落 work_order_items 用)
        contract_store.ensure_table()  # 前门两表 + tenant RLS

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            for table in _WO_TABLES + _FD_TABLES:
                cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {table} TO pearnly_app")
                cur.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(
                    "DROP TABLE IF EXISTS ai_contract_files, ai_goal_contracts, "
                    "work_order_deliverables, work_order_items, work_order_events, "
                    "work_orders CASCADE"
                )

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "TRUNCATE ai_contract_files, ai_goal_contracts, work_order_deliverables, "
                "work_order_items, work_order_events, work_orders"
            )

    def _draft_with_files(self, tenant, contents):
        """建草稿 + 暂存 N 件 → 返 (contract_id, [sha256...])。"""
        shas = []
        with self.db.get_cursor_rls(tenant, commit=True) as cur:
            contract = self.contract_store.create_draft(
                cur,
                tenant_id=tenant,
                created_by="user:1",
                workspace_client_id=7,
                period="2569-05",
                intent="monthly_vat",
            )
            cid = contract["id"]
            for i, content in enumerate(contents):
                sha = hashlib.sha256(content).hexdigest()
                shas.append(sha)
                path = self.contract_store.stage_file(tenant, cid, content, ".pdf")
                self.contract_store.add_file(
                    cur,
                    tenant_id=tenant,
                    contract_id=cid,
                    file_ref=str(path),
                    original_name=f"doc{i}.pdf",
                    sha256=sha,
                )
        return cid, shas

    def test_confirm_registers_items_with_matching_sha256(self):
        contents = [b"invoice-one-\x00\x01", b"invoice-two-\xf0\x9f\x93\x84"]
        cid, shas = self._draft_with_files(TA, contents)
        with self.db.get_cursor_rls(TA, commit=True) as cur:
            out = self.contract_store.confirm(cur, tenant_id=TA, contract_id=cid, actor="user:1")
        self.assertEqual(out["count"], 2)
        wo_id = out["work_order_id"]
        with self.db.get_cursor_rls(TA) as cur:
            cur.execute(
                "SELECT dedupe_key FROM work_order_items WHERE work_order_id = %s "
                "ORDER BY created_at",
                (wo_id,),
            )
            keys = [r["dedupe_key"] for r in cur.fetchall()]
        self.assertEqual(keys, [f"file:{s}" for s in shas], "入料指纹应与上传 sha256 逐字节一致")

    def test_reconfirm_is_idempotent(self):
        cid, _ = self._draft_with_files(TA, [b"only-one"])
        with self.db.get_cursor_rls(TA, commit=True) as cur:
            first = self.contract_store.confirm(cur, tenant_id=TA, contract_id=cid, actor="user:1")
        with self.db.get_cursor_rls(TA, commit=True) as cur:
            second = self.contract_store.confirm(cur, tenant_id=TA, contract_id=cid, actor="user:1")
        self.assertEqual(first["work_order_id"], second["work_order_id"], "同工单不重建")
        self.assertEqual(second["count"], 0, "已入料附件不重复登记")
        with self.db.get_cursor_rls(TA) as cur:
            cur.execute(
                "SELECT count(*) n FROM work_order_items WHERE work_order_id = %s",
                (first["work_order_id"],),
            )
            self.assertEqual(cur.fetchone()["n"], 1, "重复 confirm 后 items 不翻倍")

    def test_cross_tenant_cannot_read_contracts(self):
        self._draft_with_files(TA, [b"a"])
        self._draft_with_files(TB, [b"b"])
        with self.db.get_cursor_rls(TA) as cur:
            cur.execute("SELECT count(*) n FROM ai_goal_contracts")
            self.assertEqual(cur.fetchone()["n"], 1, "A 只见自己 1 行")
        with self.db.get_cursor_rls("00000000-0000-0000-0000-0000000000ff") as cur:
            cur.execute("SELECT count(*) n FROM ai_goal_contracts")
            self.assertEqual(cur.fetchone()["n"], 0, "陌生租户读合同 0 行")
            cur.execute("SELECT count(*) n FROM ai_contract_files")
            self.assertEqual(cur.fetchone()["n"], 0, "陌生租户读附件 0 行")

    def test_confirm_backfills_work_order_id_and_executing(self):
        cid, _ = self._draft_with_files(TA, [b"x"])
        with self.db.get_cursor_rls(TA, commit=True) as cur:
            out = self.contract_store.confirm(cur, tenant_id=TA, contract_id=cid, actor="user:1")
            contract = self.contract_store.get_contract(cur, tenant_id=TA, contract_id=cid)
        self.assertEqual(str(contract["work_order_id"]), str(out["work_order_id"]))
        self.assertEqual(contract["status"], self.contract_store.STATUS_EXECUTING)


if __name__ == "__main__":
    unittest.main()
