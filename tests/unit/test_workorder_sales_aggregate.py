# -*- coding: utf-8 -*-
"""本方销项票逐票聚合佐证(MC1-c.1)· 金标 + 覆盖率 + 守恒 + 佐证不夺权威。

夹具 = MC0 fresh 单真 OCR 快照(01_fresh_order_stuck_detail.json)里 seller_tax==本账套的 60 张
本方销项票,逐字节内联(测试自洽,不依赖 gitignore 外的 _artifacts 落盘件,CI 每次必跑)。金标
锁定(派单 §3):不许放宽,真跑对不上是代码的问题。纯函数 + 内存事件,零 DB / 零 OCR。
"""

from __future__ import annotations

import unittest
from decimal import Decimal

from services.workorder import decisions
from services.workorder.steps import reconcile, reconcile_gates, sales_aggregate

OWN_TAX = "0105567178203"

# 官方 ภ.พ.30 金标(权威销项 · T0 语料盘点锁定)。
GOLDEN_AUTH_SALES = "858780.16"
GOLDEN_AUTH_VAT = "60114.61"

# (invoice_number, subtotal, vat, total_amount, invoice_date) · 60 张本方销项票票面钱字段。
_SALES_ROWS = [
    ("SW02000131", "3557.01", "248.99", "3806.00", "2026-05-24"),
    ("02000130", "271.03", "18.97", "290.00", "2026-05-23"),
    ("02000129", "6139.25", "429.75", "6569.00", "2026-05-23"),
    ("02000128", "746.73", "52.27", "799.00", "2026-05-23"),
    ("02000126", "1467.29", "102.71", "1570.00", "2026-05-17"),
    ("02000127", "1382.24", "96.76", "1479.00", "2026-05-17"),
    ("02000133", "2549.53", "178.47", "2728.00", "2026-05-27"),
    ("02000134", "3867.29", "270.71", "4138.00", "2026-05-27"),
    ("02000136", "6448.60", "451.40", "6900.00", "2026-05-27"),
    ("02000135", "2289.72", "160.28", "2450.00", "2026-05-27"),
    ("02000137", "2586.92", "181.08", "2768.00", "2026-05-27"),
    ("SW02000136", "457.01", "31.99", "489.00", "2026-05-27"),
    ("02000139", "439.25", "30.75", "470.00", "2026-05-27"),
    ("02000143", "2514.02", "175.98", "2690.00", "2026-05-28"),
    ("02000140", "335.51", "23.49", "359.00", "2026-05-28"),
    ("SW02000141", "551.40", "38.60", "590.00", "2026-05-28"),
    ("02000142", "186.92", "13.08", "200.00", "2026-05-28"),
    ("02000144", "2849.53", "199.47", "3049.00", "2026-05-28"),
    ("02000145", "260.75", "18.25", "279.00", "2026-05-28"),
    ("02000132", "140.19", "9.81", "150.00", "2026-05-25"),
    ("02000093", "1654.21", "115.79", "1770.00", "2026-05-06"),
    ("02000091", "4715.89", "330.11", "5046.00", "2026-05-06"),
    ("02000070", "883.18", "61.82", "945.00", "2026-05-03"),
    ("02000071", "878.50", "61.50", "940.00", "2026-05-03"),
    ("02000072", "233.64", "16.36", "250.00", "2026-05-03"),
    ("R24P07Y*gisaxIn02000075SM", "2785.05", "194.95", "2980.00", "2026-05-03"),
    ("SWO2000076", "2156.07", "150.93", "2307.00", "2026-05-03"),
    ("02000077", "3643.93", "255.07", "3899.00", "2026-05-03"),
    ("02000085", "1578.50", "110.50", "1689.00", "2026-05-06"),
    ("02000086", "2579.44", "180.56", "2760.00", "2026-05-06"),
    ("02000088", "5308.41", "371.59", "5680.00", "2026-05-06"),
    ("02000092", "728.97", "51.03", "780.00", "2026-05-06"),
    ("02000123", "364.49", "25.51", "390.00", "2026-05-10"),
    ("02000124", "1569.16", "109.84", "1679.00", "2026-05-10"),
    ("02000073", "4055.14", "283.86", "4339.00", "2026-05-03"),
    ("02000074", "2168.22", "151.78", "2320.00", "2026-05-03"),
    ("SWO2000096", "5357.94", "375.06", "5733.00", "2026-05-09"),
    ("02000098", "140.19", "9.81", "150.00", "2026-05-09"),
    ("SW02000097", "915.89", "64.11", "980.00", "2026-05-09"),
    ("02000100", "504.67", "35.33", "540.00", "2026-05-09"),
    ("02000101", "233.64", "16.36", "250.00", "2026-05-09"),
    ("02000101", "233.64", "16.36", "250.00", "2026-05-09"),
    ("02000115", "2336.45", "163.55", "2500.00", "2026-05-10"),
    ("02000116", "728.97", "51.03", "780.00", "2026-05-10"),
    ("02000117", "1316.82", "92.18", "1409.00", "2026-05-10"),
    ("02000118", "785.05", "54.95", "840.00", "2026-05-10"),
    ("02000119", "233.64", "16.36", "250.00", "2026-05-10"),
    ("SM02000120", "728.97", "51.03", "780.00", "2026-05-10"),
    ("02000121", "914.95", "64.05", "979.00", "2026-05-10"),
    ("02000122", "2119.63", "148.37", "2268.00", "2026-05-10"),
    ("02000102", "364.49", "25.51", "390.00", "2026-05-09"),
    ("02000107", "1186.92", "83.08", "1270.00", "2026-05-09"),
    ("02000110", "1942.99", "136.01", "2079.00", "2026-05-09"),
    ("SW02000111", "625.23", "43.77", "669.00", "2026-05-09"),
    ("02000112", "364.49", "25.51", "390.00", "2026-05-09"),
    ("02000113", "186.92", "13.08", "200.00", "2026-05-09"),
    ("02000079", "4059.00", "265.54", "4180.77", "2026-05-06"),
    ("02000080", "560.75", "39.25", "600.00", "2026-05-06"),
    ("02000082", "3850.47", "269.53", "4120.00", "2026-05-06"),
    ("02000084", "3850.47", "269.53", "4120.00", "2026-05-06"),
]


def _sales_money() -> list:
    """60 张本方销项票的票面钱字段(键与 classify._money_fields 一致)。"""
    return [
        {
            "invoice_number": n,
            "subtotal": s,
            "vat": v,
            "total_amount": t,
            "invoice_date": d,
            "seller_tax": OWN_TAX,
        }
        for n, s, v, t, d in _SALES_ROWS
    ]


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


class CorroborationForDetailF6Tests(unittest.TestCase):
    """F6 写读归一:order_detail 优先消费 reconcile 落库佐证,未跑到 reconcile 回退现算,
    分叉以落库值为准标 stale。冻结与现算在数据未变时逐字节一致由本组锁死。"""

    def _sd_evt(self, item_id, money):
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

    def _base(self):
        money = _sales_money()
        items = [{"id": f"s{i}", "kind": decisions.SALES_DOC} for i in range(len(money))]
        events = [self._sd_evt(it["id"], m) for it, m in zip(items, money)]
        return events, items

    def _step_done(self, corrob):
        return {
            "event_type": "step_done",
            "step": "reconcile",
            "payload": {"gates": {"r2_sales_corroboration": corrob}},
            "actor": "system",
            "id": "done",
            "created_at": None,
        }

    def test_falls_back_to_live_when_no_reconcile(self):
        events, items = self._base()
        detail = sales_aggregate.corroboration_for_detail(events, items)
        live = sales_aggregate.corroboration_from_events(events, items)
        self.assertEqual(detail, live)
        self.assertNotIn("stale", detail)

    def test_prefers_frozen_and_agrees_with_live(self):
        events, items = self._base()
        # reconcile 冻结的佐证 = 数据未变时的现算值(单一事实源锁:两路逐字节一致)。
        frozen = sales_aggregate.corroboration_from_events(events, items)
        events2 = events + [self._step_done(frozen)]
        detail = sales_aggregate.corroboration_for_detail(events2, items)
        self.assertEqual(detail, frozen)  # 消费落库值
        self.assertNotIn("stale", detail)  # 与现算一致 → 不标 stale

    def test_divergence_prefers_frozen_and_marks_stale(self):
        events, items = self._base()
        live = sales_aggregate.corroboration_from_events(events, items)
        # 模拟算法演进 / reconcile 后补料:落库值与现算分叉。
        frozen = dict(live, net_total="999999.00")
        events2 = events + [self._step_done(frozen)]
        detail = sales_aggregate.corroboration_for_detail(events2, items)
        self.assertEqual(detail["net_total"], "999999.00")  # 以落库值为准
        self.assertTrue(detail["stale"])  # 诚实标注分叉,不糊

    def test_none_when_reconcile_ran_without_corroboration(self):
        # reconcile 跑过但无 sales_doc → 不冻结 r2_sales_corroboration 键;现算也 None → None。
        step_done = {
            "event_type": "step_done",
            "step": "reconcile",
            "payload": {"gates": {}},
            "actor": "system",
            "id": "done",
            "created_at": None,
        }
        self.assertIsNone(sales_aggregate.corroboration_for_detail([step_done], []))


if __name__ == "__main__":
    unittest.main()
