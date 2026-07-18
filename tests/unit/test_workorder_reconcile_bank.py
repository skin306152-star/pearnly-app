# -*- coding: utf-8 -*-
"""R3 银行对账逐笔对平接线测试(E1 · reconcile.py R3 + pearnly_ai_bank_recon 闸)。

闸关:R3 逐字节维持存在性判定现状(无 recon 键)。闸开+有 bank_statement 件:流水↔工单
事件流票据逐笔对平,缺票/未达两张清单挂进 r3_bank.recon,且工单绝不 stuck、能继续到 package。
全内存 FakeStore + 注入银行流水行,不碰库/OCR/密钥/真闸。
"""

import datetime
import os
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

from services.ai_gateway import attribution
from services.recon.bank_recon_types import StatementRow
from services.workorder.engine import StepContext
from services.workorder.steps import reconcile, reconcile_bank


class FakeStore:
    def __init__(self, items, events):
        self.items = items
        self.events = events

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)

    def append_event(self, cur, *, tenant_id, work_order_id, step, event_type, payload, **kw):
        # R3 检查点在内存态落 item_bank_parsed(dedupe_key 锚件,重复落只留一条)。
        key = kw.get("dedupe_key")
        if key and any(e.get("_dedupe") == key for e in self.events):
            return {}
        self.events.append(
            {"step": step, "event_type": event_type, "payload": payload, "_dedupe": key}
        )
        return {"id": len(self.events)}


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


def _rows_auto_plus_missing(ctx, item):
    """单件解析桩(检查点逐件调):p1(1070)有对应付款行 → 自动匹配;一条 555 无票 → 缺票;
    p2(214)无流水 → 未达。签名 (ctx, item) 与 reconcile_bank._parse_bank_file 一致。"""
    d = datetime.date
    return [
        StatementRow(d(2026, 6, 7), "Acme payment INV1", 1070.0, 0.0, 8930.0),
        StatementRow(d(2026, 6, 15), "unknown payee", 555.0, 0.0, 8375.0),
    ]


class GateOffKeepsPresenceOnly(unittest.TestCase):
    """闸关:R3 逐字节维持现状(only present/count,无 recon 键)。"""

    def setUp(self):
        self._prev = reconcile_bank._bank_recon_enabled
        reconcile_bank._bank_recon_enabled = lambda ctx: False
        self.addCleanup(setattr, reconcile_bank, "_bank_recon_enabled", self._prev)

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
        self._prev_flag = reconcile_bank._bank_recon_enabled
        self._prev_rows = reconcile_bank._parse_bank_file
        reconcile_bank._bank_recon_enabled = lambda ctx: True
        reconcile_bank._parse_bank_file = _rows_auto_plus_missing
        self.addCleanup(setattr, reconcile_bank, "_bank_recon_enabled", self._prev_flag)
        self.addCleanup(setattr, reconcile_bank, "_parse_bank_file", self._prev_rows)

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

    def test_bank_parse_runs_before_missing_sales_summary(self):
        store = _store()
        store.events = [
            event
            for event in store.events
            if event.get("payload", {}).get("kind") != "sales_summary"
        ]

        out = reconcile.run(_ctx(store))

        self.assertEqual(out.status, "needs")
        self.assertEqual(out.missing, ("sales_summary",))
        parsed = [event for event in store.events if event["event_type"] == "item_bank_parsed"]
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["payload"]["item_id"], "b1")
        self.assertEqual(len(parsed[0]["payload"]["rows"]), 2)

    def test_parser_failure_stops_without_success_checkpoint(self):
        def _boom(ctx, item):
            raise RuntimeError("parse blew up")

        reconcile_bank._parse_bank_file = _boom
        store = _store()
        out = reconcile.run(_ctx(store))
        self.assertEqual(out.status, "stuck")
        self.assertIn("bank_statement_parse_failed", out.reasons[0])
        self.assertFalse(any(e["event_type"] == "item_bank_parsed" for e in store.events))

    def test_empty_parser_result_stops_and_remains_retryable(self):
        reconcile_bank._parse_bank_file = lambda ctx, item: []
        store = _store()

        out = reconcile.run(_ctx(store))

        self.assertEqual(out.status, "stuck")
        self.assertIn("no_transaction_rows", out.reasons[0])
        self.assertFalse(any(e["event_type"] == "item_bank_parsed" for e in store.events))

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


class BankParseCheckpointTests(unittest.TestCase):
    """件 4:银行流水解析逐件检查点——落 item_bank_parsed 事件,续跑从事件回放零重解析(重烧)。"""

    def setUp(self):
        self._flag = reconcile_bank._bank_recon_enabled
        self._parse = reconcile_bank._parse_bank_file
        reconcile_bank._bank_recon_enabled = lambda ctx: True
        self.calls = []

        def _counting(ctx, item):
            self.calls.append(item["id"])
            return _rows_auto_plus_missing(ctx, item)

        reconcile_bank._parse_bank_file = _counting
        self.addCleanup(setattr, reconcile_bank, "_bank_recon_enabled", self._flag)
        self.addCleanup(setattr, reconcile_bank, "_parse_bank_file", self._parse)

    def test_emits_parsed_event_and_resume_skips_reparse(self):
        store = _store()
        out1 = reconcile.run(_ctx(store))
        self.assertEqual(out1.status, "ok")
        parsed = [e for e in store.events if e["event_type"] == "item_bank_parsed"]
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["payload"]["item_id"], "b1")
        self.assertEqual(self.calls, ["b1"])  # 首跑解析一次

        # 模拟续跑:再跑一遍,已解析银行件从 item_bank_parsed 事件回放,零重解析。
        out2 = reconcile.run(_ctx(store))
        self.assertEqual(self.calls, ["b1"])  # 未再解析(零重烧)
        self.assertEqual(
            len([e for e in store.events if e["event_type"] == "item_bank_parsed"]), 1
        )  # dedupe_key 锚件,事件不双落
        # 回放行喂 tx_from_statement_row 与首跑逐字节等价:对平结果一致。
        self.assertEqual(
            out2.payload["gates"]["r3_bank"]["recon"], out1.payload["gates"]["r3_bank"]["recon"]
        )


class BankParseCostAttributionTests(unittest.TestCase):
    """R3 银行流水 OCR 成本归因(L2-ATTR):_default_parse_bank_file 在发起解析前设请求级归因
    (task=workorder_bank_parse + 本租户 + 工单 trace),让管线深处的 ocr.layer2 落账记到客户
    头上,而非现状 tenant=NULL;归因请求级、跑完即清不泄漏(照 classify._ocr_safe 范式)。"""

    def test_parse_sets_attribution_task_tenant_trace_and_resets(self):
        seen = {}

        def _spy_impl(data, filename, *, tenant_id=None):
            # 在管线落点被调用的当刻抓归因态(等价 transport._observe 读到的 current())。
            seen["attr"] = attribution.current()
            seen["tenant_kwarg"] = tenant_id
            return {
                "ok": True,
                "rows": [StatementRow(datetime.date(2026, 5, 1), "transfer", 100.0, 0.0, 900.0)],
            }

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            tf.write(b"\xff\xd8\xff")  # 任意字节,解析被桩替换不真读图
            path = tf.name
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))

        item = {"id": "b9", "kind": "bank_statement", "status": "ok", "file_ref": path}
        ctx = StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=None, data={})

        with mock.patch("services.recon.bank_recon_v2._parse_bank_statement_impl", _spy_impl):
            reconcile_bank._default_parse_bank_file(ctx, item)

        self.assertEqual(seen["attr"]["task"], "workorder_bank_parse")
        self.assertEqual(seen["attr"]["tenant_id"], "t-1")
        self.assertEqual(seen["attr"]["trace_id"], "wo-1")
        self.assertEqual(seen["tenant_kwarg"], "t-1")  # 解析行为契约不变(tenant 仍逐调用透传)
        # 请求级归因跑完即清,不泄漏到后续调用。
        self.assertIsNone(attribution.current())

    def test_attribution_reset_even_when_parse_raises(self):
        def _boom(data, filename, *, tenant_id=None):
            raise RuntimeError("parse blew up")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            tf.write(b"\xff\xd8\xff")
            path = tf.name
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))

        item = {"id": "b9", "kind": "bank_statement", "status": "ok", "file_ref": path}
        ctx = StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=None, data={})

        with mock.patch("services.recon.bank_recon_v2._parse_bank_statement_impl", _boom):
            with self.assertRaises(RuntimeError):
                reconcile_bank._default_parse_bank_file(ctx, item)
        # finally 里 reset:异常路径也不把归因泄漏给下一件/下一步。
        self.assertIsNone(attribution.current())

    def test_no_file_ref_fails_without_setting_attribution(self):
        # 无 file_ref 直接失败,不进解析、不设归因(不无谓污染上下文)。
        ctx = StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=None, data={})
        with self.assertRaises(reconcile_bank.BankStatementParseError):
            reconcile_bank._default_parse_bank_file(ctx, {"id": "b9", "file_ref": None})
        self.assertIsNone(attribution.current())

    def test_parser_rejected_result_is_not_a_success(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            tf.write(b"\xff\xd8\xff")
            path = tf.name
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        item = {"id": "b9", "file_ref": path, "original_name": "bank.jpg"}
        ctx = StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=None, data={})

        with mock.patch(
            "services.recon.bank_recon_v2._parse_bank_statement_impl",
            return_value={"ok": False, "rows": [], "error_code": "ocr_failed"},
        ):
            with self.assertRaisesRegex(reconcile_bank.BankStatementParseError, "ocr_failed"):
                reconcile_bank._default_parse_bank_file(ctx, item)


if __name__ == "__main__":
    unittest.main()
