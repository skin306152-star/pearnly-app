# -*- coding: utf-8 -*-
"""GL 上传件接入工单全链测试(T4a:sort 定堆 → classify 不碰 → reconcile F2 对平)。

覆盖:① sort 按文件名/表头把 GL 台账定堆 gl_ledger(泰文报表名/ASCII GL 词边界,GL 判据
先于银行判据);② classify 对 gl_ledger 件零动作——不 OCR、不被 non_tax/ambiguous 兜底吞;
③ 真文件全链:合成 GL xlsx 走默认 _shadow_gl_rows 解析,桥全 → reconcile_gl 逐科目对平
gl_source=ok;损坏件 → parse_failed + note 逐件点名;④ 守恒:gl_ledger 归佐证桶(bank),
Σ桶=N 不破;⑤ kind 词汇表 kinds.py 与各消费端同源(收口防散字面量回潮)。
"""

import io
import tempfile
import unittest
from pathlib import Path

from services.workorder import evidence, kinds
from services.workorder.engine import StepContext
from services.workorder.steps import classify, conservation, reconcile
from services.workorder.steps import sort as sort_step


class FakeStore:
    def __init__(self, items, events=None):
        self.items = items
        self.events = list(events or [])

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def update_item(self, cur, *, tenant_id, item_id, status=None, kind=None, flag_reason=None):
        it = next(i for i in self.items if i["id"] == item_id)
        for col, val in (("status", status), ("kind", kind), ("flag_reason", flag_reason)):
            if val is not None:
                it[col] = val

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)

    def append_event(self, cur, **kw):
        self.events.append(kw)


def _item(item_id, file_ref, *, kind="unknown", status="pending"):
    return {
        "id": item_id,
        "file_ref": file_ref,
        "kind": kind,
        "status": status,
        "flag_reason": None,
    }


def _money_evt(item_id, net, vat, grand):
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": "purchase_invoice",
            "status": "ok",
            "money": {"subtotal": net, "vat": vat, "total_amount": grand, "invoice_number": "IV"},
        },
    }


def _sales_evt():
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": "s1",
            "kind": "sales_summary",
            "status": "ok",
            "sales_read": {
                "headers": ["วันที่", "ยอดขาย", "ภาษีขาย"],
                "rows": [{"cells": ["01/05/2569", "5000.00", "350.00"], "is_summary": False}],
            },
        },
    }


def _ctx(store):
    return StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data={})


# 覆盖影子 7 科目发生额的 GL 行(与 p1 进项 1000/70/1070 + 销项 5000/350 的影子完全对平)。
_GL_SHEET_ROWS = (
    ("113000", 5350, None),
    ("114000", 70, None),
    ("114000", None, 70),
    ("201000", None, 1070),
    ("203000", 350, None),
    ("203000", None, 350),
    ("204000", None, 280),
    ("401000", None, 5000),
    ("529000", 1000, None),
)
_FULL_BRIDGE = {
    "1130": "113000",
    "1140": "114000",
    "2010": "201000",
    "2030": "203000",
    "2040": "204000",
    "4010": "401000",
    "5290": "529000",
}


def _write_gl_xlsx(path):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["วันที่", "ใบสำคัญ", "คำอธิบาย", "รหัสบัญชี", "เดบิต", "เครดิต"])
    for acct, debit, credit in _GL_SHEET_ROWS:
        ws.append(["01/05/2026", "JV1", "รายการ", acct, debit, credit])
    buf = io.BytesIO()
    wb.save(buf)
    Path(path).write_bytes(buf.getvalue())


class SortBinsGlLedgerTests(unittest.TestCase):
    def _bin(self, name):
        return sort_step._bin_by_file(name)

    def test_thai_report_name_pdf(self):
        out = self._bin("/in/รายงานสมุดแยกประเภท เดือน 05.pdf")
        self.assertEqual(out, (kinds.GL_LEDGER, "pending", None))

    def test_ascii_gl_word_boundary(self):
        self.assertEqual(self._bin("/in/GL_may.xlsx")[0], kinds.GL_LEDGER)
        # GLOBAL 之类误粘不算 GL 词。
        self.assertEqual(self._bin("/in/global_sales.xlsx")[0], kinds.SALES_SUMMARY)

    def test_gl_beats_bank_filename(self):
        # 银行科目的 GL(文件名带行名)仍是 GL 佐证件,不是流水。
        out = self._bin("/in/สมุดแยกประเภท KBANK.pdf")
        self.assertEqual(out[0], kinds.GL_LEDGER)

    def test_xlsx_header_report_name(self):
        with tempfile.TemporaryDirectory() as td:
            import openpyxl

            path = Path(td) / "export_may.xlsx"
            wb = openpyxl.Workbook()
            wb.active.append(["รายงานสมุดแยกประเภท"])
            wb.active.append(["วันที่", "เดบิต", "เครดิต"])
            buf = io.BytesIO()
            wb.save(buf)
            path.write_bytes(buf.getvalue())
            self.assertEqual(self._bin(str(path))[0], kinds.GL_LEDGER)


class ClassifyLeavesGlLedgerAloneTests(unittest.TestCase):
    def setUp(self):
        def _no_ocr(path):
            raise AssertionError("gl_ledger 件绝不许进 OCR")

        for name, fake in (
            ("_ocr_image", _no_ocr),
            ("_resolve_own_tax_id", lambda ctx: "0105567178203"),
            ("_resolve_own_name", lambda ctx: None),
            ("_m1_enabled", lambda ctx: False),
        ):
            prev = getattr(classify, name)
            setattr(classify, name, fake)
            self.addCleanup(setattr, classify, name, prev)

    def test_not_ocred_not_swallowed(self):
        store = FakeStore([_item("g1", "/in/GL_may.xlsx", kind=kinds.GL_LEDGER)])
        out = classify.run(_ctx(store))
        self.assertEqual(out.status, "ok")
        g1 = store.items[0]
        # 不被 non_tax/ambiguous 兜底吞:kind 原样、无 flag、留 pending 供 reconcile 佐证消费。
        self.assertEqual(g1["kind"], kinds.GL_LEDGER)
        self.assertEqual(g1["status"], "pending")
        self.assertIsNone(g1["flag_reason"])


class GlFullChainTests(unittest.TestCase):
    """真文件全链:sort 定堆 → classify 零动作 → reconcile 默认注入点解析 → F2 对平。"""

    def setUp(self):
        self._prev_gate = reconcile._shadow_draft_enabled
        reconcile._shadow_draft_enabled = lambda ctx: True
        self.addCleanup(setattr, reconcile, "_shadow_draft_enabled", self._prev_gate)
        self._prev_bridge = reconcile._shadow_account_bridge
        self.addCleanup(setattr, reconcile, "_shadow_account_bridge", self._prev_bridge)

        def _no_ocr(path):
            raise AssertionError("gl_ledger 件绝不许进 OCR")

        for name, fake in (
            ("_ocr_image", _no_ocr),
            ("_resolve_own_tax_id", lambda ctx: "0105567178203"),
            ("_resolve_own_name", lambda ctx: None),
            ("_m1_enabled", lambda ctx: False),
        ):
            prev = getattr(classify, name)
            setattr(classify, name, fake)
            self.addCleanup(setattr, classify, name, prev)

    def _run_chain(self, gl_file, bridge):
        reconcile._shadow_account_bridge = lambda ctx: bridge
        items = [
            _item("p1", "/in/a.jpg", kind=kinds.PURCHASE_INVOICE, status="ok"),
            _item("s1", "/in/pos.xlsx", kind=kinds.SALES_SUMMARY, status="ok"),
            _item("g1", gl_file),
        ]
        store = FakeStore(items, [_money_evt("p1", "1000.00", "70.00", "1070.00"), _sales_evt()])
        ctx = _ctx(store)
        sort_out = sort_step.run(ctx)
        self.assertEqual(sort_out.payload["bins"], {kinds.GL_LEDGER: 1})
        self.assertEqual(store.items[2]["kind"], kinds.GL_LEDGER)
        classify_out = classify.run(ctx)
        self.assertEqual(classify_out.status, "ok")
        self.assertEqual(store.items[2]["status"], "pending")  # classify 对 GL 件零动作
        out = reconcile.run(ctx)
        self.assertEqual(out.status, "ok")
        return out.payload["gates"]["r5_shadow"]["reconcile_gl"]

    def test_synthetic_gl_reconciles_ok(self):
        with tempfile.TemporaryDirectory() as td:
            gl = Path(td) / "GL_may.xlsx"
            _write_gl_xlsx(gl)
            rg = self._run_chain(str(gl), _FULL_BRIDGE)
        self.assertEqual(rg["gl_source"], reconcile.GL_SOURCE_OK)
        self.assertEqual(rg["status"], "reconciled")
        self.assertFalse(rg["alert"])
        self.assertEqual(len(rg["matched"]), 7)
        self.assertEqual(rg["unmapped"], [])
        self.assertTrue(rg["totals"]["balanced"])

    def test_broken_gl_is_parse_failed_with_note(self):
        with tempfile.TemporaryDirectory() as td:
            broken = Path(td) / "GL_broken.pdf"
            broken.write_bytes(b"not a pdf at all")
            rg = self._run_chain(str(broken), _FULL_BRIDGE)
        self.assertEqual(rg["gl_source"], reconcile.GL_SOURCE_PARSE_FAILED)
        self.assertIn("GL_broken.pdf", rg["gl_source_note"])
        # rows 为空时 reconcile_gl 契约照旧 no_gl_source,但 gl_source 已把两态分开。
        self.assertEqual(rg["status"], "no_gl_source")


class ConservationWithGlTests(unittest.TestCase):
    """守恒专项(验收断言 5):GL 件进工单后七桶 Σ桶=N 仍成立,gl_ledger 归佐证桶。"""

    def test_gl_item_lands_in_evidence_bucket_and_sum_holds(self):
        items = [
            _item("p1", "/in/a.jpg", kind=kinds.PURCHASE_INVOICE, status="ok"),
            _item("s1", "/in/pos.xlsx", kind=kinds.SALES_SUMMARY, status="ok"),
            _item("b1", "/in/stm.pdf", kind=kinds.BANK_STATEMENT),
            _item("g1", "/in/GL_may.xlsx", kind=kinds.GL_LEDGER),
        ]
        cons = conservation.bucket_items(items, {})
        self.assertTrue(cons.conserved(len(items)))
        self.assertEqual(cons.total, len(items))
        bank_ids = [it["id"] for it in cons.buckets[conservation.BANK]]
        self.assertEqual(sorted(bank_ids), ["b1", "g1"])
        self.assertEqual(conservation.stuck_reasons(cons, len(items)), [])


class KindsSingleSourceTests(unittest.TestCase):
    """kind 词汇表收口:全集 8 值唯一,消费端常量与 kinds.py 同源(散字面量回潮在此翻红)。"""

    def test_all_kinds_complete_and_unique(self):
        self.assertEqual(len(kinds.ALL_KINDS), 8)
        self.assertEqual(len(set(kinds.ALL_KINDS)), 8)
        self.assertIn(kinds.GL_LEDGER, kinds.ALL_KINDS)
        self.assertIn(kinds.EDC_SETTLEMENT, kinds.ALL_KINDS)

    def test_consumers_share_the_vocabulary(self):
        self.assertIs(reconcile._PURCHASE, kinds.PURCHASE_INVOICE)
        self.assertIs(reconcile._SALES, kinds.SALES_SUMMARY)
        self.assertIs(reconcile._BANK, kinds.BANK_STATEMENT)
        self.assertIs(conservation._KIND_GL, kinds.GL_LEDGER)
        self.assertIs(conservation._KIND_EDC, kinds.EDC_SETTLEMENT)
        self.assertIs(conservation._KIND_PURCHASE, kinds.PURCHASE_INVOICE)
        self.assertIs(evidence._KIND_SALES, kinds.SALES_SUMMARY)


if __name__ == "__main__":
    unittest.main()
