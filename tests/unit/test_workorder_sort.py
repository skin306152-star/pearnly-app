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
from unittest import mock

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

    def test_pdf_sales_summary_by_filename(self):
        """销售汇总 PDF 归 sales_summary:交 OCR 既烧钱又永远产不出 sales_read。"""
        store = FakeItemStore(
            [
                _item(1, "/in/สรุปยอดขาย 7-11 กรกฎาคม.pdf"),
                _item(2, "/in/Sales Summary July 2026.pdf"),
                _item(3, "/in/รายงานการขาย.pdf"),
            ]
        )
        out = sort_step.run(_ctx(store))

        for ref in ("กรกฎาคม.pdf", "July 2026.pdf", "รายงานการขาย.pdf"):
            self.assertEqual(store.by_ref(ref)["kind"], "sales_summary")
        self.assertEqual(out.payload["pending_ocr"], 0)

    def test_pdf_invoice_names_never_taken_as_summary(self):
        """票据名反证:宁可漏归走原 OCR 路,也不把发票误归成汇总表。"""
        store = FakeItemStore(
            [
                _item(1, "/in/ใบกำกับภาษี ยอดขาย 001.pdf"),
                _item(2, "/in/Tax Invoice sales report 88.pdf"),
                _item(3, "/in/receipt_0007.pdf"),
            ]
        )
        out = sort_step.run(_ctx(store))

        self.assertEqual({i["kind"] for i in store.items}, {"unknown"})
        self.assertEqual(out.payload["pending_ocr"], 3)

    def test_gl_and_bank_pdf_judgements_unchanged(self):
        """GL / 银行判据在汇总表判据之前,优先级不许被抢。"""
        store = FakeItemStore([_item(1, "/in/GL ยอดขาย.pdf"), _item(2, "/in/KBANK สรุปยอดขาย.pdf")])
        sort_step.run(_ctx(store))

        self.assertEqual(store.by_ref("GL ยอดขาย.pdf")["kind"], "gl_ledger")
        self.assertEqual(store.by_ref("KBANK สรุปยอดขาย.pdf")["kind"], "bank_statement")

    def _head_scan(self, pages):
        with (
            mock.patch.object(sort_step.storage, "read_bytes", return_value=b"%PDF"),
            mock.patch.object(sort_step.text_layer, "extract_pages", return_value=pages),
        ):
            return sort_step._pdf_head_is_sales_summary("/in/scan_0001.pdf")

    def test_pdf_content_scan_recognizes_report_title(self):
        """文件名无线索时靠首页文字层报表抬头认;扫描件/票据 → 原 OCR 路。"""
        self.assertTrue(self._head_scan(["สรุปยอดขาย ประจำเดือน"]))
        self.assertTrue(self._head_scan(["Monthly Sales Summary"]))
        self.assertFalse(self._head_scan(["ใบกำกับภาษี สรุปยอดขาย"]))
        self.assertFalse(self._head_scan(["ยอดขาย 100.00"]))  # 裸词不作数,只认报表抬头
        self.assertFalse(self._head_scan([""]))
        self.assertFalse(self._head_scan(None))

    def test_pdf_content_scan_only_reads_first_page(self):
        """抬头只在首页;第二页出现关键词不作数(也不多花一页解析)。"""
        self.assertFalse(self._head_scan(["ใบส่งของ", "สรุปยอดขาย"]))

    def test_pdf_content_scan_survives_unreadable_file(self):
        self.assertFalse(sort_step._pdf_head_is_sales_summary("/nowhere/missing.pdf"))

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

    def test_unreadable_vat_goes_to_direction_review_not_silently_excluded(self):
        """B-2/B-3:VAT 印了但读不出 ≠ 没有 VAT。

        修前 _has_vat 对两者一律 False → 两头税号也没读出来时走「无税务要素」出口判 non_tax,
        classify 再无条件 status=excluded(B-3 的零人复核终态),这张税票的进项税就此消失。
        现在交人定向:kind=unknown + 方向通道 reason,R1 无裁决即停机点名。
        """
        for bad in ("7O.00", "N/A", "-", "NaN"):
            with self.subTest(vat=bad):
                kind, reason = sort_step.bin_ocr_fields(
                    {"document_type": "receipt", "vat": bad, "seller_tax": "", "buyer_tax": ""},
                    own_tax_id=OWN_TAX,
                )
                self.assertEqual(kind, "unknown")
                self.assertEqual(reason, "vat_unreadable:receipt")

    def test_unreadable_vat_also_beats_the_bank_statement_exit(self):
        # 另一个静默出口:提到银行 + 无 VAT → 判流水页。读不出时同样不许走。
        kind, reason = sort_step.bin_ocr_fields(
            {
                "document_type": "other",
                "vat": "7O.00",
                "seller_tax": "",
                "buyer_tax": "",
                "notes": "KASIKORNBANK",
            },
            own_tax_id=OWN_TAX,
        )
        self.assertEqual(kind, "unknown")
        self.assertTrue(reason.startswith("vat_unreadable"))

    def test_genuinely_absent_vat_still_takes_the_non_tax_exit(self):
        # 「本来就没有 VAT」的判定一字不变 —— 不许因为这条新判据把真非税件也拖进人审。
        for absent in ("0", "", None, "0.00"):
            with self.subTest(vat=absent):
                kind, reason = sort_step.bin_ocr_fields(
                    {"document_type": "receipt", "vat": absent, "seller_tax": "", "buyer_tax": ""},
                    own_tax_id=OWN_TAX,
                )
                self.assertEqual(kind, "non_tax")
                self.assertEqual(reason, "no_tax_elements:receipt")

    def test_own_tax_as_seller_bins_sales_doc_for_review(self):
        # 自家==卖方 → 自动归本方销项堆 sales_doc,flagged 留人工过目(MC1-c.1,替代旧判死 unknown)。
        kind, reason = sort_step.bin_ocr_fields(
            {
                "document_type": "tax_invoice",
                "vat": "70.00",
                "seller_tax": OWN_TAX,
                "buyer_tax": OTHER_TAX,
            },
            own_tax_id=OWN_TAX,
        )
        self.assertEqual((kind, reason), ("sales_doc", "sales_doc_review"))

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

    def test_kasikornbank_compound_name_is_bank(self):
        kind, _ = sort_step.bin_ocr_fields(
            {"document_type": "other", "seller_name": "KASIKORNBANK", "vat": "0"},
            own_tax_id=OWN_TAX,
        )
        self.assertEqual(kind, "bank_statement")

    def test_kbiz_statement_brand_is_bank(self):
        kind, _ = sort_step.bin_ocr_fields(
            {
                "document_type": "other",
                "seller_name": "K BIZ",
                "notes": "Bank statement transaction list",
                "vat": "0",
            },
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


class StatementRegroupTests(unittest.TestCase):
    """SA3R-a 对账单续页回收判据(stmt_regroup 闸)。夹具取自金标 KBANK 工单 a6dde2ce 里被 OCR
    误判 payment_evidence 的真页 + 同工单真付款样本(document_type/seller_name/notes 逐字段真值)。
    锁三条:① 命中银行名+对账单标题的续页,闸开救回 bank_statement;② 边界页(银行名在、标题
    不在)与真付款样本零误吸(闸开仍 non_tax);③ 闸关(默认)逐字节维持现状。"""

    # 5 张被误判 payment_evidence 的对账单续页(真 notes)。IMG_2487 是边界页:notes 是动作词
    # (รายงานการโอนเงิน)不是报表抬头,有意不进白名单——它 seller_name 也是银行名,正是「银行名
    # 在场但标题不在」的最强反例,锁死单靠 _mentions_bank 会误吸、必须叠标题判据。
    _STMT_PAGES = {
        "IMG_2485": "รายการเดินบัญชี / Statement",
        "IMG_2492": "รายงานความเคลื่อนไหวทางบัญชี (Statement)",
        "IMG_2494": "รายงานแสดงรายการเคลื่อนไหวบัญชีเงินฝากออมทรัพย์",
        "IMG_2500": "รายการเดินบัญชีเงินฝากออมทรัพย์",
    }
    _BOUNDARY_NOTES = "รายงานการโอนเงิน / รับฝากเงิน"  # IMG_2487 边界页
    # 6 张同工单真付款样本(seller_name=商户自己名,notes=EDC 脚注/QR/结算,均不提银行)。
    _PAYMENT_SAMPLES = {
        "IMG_2565": "BATCH:000187 TIME:16:26:52 TRACE:001263 APPR:592256",
        "IMG_2567": "BATCH:000187 TIME:16:33:21 TID:62608078 MID:401017358317001 TRACE:001264",
        "IMG_2571": "Thai QR Payment PROMPTPAY MERCHANT COPY",
        "IMG_2581": "Thai QR Payment",
        "IMG_2583": "BATCH:000186 TIME:16:19:47 TRACE:001262 APPR:592238",
        "IMG_2606": "SETTLEMENT SUCCESSFUL\nPROMPTPAY",
    }

    def _stmt_page(self, notes):
        return {
            "document_type": "payment_evidence",
            "seller_name": "ธนาคารกสิกรไทย",
            "notes": notes,
        }

    def _payment(self, notes):
        return {
            "document_type": "payment_evidence",
            "seller_name": "SISTER MAKEUP SAPHAN SUNG , BKK",
            "notes": notes,
        }

    def test_flag_on_regroups_statement_continuation_pages(self):
        for name, notes in self._STMT_PAGES.items():
            with self.subTest(page=name):
                kind, reason = sort_step.bin_ocr_fields(
                    self._stmt_page(notes), own_tax_id=OWN_TAX, stmt_regroup=True
                )
                self.assertEqual((kind, reason), ("bank_statement", None))

    def test_english_bank_statement_title_is_regrouped(self):
        kind, reason = sort_step.bin_ocr_fields(
            self._stmt_page("Bank statement transaction list"),
            own_tax_id=OWN_TAX,
            stmt_regroup=True,
        )
        self.assertEqual((kind, reason), ("bank_statement", None))

    def test_img_2501_category_and_title_rescue_without_bank_name(self):
        fields = {
            "document_type": "payment_evidence",
            "category": "bank",
            "notes": "Bank statement/transaction list",
            "seller_name": "สาขาบิ๊กซี เคหะร่มเกล้า",
            "vat": "0",
        }
        self.assertEqual(
            sort_step.bin_ocr_fields(fields, own_tax_id=OWN_TAX, stmt_regroup=True),
            ("bank_statement", None),
        )
        self.assertEqual(
            sort_step.bin_ocr_fields(fields, own_tax_id=OWN_TAX),
            ("non_tax", "no_tax_elements:payment_evidence"),
        )

    def test_bank_category_without_statement_title_stays_non_tax(self):
        fields = {
            "document_type": "payment_evidence",
            "category": "bank",
            "notes": "Transfer completed",
            "seller_name": "ร้านค้าทั่วไป",
        }
        self.assertEqual(
            sort_step.bin_ocr_fields(fields, own_tax_id=OWN_TAX, stmt_regroup=True),
            ("non_tax", "no_tax_elements:payment_evidence"),
        )

    def test_flag_off_leaves_continuation_pages_as_non_tax(self):
        # 闸关(默认)= 逐字节现状:续页照旧被 payment_evidence 短路踢 non_tax。
        for name, notes in self._STMT_PAGES.items():
            with self.subTest(page=name):
                kind, reason = sort_step.bin_ocr_fields(self._stmt_page(notes), own_tax_id=OWN_TAX)
                self.assertEqual((kind, reason), ("non_tax", "no_tax_elements:payment_evidence"))

    def test_boundary_page_bank_name_but_no_title_not_regrouped(self):
        # 边界页:银行名在场但 notes 非报表抬头 → 闸开也不救回(交第 2 层安全网),证标题判据是硬门。
        kind, reason = sort_step.bin_ocr_fields(
            self._stmt_page(self._BOUNDARY_NOTES), own_tax_id=OWN_TAX, stmt_regroup=True
        )
        self.assertEqual((kind, reason), ("non_tax", "no_tax_elements:payment_evidence"))

    def test_real_payment_samples_zero_false_capture(self):
        # 真付款样本闸开仍全数 non_tax(零误吸):它们不提银行,_mentions_bank 这道门先挡住。
        for name, notes in self._PAYMENT_SAMPLES.items():
            with self.subTest(sample=name):
                kind, _ = sort_step.bin_ocr_fields(
                    self._payment(notes), own_tax_id=OWN_TAX, stmt_regroup=True
                )
                self.assertEqual(kind, "non_tax")

    def test_statement_page_with_vat_not_regrouped(self):
        # 带 VAT 税票结构即便印银行名+标题也不回收(not has_vat 硬门,防真税票误判流水)。
        kind, _ = sort_step.bin_ocr_fields(
            {
                "document_type": "payment_evidence",
                "seller_name": "ธนาคารกสิกรไทย",
                "notes": "รายการเดินบัญชี",
                "vat": "70.00",
            },
            own_tax_id=OWN_TAX,
            stmt_regroup=True,
        )
        self.assertNotEqual(kind, "bank_statement")


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

    def test_seller_name_matches_own_bins_sales_doc(self):
        # 税号锚失灵、名集命中卖方名 → 本方销项堆 sales_doc(MC1-c.1,与税号锚路同口径)。
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
        self.assertEqual((kind, reason), ("sales_doc", "sales_doc_review"))

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


class EdcSettlementBinTests(unittest.TestCase):
    """SA-2a EDC 归堆咬人测试:真料形状(SM 5月 vertex OCR 探针原值)命中 + 近邻票据零误归。"""

    # 名集锚:法定泰文名 + 会计确认的英文商号别名(exact)——EDC 判据按 substring 门槛比对。
    ENTRIES = [("บริษัท ซิสเตอร์ เมคอัพ จำกัด", "legal"), ("Sister Makeup", "exact")]

    def _bin(self, fields, entries=None):
        return sort_step.bin_ocr_fields(
            fields, own_tax_id=OWN_TAX, own_names=self.ENTRIES if entries is None else entries
        )

    def _settlement_fields(self, **over):
        # IMG_2582 探针原值:日终结算票,notes 打印 SETTLEMENT + BATCH/TID 脚注。
        fields = {
            "document_type": "other",
            "is_not_invoice": True,
            "date": "2026-05-25",
            "seller_name": "SISTER MAKEUP SAPHAN SUNG , BKK",
            "subtotal": "540.00",
            "vat": "0.00",
            "total_amount": "540.00",
            "payment_method": "qr",
            "notes": "SETTLEMENT SUCCESSFUL\nHOST: THAIQR\nTID# 62608078\nBATCH# 000186",
        }
        fields.update(over)
        return fields

    def test_settlement_slip_bins_edc(self):
        self.assertEqual(self._bin(self._settlement_fields()), ("edc_settlement", None))

    def test_settlement_word_in_invoice_number_also_hits(self):
        # IMG_2585 形状:notes 只有 "SETTLEMENT",批次号被读进 invoice_number。
        fields = self._settlement_fields(notes="SETTLEMENT", invoice_number="000178")
        self.assertEqual(self._bin(fields), ("edc_settlement", None))

    def test_per_transaction_sale_slip_not_edc(self):
        # IMG_2565 形状:单笔 SALE 支付条(BATCH/TRACE/APPR 脚注,无 SETTLEMENT)——它是某张
        # 销售小票的收款凭证,归堆会与税票双计 → 维持 payment_evidence 排除现状。
        fields = self._settlement_fields(
            document_type="payment_evidence",
            notes="BATCH:000187 TIME:16:26:52 TRACE:001263 APPR:592256",
            total_amount="2728.00",
        )
        self.assertEqual(self._bin(fields), ("non_tax", "no_tax_elements:payment_evidence"))

    def test_bank_statement_print_not_edc(self):
        # IMG_2485 形状:K BIZ 流水打印页,"Statement" 词形不同(词边界),卖方名=银行。
        fields = {
            "document_type": "payment_evidence",
            "seller_name": "ธนาคารกสิกรไทย",
            "total_amount": "362264.36",
            "vat": "",
            "notes": "รายการเดินบัญชี / Statement",
        }
        kind, _reason = self._bin(fields)
        self.assertNotEqual(kind, "edc_settlement")

    def test_tax_invoice_mentioning_settlement_not_edc(self):
        # 真税票(带 VAT/税号)哪怕备注出现 settlement 也走方向判据,不进佐证堆。
        fields = {
            "document_type": "tax_invoice",
            "vat": "70.00",
            "seller_tax": OTHER_TAX,
            "buyer_tax": OWN_TAX,
            "notes": "settlement ref 123",
            "total_amount": "1070.00",
        }
        self.assertEqual(self._bin(fields), ("purchase_invoice", None))

    def test_merchant_name_mismatch_falls_through(self):
        # 商户名对不上本账套名集(串了别家客户的结算票)→ 维持现状排除,绝不污染本户销项聚合。
        fields = self._settlement_fields(seller_name="ANOTHER SHOP LADPRAO, BKK")
        self.assertEqual(self._bin(fields), ("non_tax", "no_tax_elements:other"))

    def test_unparseable_gross_falls_through(self):
        fields = self._settlement_fields(total_amount="", subtotal="")
        self.assertEqual(self._bin(fields), ("non_tax", "no_tax_elements:other"))

    def test_legacy_single_name_path_without_alias_falls_through(self):
        # 闸关单名路(own_names=None):泰文法定名对不上 ASCII 商户名 → 现状不变(诚实漏归,
        # 不为归堆率放宽)。
        kind, reason = sort_step.bin_ocr_fields(
            self._settlement_fields(), own_tax_id=OWN_TAX, own_name=OWN_NAME
        )
        self.assertEqual((kind, reason), ("non_tax", "no_tax_elements:other"))


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
