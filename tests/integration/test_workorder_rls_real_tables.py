# -*- coding: utf-8 -*-
"""工单制 4 表真表端到端隔离 + 幂等键验证(M0 T1 · 照 test_sales_rls_real_tables.py 配方)。

真 ensure_workorder_schema()(建表 + apply_tenant_rls)在真 postgres 上验:租户 A 的工单/
事件/条目/交付物,租户 B 一概读不到、塞不进(WITH CHECK)。附带验证 store.py 三处幂等键
真在数据库层面生效(唯一索引 + ON CONFLICT),不只是 SQL 文本看起来对。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_workorder_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

TA = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TB = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
_TABLES = ("work_orders", "work_order_events", "work_order_items", "work_order_deliverables")


class WorkOrderRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.workorder import schema, store

        cls.db, cls.store = db, store
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(
                "DROP TABLE IF EXISTS work_order_deliverables, work_order_items, "
                "work_order_events, work_orders CASCADE"
            )
        schema.ensure_workorder_schema()  # 真建表 + apply_tenant_rls × 4

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            for table in _TABLES:
                cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {table} TO pearnly_app")
                cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")
                cur.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(
                    "DROP TABLE IF EXISTS work_order_deliverables, work_order_items, "
                    "work_order_events, work_orders CASCADE"
                )

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "TRUNCATE work_order_deliverables, work_order_items, "
                "work_order_events, work_orders"
            )

    def _seed_tenant(self, tenant):
        with self.db.get_cursor_rls(tenant, commit=True) as cur:
            wo = self.store.open_work_order(
                cur, tenant_id=tenant, workspace_client_id=7, period="2569-05"
            )
            self.store.append_event(
                cur,
                tenant_id=tenant,
                work_order_id=wo["id"],
                step="intake",
                event_type="step_started",
            )
            self.store.add_item(cur, tenant_id=tenant, work_order_id=wo["id"], source="upload")
            self.store.upsert_deliverable(
                cur, tenant_id=tenant, work_order_id=wo["id"], kind="pp30_draft"
            )
        return wo["id"]

    def test_tenant_sees_only_own_rows(self):
        self._seed_tenant(TA)
        self._seed_tenant(TB)
        for table in _TABLES:
            with self.db.get_cursor_rls(TA) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 1, f"{table}: A 应只见自己 1 行")
            with self.db.get_cursor_rls("00000000-0000-0000-0000-0000000000ff") as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 0, f"{table}: 陌生租户应见 0 行")

    def test_with_check_blocks_cross_tenant_insert(self):
        import psycopg2

        with self.db.get_cursor_rls(TA, commit=True) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute(
                    "INSERT INTO work_orders (tenant_id, workspace_client_id, period) "
                    "VALUES (%s, 7, '2569-05')",
                    (TB,),
                )

    def test_bypass_sees_all(self):
        self._seed_tenant(TA)
        self._seed_tenant(TB)
        with self.db.get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT count(*) n FROM work_orders")
            self.assertEqual(cur.fetchone()["n"], 2)

    def test_reopen_same_scope_returns_existing_work_order_not_a_second_row(self):
        with self.db.get_cursor_rls(TA, commit=True) as cur:
            first = self.store.open_work_order(
                cur, tenant_id=TA, workspace_client_id=7, period="2569-05"
            )
            second = self.store.open_work_order(
                cur, tenant_id=TA, workspace_client_id=7, period="2569-05"
            )
        self.assertEqual(first["id"], second["id"])
        with self.db.get_cursor_rls(TA) as cur:
            cur.execute("SELECT count(*) n FROM work_orders")
            self.assertEqual(cur.fetchone()["n"], 1)

    def test_add_item_same_dedupe_key_does_not_duplicate(self):
        wo_id = self._seed_tenant(TA)
        with self.db.get_cursor_rls(TA, commit=True) as cur:
            self.store.add_item(
                cur,
                tenant_id=TA,
                work_order_id=wo_id,
                source="upload",
                dedupe_key="hash-1",
            )
            self.store.add_item(
                cur,
                tenant_id=TA,
                work_order_id=wo_id,
                source="upload",
                dedupe_key="hash-1",
            )
            cur.execute("SELECT count(*) n FROM work_order_items WHERE dedupe_key = 'hash-1'")
            self.assertEqual(cur.fetchone()["n"], 1)

    def test_upsert_deliverable_same_kind_replaces_not_duplicates(self):
        wo_id = self._seed_tenant(TA)
        with self.db.get_cursor_rls(TA, commit=True) as cur:
            self.store.upsert_deliverable(
                cur, tenant_id=TA, work_order_id=wo_id, kind="pp30_draft", artifact_path="v1.json"
            )
            self.store.upsert_deliverable(
                cur, tenant_id=TA, work_order_id=wo_id, kind="pp30_draft", artifact_path="v2.json"
            )
            deliverables = self.store.list_deliverables(cur, tenant_id=TA, work_order_id=wo_id)
        pp30 = [d for d in deliverables if d["kind"] == "pp30_draft"]
        self.assertEqual(len(pp30), 1)
        self.assertEqual(pp30[0]["artifact_path"], "v2.json")

    def test_events_are_append_only_and_replay_in_order(self):
        wo_id = self._seed_tenant(TA)
        with self.db.get_cursor_rls(TA, commit=True) as cur:
            self.store.append_event(
                cur, tenant_id=TA, work_order_id=wo_id, step="intake", event_type="step_done"
            )
            self.store.append_event(
                cur, tenant_id=TA, work_order_id=wo_id, step="sort", event_type="step_started"
            )
            events = self.store.list_events(cur, tenant_id=TA, work_order_id=wo_id)
        kinds = [e["event_type"] for e in events]
        self.assertEqual(kinds, ["step_started", "step_done", "step_started"])  # 落库顺序

    def test_work_order_cascade_deletes_children(self):
        wo_id = self._seed_tenant(TA)
        with self.db.get_cursor_rls(TA, commit=True) as cur:
            cur.execute("DELETE FROM work_orders WHERE tenant_id = %s AND id = %s", (TA, wo_id))
            for table in _TABLES[1:]:
                cur.execute(f"SELECT count(*) n FROM {table} WHERE work_order_id = %s", (wo_id,))
                self.assertEqual(cur.fetchone()["n"], 0, f"{table} 应随父单据级联清空")


if __name__ == "__main__":
    unittest.main()
