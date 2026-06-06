# -*- coding: utf-8 -*-
"""销项 PO-4 · 开票核心守门测试(金额计算 + 连号 + 状态写保护 · 不连库)。"""

import unittest
from datetime import date
from decimal import Decimal

from services.sales import document as doc
from services.sales import numbering


class ComputeTotalsTests(unittest.TestCase):
    def test_vat_7_percent(self):
        t = doc.compute_totals([{"qty": 2, "unit_price": "50", "discount": 0}], vat_rate=7)
        self.assertEqual(t["subtotal"], Decimal("100.00"))
        self.assertEqual(t["vat_amount"], Decimal("7.00"))
        self.assertEqual(t["grand_total"], Decimal("107.00"))

    def test_non_vat_line_excluded_from_tax(self):
        lines = [
            {"qty": 1, "unit_price": "100", "vat_applicable": True},
            {"qty": 1, "unit_price": "100", "vat_applicable": False},
        ]
        t = doc.compute_totals(lines, vat_rate=7)
        self.assertEqual(t["subtotal"], Decimal("200.00"))
        self.assertEqual(t["vat_amount"], Decimal("7.00"))  # 只对应税的 100 收税
        self.assertEqual(t["grand_total"], Decimal("207.00"))

    def test_seller_not_vat_registered_zero_tax(self):
        t = doc.compute_totals([{"qty": 1, "unit_price": "100"}], vat_rate=0)
        self.assertEqual(t["vat_amount"], Decimal("0.00"))
        self.assertEqual(t["grand_total"], Decimal("100.00"))

    def test_line_discount_and_wht(self):
        t = doc.compute_totals(
            [{"qty": 1, "unit_price": "1000", "discount": "100"}], vat_rate=7, wht_rate=3
        )
        self.assertEqual(t["subtotal"], Decimal("900.00"))
        self.assertEqual(t["discount_total"], Decimal("100.00"))
        self.assertEqual(t["vat_amount"], Decimal("63.00"))  # 900*7%
        self.assertEqual(t["wht_amount"], Decimal("27.00"))  # 900*3%(按不含税额)
        self.assertEqual(t["grand_total"], Decimal("936.00"))  # 900+63-27

    def test_line_no_assigned_sequentially(self):
        t = doc.compute_totals([{"unit_price": "1"}, {"unit_price": "2"}], vat_rate=7)
        self.assertEqual([ln["line_no"] for ln in t["lines"]], [1, 2])


class DiscountTests(unittest.TestCase):
    def test_line_percentage_discount(self):
        t = doc.compute_totals([{"qty": 2, "unit_price": "100", "discount_pct": "10"}], vat_rate=7)
        self.assertEqual(t["lines"][0]["discount"], Decimal("20.00"))  # 200 * 10%
        self.assertEqual(t["lines"][0]["discount_pct"], Decimal("10"))
        self.assertEqual(t["subtotal"], Decimal("180.00"))
        self.assertEqual(t["vat_amount"], Decimal("12.60"))  # 180 * 7%
        self.assertEqual(t["grand_total"], Decimal("192.60"))

    def test_line_total_never_negative(self):
        """折扣大于行金额时夹到 0,净额不为负(§D5)。"""
        t = doc.compute_totals([{"qty": 1, "unit_price": "50", "discount": "80"}], vat_rate=7)
        self.assertEqual(t["lines"][0]["discount"], Decimal("50.00"))
        self.assertEqual(t["lines"][0]["line_total"], Decimal("0.00"))
        self.assertEqual(t["grand_total"], Decimal("0.00"))

    def test_header_discount_amount(self):
        t = doc.compute_totals(
            [{"qty": 1, "unit_price": "1000"}], vat_rate=7, header_discount_amount="100"
        )
        self.assertEqual(t["header_discount_amount"], Decimal("100.00"))
        self.assertEqual(t["subtotal"], Decimal("1000.00"))  # 行净额合计(折前)
        self.assertEqual(t["vat_amount"], Decimal("63.00"))  # (1000-100) * 7%
        self.assertEqual(t["grand_total"], Decimal("963.00"))  # 900 + 63

    def test_header_discount_prorated_to_taxable_base(self):
        """整单折扣按比例摊到应税净额,VAT 只落应税那份的折后(§D2)。"""
        lines = [
            {"qty": 1, "unit_price": "100", "vat_applicable": True},
            {"qty": 1, "unit_price": "100", "vat_applicable": False},
        ]
        t = doc.compute_totals(lines, vat_rate=7, header_discount_pct="10")
        self.assertEqual(t["header_discount_amount"], Decimal("20.00"))  # 200 * 10%
        self.assertEqual(t["vat_amount"], Decimal("6.30"))  # (100 - 10) * 7%
        self.assertEqual(t["grand_total"], Decimal("186.30"))  # 180 + 6.30

    def test_no_discount_keeps_pct_none(self):
        t = doc.compute_totals([{"qty": 1, "unit_price": "100"}], vat_rate=7)
        self.assertIsNone(t["lines"][0]["discount_pct"])
        self.assertIsNone(t["header_discount_pct"])


class PriceIncludesVatTests(unittest.TestCase):
    """§C 价内含税:VAT 从含税额反算单列,grand 不变;默认价外保持原行为。"""

    def test_default_is_exclusive(self):
        t = doc.compute_totals([{"qty": 1, "unit_price": "100"}], vat_rate=7)
        self.assertFalse(t["price_includes_vat"])
        self.assertEqual(t["vat_amount"], Decimal("7.00"))
        self.assertEqual(t["grand_total"], Decimal("107.00"))

    def test_inclusive_extracts_vat(self):
        t = doc.compute_totals(
            [{"qty": 1, "unit_price": "107"}], vat_rate=7, price_includes_vat=True
        )
        self.assertTrue(t["price_includes_vat"])
        self.assertEqual(t["subtotal"], Decimal("107.00"))  # 含税额(录入价)
        self.assertEqual(t["vat_amount"], Decimal("7.00"))  # 107 * 7/107
        self.assertEqual(t["subtotal"] - t["vat_amount"], Decimal("100.00"))  # 不含税净额
        self.assertEqual(t["grand_total"], Decimal("107.00"))  # 含税总额不变

    def test_inclusive_with_line_discount(self):
        t = doc.compute_totals(
            [{"qty": 1, "unit_price": "107", "discount_pct": "10"}],
            vat_rate=7,
            price_includes_vat=True,
        )
        self.assertEqual(t["subtotal"], Decimal("96.30"))  # 107 - 10.70
        self.assertEqual(t["vat_amount"], Decimal("6.30"))  # 96.30 * 7/107
        self.assertEqual(t["grand_total"], Decimal("96.30"))

    def test_inclusive_with_wht(self):
        t = doc.compute_totals(
            [{"qty": 1, "unit_price": "107"}], vat_rate=7, wht_rate=3, price_includes_vat=True
        )
        self.assertEqual(t["vat_amount"], Decimal("7.00"))
        self.assertEqual(t["wht_amount"], Decimal("3.00"))  # 100(净) * 3%
        self.assertEqual(t["grand_total"], Decimal("104.00"))  # 107 - 3 WHT


class SeqCursor:
    """模拟 document_number_sequences 的取号事务,验证连号不跳。"""

    def __init__(self):
        self.store = {}
        self._last = None
        self.saw_for_update = False

    def execute(self, sql, params=None):
        if sql.startswith("INSERT INTO document_number_sequences"):
            self.store.setdefault(tuple(params[:4]), 1)
            self._last = None
        elif sql.startswith("SELECT next_number"):
            if "FOR UPDATE" in sql:
                self.saw_for_update = True
            self._last = {"next_number": self.store.get(tuple(params), 1)}
        elif sql.startswith("UPDATE document_number_sequences"):
            key = tuple(params)
            self.store[key] = self.store.get(key, 1) + 1
            self._last = None

    def fetchone(self):
        return self._last


class NumberingTests(unittest.TestCase):
    def test_gapless_sequential(self):
        cur = SeqCursor()
        got = [
            numbering.allocate(
                cur,
                tenant_id="t",
                doc_type="tax_invoice",
                prefix="INV",
                reset="yearly",
                on=date(2026, 6, 6),
            )
            for _ in range(3)
        ]
        self.assertEqual([n for _, n in got], [1, 2, 3])
        self.assertEqual([s for s, _ in got], ["INV2026-00001", "INV2026-00002", "INV2026-00003"])
        self.assertTrue(cur.saw_for_update, "取号必须走 SELECT ... FOR UPDATE 锁行")

    def test_reset_modes_format(self):
        d = date(2026, 6, 6)
        self.assertEqual(numbering.format_number("INV", "yearly", d, 5), "INV2026-00005")
        self.assertEqual(numbering.format_number("INV", "monthly", d, 5), "INV202606-00005")
        self.assertEqual(numbering.format_number("INV", "never", d, 5), "INV-00005")

    def test_period_key_buckets(self):
        d = date(2026, 6, 6)
        self.assertEqual(numbering.period_key("yearly", d), "2026")
        self.assertEqual(numbering.period_key("monthly", d), "2026-06")
        self.assertEqual(numbering.period_key("never", d), "ALL")


class StatusCursor:
    def __init__(self, status):
        self.status = status
        self._sql = ""

    def execute(self, sql, params=None):
        self._sql = sql

    def fetchone(self):
        if "SELECT status" in self._sql:
            if self.status is None:
                return None
            return {"status": self.status, "doc_type": "tax_invoice"}
        return None


class StateGuardTests(unittest.TestCase):
    def test_update_issued_is_rejected(self):
        err = doc.update_draft(
            StatusCursor("issued"), tenant_id="t", doc_id="d", vat_rate=7, wht_rate=0, lines=[]
        )
        self.assertEqual(err, "not_draft")

    def test_update_missing_is_not_found(self):
        err = doc.update_draft(
            StatusCursor(None), tenant_id="t", doc_id="d", vat_rate=7, wht_rate=0, lines=[]
        )
        self.assertEqual(err, "not_found")

    def test_update_rejected_returns_to_draft(self):
        """被驳回的单可继续改(§F:rejected→改→draft)。"""
        err = doc.update_draft(
            StatusCursor("rejected"), tenant_id="t", doc_id="d", vat_rate=7, wht_rate=0, lines=[]
        )
        self.assertIsNone(err)

    def test_issue_draft_blocked_when_approval_required(self):
        _, err = doc.issue_document(
            StatusCursor("draft"),
            tenant_id="t",
            doc_id="d",
            prefix="INV",
            reset="yearly",
            on=date(2026, 6, 6),
            approval_mode="single",
        )
        self.assertEqual(err, "approval_required")

    def test_issue_non_draft_rejected(self):
        _, err = doc.issue_document(
            StatusCursor("issued"),
            tenant_id="t",
            doc_id="d",
            prefix="INV",
            reset="yearly",
            on=date(2026, 6, 6),
        )
        self.assertEqual(err, "not_draft")

    def test_void_already_void_rejected(self):
        err = doc.void_document(StatusCursor("void"), tenant_id="t", doc_id="d")
        self.assertEqual(err, "already_void")


class CaptureCursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


_ARCH_DOC = {
    "doc_type": "tax_invoice",
    "doc_number": "INV2026-00001",
    "issue_date": "2026-06-06",
    "currency": "THB",
    "subtotal": "100.00",
    "vat_rate": "7.00",
    "vat_amount": "7.00",
    "wht_amount": "0.00",
    "grand_total": "107.00",
    "lines": [{"line_no": 1, "description": "x", "qty": "1", "unit_price": "100", "line_total": "100.00"}],
}


class ArchivalHashTests(unittest.TestCase):
    """§E3 留底:开票时存确定性 PDF 哈希(审计增强,失败不阻断)。"""

    def test_stores_sha256_and_sets_doc_field(self):
        cur = CaptureCursor()
        d = dict(_ARCH_DOC)
        doc._store_archival_hash(cur, "t", "d", d, {"seller": {"name": "A"}, "buyer": {"name": "B"}})
        self.assertEqual(len(d["pdf_sha256"]), 64)
        self.assertTrue(any("pdf_sha256=%s" in sql for sql, _ in cur.calls))

    def test_render_failure_does_not_raise(self):
        cur = CaptureCursor()
        # lines 缺字段会让渲染抛错 -> 兜底吞掉,不写哈希、不抛(assertLogs 收掉那条 ERROR)。
        with self.assertLogs("mr-pilot", level="ERROR"):
            doc._store_archival_hash(cur, "t", "d", {"lines": [object()]}, {})
        self.assertEqual(cur.calls, [])


if __name__ == "__main__":
    unittest.main()
