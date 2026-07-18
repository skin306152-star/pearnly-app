# -*- coding: utf-8 -*-
"""reconcile 勾稽四道闸守门测试(services/workorder/steps/reconcile.py · 任务包 §5 步 4 / §6)。

全程内存 FakeStore(list_items/list_events),金额从事件流回放,不碰库/OCR/密钥。覆盖:
R1 全 ok 精确合计、flagged 无裁决 stuck 点名、face_value/recalc/exclude 三条裁决路径(金标数字)、
ok 缺金额事件 stuck;R2 直读聚合+跳合计行、缺源 needs、ctx.data 兜底;R3 银行有/无;
R4 试算平/不平;幂等重跑。
"""

import unittest
from decimal import Decimal

from services.workorder.engine import StepContext
from services.workorder.steps import reconcile

# 金标常量(T0 语料盘点):按票面 vs IMG_2647 折后重算,差 9.00。
GOLDEN_INPUT_VAT = Decimal("29263.28")
GOLDEN_INPUT_VAT_RECALC = Decimal("29254.28")
UNDISPUTED_VAT = Decimal("25194.28")  # 10 张无争议票税额合计(= 金标 − IMG_2647 票面 4069)
GOLDEN_SALES_AMOUNT = Decimal("858780.16")
GOLDEN_OUTPUT_VAT = Decimal("60114.61")


class FakeStore:
    def __init__(self, items, events):
        self.items = items
        self.events = events

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)


def _pi(item_id, *, status="ok", flag_reason=None, file="IMG.jpg"):
    return {
        "id": item_id,
        "kind": "purchase_invoice",
        "status": status,
        "flag_reason": flag_reason,
        "file_ref": f"/in/{file}",
    }


def _bank(item_id):
    return {"id": item_id, "kind": "bank_statement", "status": "pending", "file_ref": "/in/b.pdf"}


def _money_evt(item_id, *, net, vat, grand, inv="IV001", status="ok"):
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": "purchase_invoice",
            "status": status,
            "money": {
                "subtotal": net,
                "vat": vat,
                "total_amount": grand,
                "invoice_number": inv,
                "seller_tax": "0735527000289",
            },
        },
    }


def _decision_evt(item_id, decision, values=None):
    return {
        "event_type": "human_decision",
        "step": "reconcile",
        "payload": {"item_id": item_id, "decision": decision, "values": values or {}},
    }


# G1 事故复现常量:定金冲抵结构(หัก เงินมัดจำ)的真进项票,VAT 3796.80 曾被 direction_ambiguous
# 判成 kind=unknown 后彻底隐形——不进队列、不进 blocked_reasons、进项静默少这一笔。
G1_DEPOSIT_VAT = Decimal("3796.80")


def _ambiguous(item_id, *, file="IMG_deposit.jpg"):
    """方向不明票在库里的形态(classify.bin_ocr_fields 判不出进/销):kind=unknown、flagged。"""
    return {
        "id": item_id,
        "kind": "unknown",
        "status": "flagged",
        "flag_reason": "direction_ambiguous",
        "file_ref": f"/in/{file}",
    }


def _ambiguous_money_evt(item_id, *, net, vat, grand, inv="DEP-01"):
    """方向不明票的 item_classified 事件:钱已 OCR 出来(kind=unknown),待人工定向。"""
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": "unknown",
            "status": "flagged",
            "money": {
                "subtotal": net,
                "vat": vat,
                "total_amount": grand,
                "invoice_number": inv,
                "seller_tax": "0735527000289",
            },
        },
    }


def _assign_kind_evt(item_id, kind):
    return {
        "event_type": "human_decision",
        "step": "reconcile",
        "payload": {"item_id": item_id, "decision": "assign_kind", "kind": kind},
    }


def _sales_evt(item_id="s1"):
    """一份销项直读:表头 ยอดขาย/ภาษีขาย + 一条数据行 + 一条合计行(应被跳过不重复计)。"""
    rows = [
        {
            "cells": ["01/05/2569", str(GOLDEN_SALES_AMOUNT), str(GOLDEN_OUTPUT_VAT)],
            "is_summary": False,
        },
        {"cells": ["รวม", str(GOLDEN_SALES_AMOUNT), str(GOLDEN_OUTPUT_VAT)], "is_summary": True},
    ]
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": "sales_summary",
            "status": "ok",
            "sales_read": {"headers": ["วันที่", "ยอดขาย", "ภาษีขาย"], "rows": rows},
        },
    }


def _ctx(store, data=None):
    return StepContext(
        cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data=data or {}
    )


class R1InputVatTests(unittest.TestCase):
    def test_all_ok_sums_precisely(self):
        items = [_pi("p1", file="a.jpg"), _pi("p2", file="b.jpg")]
        events = [
            _money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"),
            _money_evt("p2", net="2864.29", vat="200.50", grand="3064.79"),
            _sales_evt(),
        ]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.status, "ok")
        self.assertEqual(out.payload["input_vat_total"], "300.50")

    def test_flagged_without_decision_stuck_names_ticket(self):
        items = [
            _pi("p1", file="a.jpg"),
            _pi("x", status="flagged", flag_reason="amount_math_fail", file="IMG_2647.jpg"),
        ]
        events = [
            _money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"),
            _money_evt("x", net="58128.57", vat="4069.00", grand="62197.57", status="flagged"),
            _sales_evt(),
        ]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.status, "stuck")
        self.assertTrue(any("IMG_2647" in r for r in out.reasons))
        self.assertTrue(any("无人工裁决" in r for r in out.reasons))

    def test_face_value_decision_matches_golden(self):
        out = reconcile.run(_ctx(self._store_with_img2647(_decision_evt("x", "face_value"))))
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["input_vat_total"]), GOLDEN_INPUT_VAT)

    def test_recalc_decision_matches_golden(self):
        decision = _decision_evt("x", "recalc", values={"vat": "4060.00"})
        out = reconcile.run(_ctx(self._store_with_img2647(decision)))
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["input_vat_total"]), GOLDEN_INPUT_VAT_RECALC)

    def test_exclude_decision_drops_ticket(self):
        out = reconcile.run(_ctx(self._store_with_img2647(_decision_evt("x", "exclude"))))
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["input_vat_total"]), UNDISPUTED_VAT)

    def test_ok_purchase_missing_money_event_unresolved(self):
        items = [_pi("p1", file="a.jpg")]
        out = reconcile.run(_ctx(FakeStore(items, [_sales_evt()])))
        self.assertEqual(out.status, "stuck")
        self.assertTrue(any("缺 item_classified 金额事件" in r for r in out.reasons))

    def _store_with_img2647(self, decision_evt):
        """无争议票(税额合计 25194.28)+ IMG_2647 flagged + 一条裁决。"""
        items = [
            _pi("u", file="undisputed.jpg"),
            _pi("x", status="flagged", flag_reason="amount_math_fail", file="IMG_2647.jpg"),
        ]
        events = [
            _money_evt("u", net="359918.29", vat=str(UNDISPUTED_VAT), grand="385112.57"),
            _money_evt("x", net="58128.57", vat="4069.00", grand="62197.57", status="flagged"),
            decision_evt,
            _sales_evt(),
        ]
        return FakeStore(items, events)


class R1DirectionAmbiguousTests(unittest.TestCase):
    """G1 黑洞根治:方向不明票(direction_ambiguous)绝不静默,必须走人工方向裁决归位。"""

    def _events(self, *extra):
        return [
            _money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"),
            _ambiguous_money_evt("d1", net="54240.00", vat=str(G1_DEPOSIT_VAT), grand="58036.80"),
            *extra,
            _sales_evt(),
        ]

    def _store(self, *extra):
        items = [_pi("p1", file="a.jpg"), _ambiguous("d1", file="IMG_2647_deposit.jpg")]
        return FakeStore(items, self._events(*extra))

    def test_ambiguous_without_decision_stuck_names_ticket(self):
        out = reconcile.run(_ctx(self._store()))
        self.assertEqual(out.status, "stuck")
        self.assertTrue(any("IMG_2647_deposit" in r for r in out.reasons))
        self.assertTrue(any("direction_ambiguous" in r for r in out.reasons))

    def test_assign_purchase_invoice_counts_its_vat_in_r1(self):
        out = reconcile.run(_ctx(self._store(_assign_kind_evt("d1", "purchase_invoice"))))
        self.assertEqual(out.status, "ok")
        self.assertEqual(
            Decimal(out.payload["input_vat_total"]), Decimal("100.00") + G1_DEPOSIT_VAT
        )

    def test_assign_non_tax_excludes_from_r1(self):
        out = reconcile.run(_ctx(self._store(_assign_kind_evt("d1", "non_tax"))))
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["input_vat_total"]), Decimal("100.00"))

    def test_assign_sales_doc_excludes_from_r1(self):
        # 销项票面不进 R1 进项 Σ(销项合计走 R2 的 POS 直读/人工申报)。
        out = reconcile.run(_ctx(self._store(_assign_kind_evt("d1", "sales_doc"))))
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["input_vat_total"]), Decimal("100.00"))

    def test_latest_direction_decision_wins(self):
        # 先裁进项(本应计入 3796.80)后改判非税 → latest-wins 排除,不计入。
        out = reconcile.run(
            _ctx(
                self._store(
                    _assign_kind_evt("d1", "purchase_invoice"),
                    _assign_kind_evt("d1", "non_tax"),
                )
            )
        )
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["input_vat_total"]), Decimal("100.00"))


class R1RecalcBaseConsistencyTests(unittest.TestCase):
    """G1R2 采购税基 −80.89 根因回归:人工「按重算」把税额修正后,可抵扣基必须与修正后税额
    在标准税率下自洽(base = vat / 7%),绝不沿用 OCR 旧净额——旧净额对应的是被修正掉的旧
    税额,留用会让 ภ.พ.30 line6(基)÷line7(税)=7% 的申报恒等式破裂。

    形态取自真工单 6a4bfbdd(client 94)IMG_2647 折扣淡票:OCR 读 净=58048.40/税=4060.05,
    人工修正税=4069.05。修正后正确基 = 4069.05/0.07 = 58129.29,与 OCR 旧净差 80.89——这正是
    整单税基缺口的唯一来源。修前:purchase_amount_total=417965.97(用旧净);修后:418046.86。
    """

    # 无争议 10 张的真实聚合(净=税/7% 自洽):税 25194.23 → 净 359917.57(= 25194.23/0.07)。
    CLEAN_NET = "359917.57"
    CLEAN_VAT = "25194.23"
    # IMG_2647 OCR 读值(折扣淡票·净与税互不自洽,票面 total 也对不上→amount_math_fail)。
    OCR_NET, OCR_VAT, OCR_TOTAL = "58048.40", "4060.05", "62108.40"
    CORRECTED_VAT = "4069.05"  # 人工按票面印刷值修正
    OFFICIAL_PURCHASE = Decimal("418046.86")
    OFFICIAL_INPUT_VAT = Decimal("29263.28")
    GAP = Decimal("80.89")

    def _store(self):
        items = [
            _pi("clean", file="clean10.jpg"),
            _pi("x", status="flagged", flag_reason="amount_math_fail", file="IMG_2647.jpg"),
        ]
        events = [
            _money_evt(
                "clean",
                net=self.CLEAN_NET,
                vat=self.CLEAN_VAT,
                grand=str(Decimal(self.CLEAN_NET) + Decimal(self.CLEAN_VAT)),
            ),
            _money_evt(
                "x", net=self.OCR_NET, vat=self.OCR_VAT, grand=self.OCR_TOTAL, status="flagged"
            ),
            _decision_evt("x", "recalc", values={"vat": self.CORRECTED_VAT}),
            _sales_evt(),
        ]
        return FakeStore(items, events)

    def test_recalc_derives_base_from_corrected_vat_not_stale_ocr_net(self):
        out = reconcile.run(_ctx(self._store()))
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["input_vat_total"]), self.OFFICIAL_INPUT_VAT)
        # 核心断言:税基取修正后税额反推的基,整单税基精确重现官方(修前会短 80.89)。
        self.assertEqual(Decimal(out.payload["purchase_amount_total"]), self.OFFICIAL_PURCHASE)

    def test_gap_is_exactly_the_disputed_ticket_base_correction(self):
        stale = Decimal(self.CLEAN_NET) + Decimal(self.OCR_NET)  # 用旧净的历史错值
        self.assertEqual(self.OFFICIAL_PURCHASE - stale, self.GAP)

    def test_recalc_identifier_correction_becomes_effective_label(self):
        store = self._store()
        store.events[-3]["payload"]["money"]["invoice_number"] = "IN26-00575"
        store.events[-2]["payload"]["values"].update(
            {"invoice_number": "IN26-00675", "invoice_date": "2026-04-21"}
        )
        classified = reconcile._replay_money(store.events)
        decisions_by_item = reconcile._replay(store.events, "human_decision")
        result = reconcile.gates.resolve_input_vat(store.items, classified, decisions_by_item)
        self.assertTrue(any("IN26-00675" in entry["label"] for entry in result["entries"]))
        self.assertFalse(any("IN26-00575" in entry["label"] for entry in result["entries"]))


class R2SalesTests(unittest.TestCase):
    def test_aggregates_sales_and_skips_summary_row(self):
        items = [_pi("p1", file="a.jpg")]
        events = [_money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"), _sales_evt()]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(Decimal(out.payload["sales_amount_total"]), GOLDEN_SALES_AMOUNT)
        self.assertEqual(Decimal(out.payload["output_vat_total"]), GOLDEN_OUTPUT_VAT)

    def test_missing_source_needs(self):
        items = [_pi("p1", file="a.jpg")]
        events = [_money_evt("p1", net="1428.57", vat="100.00", grand="1528.57")]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.status, "needs")
        self.assertEqual(out.missing, ("sales_summary",))

    def test_ctx_data_fallback_when_no_event(self):
        items = [_pi("p1", file="a.jpg")]
        events = [_money_evt("p1", net="1428.57", vat="100.00", grand="1528.57")]
        reads = {
            "s1": {
                "headers": ["วันที่", "ยอดขาย", "ภาษีขาย"],
                "rows": [{"cells": ["x", "500.00", "35.00"], "is_summary": False}],
            }
        }
        out = reconcile.run(_ctx(FakeStore(items, events), data={"sales_summary_reads": reads}))
        self.assertEqual(out.status, "ok")
        self.assertEqual(out.payload["sales_amount_total"], "500.00")


class R3BankTests(unittest.TestCase):
    def test_bank_missing_notes_but_not_stuck(self):
        items = [_pi("p1", file="a.jpg")]
        events = [_money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"), _sales_evt()]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.status, "ok")
        self.assertEqual(out.payload["gates"]["r3_bank"]["note"], "bank_statement_missing")
        self.assertFalse(out.payload["gates"]["r3_bank"]["bank_statement_present"])

    def test_bank_present_marks_ready(self):
        items = [_pi("p1", file="a.jpg"), _bank("b1")]
        events = [_money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"), _sales_evt()]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertTrue(out.payload["gates"]["r3_bank"]["bank_statement_present"])
        self.assertEqual(out.payload["gates"]["r3_bank"]["bank_statement_count"], 1)


class R4TrialBalanceTests(unittest.TestCase):
    def test_balanced_passes(self):
        items = [_pi("p1", file="a.jpg")]
        events = [_money_evt("p1", net="1000.00", vat="70.00", grand="1070.00"), _sales_evt()]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.status, "ok")
        self.assertTrue(out.payload["gates"]["r4_trial_balance"]["balanced"])

    def test_unbalanced_stuck(self):
        # 含税额 ≠ 净+税(票面自身对不上)→ 试算不平。
        items = [_pi("p1", file="a.jpg")]
        events = [_money_evt("p1", net="1000.00", vat="70.00", grand="1099.00"), _sales_evt()]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.status, "stuck")
        self.assertTrue(any("trial_balance_unbalanced" in r for r in out.reasons))

    def test_unbalanced_stuck_names_offending_ticket(self):
        # J-11:不平时逐票点名(票号/原文件名 + 差额),总差额行仍保留。IMG_2647 场景:
        # 净 58048.40 + 税 4060.05 = 62108.45 ≠ 含税 62108.40,差 +0.05(净+税−含税)。
        items = [_pi("p1", file="a.jpg"), _pi("x", file="IMG_2647.jpg")]
        events = [
            _money_evt("p1", net="1000.00", vat="70.00", grand="1070.00"),
            _money_evt("x", net="58048.40", vat="4060.05", grand="62108.40", inv="IN26-00575"),
            _sales_evt(),
        ]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.status, "stuck")
        # 点名行:含违规票的票号且带差额;自洽的 p1 不点名。
        named = [r for r in out.reasons if "IN26-00575" in r]
        self.assertEqual(len(named), 1)
        self.assertIn("0.05", named[0])
        self.assertFalse(any("a.jpg" in r for r in out.reasons))
        # 总差额行仍在末尾(逐字节维持现状)。
        self.assertTrue(out.reasons[-1].startswith("trial_balance_unbalanced"))


class IdempotencyTests(unittest.TestCase):
    def test_rerun_yields_same_result(self):
        items = [_pi("p1", file="a.jpg")]
        events = [_money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"), _sales_evt()]
        store = FakeStore(items, events)
        first = reconcile.run(_ctx(store))
        second = reconcile.run(_ctx(store))
        self.assertEqual(first.payload, second.payload)
        self.assertEqual(first.status, second.status)


if __name__ == "__main__":
    unittest.main()
