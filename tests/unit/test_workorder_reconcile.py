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


class R1ClaimWindowTests(unittest.TestCase):
    """B-6:超 6 个月的进项票不再无声计入 ภ.พ.30。

    工单线此前零日期判据(compute 是一次减法),超期票的税额照进申报 = 多抵,被查要补税加罚;
    账本线早有这条规则却在另一处(services/tax/aggregate),两套口径。修后走同一条规则,并且
    只点名不自动剔除 —— 自动剔除同样是背着人改钱,只是方向反了。
    ★ 工单 period 是佛历(2569-05),票面日期落库是公历,不转换判据恒不触发。
    """

    def _out(self, invoice_date, period="2569-11"):
        items = [_pi("p1", file="old.jpg")]
        events = [
            _money_evt("p1", net="1000.00", vat="70.00", grand="1070.00"),
            _sales_evt(),
        ]
        events[0]["payload"]["money"]["invoice_date"] = invoice_date
        store = FakeStore(items, events)
        store.get_work_order = lambda cur, *, tenant_id, work_order_id: {"period": period}
        # 期间要真读得到才判得了超期:_shadow_period 在 cur 为空时直接返 None,给个非空游标。
        ctx = StepContext(cur=object(), tenant_id="t-1", work_order_id="wo-1", store=store, data={})
        return reconcile.run(ctx)

    def test_invoice_beyond_six_months_stucks_and_names_the_ticket(self):
        # 期间 2569-11 = 公历 2026-11;2026-01 的票已过 6 个月窗口。
        out = self._out("2026-01-15")
        self.assertEqual(out.status, "stuck")
        self.assertTrue(any("old.jpg" in r for r in out.reasons), out.reasons)
        self.assertTrue(any("2026-01-15" in r for r in out.reasons), out.reasons)
        self.assertTrue(any("不可抵" in r for r in out.reasons), out.reasons)

    def test_invoice_inside_window_counts_as_before(self):
        out = self._out("2026-06-15")
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["input_vat_total"]), Decimal("70.00"))

    def test_buddhist_period_is_converted_not_compared_raw(self):
        """佛历年直接拿去比会差 543 年 → 判据恒不触发。这条钉死转换真发生了。"""
        self.assertEqual(self._out("2026-01-15", period="2569-11").status, "stuck")
        # 同一张票放在 2026-11(万一期间已是公历)也该判超期,转换要幂等。
        self.assertEqual(self._out("2026-01-15", period="2026-11").status, "stuck")

    def test_unreadable_date_is_not_judged_here(self):
        # 日期读不出不在本闸拦(那是另一道闸的事),不硬判成超期。
        out = self._out("")
        self.assertEqual(out.status, "ok")

    def test_no_period_skips_the_check(self):
        items = [_pi("p1", file="old.jpg")]
        events = [_money_evt("p1", net="1000.00", vat="70.00", grand="1070.00"), _sales_evt()]
        events[0]["payload"]["money"]["invoice_date"] = "2020-01-01"
        out = reconcile.run(_ctx(FakeStore(items, events)))  # FakeStore 无 get_work_order
        self.assertEqual(out.status, "ok")


class R1UnreadableMoneyTests(unittest.TestCase):
    """A-5 根治:票面钱字段「印了但读不出」绝不当 0 静默进合计,一律停机点名到票到字段。

    修前:to_dec 把 "7O.00"(字母 O)归 0,这张票贡献 ฿0 进项税、工单照样 ok 出数 —— 进项税
    少算而没有任何人知道。判据只此一份(_face_value),四条取数路径共用。
    """

    # 含税额一律不给:让 _effective 派生成 净+税,票面自身恒自洽 → R4 试算闸永远拦不住这张票。
    # 只有 A-5 这道闸能拦。回滚验证时若含税额写死,红的会是 R4 而不是 A-5,等于测了个寂寞。
    def _out(self, vat, *, net="1428.57"):
        items = [_pi("p1", file="clean.jpg"), _pi("p2", file="IMG_2647.jpg")]
        events = [
            _money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"),
            _money_evt("p2", net=net, vat=vat, grand=None, inv="IV002"),
            _sales_evt(),
        ]
        return reconcile.run(_ctx(FakeStore(items, events)))

    def test_readable_twin_proves_the_money_at_stake(self):
        # 同一张票读对时它贡献 ฿70:这就是修前被静默吞掉的数额。
        out = self._out("70.00")
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["input_vat_total"]), Decimal("170.00"))

    def test_ocr_misread_vat_stucks_and_names_ticket_and_field(self):
        out = self._out("7O.00")
        self.assertEqual(out.status, "stuck")
        self.assertTrue(any("IMG_2647" in r for r in out.reasons), out.reasons)
        self.assertTrue(any("税额" in r and "7O.00" in r for r in out.reasons), out.reasons)
        self.assertTrue(any("读不出" in r for r in out.reasons), out.reasons)
        # 停机时绝不能顺手把少算的合计发出去。
        self.assertIsNone(out.payload.get("input_vat_total"))

    def test_na_and_dash_placeholders_are_misreads_not_zero(self):
        for placeholder in ("N/A", "-", "—"):
            with self.subTest(placeholder=placeholder):
                self.assertEqual(self._out(placeholder).status, "stuck")

    def test_nan_literal_never_poisons_the_total(self):
        # Decimal("NaN") 是合法字面量,不抛错;修前它一路走到 R4 让整步崩 InvalidOperation。
        self.assertEqual(self._out("NaN").status, "stuck")

    def test_unreadable_subtotal_also_stucks(self):
        self.assertEqual(self._out("100.00", net="1,4二8.57").status, "stuck")

    def test_absent_money_field_keeps_current_derive_behaviour(self):
        # None/空串是「票上没印这个数」,交给 _effective 派生兜底,不算读花 —— 不许因此卡单。
        for absent in (None, "", "   "):
            with self.subTest(absent=absent):
                items = [_pi("p1", file="clean.jpg")]
                events = [
                    _money_evt("p1", net="1428.57", vat="100.00", grand=absent),
                    _sales_evt(),
                ]
                out = reconcile.run(_ctx(FakeStore(items, events)))
                self.assertEqual(out.status, "ok")
                self.assertEqual(Decimal(out.payload["input_vat_total"]), Decimal("100.00"))

    def test_face_value_decision_on_misread_ticket_stucks(self):
        items = [
            _pi("p1", file="clean.jpg"),
            _pi("x", status="flagged", flag_reason="amount_math_fail", file="IMG_2647.jpg"),
        ]
        events = [
            _money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"),
            _money_evt("x", net="58128.57", vat="4O69.00", grand=None, status="flagged"),
            _decision_evt("x", "face_value"),
            _sales_evt(),
        ]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.status, "stuck")
        self.assertTrue(any("读不出" in r for r in out.reasons), out.reasons)

    def test_direction_assigned_purchase_on_misread_ticket_stucks(self):
        # 方向不明票必须 kind=unknown 才进方向通道;写成 purchase 会先被「未知裁决」拦下,
        # 那样测的就不是这道闸了。
        items = [_pi("p1", file="clean.jpg"), _ambiguous("d", file="DIR.jpg")]
        events = [
            _money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"),
            _ambiguous_money_evt("d", net="1000.00", vat="7O.00", grand=None),
            {
                "event_type": "human_decision",
                "step": "reconcile",
                "payload": {"item_id": "d", "kind": "purchase_invoice"},
            },
            _sales_evt(),
        ]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.status, "stuck")
        self.assertTrue(any("DIR.jpg" in r and "读不出" in r for r in out.reasons), out.reasons)

    def test_helper_reports_only_printed_but_unreadable_fields(self):
        from services.workorder.steps.reconcile_gates import unreadable_money_fields

        self.assertEqual(unreadable_money_fields({"vat": "7O.00"}), ["vat"])
        self.assertEqual(unreadable_money_fields({"subtotal": None, "vat": ""}), [])
        self.assertEqual(
            unreadable_money_fields({"subtotal": "x", "vat": "1", "total_amount": "N/A"}),
            ["subtotal", "total_amount"],
        )
        self.assertEqual(unreadable_money_fields({"vat": "1,234.50"}), [])


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

    def test_direction_plus_recalc_both_apply_either_order(self):
        # SM 2569-05 死锁根治:同一件先定向再改数(或反序),两裁决必须都生效——
        # 旧单槽 latest-wins 下 recalc 顶掉方向(方向卡)或方向顶掉 recalc(金额卡),永远出不了包。
        recalc = _decision_evt(
            "d1", "recalc", values={"net": "5284.49", "vat": "369.91", "grand_total": "5654.40"}
        )
        assign = _assign_kind_evt("d1", "purchase_invoice")
        for name, pair in (
            ("recalc→assign", [recalc, assign]),
            ("assign→recalc", [assign, recalc]),
        ):
            with self.subTest(order=name):
                store = FakeStore(
                    [_pi("p1", file="a.jpg"), _ambiguous("d1", file="IMG_2648.jpg")],
                    [
                        _money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"),
                        # 票面读错:净+税≠含税(差 -1000),recalc 人工补正为自洽三数。
                        _ambiguous_money_evt("d1", net="4284.49", vat="369.91", grand="5654.40"),
                        *pair,
                        _sales_evt(),
                    ],
                )
                out = reconcile.run(_ctx(store))
                self.assertEqual(out.status, "ok")
                self.assertEqual(
                    Decimal(out.payload["input_vat_total"]),
                    Decimal("100.00") + Decimal("369.91"),
                )

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

    def test_summary_row_cross_check_recorded_on_gate(self):
        items = [_pi("p1", file="a.jpg")]
        events = [_money_evt("p1", net="1428.57", vat="100.00", grand="1528.57"), _sales_evt()]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.payload["gates"]["r2_sales"]["total_check"], "matched")

    def test_summary_row_mismatch_stops_and_names_both_numbers(self):
        """表内合计行与逐行求和打架 → 停机点名,绝不悄悄采信其中一个数。"""
        items = [_pi("p1", file="a.jpg")]
        reads = {
            "s1": {
                "headers": ["วันที่", "ยอดขาย", "ภาษีขาย"],
                "rows": [
                    {"cells": ["1", "500.00", "35.00"], "is_summary": False},
                    {"cells": ["รวม", "900.00", "63.00"], "is_summary": True},
                ],
            }
        }
        events = [_money_evt("p1", net="1428.57", vat="100.00", grand="1528.57")]
        out = reconcile.run(_ctx(FakeStore(items, events), data={"sales_summary_reads": reads}))
        self.assertEqual(out.status, "stuck")
        joined = " ".join(out.reasons)
        self.assertIn("sales_total_mismatch[s1]", joined)
        self.assertIn("500.00", joined)
        self.assertIn("900.00", joined)

    def test_truncated_summary_stops_and_names_it(self):
        """行数超上限被截断 → 停机点名(与合计行打架同级):少算的行不进 R2,合计行常被一并
        截走让交叉校验退成 absent,不拦就一路绿灯少算销售额/销项税(交接 A-3)。"""
        items = [_pi("p1", file="a.jpg")]
        reads = {
            "big": {
                "headers": ["วันที่", "ยอดขาย", "ภาษีขาย"],
                "rows": [{"cells": ["1", "500.00", "35.00"], "is_summary": False}],
                "truncated": True,
            }
        }
        events = [_money_evt("p1", net="1428.57", vat="100.00", grand="1528.57")]
        out = reconcile.run(_ctx(FakeStore(items, events), data={"sales_summary_reads": reads}))
        self.assertEqual(out.status, "stuck")
        self.assertIn("sales_rows_truncated[big]", " ".join(out.reasons))


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
