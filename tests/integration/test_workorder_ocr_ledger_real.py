# -*- coding: utf-8 -*-
"""工单 OCR ↔ ocr_history 台账双写真复现(MC2-A2 ② · 件 1 · 本地真库)。

方案 件1 验收:真跑一单(OCR 桩,不触真付费),逐件 ocr_history_id 非空且指向的 ocr_history
行字段与事件流 item_classified 的钱字段同源一致;source=workorder_classify 与主站台账分得开;
双写不产生第二条 ai_usage(成本归因只在 classify._ocr_safe 记一次,这里纯搬读值)。

跑法(CI 无真库自动 skip):
    PEARNLY_INTEGRATION_DB=1 DATABASE_URL=postgresql://... PGSSLMODE=disable \
    python -m unittest tests.integration.test_workorder_ocr_ledger_real
"""

from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path

from tests.integration._helpers import require_db

_OWN_TAX = "0105561000013"


class OcrLedgerDoubleWriteRealDb(unittest.TestCase):
    def setUp(self):
        require_db()
        from core import db
        from services.workorder import engine, store
        from services.workorder.steps import classify, intake
        from tests.integration._workorder_schema import build_workorder_schema

        self.db, self.store, self.engine = db, store, engine
        build_workorder_schema()
        store.ensure_runtime()

        self.tenant = str(uuid.uuid4())
        self.user = str(uuid.uuid4())
        with self.db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users(id, username, password_hash, tenant_id) VALUES (%s, %s, 'x', %s)",
                (self.user, f"wo-ledger-{self.user[:8]}", self.tenant),
            )
            cur.execute(
                "INSERT INTO workspace_clients(tenant_id, user_id, name, tax_id) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (self.tenant, self.user, "Ledger Test Co", _OWN_TAX),
            )
            self.ws_id = int(cur.fetchone()["id"])
            wo = self.store.open_work_order(
                cur, tenant_id=self.tenant, workspace_client_id=self.ws_id, period="2569-06"
            )
            self.wo_id = str(wo["id"])

        self.addCleanup(self._cleanup)

        # OCR 桩:一张买方=本账套的进项票(不触真 OCR/付费)。resolver 桩避免真 workspace 查询。
        stub = {
            "document_type": "tax_invoice",
            "buyer_tax": _OWN_TAX,
            "seller_tax": "0735527000289",
            "invoice_number": "IV-LEDGER-1",
            "subtotal": "100.00",
            "vat": "7.00",
            "total_amount": "107.00",
        }
        for name, repl in (
            ("_ocr_image", lambda path: dict(stub)),
            ("_resolve_own_tax_id", lambda ctx: _OWN_TAX),
            ("_resolve_own_name", lambda ctx: None),
            ("_resolve_own_names", lambda ctx: []),
            ("_m1_enabled", lambda ctx: False),
        ):
            self.addCleanup(setattr, classify, name, getattr(classify, name))
            setattr(classify, name, repl)
        self.classify, self.intake = classify, intake

    def _cleanup(self):
        with self.db.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM ocr_history WHERE user_id = %s", (self.user,))
            cur.execute("DELETE FROM work_order_events WHERE work_order_id = %s", (self.wo_id,))
            cur.execute("DELETE FROM work_order_items WHERE work_order_id = %s", (self.wo_id,))
            cur.execute("DELETE FROM work_orders WHERE id = %s", (self.wo_id,))
            cur.execute("DELETE FROM workspace_clients WHERE id = %s", (self.ws_id,))
            cur.execute("DELETE FROM users WHERE id = %s", (self.user,))

    def test_classify_double_writes_ledger_and_backfills_link(self):
        tmp = tempfile.mkdtemp(prefix="wo-ledger-")
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        p = Path(tmp) / "inv.jpg"
        p.write_bytes(f"fake-jpeg-{uuid.uuid4()}".encode())
        with self.db.get_cursor(commit=True) as cur:
            ctx = self.engine.StepContext(cur=cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            self.intake.register_file(ctx, p, "upload")

        with self.db.get_cursor(commit=True) as cur:
            ctx = self.engine.StepContext(cur=cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            self.classify.run(ctx)

        with self.db.get_cursor() as cur:
            items = self.store.list_items(cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            events = self.store.list_events(cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            self.assertEqual(len(items), 1)
            hid = items[0]["ocr_history_id"]
            self.assertIsNotNone(hid, "件1:ocr_history_id 必须回填")

            # 台账行:source=workorder_classify,归属本账套,pages 钱字段与事件流一致。
            cur.execute(
                "SELECT source, workspace_client_id, total_amount, pages FROM ocr_history WHERE id = %s",
                (hid,),
            )
            row = cur.fetchone()
        self.assertEqual(row["source"], "workorder_classify")
        self.assertEqual(int(row["workspace_client_id"]), self.ws_id)

        evt = next(e for e in events if e["event_type"] == "item_classified")
        money = evt["payload"]["money"]
        self.assertEqual(money["total_amount"], "107.00")
        # ocr_history 行的 fields 与事件流钱字段同源同值(逐字节)。
        fields = (row["pages"] or [{}])[0].get("fields") or {}
        self.assertEqual(fields.get("total_amount"), money["total_amount"])
        self.assertEqual(fields.get("vat"), money["vat"])
        self.assertEqual(fields.get("invoice_number"), money["invoice_number"])

    def _insert_ledger_row(self, source, total):
        with self.db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO ocr_history(user_id, tenant_id, workspace_client_id, filename, "
                "pages, source, total_amount) VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s) RETURNING id",
                (self.user, self.tenant, self.ws_id, "x.jpg", "[]", source, total),
            )
            return str(cur.fetchone()["id"])

    def _enriched_ws_stats(self):
        from services.workspace import store as ws_store

        rows = ws_store.list_workspace_clients_enriched(self.user, tenant_id=self.tenant)
        return next(r for r in rows if int(r["id"]) == self.ws_id)

    def test_workorder_ledger_row_excluded_from_workspace_enriched_stats(self):
        # 裁定②:件1 双写行不进套账管理页发票统计——加一条 workorder_classify 行后
        # invoice_count/total_amount 逐字节不变(去掉 source 黑名单该断言必红)。
        self._insert_ledger_row("manual", 500)
        base = self._enriched_ws_stats()
        self.assertEqual(int(base["invoice_count"]), 1)
        self.assertEqual(float(base["total_amount"]), 500.0)

        self._insert_ledger_row("workorder_classify", 999)
        after = self._enriched_ws_stats()
        self.assertEqual(int(after["invoice_count"]), 1)  # 工单行不计入
        self.assertEqual(float(after["total_amount"]), 500.0)  # 金额逐字节不变

    def test_backfill_is_forward_only_no_ai_usage_double_count(self):
        # ai_usage 不双计:双写不经付费 OCR 调用,ai_usage 表零新增(桩不落 ai_usage)。
        tmp = tempfile.mkdtemp(prefix="wo-ledger2-")
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        p = Path(tmp) / "inv2.jpg"
        p.write_bytes(f"fake-jpeg-{uuid.uuid4()}".encode())
        with self.db.get_cursor(commit=True) as cur:
            ctx = self.engine.StepContext(cur=cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            self.intake.register_file(ctx, p, "upload")
            cur.execute("SELECT count(*) AS n FROM ai_usage WHERE tenant_id = %s", (self.tenant,))
            before = int(cur.fetchone()["n"])
        with self.db.get_cursor(commit=True) as cur:
            ctx = self.engine.StepContext(cur=cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            self.classify.run(ctx)
        with self.db.get_cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM ai_usage WHERE tenant_id = %s", (self.tenant,))
            after = int(cur.fetchone()["n"])
        # 双写自身不产生 ai_usage(桩 OCR 不计费);台账写入零成本记账副作用。
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
