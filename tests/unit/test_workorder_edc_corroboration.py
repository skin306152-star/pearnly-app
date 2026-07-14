# -*- coding: utf-8 -*-
"""EDC 聚合佐证适配器守门(services/workorder/steps/edc_corroboration.py · SA-2b)。

覆盖:① 事件回放 → SA-1 payload 映射(过滤/排序/ref);② 适配器聚合与 sales_agg CLI
直跑同料逐字节一致(证明工单侧没有第二套聚合口径);③ 覆盖率诚实(amber/needs);
④ 冻结/现算写读归一 + stale 点破;⑤ reconcile 挂钩:零 EDC 件 gates 逐字节不变、
佐证异常隔离不阻断。
"""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from services.workorder.steps import edc_corroboration, reconcile

# 真料形状(SM 5月 vertex OCR 探针原值,classify._edc_fields 快照后的事件 payload)。
_EDC_A = {
    "settle_date": "2026-05-25",
    "gross_amount": "540.00",
    "fee_amount": None,
    "net_amount": None,
    "batch_no": "000186",
    "terminal_id": "62608078",
}
_EDC_B = {
    "settle_date": "2026-05-10",
    "gross_amount": "39375.00",
    "fee_amount": None,
    "net_amount": None,
    "batch_no": "",
    "terminal_id": "",
}


def _classified_evt(item_id, *, kind="edc_settlement", edc=None, extra=None):
    payload = {"item_id": item_id, "kind": kind, "status": "ok"}
    if edc is not None:
        payload["edc"] = edc
    payload.update(extra or {})
    return {"id": 1, "event_type": "item_classified", "step": "classify", "payload": payload}


def _sales_read_evt(item_id="s1"):
    return {
        "id": 2,
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": "sales_summary",
            "status": "ok",
            "sales_read": {
                "headers": ["วันที่", "ยอดขาย", "ภาษีขาย"],
                "rows": [{"cells": ["05/2569", "858780.16", "60114.61"], "is_summary": False}],
            },
        },
    }


class PayloadsFromEventsTests(unittest.TestCase):
    def test_filters_kind_and_snapshot_and_sorts_by_item_id(self):
        events = [
            _classified_evt("i9", edc=_EDC_B),
            _classified_evt("i1", edc=_EDC_A),
            _classified_evt("p1", kind="purchase_invoice", extra={"money": {"vat": "7.00"}}),
            _classified_evt("i5"),  # EDC 件但无快照(手造事件)→ 不硬造空行
        ]
        out = edc_corroboration.payloads_from_events(events)
        self.assertEqual([p["ref"] for p in out], ["i1", "i9"])
        self.assertEqual(out[0]["gross_amount"], "540.00")

    def test_no_edc_items_yields_empty(self):
        self.assertEqual(edc_corroboration.payloads_from_events([_sales_read_evt()]), [])


class CliByteIdenticalTests(unittest.TestCase):
    """命门:适配器路与 CLI 直跑同料,聚合报告逐字节一致(SA-1 是唯一算法)。"""

    def test_adapter_report_equals_cli_report(self):
        from services.sales_agg import cli

        events = [_classified_evt("i1", edc=_EDC_A), _classified_evt("i2", edc=_EDC_B)]
        payloads = edc_corroboration.payloads_from_events(events)
        adapter_report = edc_corroboration.aggregate_report(payloads)

        with tempfile.TemporaryDirectory() as td:
            in_path = Path(td) / "in.json"
            out_path = Path(td) / "out.json"
            in_path.write_text(
                json.dumps({"edc_settlement": payloads}, ensure_ascii=False), encoding="utf-8"
            )
            with redirect_stdout(io.StringIO()):
                code = cli.main([str(in_path), str(out_path)])
            self.assertIn(code, (0, 2))
            cli_report = json.loads(out_path.read_text(encoding="utf-8"))

        # 适配器报告过一次 JSON 序列化对齐类型(CLI 落盘也是 JSON),再逐字节比对。
        self.assertEqual(
            json.dumps(adapter_report, ensure_ascii=False, sort_keys=True),
            json.dumps(cli_report, ensure_ascii=False, sort_keys=True),
        )


class BuildCorroborationTests(unittest.TestCase):
    def _report(self):
        return edc_corroboration.aggregate_report([dict(_EDC_A, ref="i1"), dict(_EDC_B, ref="i2")])

    def test_amber_with_authoritative_and_coverage_facts(self):
        out = edc_corroboration.build_corroboration(
            self._report(), authoritative_net="858780.16", authoritative_vat="60114.61"
        )
        self.assertEqual(out["source"], "edc_aggregate")
        self.assertEqual(out["invoice_count"], 2)
        self.assertEqual(out["deduped_count"], 2)
        self.assertEqual(out["gross_total"], "39915.00")
        # 毛额 39915 → 销售额 37303.74 + 税 2611.26(7/107 先加总再拆)。
        self.assertEqual(out["net_total"], "37303.74")
        self.assertEqual(out["vat_total"], "2611.26")
        self.assertEqual(out["covered_state"], "amber")
        self.assertEqual(out["authoritative_net"], "858780.16")
        self.assertEqual(out["date_from"], "2026-05-10")
        self.assertEqual(out["date_to"], "2026-05-25")
        self.assertEqual(len(out["daily"]), 2)
        # 银行渠道刻意不混入,SA-1 如实记 note(覆盖事实不装完整)。
        self.assertTrue(any("bank_channel_absent" in n for n in out["notes"]))

    def test_needs_without_authoritative_does_not_invent_gap(self):
        out = edc_corroboration.build_corroboration(self._report())
        self.assertEqual(out["covered_state"], "needs")
        self.assertIsNone(out["gap_net"])
        self.assertIsNone(out["coverage"])


class DetailReadSideTests(unittest.TestCase):
    def test_live_compute_when_reconcile_not_reached(self):
        events = [_classified_evt("i1", edc=_EDC_A), _sales_read_evt()]
        out = edc_corroboration.corroboration_for_detail(events)
        self.assertEqual(out["source"], "edc_aggregate")
        self.assertEqual(out["covered_state"], "amber")
        self.assertNotIn("stale", out)

    def test_frozen_wins_and_stale_marked_on_divergence(self):
        events = [_classified_evt("i1", edc=_EDC_A), _sales_read_evt()]
        live = edc_corroboration.corroboration_from_events(events)
        frozen_same = {
            "id": 9,
            "event_type": "step_done",
            "step": "reconcile",
            "payload": {"gates": {"r2_edc_corroboration": dict(live)}},
        }
        out = edc_corroboration.corroboration_for_detail(events + [frozen_same])
        self.assertNotIn("stale", out)

        diverged = dict(live, net_total="1.00")
        frozen_old = {
            "id": 9,
            "event_type": "step_done",
            "step": "reconcile",
            "payload": {"gates": {"r2_edc_corroboration": diverged}},
        }
        out2 = edc_corroboration.corroboration_for_detail(events + [frozen_old])
        self.assertTrue(out2["stale"])
        self.assertEqual(out2["net_total"], "1.00")  # 以冻结值为准,不静默糊成现算

    def test_none_when_no_edc_items(self):
        self.assertIsNone(edc_corroboration.corroboration_for_detail([_sales_read_evt()]))


class ReconcileGateHookTests(unittest.TestCase):
    def test_no_edc_events_returns_none_gate_key_absent(self):
        r2 = {"sales_amount": "858780.16", "output_vat": "60114.61"}
        self.assertIsNone(reconcile._run_edc_aggregate([_sales_read_evt()], r2))

    def test_gate_payload_present_with_edc_events(self):
        r2 = {"sales_amount": "858780.16", "output_vat": "60114.61"}
        out = reconcile._run_edc_aggregate([_classified_evt("i1", edc=_EDC_A)], r2)
        self.assertEqual(out["source"], "edc_aggregate")
        self.assertEqual(out["covered_state"], "amber")

    def test_exception_isolated_into_note_never_raises(self):
        prev = edc_corroboration.aggregate_report
        edc_corroboration.aggregate_report = lambda payloads: (_ for _ in ()).throw(
            RuntimeError("boom")
        )
        self.addCleanup(setattr, edc_corroboration, "aggregate_report", prev)
        r2 = {"sales_amount": "1", "output_vat": "0.07"}
        out = reconcile._run_edc_aggregate([_classified_evt("i1", edc=_EDC_A)], r2)
        self.assertEqual(out, {"error": "RuntimeError", "note": "edc_aggregate_skipped"})


if __name__ == "__main__":
    unittest.main()
