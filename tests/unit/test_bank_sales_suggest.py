# -*- coding: utf-8 -*-
"""SA-3a 银行流水倒推销项引擎守门(services/workorder/steps/bank_sales_suggest.py)。

纯函数三层漏斗(确定性剔除/强信号 → 大脑 overlay → 人裁 overlay)+ ÷1.07 金标(SM 5月会计
底稿分组 918,894.77 → 858,780.16 + 60,114.61 逐字)+ 行指纹幂等/latest-wins/闸关无键/现金型
诚实降级 + 覆盖可信度(打回 R1:余额链断点量化缺口,64% 捕获真形态必须降级不得出建议值)。
钱数只由确定性代码算,大脑只碰分类——本套锁死这条硬闸的边界。
"""

from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

from services.workorder import api
from services.workorder.steps import bank_sales_suggest as bss
from tests.unit._workorder_fakes import WorkOrderFakeStoreBase

# 金标工单真 12 事件的脱敏快照(只留钱数/余额,64% 捕获形态)——覆盖降级守门唯一夹具。
_COVERAGE_FIXTURE = Path(__file__).with_name("_golden_bank_sales_coverage.json")


def _dep(date, amount, desc="รับโอนเงิน", balance=None):
    return {
        "date": date,
        "deposit": amount,
        "withdrawal": 0.0,
        "description": desc,
        "balance": balance,
    }


def _wd(date, amount, desc="Transfer Withdrawal", balance=None):
    return {
        "date": date,
        "deposit": 0.0,
        "withdrawal": amount,
        "description": desc,
        "balance": balance,
    }


def _bank_event(rows, item_id="i1", eid=1):
    return {
        "id": eid,
        "event_type": "item_bank_parsed",
        "payload": {"item_id": item_id, "rows": rows},
    }


def _human(fp, verdict, eid):
    return {
        "id": eid,
        "event_type": "human_decision",
        "payload": {bss.HUMAN_ROW_KEY: fp, bss.HUMAN_VERDICT_KEY: verdict},
    }


def _brain(fp, verdict, eid, valid=True):
    return {
        "id": eid,
        "event_type": bss.EVT_SUGGESTED,
        "payload": {"fingerprint": fp, "verdict": verdict, "valid": valid},
    }


def _totals_event(*, pages=None, deposits=None, withdrawals=None):
    """锚页自报总数事件(SA3R-b):对账单页 1 印的 N 页 / รวมฝาก+รวมถอน 笔数。"""
    return {
        "event_type": bss.stmt_totals.EVT_STMT_TOTALS,
        "payload": {
            "total_pages": pages,
            "deposit_count": deposits,
            "withdrawal_count": withdrawals,
        },
    }


class DeterministicFunnelTests(unittest.TestCase):
    def test_not_applicable_without_bank_rows(self):
        self.assertEqual(bss.suggest([]), {"applicable": False, "reason": "no_bank_rows"})

    def test_withdrawal_and_zero_and_fee_and_cancel_excluded(self):
        events = [
            _bank_event(
                [
                    _dep("2569-05-01", 1000.0),  # 入账无强信号 → 待定
                    _wd("2569-05-01", 500.0),  # 转出 → 非销售
                    {"date": "2569-05-01", "deposit": 0.0, "withdrawal": 0.0, "description": "B/F"},
                    _dep("2569-05-02", 838.93, "ค่าธรรมเนียม"),  # 手续费关键词 → 非销售
                    _dep("2569-05-02", 200.0, "ยกเลิกรายการ"),  # 取消关键词 → 非销售
                ]
            )
        ]
        result = bss.suggest(events)
        self.assertTrue(result["applicable"])
        self.assertEqual(result["counts"], {"sales": 0, "non_sales": 4, "pending": 1, "total": 5})
        by_reason = {r["reason"] for r in result["rows"] if r["verdict"] == bss.NON_SALES}
        self.assertEqual(by_reason, {bss.R_WITHDRAWAL, bss.R_ZERO, bss.R_FEE, bss.R_CANCEL})
        self.assertEqual(result["gross_total"], "0")

    def test_edc_settlement_match_is_deterministic_sale(self):
        # 漏斗第 1 层「必是销售」:入账 (日期,毛额) 命中 EDC 结算单快照。
        events = [
            _bank_event([_dep("2569-05-10", 5000.0)]),
            {
                "id": 2,
                "event_type": "item_classified",
                "payload": {
                    "item_id": "edc1",
                    "kind": "edc_settlement",
                    "edc": {"settle_date": "2569-05-10", "gross_amount": "5000.00"},
                },
            },
        ]
        result = bss.suggest(events)
        self.assertEqual(result["counts"]["sales"], 1)
        row = result["rows"][0]
        self.assertEqual(
            (row["verdict"], row["reason"], row["source"]),
            (bss.SALES, bss.R_MATCHED_SETTLEMENT, bss.SRC_RULE),
        )
        self.assertEqual(result["gross_total"], "5000.0")


class OverlayPrecedenceTests(unittest.TestCase):
    def test_brain_overlay_classifies_pending_row(self):
        events = [_bank_event([_dep("2569-05-01", 1000.0)])]
        fp = bss.parsed_rows_from_events(events)[0]["fingerprint"]
        result = bss.suggest(events + [_brain(fp, bss.SALES, eid=2)])
        self.assertEqual(result["counts"]["sales"], 1)
        self.assertEqual(result["rows"][0]["source"], bss.SRC_BRAIN)
        self.assertEqual(result["gross_total"], "1000.0")

    def test_invalid_brain_suggestion_does_not_classify(self):
        events = [_bank_event([_dep("2569-05-01", 1000.0)])]
        fp = bss.parsed_rows_from_events(events)[0]["fingerprint"]
        result = bss.suggest(events + [_brain(fp, bss.SALES, eid=2, valid=False)])
        self.assertEqual(result["counts"]["pending"], 1)

    def test_human_overrides_brain_and_rule_latest_wins(self):
        events = [_bank_event([_dep("2569-05-01", 1000.0)])]
        fp = bss.parsed_rows_from_events(events)[0]["fingerprint"]
        # 大脑判销售 → 人裁先判非销售 → 人裁改回销售(latest-wins)。
        stream = events + [
            _brain(fp, bss.SALES, eid=2),
            _human(fp, bss.NON_SALES, eid=3),
            _human(fp, bss.SALES, eid=4),
        ]
        result = bss.suggest(stream)
        self.assertEqual(result["rows"][0]["source"], bss.SRC_HUMAN)
        self.assertEqual(result["counts"]["sales"], 1)
        self.assertEqual(result["gross_total"], "1000.0")


class FingerprintTests(unittest.TestCase):
    def test_identical_date_amount_rows_get_distinct_fingerprints(self):
        events = [_bank_event([_dep("2569-05-01", 450.0), _dep("2569-05-01", 450.0)])]
        rows = bss.parsed_rows_from_events(events)
        self.assertNotEqual(rows[0]["fingerprint"], rows[1]["fingerprint"])
        # 裁决只作用于被点名那条,另一条不受牵连。
        result = bss.suggest(events + [_human(rows[0]["fingerprint"], bss.SALES, eid=2)])
        self.assertEqual(result["counts"], {"sales": 1, "non_sales": 0, "pending": 1, "total": 2})

    def test_same_item_replayed_twice_not_double_counted(self):
        rows = [_dep("2569-05-01", 1000.0)]
        events = [_bank_event(rows, item_id="i1", eid=1), _bank_event(rows, item_id="i1", eid=2)]
        self.assertEqual(len(bss.parsed_rows_from_events(events)), 1)

    def test_invalidation_ignores_old_rows_and_old_row_decisions(self):
        old = [_bank_event([_dep("2023-05-01", 1000.0)], item_id="i1", eid=1)]
        old_fp = bss.parsed_rows_from_events(old)[0]["fingerprint"]
        events = old + [
            _human(old_fp, bss.SALES, eid=2),
            {
                "id": 3,
                "event_type": bss.reconcile_bank.EVT_BANK_PARSE_INVALIDATED,
                "payload": {"reason": "date_parser_fixed"},
            },
            _bank_event([_dep("2026-05-01", 2000.0)], item_id="i1", eid=4),
        ]

        result = bss.suggest(events)

        self.assertEqual(result["counts"], {"sales": 0, "non_sales": 0, "pending": 1, "total": 1})
        self.assertEqual(result["rows"][0]["date"], "2026-05-01")


class GoldenWorksheetTests(unittest.TestCase):
    """IMG_2481 会计底稿分组金标:四组销售 + 手续费 + 取消,人裁 overlay 模拟会计分组。
    行带完整余额链(逐对守恒)——完整行数据路径必须通过覆盖判定并出三数逐字(打回 R1 #3)。"""

    def _worksheet_events(self):
        rows = [
            _dep("2569-05-31", "347418.00", "รายได้ค่าบริการ", balance="447418.00"),
            _dep("2569-05-31", "397721.00", "รายได้ขายสินค้า", balance="845139.00"),
            _dep("2569-05-31", "36400.00", "รายได้", balance="881539.00"),
            _dep("2569-05-31", "137355.77", "มี Slip", balance="1018894.77"),
            # 手续费转出 → 确定性非销售
            _wd("2569-05-31", "838.93", "ค่าธรรมเนียม", balance="1018055.84"),
            # 取消关键词 → 确定性非销售
            _dep("2569-05-31", "2520.00", "ยกเลิก", balance="1020575.84"),
        ]
        return [_bank_event(rows)]

    def test_golden_918894_77_split(self):
        events = self._worksheet_events()
        parsed = bss.parsed_rows_from_events(events)
        overlay = [
            _human(r["fingerprint"], bss.SALES, eid=100 + i)
            for i, r in enumerate(parsed)
            if r["deposit"] > 0 and "ยกเลิก" not in r["description"]
        ]
        result = bss.suggest(events + overlay)
        self.assertTrue(result["reliable"])
        self.assertEqual(result["coverage"]["verified_pairs"], 5)
        self.assertEqual(result["coverage"]["chain_breaks"], 0)
        self.assertEqual(result["gross_total"], "918894.77")
        self.assertEqual(result["sales_amount"], "858780.16")
        self.assertEqual(result["output_vat"], "60114.61")
        self.assertEqual(result["counts"], {"sales": 4, "non_sales": 2, "pending": 0, "total": 6})


class CoverageDegradeTests(unittest.TestCase):
    """覆盖可信度守门(打回 R1):余额链断点量化无解释入账,显著缺口 → 降级不出建议值。"""

    def test_real_golden_12_events_shape_must_degrade(self):
        # 金标工单真 12 事件(64% 捕获):链断 65 处、无解释入账 77,733.79(占证据入账 11.6%)。
        # 引擎必须降级——三个建议值键一个都不许出,这正是 R1 抓到的「自信地错」形态。
        events = json.loads(_COVERAGE_FIXTURE.read_text(encoding="utf-8"))["events"]
        result = bss.suggest(events)
        self.assertTrue(result["applicable"])
        self.assertFalse(result["reliable"])
        self.assertEqual(result["degrade_reason"], bss.DEGRADE_COVERAGE)
        for key in ("gross_total", "sales_amount", "output_vat", "pending_count"):
            self.assertNotIn(key, result)
        cov = result["coverage"]
        self.assertEqual(cov["row_count"], 519)
        self.assertEqual(cov["chain_breaks"], 65)
        self.assertEqual(cov["unexplained_inflow"], "77733.79")
        # 降级时不烧大脑钱:未决行恒空,run 端点问 0 题。
        self.assertEqual(bss.pending_rows(events), [])

    def test_golden_12_pages_vs_self_reported_18_names_missing_6(self):
        # SA3R-b 安全网:金标真形态归到 12 页 519 行,页 1 自报 18 页 / 728+33=761 笔。补上自报
        # 总数事件后,coverage 从「页内链断」升级为点名「缺整页」——这正是尸检暴露的 SA-3 盲区
        # (12 页时页内链完好会误判 reliable,漏 6 页 330k 入账无人察觉)。
        events = json.loads(_COVERAGE_FIXTURE.read_text(encoding="utf-8"))["events"]
        events = events + [_totals_event(pages=18, deposits=728, withdrawals=33)]
        result = bss.suggest(events)
        self.assertFalse(result["reliable"])
        self.assertEqual(result["degrade_reason"], bss.DEGRADE_INCOMPLETE)
        stmt = result["coverage"]["statement"]
        self.assertTrue(stmt["incomplete"])
        self.assertEqual(stmt["expected_pages"], 18)
        self.assertEqual(stmt["parsed_pages"], 12)
        self.assertEqual(stmt["missing_pages"], 6)
        self.assertEqual(stmt["expected_rows"], 761)
        self.assertEqual(stmt["parsed_rows"], 519)
        self.assertEqual(stmt["missing_rows"], 242)
        # 缺料话术四语齐 + 抬到顶层供缺料卡直接渲染;建议值三键一个不出。
        self.assertEqual(set(result["message"]), {"th", "en", "zh", "ja"})
        self.assertIn("18", result["message"]["zh"])
        for key in ("gross_total", "sales_amount", "output_vat"):
            self.assertNotIn(key, result)
        self.assertEqual(bss.pending_rows(events), [])

    def test_self_reported_totals_all_present_stays_reliable(self):
        # 页数与笔数都对得上 → 不判 incomplete;链也无异常 → 建议值照出(自报总数不误伤完整对账单)。
        events = [
            _bank_event(
                [
                    _dep("2569-05-01", 100.0, balance=1100.0),
                    _dep("2569-05-02", 100.0, balance=1200.0),
                    _dep("2569-05-03", 100.0, balance=1300.0),
                    _dep("2569-05-04", 100.0, balance=1400.0),
                    _dep("2569-05-05", 100.0, balance=1500.0),
                ],
                item_id="i1",
            ),
            _totals_event(pages=1, deposits=5, withdrawals=0),
        ]
        result = bss.suggest(events)
        self.assertTrue(result["reliable"])
        self.assertFalse(result["coverage"]["statement"]["incomplete"])
        self.assertIn("gross_total", result)

    def test_no_totals_event_shape_byte_identical(self):
        # 无自报总数事件(闸关/非对账单场景)→ coverage 不挂 statement 块,行为逐字节现状。
        events = [_bank_event([_dep("2569-05-01", 100.0, balance=1100.0)])]
        cov = bss.coverage_check(events)
        self.assertNotIn("statement", cov)

    def test_large_unexplained_inflow_degrades(self):
        # 两行间余额跳 +5000 但行上入账只有 100:漏行净入账 4900,远超 2% 线 → 降级。
        events = [
            _bank_event(
                [
                    _dep("2569-05-01", "100.00", balance="1100.00"),
                    _dep("2569-05-02", "100.00", balance="6100.00"),
                ]
            )
        ]
        result = bss.suggest(events)
        self.assertFalse(result["reliable"])
        self.assertEqual(result["coverage"]["unexplained_inflow"], "4900.00")
        self.assertNotIn("sales_amount", result)

    def test_rounding_delta_within_tolerance_stays_reliable(self):
        events = [
            _bank_event(
                [
                    _dep("2569-05-01", 100.0, balance=1100.0),
                    _dep("2569-05-02", 100.0, balance=1200.01),  # 0.01 分位舍入,不算断链
                ]
            )
        ]
        result = bss.suggest(events)
        self.assertTrue(result["reliable"])
        self.assertEqual(result["coverage"]["verified_pairs"], 1)
        self.assertIn("gross_total", result)

    def test_no_balance_data_reports_zero_verified_pairs(self):
        # 无余额列的行验不了链:无断链证据 → 不降级,但 verified_pairs=0 如实报告证据基数
        # (读侧可见「这份建议没有余额链背书」,探不到 ≠ 没有,证据面诚实)。
        events = [_bank_event([_dep("2569-05-01", 100.0), _dep("2569-05-02", 200.0)])]
        result = bss.suggest(events)
        self.assertTrue(result["reliable"])
        self.assertEqual(result["coverage"]["verified_pairs"], 0)
        self.assertEqual(result["coverage"]["chain_breaks"], 0)

    def test_buddhist_period_conversion_and_invalid_period(self):
        self.assertEqual(bss.stmt_totals.period_month("2569-05"), (2026, 5))
        self.assertIsNone(bss.stmt_totals.period_month("May-2569"))

    def test_three_missing_tail_days_degrade_and_name_dates(self):
        days = list(range(1, 18)) + [28]
        events = [
            _bank_event(
                [_dep(f"2026-05-{day:02d}", 100 + row) for row in range(5)],
                item_id=f"page-{page}",
                eid=page,
            )
            for page, day in enumerate(days, start=1)
        ]
        result = bss.suggest(events, period="2569-05")
        self.assertFalse(result["reliable"])
        self.assertEqual(result["degrade_reason"], bss.DEGRADE_DATE_GAP)
        self.assertEqual(
            result["coverage"]["date_coverage"]["missing_dates"],
            ["2026-05-29", "2026-05-30", "2026-05-31"],
        )
        self.assertIn("2026-05-29", result["message"]["zh"])

    def test_single_missing_day_warns_without_degrading(self):
        events = [_bank_event([_dep("2026-05-01", 100), _dep("2026-05-30", 200)])]
        result = bss.suggest(events, period="2569-05")
        self.assertTrue(result["reliable"])
        self.assertEqual(result["coverage"]["date_coverage"]["missing_dates"], ["2026-05-31"])
        self.assertIn("message", result)

    def test_invalid_period_does_not_enable_date_gate(self):
        events = [_bank_event([_dep("2026-05-01", 100), _dep("2026-05-28", 200)])]
        result = bss.suggest(events, period="bad")
        self.assertTrue(result["reliable"])
        self.assertNotIn("date_coverage", result["coverage"])

    def test_single_row_fragment_is_not_counted_as_statement_page(self):
        events = [
            _bank_event([_dep("2026-05-01", i) for i in range(5)], item_id="page"),
            _bank_event([_dep("2026-05-02", 1)], item_id="IMG_2586", eid=2),
            _totals_event(pages=1, deposits=None, withdrawals=None),
        ]
        coverage = bss.coverage_check(events)
        self.assertEqual(coverage["statement"]["parsed_pages"], 1)
        self.assertFalse(coverage["statement"]["incomplete"])

    @staticmethod
    def _handoff_events(balance_shift="0"):
        """跨页交接两页夹具:第 2 页余额整体平移 shift(Decimal 口径)造断链,0=严丝合缝。"""
        shift = Decimal(balance_shift)
        first = [
            _dep("2026-05-10", 100, balance="327500.00"),
            _dep("2026-05-10", 100, balance="327600.00"),
            _dep("2026-05-10", "75.62", balance="327675.62"),
        ]
        second = [
            _dep("2026-05-11", 390, balance=str(Decimal("328065.62") + shift)),
            _dep("2026-05-11", 100, balance=str(Decimal("328165.62") + shift)),
            _wd("2026-05-11", 50, balance=str(Decimal("328115.62") + shift)),
        ]
        return [_bank_event(first, item_id="a"), _bank_event(second, item_id="b", eid=2)]

    def test_cross_file_balance_handoff_and_break(self):
        connected = bss.suggest(self._handoff_events())
        self.assertTrue(connected["coverage"]["segment_chain"]["reliable"])

        # 材料性断链(差额 100/捕获 765.62 ≈ 13% > 2%)→ 降级
        broken = bss.suggest(self._handoff_events(balance_shift="100"))
        self.assertFalse(broken["reliable"])
        self.assertEqual(broken["degrade_reason"], bss.DEGRADE_CHAIN_BREAK)
        self.assertIn("2026-05-10", broken["message"]["zh"])

    def test_immaterial_boundary_gap_warns_without_degrading(self):
        # 噪声级断链(差额 10/捕获 765.62 ≈ 1.3% ≤ 2%)→ 保留 breaks+gap_total 供人核对,不降级。
        # SM 2569-05 真人重跑实锤:19 页照片单代必有 ±฿8~2,500 页边界抖动,零容忍=永远出不了建议。
        result = bss.suggest(self._handoff_events(balance_shift="10"))
        seg = result["coverage"]["segment_chain"]
        self.assertTrue(seg["reliable"])
        self.assertEqual(len(seg["breaks"]), 1)
        self.assertEqual(seg["gap_total"], "10.00")
        self.assertNotEqual(result.get("degrade_reason"), bss.DEGRADE_CHAIN_BREAK)


class PendingRowsTests(unittest.TestCase):
    def test_pending_excludes_decided_and_already_suggested(self):
        events = [
            _bank_event(
                [_dep("2569-05-01", 100.0), _dep("2569-05-02", 200.0), _dep("2569-05-03", 300.0)]
            )
        ]
        rows = bss.parsed_rows_from_events(events)
        stream = events + [
            _human(rows[0]["fingerprint"], bss.NON_SALES, eid=2),  # 人裁过
            _brain(rows[1]["fingerprint"], bss.SALES, eid=3),  # 大脑问过
        ]
        pend = bss.pending_rows(stream)
        self.assertEqual([r["fingerprint"] for r in pend], [rows[2]["fingerprint"]])

    def test_cannot_judge_suggestion_not_reasked(self):
        events = [_bank_event([_dep("2569-05-01", 100.0)])]
        fp = bss.parsed_rows_from_events(events)[0]["fingerprint"]
        # 认怂建议(verdict=cannot_judge)仍算「问过」,不重问(读侧该行仍待定)。
        stream = events + [_brain(fp, bss.CANNOT_JUDGE, eid=2)]
        self.assertEqual(bss.pending_rows(stream), [])
        self.assertEqual(bss.suggest(stream)["counts"]["pending"], 1)


class _DetailStore(WorkOrderFakeStoreBase):
    def __init__(self, events):
        super().__init__()
        self.events = events

    def _on_event_appended(self, row):
        self.events.append(row)

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        return {
            "id": "wo-1",
            "tenant_id": tenant_id,
            "workspace_client_id": 7,
            "period": "2569-05",
            "intent": "monthly_vat",
            "status": "stuck",
            "current_step": "reconcile",
            "updated_at": "2026-07-17T08:30:00+07:00",
        }

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return []

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]

    def list_deliverables(self, cur, *, tenant_id, work_order_id):
        return []


class OrderDetailGateTests(unittest.TestCase):
    """硬闸:闸关 order_detail 无 bank_sales_suggestion 键(逐字节维持现状);闸开才挂键。"""

    def setUp(self):
        self._orig = api.store
        api.store = _DetailStore([_bank_event([_dep("2569-05-01", 1070.0)])])
        self.addCleanup(setattr, api, "store", self._orig)

    def test_gate_off_has_no_key(self):
        with mock.patch.object(
            api.feature_flags, "pearnly_ai_bank_sales_suggest_enabled_for", return_value=False
        ):
            detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertNotIn("bank_sales_suggestion", detail)

    def test_gate_on_attaches_projection(self):
        with mock.patch.object(
            api.feature_flags, "pearnly_ai_bank_sales_suggest_enabled_for", return_value=True
        ):
            detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertIn("bank_sales_suggestion", detail)
        self.assertTrue(detail["bank_sales_suggestion"]["applicable"])


if __name__ == "__main__":
    unittest.main()
