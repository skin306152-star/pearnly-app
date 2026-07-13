# -*- coding: utf-8 -*-
"""R3 银行对账逐笔对平接线测试(E1 · reconcile.py R3 + pearnly_ai_bank_recon 闸)。

闸关:R3 逐字节维持存在性判定现状(无 recon 键)。闸开+有 bank_statement 件:流水↔工单
事件流票据逐笔对平,缺票/未达两张清单挂进 r3_bank.recon,且工单绝不 stuck、能继续到 package。
全内存 FakeStore + 注入银行流水行,不碰库/OCR/密钥/真闸。
"""

import datetime
import unittest
from decimal import Decimal

from services.recon.bank_recon_types import StatementRow
from services.workorder.engine import StepContext
from services.workorder.steps import reconcile


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


def _bank(item_id):
    return {"id": item_id, "kind": "bank_statement", "status": "ok", "file_ref": "/in/b.pdf"}


def _money_evt(item_id, *, net, vat, grand, inv, date, vendor):
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": "purchase_invoice",
            "status": "ok",
            "money": {
                "subtotal": net,
                "vat": vat,
                "total_amount": grand,
                "invoice_number": inv,
                "seller_tax": "0735527000289",
                "invoice_date": date,
                "vendor": vendor,
            },
        },
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


def _store():
    items = [_pi("p1", "a.jpg"), _pi("p2", "b.jpg"), _bank("b1")]
    events = [
        _money_evt(
            "p1",
            net="1000.00",
            vat="70.00",
            grand="1070.00",
            inv="INV1",
            date="2026-06-07",
            vendor="Acme",
        ),
        _money_evt(
            "p2",
            net="200.00",
            vat="14.00",
            grand="214.00",
            inv="INV2",
            date="2026-06-09",
            vendor="Beta",
        ),
        _sales_evt(),
    ]
    return FakeStore(items, events)


def _rows_auto_plus_missing(ctx, banks):
    """p1(1070)有对应付款行 → 自动匹配;一条 555 无票 → 缺票;p2(214)无流水 → 未达。"""
    d = datetime.date
    return [
        StatementRow(d(2026, 6, 7), "Acme payment INV1", 1070.0, 0.0, 8930.0),
        StatementRow(d(2026, 6, 15), "unknown payee", 555.0, 0.0, 8375.0),
    ]


class GateOffKeepsPresenceOnly(unittest.TestCase):
    """闸关:R3 逐字节维持现状(only present/count,无 recon 键)。"""

    def setUp(self):
        self._prev = reconcile._bank_recon_enabled
        reconcile._bank_recon_enabled = lambda ctx: False
        self.addCleanup(setattr, reconcile, "_bank_recon_enabled", self._prev)

    def test_r3_has_no_recon_key_when_gate_off(self):
        out = reconcile.run(_ctx(_store()))
        self.assertEqual(out.status, "ok")
        r3 = out.payload["gates"]["r3_bank"]
        self.assertTrue(r3["bank_statement_present"])
        self.assertEqual(r3["bank_statement_count"], 1)
        self.assertNotIn("recon", r3)


class GateOnRunsReconWithoutBlockingPackage(unittest.TestCase):
    """闸开:产出两张清单进 r3_bank.recon,工单 ok(不 stuck,能继续到 package)。"""

    def setUp(self):
        self._prev_flag = reconcile._bank_recon_enabled
        self._prev_rows = reconcile._bank_statement_rows
        reconcile._bank_recon_enabled = lambda ctx: True
        reconcile._bank_statement_rows = _rows_auto_plus_missing
        self.addCleanup(setattr, reconcile, "_bank_recon_enabled", self._prev_flag)
        self.addCleanup(setattr, reconcile, "_bank_statement_rows", self._prev_rows)

    def test_recon_produces_two_lists_and_stays_ok(self):
        out = reconcile.run(_ctx(_store()))
        # 关键:对不平也绝不 stuck，工单 ok（编排层据此继续推进到 package）。
        self.assertEqual(out.status, "ok")
        recon = out.payload["gates"]["r3_bank"]["recon"]

        self.assertEqual(recon["auto_matched_count"], 1)
        self.assertEqual(recon["auto_matched"][0]["candidate_id"], "p1")

        # 缺票清单：555 那条付款无对应票。
        self.assertEqual(recon["missing_invoice_count"], 1)
        self.assertEqual(recon["missing_invoice"][0]["amount"], "555.0")

        # 未达清单:p2(214)有票无流水。
        unmatched_ids = {u["candidate_id"] for u in recon["unmatched_invoice"]}
        self.assertIn("p2", unmatched_ids)

        # 差额结算存在且自洽。
        self.assertEqual(
            Decimal(recon["diff"]["missing_invoice_total"])
            - Decimal(recon["diff"]["unmatched_invoice_total"]),
            Decimal(recon["diff"]["net"]),
        )

    def test_r1_r2_unaffected_by_bank_recon(self):
        # R3 是佐证层:开闸对平不动 R1 进项税合计(p1 70 + p2 14 = 84)。
        out = reconcile.run(_ctx(_store()))
        self.assertEqual(Decimal(out.payload["input_vat_total"]), Decimal("84.00"))

    def test_parser_failure_is_isolated_not_fatal(self):
        def _boom(ctx, banks):
            raise RuntimeError("parse blew up")

        reconcile._bank_statement_rows = _boom
        out = reconcile.run(_ctx(_store()))
        self.assertEqual(out.status, "ok")
        self.assertEqual(out.payload["gates"]["r3_bank"]["recon"]["note"], "bank_recon_skipped")

    def test_bank_recon_human_decision_events_are_tax_invisible(self):
        # MC1-b3 验收断言:银行对账 review 人审裁决(human_decision · statement_tx_id 载荷,
        # 无 item_id)不该被 reconcile 的任何回放捡到——它只在 api._bank_recon 读侧覆盖呈现,
        # 一进 reconcile.run() 就该跟没发生过一样。逐字节比对 R1/R2/R4/税额产出。
        baseline = reconcile.run(_ctx(_store()))

        store_with_decision = _store()
        store_with_decision.events.append(
            {
                "event_type": "human_decision",
                "step": "reconcile",
                "payload": {
                    "statement_tx_id": "some-bank-row-hash",
                    "decision": "bank_recon_accept",
                    "candidate_id": "p1",
                },
            }
        )
        out = reconcile.run(_ctx(store_with_decision))

        self.assertEqual(out.status, baseline.status)
        self.assertEqual(out.payload["input_vat_total"], baseline.payload["input_vat_total"])
        self.assertEqual(
            out.payload["purchase_amount_total"], baseline.payload["purchase_amount_total"]
        )
        self.assertEqual(out.payload["sales_amount_total"], baseline.payload["sales_amount_total"])
        self.assertEqual(
            out.payload["gates"]["r1_input_vat"], baseline.payload["gates"]["r1_input_vat"]
        )
        self.assertEqual(
            out.payload["gates"]["r4_trial_balance"], baseline.payload["gates"]["r4_trial_balance"]
        )


if __name__ == "__main__":
    unittest.main()
