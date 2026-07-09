# -*- coding: utf-8 -*-
"""sort 步守门测试(services/workorder/steps/sort.py · 任务包 §5 步 2)。

覆盖两半:① 规则可判的当场定堆(xlsx→sales_summary / 文件名·表头像银行→bank_statement /
不支持格式→non_tax 留原因 / 图片留给 classify 过 OCR);② 图片过 OCR 后的归堆纯函数
bin_ocr_fields(税号锚点判方向 · 借 express_push/direction.py 规则不 import 推送模块),
T4 classify 接生产 OCR 后直接调它。xlsx 用 openpyxl 现造,不依赖真语料。
"""

import io
import tempfile
import unittest
from pathlib import Path

from services.workorder.engine import StepContext
from services.workorder.steps import sort as sort_step

OWN_TAX = "0105567178203"
OTHER_TAX = "0735527000289"
OWN_NAME = "บริษัท ซิสเตอร์ ตัวอย่าง จำกัด"


class FakeItemStore:
    """list_items/update_item 的内存替身(sort 只用这两个)。"""

    def __init__(self, items):
        self.items = items

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def update_item(self, cur, *, tenant_id, item_id, status=None, kind=None, flag_reason=None):
        it = next(i for i in self.items if i["id"] == item_id)
        for col, val in (("status", status), ("kind", kind), ("flag_reason", flag_reason)):
            if val is not None:
                it[col] = val

    def by_ref(self, suffix):
        return next(i for i in self.items if i["file_ref"].endswith(suffix))


def _item(n, file_ref):
    return {
        "id": f"item-{n}",
        "file_ref": file_ref,
        "kind": "unknown",
        "status": "pending",
        "flag_reason": None,
    }


def _ctx(store):
    return StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data={})


def _write_xlsx(path, header):
    import openpyxl

    wb = openpyxl.Workbook()
    wb.active.append(header)
    buf = io.BytesIO()
    wb.save(buf)
    Path(path).write_bytes(buf.getvalue())


class SortByFileTests(unittest.TestCase):
    def test_bins_by_extension_and_filename(self):
        with tempfile.TemporaryDirectory() as td:
            pos = Path(td) / "pos_may.xlsx"
            _write_xlsx(pos, ["วันที่", "เลขที่ใบเสร็จ", "ยอดขาย", "VAT"])
            stmt = Path(td) / "STM TTB.xlsx"
            _write_xlsx(stmt, ["date", "detail", "amount"])
            note = Path(td) / "note.txt"
            note.write_text("memo", encoding="utf-8")

            store = FakeItemStore(
                [
                    _item(1, str(pos)),
                    _item(2, str(stmt)),
                    _item(3, str(td + "/IMG_0001.jpg")),
                    _item(4, str(note)),
                ]
            )
            out = sort_step.run(_ctx(store))

        self.assertEqual(out.status, "ok")
        self.assertEqual(store.by_ref("pos_may.xlsx")["kind"], "sales_summary")
        self.assertEqual(store.by_ref("STM TTB.xlsx")["kind"], "bank_statement")

        # 图片留给 classify 过 OCR 再归堆,sort 不动它。
        img = store.by_ref("IMG_0001.jpg")
        self.assertEqual(img["kind"], "unknown")
        self.assertEqual(img["status"], "pending")

        # 无税务要素的格式:non_tax + 排除 + 留原因。
        txt = store.by_ref("note.txt")
        self.assertEqual(txt["kind"], "non_tax")
        self.assertEqual(txt["status"], "excluded")
        self.assertEqual(txt["flag_reason"], "unsupported_format:.txt")

        self.assertEqual(
            out.payload,
            {
                "bins": {"sales_summary": 1, "bank_statement": 1, "non_tax": 1},
                "pending_ocr": 1,
            },
        )

    def test_xlsx_with_bank_header_beats_sales_default(self):
        with tempfile.TemporaryDirectory() as td:
            stmt = Path(td) / "export_may.xlsx"
            _write_xlsx(stmt, ["วันที่", "รายการ", "ถอน", "ฝาก", "ยอดคงเหลือ"])
            store = FakeItemStore([_item(1, str(stmt))])
            sort_step.run(_ctx(store))

        self.assertEqual(store.by_ref("export_may.xlsx")["kind"], "bank_statement")

    def test_pdf_bank_by_filename_else_waits_for_ocr(self):
        store = FakeItemStore([_item(1, "/in/STM KBANK.pdf"), _item(2, "/in/scan_0001.pdf")])
        out = sort_step.run(_ctx(store))

        self.assertEqual(store.by_ref("STM KBANK.pdf")["kind"], "bank_statement")
        self.assertEqual(store.by_ref("scan_0001.pdf")["kind"], "unknown")
        self.assertEqual(out.payload["pending_ocr"], 1)

    def test_already_binned_items_untouched(self):
        done = _item(1, "/in/pos.xlsx")
        done.update(kind="sales_summary", status="ok")
        store = FakeItemStore([done])
        out = sort_step.run(_ctx(store))

        self.assertEqual(out.status, "ok")
        self.assertEqual(store.items[0]["status"], "ok")
        self.assertEqual(out.payload, {"bins": {}, "pending_ocr": 0})


class BinOcrFieldsTests(unittest.TestCase):
    def test_own_tax_as_buyer_is_purchase_invoice(self):
        kind, reason = sort_step.bin_ocr_fields(
            {
                "document_type": "tax_invoice",
                "vat": "28.04",
                "seller_tax": OTHER_TAX,
                "buyer_tax": OWN_TAX,
            },
            own_tax_id=OWN_TAX,
        )
        self.assertEqual((kind, reason), ("purchase_invoice", None))

    def test_payment_evidence_is_non_tax(self):
        kind, reason = sort_step.bin_ocr_fields(
            {"document_type": "payment_evidence", "vat": "0"}, own_tax_id=OWN_TAX
        )
        self.assertEqual(kind, "non_tax")
        self.assertEqual(reason, "no_tax_elements:payment_evidence")

    def test_no_vat_and_no_tax_ids_is_non_tax(self):
        kind, reason = sort_step.bin_ocr_fields(
            {"document_type": "receipt", "vat": "0", "seller_tax": "", "buyer_tax": ""},
            own_tax_id=OWN_TAX,
        )
        self.assertEqual(kind, "non_tax")
        self.assertEqual(reason, "no_tax_elements:receipt")

    def test_own_tax_as_seller_stays_unknown_for_review(self):
        # M0 销项事实源 = POS 直读,单张销项票不自动归堆,留人工(T0 §四.4)。
        kind, reason = sort_step.bin_ocr_fields(
            {
                "document_type": "tax_invoice",
                "vat": "70.00",
                "seller_tax": OWN_TAX,
                "buyer_tax": OTHER_TAX,
            },
            own_tax_id=OWN_TAX,
        )
        self.assertEqual((kind, reason), ("unknown", "sales_direction_unhandled"))

    def test_tax_elements_but_no_anchor_match_is_ambiguous(self):
        kind, reason = sort_step.bin_ocr_fields(
            {
                "document_type": "tax_invoice",
                "vat": "35.00",
                "seller_tax": OTHER_TAX,
                "buyer_tax": "",
            },
            own_tax_id=OWN_TAX,
        )
        self.assertEqual((kind, reason), ("unknown", "direction_ambiguous"))

    def test_dirty_tax_ids_never_route(self):
        # 弱信号税号(OCR 残留)归一成空 → 不匹配 → ambiguous,与 direction.py 同口径。
        kind, reason = sort_step.bin_ocr_fields(
            {
                "document_type": "tax_invoice",
                "vat": "10.00",
                "seller_tax": "13",
                "buyer_tax": OWN_TAX[:12],
            },
            own_tax_id=OWN_TAX,
        )
        self.assertEqual((kind, reason), ("unknown", "direction_ambiguous"))


class BankContentDetectionTests(unittest.TestCase):
    def test_bank_keyword_without_vat_is_bank_statement(self):
        kind, reason = sort_step.bin_ocr_fields(
            {"document_type": "other", "seller_name": "ธนาคารกสิกรไทย", "vat": "0"},
            own_tax_id=OWN_TAX,
        )
        self.assertEqual((kind, reason), ("bank_statement", None))

    def test_ascii_bank_code_word_boundary_hit(self):
        kind, _ = sort_step.bin_ocr_fields(
            {"document_type": "other", "notes": "STATEMENT - SCB", "vat": ""},
            own_tax_id=OWN_TAX,
        )
        self.assertEqual(kind, "bank_statement")

    def test_bank_word_but_has_vat_is_not_bank(self):
        # 真税票里印付款银行(带 VAT 结构)不能被误判成流水页——无 VAT 才认银行。
        kind, _ = sort_step.bin_ocr_fields(
            {
                "document_type": "tax_invoice",
                "seller_name": "ธนาคารกสิกรไทย",
                "seller_tax": OTHER_TAX,
                "buyer_tax": OWN_TAX,
                "vat": "70.00",
            },
            own_tax_id=OWN_TAX,
        )
        self.assertEqual(kind, "purchase_invoice")

    def test_no_bank_word_no_tax_stays_non_tax(self):
        kind, reason = sort_step.bin_ocr_fields(
            {"document_type": "other", "seller_name": "ร้านค้าทั่วไป", "vat": "0"},
            own_tax_id=OWN_TAX,
        )
        self.assertEqual((kind, reason), ("non_tax", "no_tax_elements:other"))


class NameAnchorFallbackTests(unittest.TestCase):
    def test_missing_buyer_tax_but_buyer_name_matches_own_is_purchase(self):
        kind, reason = sort_step.bin_ocr_fields(
            {
                "document_type": "tax_invoice",
                "vat": "91.00",
                "seller_tax": OTHER_TAX,
                "buyer_tax": "",
                "buyer_name": "ซิสเตอร์ ตัวอย่าง",  # 缺前后缀,归一化后同字号
            },
            own_tax_id=OWN_TAX,
            own_name=OWN_NAME,
        )
        self.assertEqual((kind, reason), ("purchase_invoice", None))

    def test_seller_name_matches_own_is_sales_direction(self):
        kind, reason = sort_step.bin_ocr_fields(
            {
                "document_type": "tax_invoice",
                "vat": "50.00",
                "seller_tax": "",
                "buyer_tax": OTHER_TAX,
                "seller_name": "บริษัท ซิสเตอร์ ตัวอย่าง จำกัด (สำนักงานใหญ่)",
            },
            own_tax_id=OWN_TAX,
            own_name=OWN_NAME,
        )
        self.assertEqual((kind, reason), ("unknown", "sales_direction_unhandled"))

    def test_name_mismatch_stays_ambiguous(self):
        kind, reason = sort_step.bin_ocr_fields(
            {
                "document_type": "tax_invoice",
                "vat": "20.00",
                "seller_tax": OTHER_TAX,
                "buyer_tax": "",
                "buyer_name": "ร้านอื่น ไม่เกี่ยว",
            },
            own_tax_id=OWN_TAX,
            own_name=OWN_NAME,
        )
        self.assertEqual((kind, reason), ("unknown", "direction_ambiguous"))

    def test_no_own_name_falls_back_to_ambiguous(self):
        kind, reason = sort_step.bin_ocr_fields(
            {
                "document_type": "tax_invoice",
                "vat": "20.00",
                "seller_tax": OTHER_TAX,
                "buyer_tax": "",
                "buyer_name": "ซิสเตอร์ ตัวอย่าง",
            },
            own_tax_id=OWN_TAX,
            own_name=None,
        )
        self.assertEqual((kind, reason), ("unknown", "direction_ambiguous"))


class CompanyNameNormalizeTests(unittest.TestCase):
    def test_normalize_strips_affixes_and_whitespace(self):
        a = sort_step._normalize_company_name("บริษัท ซิสเตอร์ ตัวอย่าง จำกัด")
        b = sort_step._normalize_company_name("ซิสเตอร์ตัวอย่าง")
        self.assertEqual(a, b)

    def test_match_requires_min_length_for_substring(self):
        # 短字号子串(<4)不算命中,防琐碎误匹配。
        self.assertFalse(sort_step._company_name_match("abc", "abcdefg company limited"))
        self.assertTrue(sort_step._company_name_match("abcd", "abcdefg co.,ltd"))

    def test_empty_names_never_match(self):
        self.assertFalse(sort_step._company_name_match("", "บริษัท จำกัด"))
        self.assertFalse(sort_step._company_name_match("บริษัท จำกัด", ""))


if __name__ == "__main__":
    unittest.main()
