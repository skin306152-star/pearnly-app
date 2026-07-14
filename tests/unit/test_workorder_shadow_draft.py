# -*- coding: utf-8 -*-
"""R5 影子底稿接线测试(F1 · reconcile R5 + pearnly_ai_shadow_draft 闸 + api 投影 + package 交付物)。

闸关:reconcile 逐字节维持现状(gates 无 r5_shadow 键)。闸开:R4 通过后把已裁进项分录 + 聚合
销项过纯函数复式引擎 → 建议分录/科目余额/试算平衡挂 r5_shadow,工单 ok(不 stuck、不阻断 package)。
方向裁决(non_tax 排除 / latest-wins)由 R1 上游保证,影子继承其结论。全内存 FakeStore,不碰库/闸。
"""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from services.accounting import workorder_shadow_adapter
from services.workorder import api
from services.workorder.engine import StepContext
from services.workorder.steps import package, reconcile


class FakeStore:
    def __init__(self, items, events):
        self.items = items
        self.events = events

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)


def _pi(item_id, file="IMG.jpg"):
    return {
        "id": item_id,
        "kind": "purchase_invoice",
        "status": "ok",
        "flag_reason": None,
        "file_ref": f"/in/{file}",
    }


def _ambiguous(item_id, file="AMB.jpg"):
    return {
        "id": item_id,
        "kind": "unknown",
        "status": "flagged",
        "flag_reason": "direction_ambiguous",
        "file_ref": f"/in/{file}",
    }


def _money_evt(item_id, *, net, vat, grand, kind="purchase_invoice", status="ok", inv="IV"):
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": kind,
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


def _assign_kind_evt(item_id, kind):
    return {
        "event_type": "human_decision",
        "step": "reconcile",
        "payload": {"item_id": item_id, "decision": "assign_kind", "kind": kind},
    }


def _sales_evt():
    rows = [{"cells": ["01/05/2569", "858780.16", "60114.61"], "is_summary": False}]
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": "s1",
            "kind": "sales_summary",
            "status": "ok",
            "sales_read": {"headers": ["วันที่", "ยอดขาย", "ภาษีขาย"], "rows": rows},
        },
    }


def _ctx(store):
    return StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data={})


def _two_purchase_store():
    items = [_pi("p1", "a.jpg"), _pi("p2", "b.jpg")]
    events = [
        _money_evt("p1", net="1000.00", vat="70.00", grand="1070.00"),
        _money_evt("p2", net="200.00", vat="14.00", grand="214.00"),
        _sales_evt(),
    ]
    return FakeStore(items, events)


class GateOffKeepsNoShadowKey(unittest.TestCase):
    def setUp(self):
        self._prev = reconcile._shadow_draft_enabled
        reconcile._shadow_draft_enabled = lambda ctx: False
        self.addCleanup(setattr, reconcile, "_shadow_draft_enabled", self._prev)

    def test_gates_have_no_r5_shadow_when_off(self):
        out = reconcile.run(_ctx(_two_purchase_store()))
        self.assertEqual(out.status, "ok")
        self.assertNotIn("r5_shadow", out.payload["gates"])


class GateOnProducesShadow(unittest.TestCase):
    def setUp(self):
        self._prev = reconcile._shadow_draft_enabled
        reconcile._shadow_draft_enabled = lambda ctx: True
        self.addCleanup(setattr, reconcile, "_shadow_draft_enabled", self._prev)

    def test_shadow_has_three_pieces_and_balanced_and_stays_ok(self):
        out = reconcile.run(_ctx(_two_purchase_store()))
        self.assertEqual(out.status, "ok")
        shadow = out.payload["gates"]["r5_shadow"]
        for key in ("entries", "accounts", "trial_balance"):
            self.assertIn(key, shadow)
        tb = shadow["trial_balance"]
        self.assertTrue(tb["balanced"])
        self.assertLessEqual(Decimal(tb["diff"]), Decimal("0.01"))
        self.assertEqual(Decimal(tb["debit"]), Decimal(tb["credit"]))
        # 两张进项票 → 两条 purchase source + 聚合销项 + VAT 结转。
        purchase_sources = [s for s in shadow["sources"] if s["label"].startswith("进项票")]
        self.assertEqual(len(purchase_sources), 2)

    def test_r1_r2_unaffected_by_shadow(self):
        out = reconcile.run(_ctx(_two_purchase_store()))
        # 影子是佐证层:不动 R1 进项税合计(70 + 14 = 84)/ R2 销项。
        self.assertEqual(Decimal(out.payload["input_vat_total"]), Decimal("84.00"))
        self.assertEqual(Decimal(out.payload["output_vat_total"]), Decimal("60114.61"))

    def test_engine_exception_isolated_not_fatal(self):
        def _boom(*a, **k):
            raise RuntimeError("shadow blew up")

        prev = workorder_shadow_adapter.build_shadow
        workorder_shadow_adapter.build_shadow = _boom
        self.addCleanup(setattr, workorder_shadow_adapter, "build_shadow", prev)
        out = reconcile.run(_ctx(_two_purchase_store()))
        self.assertEqual(out.status, "ok")
        self.assertEqual(out.payload["gates"]["r5_shadow"]["note"], "shadow_draft_skipped")

    def test_non_tax_direction_ticket_excluded_from_shadow(self):
        # 方向不明票裁 non_tax → 不入 R1 → 不入影子分录(只 p1 一条 purchase source)。
        items = [_pi("p1", "a.jpg"), _ambiguous("d1", "dep.jpg")]
        events = [
            _money_evt("p1", net="1000.00", vat="70.00", grand="1070.00"),
            _money_evt(
                "d1", net="500.00", vat="35.00", grand="535.00", kind="unknown", status="flagged"
            ),
            _assign_kind_evt("d1", "non_tax"),
            _sales_evt(),
        ]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        self.assertEqual(out.status, "ok")
        shadow = out.payload["gates"]["r5_shadow"]
        purchase_sources = [s for s in shadow["sources"] if s["label"].startswith("进项票")]
        self.assertEqual(len(purchase_sources), 1)

    def test_latest_direction_decision_wins_in_shadow(self):
        # 先裁进项后改判 non_tax → latest-wins 排除,影子只剩 p1。
        items = [_pi("p1", "a.jpg"), _ambiguous("d1", "dep.jpg")]
        events = [
            _money_evt("p1", net="1000.00", vat="70.00", grand="1070.00"),
            _money_evt(
                "d1", net="500.00", vat="35.00", grand="535.00", kind="unknown", status="flagged"
            ),
            _assign_kind_evt("d1", "purchase_invoice"),
            _assign_kind_evt("d1", "non_tax"),
            _sales_evt(),
        ]
        out = reconcile.run(_ctx(FakeStore(items, events)))
        shadow = out.payload["gates"]["r5_shadow"]
        purchase_sources = [s for s in shadow["sources"] if s["label"].startswith("进项票")]
        self.assertEqual(len(purchase_sources), 1)


def _reconcile_done_with_shadow(shadow_payload):
    return {
        "id": 30,
        "step": "reconcile",
        "event_type": "step_done",
        "payload": {"gates": {"r5_shadow": shadow_payload}},
    }


class ApiShadowProjectionTests(unittest.TestCase):
    """读侧投影 api.shadow_draft:闸开有底稿→dict,闸关/无数据/异常残影→None 诚实降级。"""

    def _shadow_payload(self):
        result = workorder_shadow_adapter.build_shadow(
            purchase_entries=[
                {"net": Decimal("1000"), "vat": Decimal("70"), "grand": Decimal("1070")}
            ],
            sales_amount=Decimal("5000"),
            output_vat=Decimal("350"),
        )
        return result.as_gate_payload()

    def test_projection_returns_shadow_when_present(self):
        events = [_reconcile_done_with_shadow(self._shadow_payload())]
        out = api.shadow_draft(events)
        self.assertIsNotNone(out)
        self.assertIn("trial_balance", out)

    def test_projection_none_when_no_reconcile_done(self):
        self.assertIsNone(api.shadow_draft([]))

    def test_projection_none_on_skipped_residue(self):
        # _run_shadow_draft 异常残影缺 trial_balance → 诚实 None。
        events = [_reconcile_done_with_shadow({"note": "shadow_draft_skipped", "error": "X"})]
        self.assertIsNone(api.shadow_draft(events))


class PackageShadowDeliverableTests(unittest.TestCase):
    """交付物 _write_shadow:从 gates.r5_shadow 渲染建议分录/科目余额/试算平衡,只渲染不重算。"""

    def _shadow_payload(self):
        result = workorder_shadow_adapter.build_shadow(
            purchase_entries=[
                {"net": Decimal("1000"), "vat": Decimal("70"), "grand": Decimal("1070")}
            ],
            sales_amount=Decimal("5000"),
            output_vat=Decimal("350"),
        )
        return result.as_gate_payload()

    def test_write_shadow_renders_three_sections_and_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, snap = package._write_shadow(Path(tmp), self._shadow_payload())
            md = Path(path).read_text(encoding="utf-8")
            self.assertIn("影子底稿", md)
            self.assertIn("建议分录", md)
            self.assertIn("科目余额", md)
            self.assertIn("试算平衡", md)
            self.assertTrue(snap["balanced"])
            self.assertEqual(Decimal(snap["debit"]), Decimal(snap["credit"]))


if __name__ == "__main__":
    unittest.main()
