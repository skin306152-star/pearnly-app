# -*- coding: utf-8 -*-
"""R3 银行流水解析逐件检查点真复现(MC2-A2 ① · 件 4 · 本地真库)。

命门 = 银行流水解析(≈OCR,慢)原本整批压在 reconcile 单事务里,中断即整批重烧。检查点后:
每件独立子事务落 item_bank_parsed,主步事务回滚(=进程被杀)也不带走已提交的检查点事件。
本测在真库真事务边界上证:第一件解析已提交 → 第二件解析炸(模拟崩) → 主步回滚 → 已解析件
的 item_bank_parsed 事件仍在(内存 FakeStore 建模不了事务回滚,故必须真库)→ 续跑从事件回放,
零重解析(重烧),事件计数守恒(dedupe_key 锚件,不双落)。

跑法(CI 无真库自动 skip):
    PEARNLY_INTEGRATION_DB=1 DATABASE_URL=postgresql://... PGSSLMODE=disable \
    python -m unittest tests.integration.test_workorder_bank_checkpoint_interrupt
"""

from __future__ import annotations

import tempfile
import unittest
import uuid
from datetime import date
from pathlib import Path

from tests.integration._helpers import require_db


def _bank_parsed_events(store, cur, tenant, wo_id):
    return [
        e
        for e in store.list_events(cur, tenant_id=tenant, work_order_id=wo_id)
        if e["event_type"] == "item_bank_parsed"
    ]


class BankCheckpointInterruptIntegration(unittest.TestCase):
    def setUp(self):
        require_db()
        from core import db
        from services.workorder import engine, store
        from services.workorder.steps import reconcile_bank
        from tests.integration._workorder_schema import build_workorder_schema

        self.db, self.store, self.engine, self.reconcile_bank = db, store, engine, reconcile_bank
        build_workorder_schema()
        store.ensure_runtime()

        self.tenant = str(uuid.uuid4())
        with self.db.get_cursor(commit=True) as cur:
            wo = self.store.open_work_order(
                cur, tenant_id=self.tenant, workspace_client_id=1, period="2569-06"
            )
            self.wo_id = str(wo["id"])
            self.bank_ids = []
            tmp = tempfile.mkdtemp(prefix="wo-bankck-")
            self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
            for i in range(2):
                p = Path(tmp) / f"bank{i}.pdf"
                p.write_bytes(f"fake-bank-{uuid.uuid4()}".encode())
                it = self.store.add_item(
                    cur,
                    tenant_id=self.tenant,
                    work_order_id=self.wo_id,
                    source="upload",
                    kind="bank_statement",
                    file_ref=str(p),
                )
                self.bank_ids.append(it["id"])

        self._saved_parse = reconcile_bank._parse_bank_file
        self.addCleanup(setattr, reconcile_bank, "_parse_bank_file", self._saved_parse)

    def _ctx(self, main_cur):
        return self.engine.StepContext(
            cur=main_cur,
            tenant_id=self.tenant,
            work_order_id=self.wo_id,
            store=self.store,
            data={},
            cursor_factory=lambda: self.db.get_cursor(commit=True),
        )

    def _row(self, seq):
        from services.recon.bank_recon_types import StatementRow

        return StatementRow(date(2026, 6, 7), f"row-{seq}", float(seq), 0.0, 1000.0 - seq)

    def test_checkpoint_survives_crash_and_resume_skips_reparse(self):
        banks = None
        with self.db.get_cursor() as cur:
            banks = self.store.list_items(cur, tenant_id=self.tenant, work_order_id=self.wo_id)
        banks = [b for b in banks if b["kind"] == "bank_statement"]

        # 第一阶段:第 2 件解析炸(模拟崩)。第 1 件的检查点已在独立子事务提交。
        calls = []

        def _parse_crash(ctx, item):
            calls.append(item["id"])
            if item["id"] == self.bank_ids[1]:
                raise RuntimeError("boom mid-parse")
            return [self._row(1)]

        self.reconcile_bank._parse_bank_file = _parse_crash
        with self.assertRaises(RuntimeError):
            with self.db.get_cursor(commit=True) as main_cur:
                self.reconcile_bank._checkpointed_rows(self._ctx(main_cur), banks)

        # 崩后:恰一条 item_bank_parsed(第 1 件)提交并幸存(主步回滚带不走它)。
        with self.db.get_cursor() as cur:
            evts = _bank_parsed_events(self.store, cur, self.tenant, self.wo_id)
        self.assertEqual(len(evts), 1)
        self.assertEqual(evts[0]["payload"]["item_id"], self.bank_ids[0])
        self.assertEqual(calls, [self.bank_ids[0], self.bank_ids[1]])

        # 第二阶段(续跑):换不崩的解析桩。第 1 件从事件回放,零重解析;只解第 2 件。
        resumed = []

        def _parse_ok(ctx, item):
            resumed.append(item["id"])
            return [self._row(2)]

        self.reconcile_bank._parse_bank_file = _parse_ok
        with self.db.get_cursor(commit=True) as main_cur:
            rows = self.reconcile_bank._checkpointed_rows(self._ctx(main_cur), banks)

        self.assertEqual(resumed, [self.bank_ids[1]])  # 只解第 2 件(第 1 件零重烧)
        # 事件计数守恒:两件各一条 item_bank_parsed,dedupe_key 锚件不双落。
        with self.db.get_cursor() as cur:
            evts = _bank_parsed_events(self.store, cur, self.tenant, self.wo_id)
        self.assertEqual(len(evts), 2)
        self.assertEqual({e["payload"]["item_id"] for e in evts}, set(self.bank_ids))
        # 回放行 + 新解析行都在:两件各一行。
        self.assertEqual(len(rows), 2)
        self.assertEqual({r.description for r in rows}, {"row-1", "row-2"})


if __name__ == "__main__":
    unittest.main()
