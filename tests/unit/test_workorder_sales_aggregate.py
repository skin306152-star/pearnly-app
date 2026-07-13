# -*- coding: utf-8 -*-
"""本方销项票逐票聚合佐证(MC1-c.1)· 金标 + 覆盖率 + 守恒 + 佐证不夺权威。

夹具 = MC0 fresh 单真 OCR 快照(tests/e2e/_artifacts/mc0/01_fresh_order_stuck_detail.json)里
seller_tax==本账套的 60 张本方销项票。金标锁定(派单 §3):不许放宽,真跑对不上是代码的问题。
CI 每次 push 必跑(纯函数 + 内存事件,零 DB / 零 OCR)。
"""

from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path

from services.workorder import decisions
from services.workorder.steps import reconcile, reconcile_gates, sales_aggregate

_ARTIFACT = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "e2e"
    / "_artifacts"
    / "mc0"
    / "01_fresh_order_stuck_detail.json"
)
OWN_TAX = "0105567178203"

# 官方 ภ.พ.30 金标(权威销项 · T0 语料盘点锁定)。
GOLDEN_AUTH_SALES = "858780.16"
GOLDEN_AUTH_VAT = "60114.61"


def _sales_money() -> list:
    """从快照取 60 张本方销项票的票面钱字段(ocr_read 与 classify._money_fields 同键)。"""
    art = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
    return [it["ocr_read"] for it in art["flagged"] if it["ocr_read"].get("seller_tax") == OWN_TAX]


class AggregateGoldenTests(unittest.TestCase):
    """派单 §3 断言 1-3:聚合金标 + 覆盖率钉死 + 守恒点名。"""

    @classmethod
    def setUpClass(cls):
        cls.money = _sales_money()
        cls.agg = sales_aggregate.aggregate_invoice_sales(cls.money)

    def test_fixture_has_60_sales_tickets(self):
        self.assertEqual(len(self.money), 60)

    def test_golden_full_totals(self):
        # 断言 1(去重前全量):净/税/含税三口径逐字节 = 官方聚合金标。
        self.assertEqual(self.agg["net_total"], "107885.17")
        self.assertEqual(self.agg["vat_total"], "7533.37")
        self.assertEqual(self.agg["gross_total"], "115274.77")
        self.assertEqual(self.agg["invoice_count"], 60)

    def test_dedupe_drops_one_and_reduces_gross_by_250(self):
        # 断言 1(去重后):02000101 双件去重 → 59 张;含税减 250(该票票面),净减 233.64。
        self.assertEqual(self.agg["deduped_count"], 59)
        self.assertEqual(self.agg["duplicates"], ["02000101"])
        self.assertEqual(self.agg["net_deduped"], "107651.53")
        self.assertEqual(self.agg["gross_deduped"], "115024.77")
        self.assertEqual(
            Decimal(self.agg["gross_total"]) - Decimal(self.agg["gross_deduped"]), Decimal("250.00")
        )
        self.assertEqual(
            Decimal(self.agg["net_total"]) - Decimal(self.agg["net_deduped"]), Decimal("233.64")
        )

    def test_conservation_exactly_one_violation(self):
        # 断言 3:恰好 02000079 一张守恒违反(净×7%≠票面税 且 净+税≠含税),其余 59 张过,点名不静默。
        self.assertEqual(self.agg["conservation_violations"], ["02000079"])
        self.assertEqual(self.agg["conserved_count"], 59)

    def test_date_coverage(self):
        self.assertEqual(self.agg["date_from"], "2026-05-03")
        self.assertEqual(self.agg["date_to"], "2026-05-28")

    def test_coverage_pinned_at_one_eighth(self):
        # 断言 2:覆盖率钉死 0.126±0.005(防未来误接成权威——若突然=100% 说明混入非本店票)。
        crb = sales_aggregate.build_corroboration(
            self.agg, authoritative_net=GOLDEN_AUTH_SALES, authoritative_vat=GOLDEN_AUTH_VAT
        )
        self.assertLessEqual(abs(Decimal(crb["coverage"]) - Decimal("0.126")), Decimal("0.005"))
        self.assertEqual(crb["gap_net"], "750894.99")
        self.assertEqual(crb["covered_state"], "amber")
        self.assertEqual(crb["authoritative_net"], GOLDEN_AUTH_SALES)


class CorroborationStateTests(unittest.TestCase):
    """派单 §3 断言 6:四态呈现(绿/黄/needs)。守恒违反单列由 conservation_violations 承载。"""

    def _agg(self, net, vat, total):
        return sales_aggregate.aggregate_invoice_sales(
            [{"subtotal": net, "vat": vat, "total_amount": total, "invoice_number": "X1"}]
        )

    def test_amber_when_coverage_incomplete(self):
        crb = sales_aggregate.build_corroboration(
            self._agg("100.00", "7.00", "107.00"), authoritative_net="1000.00"
        )
        self.assertEqual(crb["covered_state"], "amber")
        self.assertEqual(crb["gap_net"], "900.00")

    def test_green_when_coverage_at_or_above_98pct(self):
        crb = sales_aggregate.build_corroboration(
            self._agg("990.00", "69.30", "1059.30"), authoritative_net="1000.00"
        )
        self.assertEqual(crb["covered_state"], "green")

    def test_needs_when_no_authoritative(self):
        # 无权威销项(未申报)→ needs 态:只显已开票,不编造缺口(现状诚实)。
        crb = sales_aggregate.build_corroboration(self._agg("100.00", "7.00", "107.00"))
        self.assertEqual(crb["covered_state"], "needs")
        self.assertIsNone(crb["gap_net"])
        self.assertIsNone(crb["coverage"])


class CorroborationDoesNotSeizeAuthorityTests(unittest.TestCase):
    """派单 §3 断言 5:挂佐证后 R2 权威取值逻辑一行不改(佐证不夺权威的机器证明)。"""

    def test_r2_authoritative_untouched_by_aggregate(self):
        # 权威销项走 aggregate_sales(人工申报直读),聚合佐证走 _run_invoice_aggregate,两路互不影响。
        manual_read = {
            "manual-1": {
                "headers": ["ยอดขาย", "ภาษีขาย"],
                "rows": [{"cells": [GOLDEN_AUTH_SALES, GOLDEN_AUTH_VAT], "is_summary": False}],
                "source": "manual_entry",
            }
        }
        r2 = reconcile_gates.aggregate_sales(manual_read)
        self.assertEqual(str(r2["sales_amount"]), GOLDEN_AUTH_SALES)
        self.assertEqual(str(r2["output_vat"]), GOLDEN_AUTH_VAT)

        items = [{"id": f"s{i}", "kind": decisions.SALES_DOC} for i in range(len(_sales_money()))]
        classified = {it["id"]: m for it, m in zip(items, _sales_money())}
        corrob = reconcile._run_invoice_aggregate(items, classified, r2)

        # 佐证挂上了(已开票 107,885),但 R2 权威值(858,780.16/60,114.61)逐字节不变。
        self.assertEqual(corrob["net_total"], "107885.17")
        self.assertEqual(corrob["authoritative_net"], GOLDEN_AUTH_SALES)
        self.assertEqual(corrob["authoritative_vat"], GOLDEN_AUTH_VAT)
        self.assertEqual(str(r2["sales_amount"]), GOLDEN_AUTH_SALES)  # 再证一次:未被 corrob 触碰


class OrderDetailProjectionTests(unittest.TestCase):
    """派单 §3 断言 7(后端读侧):order_detail 现算佐证,独立于 reconcile 是否 ok;无 sales_doc → None。"""

    def _classified_event(self, item_id, money):
        return {
            "event_type": "item_classified",
            "step": "classify",
            "payload": {
                "item_id": item_id,
                "kind": "sales_doc",
                "status": "flagged",
                "money": money,
            },
            "actor": "system",
            "id": item_id,
            "created_at": None,
        }

    def test_projection_present_even_without_authoritative(self):
        # 无 sales_summary(工单停在 R2 needs)→ 佐证照样出,covered_state=needs、只显已开票不编缺口。
        money = _sales_money()
        items = [{"id": f"s{i}", "kind": decisions.SALES_DOC} for i in range(len(money))]
        events = [self._classified_event(it["id"], m) for it, m in zip(items, money)]
        crb = sales_aggregate.corroboration_from_events(events, items)
        self.assertEqual(crb["net_total"], "107885.17")
        self.assertEqual(crb["covered_state"], "needs")
        self.assertEqual(crb["conservation_violations"], ["02000079"])

    def test_projection_computes_gap_when_authoritative_filed(self):
        money = _sales_money()
        items = [{"id": f"s{i}", "kind": decisions.SALES_DOC} for i in range(len(money))]
        items.append({"id": "manual", "kind": "sales_summary"})
        events = [self._classified_event(it["id"], m) for it, m in zip(items, money)]
        events.append(
            {
                "event_type": "item_classified",
                "step": "classify",
                "payload": {
                    "item_id": "manual",
                    "kind": "sales_summary",
                    "status": "ok",
                    "sales_read": {
                        "headers": ["ยอดขาย", "ภาษีขาย"],
                        "rows": [
                            {"cells": [GOLDEN_AUTH_SALES, GOLDEN_AUTH_VAT], "is_summary": False}
                        ],
                        "source": "manual_entry",
                    },
                },
                "actor": "user",
                "id": "manual",
                "created_at": None,
            }
        )
        crb = sales_aggregate.corroboration_from_events(events, items)
        self.assertEqual(crb["net_total"], "107885.17")
        self.assertEqual(crb["gap_net"], "750894.99")
        self.assertEqual(crb["covered_state"], "amber")

    def test_projection_none_when_no_sales_doc(self):
        items = [{"id": "p1", "kind": "purchase_invoice"}]
        events = [self._classified_event("p1", {"subtotal": "1", "vat": "0"})]
        events[0]["payload"]["kind"] = "purchase_invoice"
        self.assertIsNone(sales_aggregate.corroboration_from_events(events, items))


if __name__ == "__main__":
    unittest.main()
