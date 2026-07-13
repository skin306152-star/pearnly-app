# -*- coding: utf-8 -*-
"""waive 豁免全链路测试(engine.run_work_order 级,非单步直调)。

A2 打回修复的守门:waive =「显式放弃计入、放行出包、留痕」,必须在产品全链上可达——
R1(resolve_input_vat/_apply_direction)把 waive 认作已处置(不进 Σ、不进 unresolved),
流程才走得到 package 的守恒闸(waived 桶放行)与备忘留痕。修前 waive 只被 package 认识,
reconcile 步先 stuck,豁免出包分支永远不可达(假通)。

复用 test_workorder_golden_synthetic 的 FakeStore/合成语料装配件:零真库/零真 OCR,
intake→sort→classify→reconcile→compute→package 全走生产代码路径。
"""

from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path

from tests.unit.test_workorder_golden_synthetic import (
    _GoldenSyntheticTestCase,
    _purchase_fields,
    DISPUTED_FACE_VAT,
    GOOD_VAT,
    OTHER_TAX,
    OWN_TAX,
    OUTPUT_VAT,
)

# 自家==卖方的合成本方销项票(sort.bin_ocr_fields → kind=sales_doc/sales_doc_review · MC1-c.1)。
DIR_NET, DIR_VAT, DIR_TOTAL = Decimal("54240.00"), Decimal("3796.80"), Decimal("58036.80")

WAIVE_REASON = "客户 LINE 确认为对方留底联·原件不归本方申报"
WAIVE_ACTOR = "user:audit"


class _WaivePipelineTestCase(_GoldenSyntheticTestCase):
    def _waive(self, path: Path) -> None:
        """对指定文件的 item 落 waive 裁决事件(带 reason + actor,api.record_decision 同构)。"""
        item = self.corpus.item_by_file(path)
        self.corpus.store.append_event(
            None,
            tenant_id=self.corpus.tenant_id,
            work_order_id=self.corpus.work_order_id,
            step="reconcile",
            event_type="human_decision",
            payload={"item_id": item["id"], "decision": "waive", "reason": WAIVE_REASON},
            actor=WAIVE_ACTOR,
        )

    def _memo_text(self) -> str:
        bucket = self.corpus.store.deliverables[self.corpus.work_order_id]
        return Path(bucket["missing_doc_memo"]["artifact_path"]).read_text(encoding="utf-8")


class WaivedSalesDirectionTicketTests(_WaivePipelineTestCase):
    """1 张自动判本方销项票(kind=sales_doc)不再判死停机;waive 后重跑 → completed,
    五件套齐、memo 留痕、pp30 金额不含该票——验证 waive 在 sales_doc 上仍全链可达。"""

    def setUp(self):
        super().setUp()
        self.p_dir = self.corpus.dir / "own_sales_doc.jpg"
        self.p_dir.write_bytes(b"jpeg-own-sales")
        # seller==自家税号 → 自动归本方销项堆 sales_doc(MC1-c.1,flagged 留人工过目)。
        self.corpus.ocr_map[str(self.p_dir)] = _purchase_fields(
            seller=OWN_TAX,
            buyer=OTHER_TAX,
            invoice_no="SL001",
            subtotal=DIR_NET,
            vat=DIR_VAT,
            total=DIR_TOTAL,
        )

    def _first_run_ctx(self):
        files = self.corpus.intake_files() + [str(self.p_dir)]
        return self.corpus.ctx(intake_files=files)

    def test_sales_doc_binned_then_waive_completes_with_memo_trace(self):
        out1 = self._run(self._first_run_ctx())
        self.assertFalse(out1.completed)
        self.assertEqual(out1.stopped_at, "reconcile")
        # 本方销项票(sales_doc)不再判死进 R1 停机;首跑停在待裁决的争议进项票(amount_math_fail)。
        self.assertTrue(any("amount_math_fail" in r for r in out1.result.reasons))
        self.assertFalse(any("sales_direction_unhandled" in r for r in out1.result.reasons))

        dir_item = self.corpus.item_by_file(self.p_dir)
        self.assertEqual(dir_item["kind"], "sales_doc")
        self.assertEqual(dir_item["flag_reason"], "sales_doc_review")

        # 争议票走常规裁决,方向票走豁免——重跑必须一路推进到 completed(review)。
        self.corpus.decide("face_value")
        self._waive(self.p_dir)
        out2 = self._run()
        self.assertTrue(out2.completed)

        bucket = self.corpus.store.deliverables[self.corpus.work_order_id]
        self.assertEqual(
            set(bucket.keys()),
            {
                "pp30_draft",
                "ledger_workpaper",
                "bank_workpaper",
                "missing_doc_memo",
                "evidence_index",
            },
        )
        for kind, row in bucket.items():
            self.assertTrue(Path(row["artifact_path"]).is_file(), f"{kind} 未真落盘")

        # memo 留痕三要素:谁豁免 · 为何 · 哪张文件。
        memo = self._memo_text()
        self.assertIn(WAIVE_ACTOR, memo)
        self.assertIn(WAIVE_REASON, memo)
        self.assertIn("own_sales_doc.jpg", memo)

        # pp30 金额不含豁免票:进项税 = 正常票 + 争议票(票面),精确不多不少。
        numbers = self.corpus.pp30_numbers()
        expected_vat = GOOD_VAT + DISPUTED_FACE_VAT
        self.assertEqual(Decimal(numbers["input_vat"]), expected_vat)
        self.assertEqual(Decimal(numbers["tax_due"]), OUTPUT_VAT - expected_vat)

        # 证据索引同口径:豁免票没进合计,不得被列为 input_vat 的支撑证据。
        index = json.loads(Path(bucket["evidence_index"]["artifact_path"]).read_text("utf-8"))
        self.assertNotIn(str(self.p_dir), index["numbers"]["input_vat"]["source_files"])


class WaivedFlaggedPurchaseTests(_WaivePipelineTestCase):
    """1 张 amount_math_fail flagged 进项票 waive → completed,其 VAT 不进 input_vat_total。"""

    def test_waive_completes_and_vat_excluded_by_exact_amount(self):
        out1 = self._run(self.corpus.first_run_ctx())
        self.assertFalse(out1.completed)
        self.assertEqual(out1.stopped_at, "reconcile")

        self._waive(self.corpus.p_fail)
        out2 = self._run()
        self.assertTrue(out2.completed)

        # 精确差额:相对「按票面采纳」少的恰是被豁免那张的票面 VAT(45.00)。
        numbers = self.corpus.pp30_numbers()
        self.assertEqual(Decimal(numbers["input_vat"]), GOOD_VAT)
        self.assertEqual(
            (GOOD_VAT + DISPUTED_FACE_VAT) - Decimal(numbers["input_vat"]), DISPUTED_FACE_VAT
        )

        memo = self._memo_text()
        self.assertIn(WAIVE_ACTOR, memo)
        self.assertIn(WAIVE_REASON, memo)
        self.assertIn("invoice_mathfail.jpg", memo)

        # 证据索引:豁免的 flagged 进项票(item_classified.kind=purchase_invoice)没进合计,
        # 不得再被列为 input_vat 的支撑证据——与 exclude 同口径。
        bucket = self.corpus.store.deliverables[self.corpus.work_order_id]
        index = json.loads(Path(bucket["evidence_index"]["artifact_path"]).read_text("utf-8"))
        self.assertNotIn(str(self.corpus.p_fail), index["numbers"]["input_vat"]["source_files"])


if __name__ == "__main__":
    unittest.main()
