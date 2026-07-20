# -*- coding: utf-8 -*-
"""断链页换眼重读(GC-D-2)单测:页级断链定位纯函数 + 换眼重读编排 + escalations 留痕接线。

模型/渲染全 mock(注入 bank_stmt_reread._render_pages / _read_page_rows),绝不触真 fitz / 真付费。
"""

import datetime
import os
import tempfile
import unittest
from unittest import mock

from services.recon import bank_stmt_reread
from services.recon.bank_recon_types import StatementRow
from services.recon.bank_stmt_balance import _verify_row_balances
from services.workorder.engine import StepContext
from services.workorder.steps import reconcile_bank

_D = datetime.date(2026, 6, 1)


def _row(deposit=0.0, withdrawal=0.0, balance=0.0, desc="tx"):
    return StatementRow(_D, desc, withdrawal, deposit, balance)


class FindBreakPagesTests(unittest.TestCase):
    """页级断链定位:无断链 / 页内断 / 页边界断 / 多处断,各返回正确候选页集(0-based)。"""

    def test_no_break_returns_empty(self):
        page0 = [_row(deposit=100.0, balance=1100.0), _row(deposit=50.0, balance=1150.0)]
        self.assertEqual(bank_stmt_reread.find_break_pages([page0], 1000.0), [])

    def test_intra_page_break_marks_only_that_page(self):
        page0 = [_row(deposit=100.0, balance=1100.0)]
        page1 = [
            _row(deposit=100.0, balance=1200.0),  # 1100+100=1200 ✓
            _row(deposit=50.0, balance=9999.0),  # 1200+50≠9999 ✗ 页内断
        ]
        self.assertEqual(bank_stmt_reread.find_break_pages([page0, page1], 1000.0), [1])

    def test_page_boundary_break_marks_both_sides(self):
        page0 = [_row(deposit=100.0, balance=1100.0)]
        page1 = [_row(deposit=50.0, balance=2000.0)]  # 1100+50≠2000 ✗ 跨页交接断
        self.assertEqual(bank_stmt_reread.find_break_pages([page0, page1], 1000.0), [0, 1])

    def test_multiple_intra_page_breaks(self):
        page0 = [_row(deposit=100.0, balance=1100.0), _row(deposit=100.0, balance=1200.0)]
        page1 = [
            _row(deposit=100.0, balance=1300.0),  # 1200+100=1300 ✓ 交接不断
            _row(deposit=100.0, balance=9999.0),  # ✗ 页内断
        ]
        page2 = [
            _row(deposit=100.0, balance=10099.0),  # 9999+100=10099 ✓ 交接不断
            _row(deposit=100.0, balance=88888.0),  # ✗ 页内断
        ]
        self.assertEqual(bank_stmt_reread.find_break_pages([page0, page1, page2], 1000.0), [1, 2])


class MaybeRereadTests(unittest.TestCase):
    """换眼重读编排:更好→采纳+留痕;更差→保原读;异常→保原读不炸;无断链/非PDF/闸关→零重读。"""

    def setUp(self):
        self._prev_render = bank_stmt_reread._render_pages
        self._prev_read = bank_stmt_reread._read_page_rows
        self.addCleanup(setattr, bank_stmt_reread, "_render_pages", self._prev_render)
        self.addCleanup(setattr, bank_stmt_reread, "_read_page_rows", self._prev_read)

    def _original_with_one_break(self):
        rows = [_row(deposit=100.0, balance=1100.0), _row(deposit=50.0, balance=2000.0)]
        _verify_row_balances(rows, 1000.0)  # 第 2 行 balance_ok=False → breaks_before=1
        return rows

    def _clean_pages(self, _bytes):
        return [b"pg1", b"pg2"]

    def test_better_reread_is_adopted_and_recorded(self):
        original = self._original_with_one_break()
        bank_stmt_reread._render_pages = self._clean_pages

        def _read(_img, page_number, filename, _key):
            if page_number == 1:
                return [_row(deposit=100.0, balance=1100.0)]
            return [_row(deposit=50.0, balance=1150.0)]  # 干净链:0 断

        bank_stmt_reread._read_page_rows = _read
        rows, esc = bank_stmt_reread.maybe_reread_chain_breaks(
            original, 1000.0, file_bytes=b"%PDF", filename="b.pdf", ext="pdf"
        )
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r.balance_ok is not False for r in rows))
        self.assertEqual(len(esc), 1)
        self.assertEqual(esc[0]["kept"], True)
        self.assertEqual(esc[0]["breaks_before"], 1)
        self.assertEqual(esc[0]["breaks_after"], 0)
        self.assertEqual(esc[0]["eye_from"], "vision")
        self.assertEqual(esc[0]["eye_to"], "direct")
        self.assertEqual(esc[0]["pages"], [1, 2])

    def test_worse_reread_keeps_original(self):
        original = self._original_with_one_break()
        bank_stmt_reread._render_pages = self._clean_pages

        def _read(_img, page_number, filename, _key):
            if page_number == 1:
                return [_row(deposit=100.0, balance=9999.0)]  # ✗ 对不上期初
            return [_row(deposit=50.0, balance=8888.0)]  # ✗ 又一断 → 2 断 > 1

        bank_stmt_reread._read_page_rows = _read
        rows, esc = bank_stmt_reread.maybe_reread_chain_breaks(
            original, 1000.0, file_bytes=b"%PDF", filename="b.pdf", ext="pdf"
        )
        self.assertIs(rows, original)  # 保原读(同一对象)
        self.assertEqual(esc[0]["kept"], False)
        self.assertEqual(esc[0]["breaks_before"], 1)
        self.assertEqual(esc[0]["breaks_after"], 2)

    def test_page_read_exception_keeps_original_no_crash(self):
        original = self._original_with_one_break()
        bank_stmt_reread._render_pages = self._clean_pages

        def _boom(_img, page_number, filename, _key):
            if page_number == 2:
                raise RuntimeError("model blew up")
            return [_row(deposit=100.0, balance=1100.0)]

        bank_stmt_reread._read_page_rows = _boom
        rows, esc = bank_stmt_reread.maybe_reread_chain_breaks(
            original, 1000.0, file_bytes=b"%PDF", filename="b.pdf", ext="pdf"
        )
        self.assertIs(rows, original)
        self.assertEqual(esc, [])  # 重读崩 → 保原读、无留痕

    def test_render_exception_keeps_original(self):
        original = self._original_with_one_break()

        def _render_boom(_bytes):
            raise RuntimeError("fitz missing")

        bank_stmt_reread._render_pages = _render_boom
        rows, esc = bank_stmt_reread.maybe_reread_chain_breaks(
            original, 1000.0, file_bytes=b"%PDF", filename="b.pdf", ext="pdf"
        )
        self.assertIs(rows, original)
        self.assertEqual(esc, [])

    def test_no_break_does_not_render(self):
        clean = [_row(deposit=100.0, balance=1100.0), _row(deposit=50.0, balance=1150.0)]
        _verify_row_balances(clean, 1000.0)  # breaks_before=0

        def _must_not_render(_bytes):
            raise AssertionError("render must not run when there is no chain break")

        bank_stmt_reread._render_pages = _must_not_render
        rows, esc = bank_stmt_reread.maybe_reread_chain_breaks(
            clean, 1000.0, file_bytes=b"%PDF", filename="b.pdf", ext="pdf"
        )
        self.assertIs(rows, clean)
        self.assertEqual(esc, [])

    def test_non_pdf_is_noop(self):
        original = self._original_with_one_break()

        def _must_not_render(_bytes):
            raise AssertionError("render must not run for non-pdf")

        bank_stmt_reread._render_pages = _must_not_render
        rows, esc = bank_stmt_reread.maybe_reread_chain_breaks(
            original, 1000.0, file_bytes=b"img", filename="b.jpg", ext="jpg"
        )
        self.assertIs(rows, original)
        self.assertEqual(esc, [])

    def test_kill_switch_disables_reread(self):
        original = self._original_with_one_break()

        def _must_not_render(_bytes):
            raise AssertionError("render must not run when kill switch off")

        bank_stmt_reread._render_pages = _must_not_render
        with mock.patch.dict(os.environ, {"OCR_BANK_CHAIN_REREAD": "0"}):
            rows, esc = bank_stmt_reread.maybe_reread_chain_breaks(
                original, 1000.0, file_bytes=b"%PDF", filename="b.pdf", ext="pdf"
            )
        self.assertIs(rows, original)
        self.assertEqual(esc, [])


class _CaptureStore:
    def __init__(self):
        self.events = []

    def append_event(self, cur, *, tenant_id, work_order_id, step, event_type, payload, **kw):
        self.events.append({"event_type": event_type, "payload": payload})
        return {"id": len(self.events)}


class EscalationThreadingTests(unittest.TestCase):
    """留痕接线:_split_parsed 向后兼容 + item_bank_parsed payload 有/无升档形状。"""

    def test_split_parsed_tuple_and_legacy_list(self):
        rows = [_row(deposit=1.0, balance=1.0)]
        esc = [{"kept": True}]
        self.assertEqual(reconcile_bank._split_parsed((rows, esc)), (rows, esc))
        self.assertEqual(reconcile_bank._split_parsed(rows), (rows, []))  # 历史裸列表
        self.assertEqual(reconcile_bank._split_parsed([]), ([], []))

    def test_emit_includes_escalations_only_when_present(self):
        store = _CaptureStore()
        ctx = StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data={})
        rows = [_row(deposit=100.0, balance=1100.0)]

        reconcile_bank._emit_bank_parsed(ctx, {"id": "b1"}, rows, 0, [{"kept": True}])
        reconcile_bank._emit_bank_parsed(ctx, {"id": "b2"}, rows, 0, [])
        reconcile_bank._emit_bank_parsed(ctx, {"id": "b3"}, rows, 0)  # 缺参 = 无升档

        p1, p2, p3 = (e["payload"] for e in store.events)
        self.assertEqual(p1["escalations"], [{"kept": True}])
        self.assertNotIn("escalations", p2)  # 空 → 不加字段(老形状)
        self.assertNotIn("escalations", p3)
        self.assertEqual(set(p3.keys()), {"item_id", "rows"})  # 逐字节维持老 payload 形状

    def test_default_parse_bank_file_surfaces_escalations(self):
        from services.recon import bank_recon_v2

        rows = [_row(deposit=100.0, balance=1100.0)]
        esc = [{"pages": [1, 2], "kept": True}]
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            tf.write(b"%PDF-1.4")
            path = tf.name
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        item = {"id": "b9", "kind": "bank_statement", "status": "ok", "file_ref": path}
        ctx = StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=None, data={})

        with mock.patch.object(
            bank_recon_v2,
            "_parse_bank_statement_impl",
            return_value={"ok": True, "rows": rows, "escalations": esc},
        ):
            out = reconcile_bank._default_parse_bank_file(ctx, item)
        self.assertEqual(out, (rows, esc))


if __name__ == "__main__":
    unittest.main()
