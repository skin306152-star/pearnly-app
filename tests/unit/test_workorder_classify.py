# -*- coding: utf-8 -*-
"""classify 步守门测试(services/workorder/steps/classify.py · 任务包 §5 步 3)。

全程注入假 OCR/直读入口(classify._ocr_image / classify._read_sales_summary /
classify._resolve_own_tax_id),绝不触达生产 OCR 管线或任何 API key——覆盖归堆、
查重指纹、non_tax、ambiguous、OCR 异常单件隔离、销项直读成败、幂等重跑。
"""

import unittest

from services.workorder.engine import StepContext
from services.workorder.steps import classify

OWN_TAX = "0105567178203"
OTHER_TAX = "0735527000289"
OWN_NAME = "บริษัท ซิสเตอร์ ตัวอย่าง จำกัด"


class FakeItemStore:
    """list_items/update_item/list_events 的内存替身(classify 只用这三个)。"""

    def __init__(self, items):
        self.items = items
        self.events = []

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]

    def update_item(self, cur, *, tenant_id, item_id, status=None, kind=None, flag_reason=None):
        it = next(i for i in self.items if i["id"] == item_id)
        it["status"] = status
        it["kind"] = kind if kind is not None else it["kind"]
        it["flag_reason"] = flag_reason

    def append_event(
        self,
        cur,
        *,
        tenant_id,
        work_order_id,
        step,
        event_type,
        payload=None,
        actor="system",
        dedupe_key=None,
    ):
        self.events.append(
            {
                "id": len(self.events) + 1,
                "step": step,
                "event_type": event_type,
                "payload": payload or {},
            }
        )

    def by_id(self, item_id):
        return next(i for i in self.items if i["id"] == item_id)

    def classified(self, item_id):
        for e in self.events:
            p = e["payload"]
            if e["event_type"] == "item_classified" and p.get("item_id") == item_id:
                return p
        return None


def _item(item_id, file_ref, kind="unknown"):
    return {
        "id": item_id,
        "file_ref": file_ref,
        "kind": kind,
        "status": "pending",
        "flag_reason": None,
    }


def _ctx(store, data=None):
    return StepContext(
        cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data=data or {}
    )


def _purchase_fields(
    *, seller=OTHER_TAX, buyer=OWN_TAX, invoice_no="IV001", total="107.00", vat="7.00"
):
    return {
        "document_type": "tax_invoice",
        "seller_tax": seller,
        "buyer_tax": buyer,
        "invoice_number": invoice_no,
        "total_amount": total,
        "vat": vat,
    }


class ClassifyImageTests(unittest.TestCase):
    """purchase_invoice 归堆 + 票面指纹。"""

    def setUp(self):
        classify._resolve_own_tax_id = lambda ctx: OWN_TAX
        classify._resolve_own_name = lambda ctx: OWN_NAME
        self.addCleanup(
            setattr, classify, "_resolve_own_tax_id", classify._default_resolve_own_tax_id
        )
        self.addCleanup(setattr, classify, "_resolve_own_name", classify._default_resolve_own_name)
        self.addCleanup(setattr, classify, "_ocr_image", classify._default_ocr_image)

    def test_purchase_invoice_bins_and_marks_ok(self):
        item = _item("i1", "/in/IMG_0001.jpg")
        store = FakeItemStore([item])
        classify._ocr_image = lambda path: _purchase_fields()

        out = classify.run(_ctx(store))

        self.assertEqual(out.status, "ok")
        self.assertEqual(out.payload["bins"], {"purchase_invoice": 1})
        self.assertEqual(out.payload["flagged"], 0)
        self.assertEqual(store.by_id("i1")["kind"], "purchase_invoice")
        self.assertEqual(store.by_id("i1")["status"], "ok")
        # 归堆即落 item_classified 证据事件,带票面钱字段供 reconcile 回放。
        evt = store.classified("i1")
        self.assertEqual(evt["kind"], "purchase_invoice")
        self.assertEqual(evt["status"], "ok")
        self.assertEqual(evt["money"]["vat"], "7.00")
        self.assertEqual(evt["money"]["total_amount"], "107.00")

    def test_duplicate_invoice_second_copy_excluded_with_reason(self):
        first = _item("i1", "/in/IMG_0001.jpg")
        second = _item("i2", "/in/IMG_0001_copy.jpg")
        store = FakeItemStore([first, second])
        fields_by_path = {
            "/in/IMG_0001.jpg": _purchase_fields(invoice_no="IV777", total="500.00"),
            "/in/IMG_0001_copy.jpg": _purchase_fields(invoice_no="IV777", total="500.00"),
        }
        classify._ocr_image = lambda path: fields_by_path[path]

        out = classify.run(_ctx(store))

        self.assertEqual(out.payload["bins"], {"purchase_invoice": 1, "duplicate": 1})
        dup = store.by_id("i2")
        self.assertEqual(dup["kind"], "duplicate")
        self.assertEqual(dup["status"], "excluded")
        self.assertEqual(dup["flag_reason"], "duplicate_of:IMG_0001.jpg")
        # 第一张不受影响,仍正常归堆。
        self.assertEqual(store.by_id("i1")["kind"], "purchase_invoice")

    def test_non_tax_carries_reason_through_bin_ocr_fields(self):
        item = _item("i1", "/in/qr.jpg")
        store = FakeItemStore([item])
        classify._ocr_image = lambda path: {"document_type": "payment_evidence", "vat": "0"}

        out = classify.run(_ctx(store))

        self.assertEqual(store.by_id("i1")["kind"], "non_tax")
        self.assertEqual(store.by_id("i1")["status"], "excluded")
        self.assertEqual(store.by_id("i1")["flag_reason"], "no_tax_elements:payment_evidence")
        # non_tax 不是「结构上有问题」,不计入 flagged(sort 的既有语义:排除但不留人工)。
        self.assertEqual(out.payload["flagged"], 0)

    def test_ambiguous_direction_flagged_for_review(self):
        item = _item("i1", "/in/weird.jpg")
        store = FakeItemStore([item])
        classify._ocr_image = lambda path: _purchase_fields(seller=OTHER_TAX, buyer="")

        out = classify.run(_ctx(store))

        row = store.by_id("i1")
        self.assertEqual(row["kind"], "unknown")
        self.assertEqual(row["status"], "flagged")
        self.assertEqual(row["flag_reason"], "direction_ambiguous")
        self.assertEqual(out.payload["flagged"], 1)

    def test_gate_warning_with_amount_keyword_flags_amount_math_fail(self):
        item = _item("i1", "/in/IMG_2647.jpg")
        store = FakeItemStore([item])
        fields = _purchase_fields(invoice_no="IV2647", total="4069.00")
        fields["_validation_warnings"] = [
            "VAT 4069 既非小计 58128.57 × 7% 也非净额 × 7%(自洽性幻觉)"
        ]
        classify._ocr_image = lambda path: fields

        out = classify.run(_ctx(store))

        row = store.by_id("i1")
        self.assertEqual(row["kind"], "purchase_invoice")
        self.assertEqual(row["status"], "flagged")
        self.assertEqual(row["flag_reason"], "amount_math_fail")
        self.assertEqual(out.payload["flagged"], 1)

    def test_sales_receipt_with_math_warning_bins_sales_doc_not_amount_math_fail(self):
        # 自家==卖方的销售小票:OCR 也会报「净+税≠总额」,但销项票不进数学闸——归本方销项堆
        # sales_doc(MC1-c.1),不被误挂 amount_math_fail(L2 首跑 47 张误判的形态)。
        item = _item("i1", "/in/IMG_ocha_sale.jpg")
        store = FakeItemStore([item])
        fields = _purchase_fields(seller=OWN_TAX, buyer=OTHER_TAX, invoice_no="POS-88", vat="7.00")
        fields["_validation_warnings"] = ["小计 100.00 + vat 7.00 != 总额 108.00(不平)"]
        classify._ocr_image = lambda path: fields

        out = classify.run(_ctx(store))

        row = store.by_id("i1")
        self.assertEqual(row["kind"], "sales_doc")
        self.assertEqual(row["status"], "flagged")
        self.assertEqual(row["flag_reason"], "sales_doc_review")
        self.assertEqual(out.payload["flagged"], 1)

    def test_bank_statement_keyword_without_vat_bins_bank_and_skips_math_gate(self):
        # 无名 KBANK 流水照片:正文出现行名且无 VAT 结构 → bank_statement,不进数学闸、不挂 flag。
        item = _item("i1", "/in/IMG_5566.jpg")
        store = FakeItemStore([item])
        fields = {
            "document_type": "other",
            "seller_name": "ธนาคารกสิกรไทย จำกัด (มหาชน)",
            "seller_tax": "",
            "buyer_tax": "",
            "vat": "0",
        }
        fields["_validation_warnings"] = ["总额 5246.00 > 上限(不平)"]
        classify._ocr_image = lambda path: fields

        out = classify.run(_ctx(store))

        row = store.by_id("i1")
        self.assertEqual(row["kind"], "bank_statement")
        self.assertEqual(row["status"], "ok")
        self.assertIsNone(row["flag_reason"])
        self.assertEqual(out.payload["flagged"], 0)

    def test_missing_buyer_tax_but_name_matches_own_bins_purchase(self):
        # 买方税号被 OCR 读花/缺失,但买方名称容差匹配本公司名 → 归进项(找回 L2 被踢进 unknown 的真进项票)。
        item = _item("i1", "/in/IMG_2650.jpg")
        store = FakeItemStore([item])
        fields = _purchase_fields(seller=OTHER_TAX, buyer="", invoice_no="IN26-0700", vat="91.00")
        fields["buyer_name"] = "ซิสเตอร์ ตัวอย่าง"  # 少了 บริษัท/จำกัด 前后缀,归一化后仍同字号
        classify._ocr_image = lambda path: fields

        out = classify.run(_ctx(store))

        row = store.by_id("i1")
        self.assertEqual(row["kind"], "purchase_invoice")
        self.assertEqual(row["status"], "ok")
        self.assertIsNone(row["flag_reason"])
        self.assertEqual(out.payload["flagged"], 0)

    def test_needs_review_without_amount_keyword_flags_low_confidence(self):
        item = _item("i1", "/in/blurry.jpg")
        store = FakeItemStore([item])
        fields = _purchase_fields()
        fields["_needs_review"] = True
        fields["_confidence_band"] = "yellow_confirm"
        classify._ocr_image = lambda path: fields

        out = classify.run(_ctx(store))

        row = store.by_id("i1")
        self.assertEqual(row["status"], "flagged")
        self.assertEqual(row["flag_reason"], "ocr_low_confidence:yellow_confirm")

    def test_ocr_exception_flags_only_that_item_not_the_whole_step(self):
        good = _item("i1", "/in/good.jpg")
        bad = _item("i2", "/in/corrupt.jpg")
        store = FakeItemStore([good, bad])

        def flaky_ocr(path):
            if path == "/in/corrupt.jpg":
                raise ValueError("cannot decode image")
            return _purchase_fields()

        classify._ocr_image = flaky_ocr
        out = classify.run(_ctx(store))

        self.assertEqual(out.status, "ok")
        self.assertEqual(store.by_id("i1")["status"], "ok")
        bad_row = store.by_id("i2")
        self.assertEqual(bad_row["status"], "flagged")
        self.assertEqual(bad_row["flag_reason"], "ocr_error:ValueError")
        self.assertEqual(out.payload["flagged"], 1)

    def test_idempotent_rerun_does_not_reprocess_done_items(self):
        item = _item("i1", "/in/IMG_0001.jpg")
        store = FakeItemStore([item])
        calls = []

        def counting_ocr(path):
            calls.append(path)
            return _purchase_fields()

        classify._ocr_image = counting_ocr
        classify.run(_ctx(store))
        events_after_first = len(store.events)
        out2 = classify.run(_ctx(store))

        self.assertEqual(len(calls), 1)
        self.assertEqual(out2.payload, {"bins": {}, "flagged": 0, "sales_summary_reads": {}})
        # 重跑无 pending 件 → 不再落 item_classified 事件(证据流不翻倍)。
        self.assertEqual(len(store.events), events_after_first)


class ClassifySalesSummaryTests(unittest.TestCase):
    def setUp(self):
        classify._resolve_own_tax_id = lambda ctx: OWN_TAX
        classify._resolve_own_name = lambda ctx: OWN_NAME
        self.addCleanup(
            setattr, classify, "_resolve_own_tax_id", classify._default_resolve_own_tax_id
        )
        self.addCleanup(setattr, classify, "_resolve_own_name", classify._default_resolve_own_name)
        self.addCleanup(
            setattr, classify, "_read_sales_summary", classify._default_read_sales_summary
        )

    def test_successful_direct_read_lands_in_ctx_data(self):
        item = _item("i1", "/in/pos_may.xlsx", kind="sales_summary")
        store = FakeItemStore([item])
        parsed = {"sheet_name": "Sheet1", "headers": ["date", "amount"], "rows": [{"index": 0}]}
        classify._read_sales_summary = lambda path: parsed

        out = classify.run(_ctx(store))

        self.assertEqual(store.by_id("i1")["status"], "ok")
        self.assertEqual(out.payload["sales_summary_reads"], {"i1": parsed})
        self.assertEqual(out.payload["flagged"], 0)
        # 直读结果同时落进 item_classified 事件的 sales_read,让 reconcile 续跑不依赖 ctx.data。
        self.assertEqual(store.classified("i1")["sales_read"], parsed)

    def test_unparseable_summary_flagged_not_swallowed(self):
        item = _item("i1", "/in/broken.xlsx", kind="sales_summary")
        store = FakeItemStore([item])
        classify._read_sales_summary = lambda path: {"headers": [], "rows": []}

        out = classify.run(_ctx(store))

        row = store.by_id("i1")
        self.assertEqual(row["status"], "flagged")
        self.assertEqual(row["flag_reason"], "summary_unparseable")
        self.assertEqual(out.payload["sales_summary_reads"], {})
        self.assertEqual(out.payload["flagged"], 1)

    def test_summary_read_exception_flagged_with_error_type(self):
        item = _item("i1", "/in/locked.xlsx", kind="sales_summary")
        store = FakeItemStore([item])

        def raising_read(path):
            raise OSError("file locked")

        classify._read_sales_summary = raising_read
        out = classify.run(_ctx(store))

        row = store.by_id("i1")
        self.assertEqual(row["status"], "flagged")
        self.assertEqual(row["flag_reason"], "summary_read_error:OSError")
        self.assertEqual(out.payload["flagged"], 1)


if __name__ == "__main__":
    unittest.main()
