# -*- coding: utf-8 -*-
"""工单制 L2 真金标测试(真客户 Sister Makeup 2569-05 · M0 任务包 §6)。

不进 CI:skipUnless(PEARNLY_LOCAL_CORPUS)。真语料不进 git,金标数字锁在
`桌面\\pearnly ai\\施工\\T0-语料盘点.md`(策划窗亲读官方 ภ.พ.30 原件锁定)。本文件只跑真
OCR 一次(classify 是唯一付费步):face_value/recalc 两条人工裁决路径复用同一批已分类
结果,靠 reconcile.run() 单步重跑 + 追加第二条 human_decision 事件(同 item 后者胜)
验证,不二次过 OCR。

本地跑法(策划窗):
    set PEARNLY_LOCAL_CORPUS=1
    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://...(真库,workspace_clients 需已有该客户账套记录)
    set GEMINI 等密钥按 ocr-local-eval-recipe 配方就位(本文件不读密钥文件,交生产
    OCR 入口自己解析)
    python -m unittest tests.workorder.test_golden_sister_makeup -v

预期首跑(test_01)停在 reconcile:IMG_2647 flagged(amount_math_fail)无人工裁决。
"""

from __future__ import annotations

import os
import unittest
from decimal import Decimal
from pathlib import Path

from tests.integration._helpers import require_db

CORPUS_ROOT = Path(r"C:\Users\skin3\Desktop\5月")
INTAKE_DIR = CORPUS_ROOT / "A_客户给的原料"
OUT_DIR = CORPUS_ROOT / "_workorder_out"

# 金标常量(T0 语料盘点 · 锁定不许改,真跑对不上是代码的问题不是常量的问题)
GOLDEN_SALES_AMOUNT = Decimal("858780.16")
GOLDEN_OUTPUT_VAT = Decimal("60114.61")
GOLDEN_PURCHASE_AMOUNT = Decimal("418046.86")
GOLDEN_INPUT_VAT = Decimal("29263.28")  # 人工按票面路径(与已申报一致)
GOLDEN_INPUT_VAT_RECALC = Decimal("29254.28")  # IMG_2647 折后重算路径
GOLDEN_TAX_DUE = Decimal("30851.33")
GOLDEN_UNDISPUTED_INPUT_VAT = Decimal("25194.28")  # 10 张无争议票合计 = 金标 − IMG_2647 票面
DISPUTED_TICKET_MARK = "IMG_2647"

TENANT_ID = "22222222-2222-2222-2222-222222222222"  # 本地测试租户,策划窗按真账套改
CLIENT_TAX_ID = "0105567178203"  # บริษัท ซิสเตอร์ เมคอัพ จำกัด
PERIOD = "2569-05"


@unittest.skipUnless(
    os.environ.get("PEARNLY_LOCAL_CORPUS"), "requires-local-corpus(见文件头运行说明)"
)
class GoldenSisterMakeupTests(unittest.TestCase):
    """七条断言对应任务包 §6,不许放水。测试方法按编号顺序执行(unittest 默认按名字母
    序跑同一 TestCase 的方法),同一工单 test_01 完成的 classify 结果被后续测试复用。"""

    work_order_id = None

    @classmethod
    def setUpClass(cls):
        require_db()
        if not INTAKE_DIR.is_dir():
            raise unittest.SkipTest(f"语料目录不存在:{INTAKE_DIR}")

        from core import db
        from services.workorder import engine, store
        from services.workorder.steps import real_handlers

        cls.db, cls.store, cls.engine, cls.real_handlers = db, store, engine, real_handlers
        OUT_DIR.mkdir(exist_ok=True)

    def _client_id(self, cur) -> int:
        cur.execute("SELECT id FROM workspace_clients WHERE tax_id = %s", (CLIENT_TAX_ID,))
        row = cur.fetchone()
        if not row:
            raise unittest.SkipTest(f"workspace_clients 无税号 {CLIENT_TAX_ID} 的账套,先建/核对")
        return row["id"]

    def _items(self, cur):
        return self.store.list_items(
            cur, tenant_id=TENANT_ID, work_order_id=type(self).work_order_id
        )

    def _events(self, cur):
        return self.store.list_events(
            cur, tenant_id=TENANT_ID, work_order_id=type(self).work_order_id
        )

    def test_01_first_run_stops_at_reconcile_on_disputed_ticket(self):
        """跑到 reconcile:IMG_2647 折扣淡票必须 flagged 停下,静默吃掉即测试失败。"""
        files = sorted(str(p) for p in INTAKE_DIR.iterdir() if p.is_file())
        with self.db.get_cursor(commit=True) as cur:
            wo = self.store.open_work_order(
                cur, tenant_id=TENANT_ID, workspace_client_id=self._client_id(cur), period=PERIOD
            )
            type(self).work_order_id = wo["id"]
            ctx = self.engine.StepContext(
                cur=cur,
                tenant_id=TENANT_ID,
                work_order_id=wo["id"],
                data={"intake_files": files, "deliverables_dir": str(OUT_DIR)},
            )
            out = self.engine.run_work_order(ctx, handlers=self.real_handlers())

        self.assertEqual(out.stopped_at, "reconcile")
        self.assertTrue(any("无人工裁决" in r for r in out.result.reasons))

    def test_02_disputed_ticket_flagged_amount_math_fail(self):
        with self.db.get_cursor() as cur:
            target = next(
                it for it in self._items(cur) if DISPUTED_TICKET_MARK in (it["file_ref"] or "")
            )
        self.assertEqual(target["status"], "flagged")
        self.assertEqual(target["flag_reason"], "amount_math_fail")

    def test_03_undisputed_ten_tickets_sum_exactly(self):
        """无争议进项票(kind=purchase_invoice,status=ok)税额合计精确重现金标。"""
        from services.workorder import evidence

        with self.db.get_cursor() as cur:
            items = self._items(cur)
            events = self._events(cur)
        classified = evidence.replay_items_by_type(events, "item_classified")
        ok_purchases = [
            it for it in items if it["kind"] == "purchase_invoice" and it["status"] == "ok"
        ]
        total = sum(
            (Decimal(str((classified[it["id"]]["payload"]["money"] or {}).get("vat") or "0")))
            for it in ok_purchases
        )
        self.assertEqual(len(ok_purchases), 10)
        self.assertEqual(total, GOLDEN_UNDISPUTED_INPUT_VAT)

    def test_04_face_value_then_recalc_decision_paths(self):
        """两条裁决路径都测:先 face_value 跑完(官方对齐),再追加 recalc 裁决(同 item
        后者胜)单步重跑 reconcile 验证折后重算终值——不二次过 OCR。"""
        from services.workorder.steps import reconcile

        with self.db.get_cursor(commit=True) as cur:
            disputed = next(
                it for it in self._items(cur) if DISPUTED_TICKET_MARK in (it["file_ref"] or "")
            )
            self.store.append_event(
                cur,
                tenant_id=TENANT_ID,
                work_order_id=type(self).work_order_id,
                step="reconcile",
                event_type="human_decision",
                actor="user:cli",
                payload={"item_id": disputed["id"], "decision": "face_value", "values": {}},
            )
            ctx = self.engine.StepContext(
                cur=cur,
                tenant_id=TENANT_ID,
                work_order_id=type(self).work_order_id,
                data={"deliverables_dir": str(OUT_DIR)},
            )
            out = self.engine.run_work_order(ctx, handlers=self.real_handlers())
            self.assertTrue(out.completed, f"face_value 裁决后应完整走完:{out.status}")

            pp30 = next(
                d
                for d in self.store.list_deliverables(
                    cur, tenant_id=TENANT_ID, work_order_id=type(self).work_order_id
                )
                if d["kind"] == "pp30_draft"
            )
            self.assertEqual(Decimal(pp30["numbers"]["input_vat"]), GOLDEN_INPUT_VAT)
            self.assertEqual(Decimal(pp30["numbers"]["sales_amount"]), GOLDEN_SALES_AMOUNT)
            self.assertEqual(Decimal(pp30["numbers"]["output_vat"]), GOLDEN_OUTPUT_VAT)
            self.assertEqual(Decimal(pp30["numbers"]["purchase_amount"]), GOLDEN_PURCHASE_AMOUNT)
            self.assertEqual(Decimal(pp30["numbers"]["tax_due"]), GOLDEN_TAX_DUE)

            # 追加 recalc 裁决(同一票),reconcile 回放取最新一条 → 单步重跑验证折后终值。
            self.store.append_event(
                cur,
                tenant_id=TENANT_ID,
                work_order_id=type(self).work_order_id,
                step="reconcile",
                event_type="human_decision",
                actor="user:cli",
                payload={
                    "item_id": disputed["id"],
                    "decision": "recalc",
                    "values": {"vat": "4060.00"},
                },
            )
            recalced = reconcile.run(ctx)
            self.assertEqual(Decimal(recalced.payload["input_vat_total"]), GOLDEN_INPUT_VAT_RECALC)

    def test_05_tax_due_diff_only_explained_by_disputed_ticket(self):
        """应缴(按票面裁决路径)与官方一致,且这是唯一差异来源——用 03 的无争议合计
        佐证:金标 = 无争议合计 + IMG_2647 票面 VAT(4069.00),差额可枚举解释。"""
        disputed_face_vat = GOLDEN_INPUT_VAT - GOLDEN_UNDISPUTED_INPUT_VAT
        self.assertEqual(disputed_face_vat, Decimal("4069.00"))
        self.assertEqual(GOLDEN_OUTPUT_VAT - GOLDEN_INPUT_VAT, GOLDEN_TAX_DUE)

    def test_06_idempotent_rerun_keeps_events_and_deliverables_stable(self):
        with self.db.get_cursor(commit=True) as cur:
            events_before = len(self._events(cur))
            deliverables_before = self.store.list_deliverables(
                cur, tenant_id=TENANT_ID, work_order_id=type(self).work_order_id
            )
            ctx = self.engine.StepContext(
                cur=cur,
                tenant_id=TENANT_ID,
                work_order_id=type(self).work_order_id,
                data={"deliverables_dir": str(OUT_DIR)},
            )
            out = self.engine.run_work_order(ctx, handlers=self.real_handlers())
            events_after = len(self._events(cur))
            deliverables_after = self.store.list_deliverables(
                cur, tenant_id=TENANT_ID, work_order_id=type(self).work_order_id
            )

        self.assertTrue(out.completed)
        self.assertEqual(events_before, events_after)
        self.assertEqual(len(deliverables_before), len(deliverables_after))

    def test_07_resume_after_kill_mid_classify_matches_uninterrupted_run(self):
        """断点续跑:人为在 classify 后、reconcile 真正跑之前切断(模拟进程被杀),续跑
        重建的数字须与常规流程(test_01→04)完全一致。开独立 intent 的工单,避免复用
        已完成工单——本测试会再跑一次真 OCR,成本较高,可按需单独执行/跳过。"""
        from services.workorder.engine import StepResult

        files = sorted(str(p) for p in INTAKE_DIR.iterdir() if p.is_file())
        paused = {"once": False}
        handlers = dict(self.real_handlers())
        real_reconcile = handlers["reconcile"]

        def _pause_once_then_real(ctx):
            if not paused["once"]:
                paused["once"] = True
                return StepResult.needs(["manual_pause_after_classify"])
            return real_reconcile(ctx)

        handlers["reconcile"] = _pause_once_then_real

        with self.db.get_cursor(commit=True) as cur:
            wo = self.store.open_work_order(
                cur,
                tenant_id=TENANT_ID,
                workspace_client_id=self._client_id(cur),
                period=PERIOD,
                intent="monthly_vat_resume_check",
            )
            ctx = self.engine.StepContext(
                cur=cur,
                tenant_id=TENANT_ID,
                work_order_id=wo["id"],
                data={"intake_files": files, "deliverables_dir": str(OUT_DIR / "resume_check")},
            )
            out1 = self.engine.run_work_order(ctx, handlers=handlers)
            self.assertEqual(out1.stopped_at, "reconcile")
            self.assertEqual(out1.result.missing, ("manual_pause_after_classify",))

            disputed = next(
                it
                for it in self.store.list_items(cur, tenant_id=TENANT_ID, work_order_id=wo["id"])
                if DISPUTED_TICKET_MARK in (it["file_ref"] or "")
            )
            self.store.append_event(
                cur,
                tenant_id=TENANT_ID,
                work_order_id=wo["id"],
                step="reconcile",
                event_type="human_decision",
                actor="user:cli",
                payload={"item_id": disputed["id"], "decision": "face_value", "values": {}},
            )
            ctx2 = self.engine.StepContext(
                cur=cur,
                tenant_id=TENANT_ID,
                work_order_id=wo["id"],
                data={"deliverables_dir": str(OUT_DIR / "resume_check")},
            )
            out2 = self.engine.run_work_order(ctx2, handlers=handlers)

            pp30 = next(
                d
                for d in self.store.list_deliverables(
                    cur, tenant_id=TENANT_ID, work_order_id=wo["id"]
                )
                if d["kind"] == "pp30_draft"
            )

        self.assertTrue(out2.completed)
        self.assertEqual(Decimal(pp30["numbers"]["input_vat"]), GOLDEN_INPUT_VAT)


if __name__ == "__main__":
    unittest.main()
