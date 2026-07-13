# -*- coding: utf-8 -*-
"""LINE 客户答完题 → 工单自动续跑,真库全链(MC2-A1 件 5 · D2/R3 终验剧本的本地版)。

剧本:方向不明票把工单卡在 reconcile(classify 判不出进/销 → flagged,reconcile 停机点名)
→ 会计把问题挂进待问池并推送(mark_sent 落 batch_seq)→ 客户 LINE 答「1 ซื้อ」→
handle_answer 全链:定位批次 → record_decision(assign_kind·purchase_invoice,
actor=line_client:…)→ 问题转 applied → 自动续跑(runner.request_run 守护线程)→ 引擎
重跑 reconcile 越过方向停机点、推进到下一自然停点(缺销项 → needs),全程零人手。

OCR 全程注入桩(不触达付费调用);LINE 回执走 reply_token=None 静默路;闸 patch 开
(闸机制本身有独立守门测试)。跑法同 test_workorder_reaper_interrupt(CI 无真库自动 skip)。
"""

from __future__ import annotations

import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from tests.integration._helpers import require_db

_OWN_TAX = "0105561000013"


class LineAnswerAutoResumeIntegration(unittest.TestCase):
    def setUp(self):
        require_db()
        from core import db
        from services.line_binding import line_client_contact
        from services.line_binding import line_client_pool_store as pool_store
        from services.workorder import store
        from services.workorder.steps import classify
        from tests.integration._workorder_schema import build_workorder_schema

        self.db, self.store, self.pool_store = db, store, pool_store
        build_workorder_schema()
        store.ensure_runtime()
        pool_store.ensure_table()
        line_client_contact.ensure_table()

        # OCR 桩:文件名带 amb 的票双边税号都不是自家 → direction_ambiguous;其余为干净进项票。
        def stub_ocr(path):
            name = Path(path).stem
            seq = "".join(ch for ch in name if ch.isdigit()) or "0"
            fields = {
                "document_type": "tax_invoice",
                "invoice_number": f"INV-{name}",
                "subtotal": "100.00",
                "vat": "7.00",
                "total_amount": "107.00",
                "seller_tax": f"1{int(seq):012d}",
            }
            if "amb" not in name:
                fields["buyer_tax"] = _OWN_TAX
            return fields

        for attr, repl in (
            ("_ocr_image", stub_ocr),
            ("_resolve_own_tax_id", lambda ctx: _OWN_TAX),
            ("_resolve_own_name", lambda ctx: None),
            ("_resolve_own_names", lambda ctx: []),
            ("_m1_enabled", lambda ctx: False),
        ):
            self.addCleanup(setattr, classify, attr, getattr(classify, attr))
            setattr(classify, attr, repl)

        self.tenant = str(uuid.uuid4())
        self.ws_id = 1
        self.line_user = f"U-e2e-{uuid.uuid4().hex[:12]}"
        with self.db.get_cursor(commit=True) as cur:
            wo = self.store.open_work_order(
                cur, tenant_id=self.tenant, workspace_client_id=self.ws_id, period="2569-06"
            )
        self.wo_id = str(wo["id"])

    def _register_materials(self, names):
        from services.workorder import engine
        from services.workorder.steps import intake

        tmp = tempfile.mkdtemp(prefix="wo-line-")
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        with self.db.get_cursor(commit=True) as cur:
            ctx = engine.StepContext(cur=cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            for name in names:
                p = Path(tmp) / name
                p.write_bytes(f"fake-jpeg-{uuid.uuid4()}".encode())
                intake.register_file(ctx, p, "upload")

    def _events(self, cur):
        return self.store.list_events(cur, tenant_id=self.tenant, work_order_id=self.wo_id)

    def _poll(self, predicate, timeout=90, desc=""):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self.db.get_cursor() as cur:
                got = predicate(cur)
            if got:
                return got
            time.sleep(0.2)
        self.fail(f"等待超时({timeout}s): {desc}")

    def test_line_answer_resumes_order_without_human(self):
        from services.line_binding import line_client_answer, line_client_contact
        from services.workorder import runner

        # ① 卡单:方向不明票 + 一张干净票,推进到 reconcile 停机(flagged 无裁决点名)。
        self._register_materials(["amb0.jpg", "item1.jpg"])
        out = runner.advance(self.tenant, self.wo_id)
        self.assertEqual(out["status"], "stuck")
        with self.db.get_cursor() as cur:
            items = self.store.list_items(cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            evts = self._events(cur)
        amb = next(i for i in items if (i.get("flag_reason") or "").startswith("direction"))
        boundary_id = max(e["id"] for e in evts)

        # ② 入池 + 推送(mark_sent 落 batch_seq=1,与生产攒批同一写口)+ 绑定客户 LINE。
        self.assertTrue(line_client_contact.bind_contact(self.tenant, self.ws_id, self.line_user))
        from services.line_binding import client_pool_vocab as vocab

        question = self.pool_store.stage(
            self.tenant,
            workspace_client_id=self.ws_id,
            work_order_id=self.wo_id,
            item_id=amb["id"],
            period="2569-06",
            question_type=vocab.QUESTION_DIRECTION,
            question_payload={"invoice_number": "INV-amb0"},
            created_by="user:accountant",
        )
        batch_id = str(uuid.uuid4())
        self.pool_store.mark_sent(self.tenant, question["id"], batch_id, 1)

        # ③ 客户答「1 ซื้อ」:吃题 → 裁决落库 → applied → 自动续跑,全程零人手。
        with patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True):
            consumed = line_client_answer.handle_answer(self.line_user, "1 ซื้อ", None, None)
        self.assertTrue(consumed)

        # ④ 裁决与续跑证据链:human_decision(line_client)→ run_requested(line_client)→
        #    引擎重跑 reconcile 越过方向停机点 → 停在缺销项(needs sales_summary)。
        self._poll(
            lambda cur: sum(
                1
                for e in self._events(cur)
                if e["id"] > boundary_id and e["event_type"] == "run_finished"
            )
            or None,
            desc="答题后自动续跑收尾",
        )
        with self.db.get_cursor() as cur:
            evts = self._events(cur)
            wo = self.store.get_work_order(cur, tenant_id=self.tenant, work_order_id=self.wo_id)
        tail = [e for e in evts if e["id"] > boundary_id]
        from services.workorder import decisions

        decision = next(e for e in tail if e["event_type"] == "human_decision")
        self.assertEqual(decision["actor"], f"line_client:{self.line_user}")
        self.assertEqual(decision["payload"]["decision"], decisions.ASSIGN_KIND)
        self.assertEqual(decision["payload"]["kind"], decisions.PURCHASE_INVOICE)
        requested = next(e for e in tail if e["event_type"] == "run_requested")
        self.assertEqual(requested["actor"], f"line_client:{self.line_user}")
        self.assertGreater(requested["id"], decision["id"])
        needs = [e for e in tail if e["event_type"] == "step_needs"]
        self.assertTrue(
            needs and "sales_summary" in needs[-1]["payload"]["missing"],
            f"应越过方向停机点、停在缺销项,实际尾部事件: {[e['event_type'] for e in tail]}",
        )
        self.assertEqual(wo["status"], "stuck")  # 新的自然停点,状态诚实
        with self.db.get_cursor() as cur:
            holder = self.store.run_lease_holder(
                cur, tenant_id=self.tenant, work_order_id=self.wo_id
            )
        self.assertIsNone(holder, "续跑收尾必须释放租约")

        # ⑤ 池侧闭环:问题转 applied,resolution 带裁决事件 id。
        rows = self.pool_store.list_batch(self.tenant, self.ws_id, batch_id)
        self.assertEqual(rows[0]["status"], vocab.APPLIED)
        self.assertEqual(rows[0]["resolution"]["decision"], decisions.ASSIGN_KIND)


if __name__ == "__main__":
    unittest.main()
