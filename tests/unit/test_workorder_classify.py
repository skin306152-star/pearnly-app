# -*- coding: utf-8 -*-
"""classify 步守门测试(services/workorder/steps/classify.py · 任务包 §5 步 3)。

全程注入假 OCR/直读入口(classify._ocr_image / classify._read_sales_summary /
classify._resolve_own_tax_id),绝不触达生产 OCR 管线或任何 API key——覆盖归堆、
查重指纹、non_tax、ambiguous、OCR 异常单件隔离、销项直读成败、幂等重跑。
"""

import os
import unittest
from pathlib import Path

from services.workorder.engine import StepContext
from services.workorder.steps import classify, statement_regroup

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

    def reset_quota_deferred_items(self, cur, *, tenant_id, work_order_id, flag_reason):
        n = 0
        for it in self.items:
            if it.get("status") == "flagged" and it.get("flag_reason") == flag_reason:
                it["status"] = "pending"
                it["flag_reason"] = None
                n += 1
        return n

    def sum_workorder_ocr_cost(self, cur, *, tenant_id, item_ids):
        # 默认零成本(不触发封顶);成本封顶用例用子类/替身覆写返回值。
        return 0.0

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
        self.assertEqual(store.classified("i1")["reason"], "no_tax_elements:payment_evidence")
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

    def test_statement_sequence_recovers_ambiguous_continuation_pages(self):
        items = [_item(str(number), f"/in/IMG_{number}.jpg") for number in range(2484, 2490)]
        store = FakeItemStore(items)
        fields = {
            2484: {
                "document_type": "other",
                "seller_name": "KASIKORNBANK",
                "notes": "Bank statement transaction list",
            },
            2485: {
                "document_type": "other",
                "seller_name": "KASIKORNBANK",
                "notes": "Bank statement transaction list",
            },
            2486: {
                "document_type": "payment_evidence",
                "seller_name": "KASIKORNBANK",
                "notes": "Transfer record",
            },
            2487: {
                "document_type": "payment_evidence",
                "seller_name": "K-Contact Center",
                "notes": "www.kasikornbank.com",
            },
            2488: {
                "document_type": "payment_evidence",
                "seller_name": "KASIKORNBANK",
                "notes": "Transfer record",
            },
            2489: {
                "document_type": "other",
                "seller_name": "KASIKORNBANK",
                "notes": "Bank statement transaction list",
            },
        }
        classify._ocr_image = lambda path: fields[int(Path(path).stem.split("_")[-1])]
        classify._stmt_regroup_enabled = lambda ctx: True
        self.addCleanup(
            setattr,
            classify,
            "_stmt_regroup_enabled",
            classify._default_stmt_regroup_enabled,
        )

        out = classify.run(_ctx(store))

        self.assertEqual(out.payload["bins"], {"bank_statement": 6})
        for item in store.items:
            self.assertEqual((item["kind"], item["status"]), ("bank_statement", "ok"))
        regrouped = [e for e in store.events if e["event_type"] == "item_regrouped"]
        self.assertEqual(
            {e["payload"]["item_id"] for e in regrouped},
            {"2486", "2487", "2488"},
        )

    def test_statement_sequence_extends_past_last_anchor_only_with_title(self):
        numbers = [2484, 2488, 2492, 2496, 2500, 2501, 2503]
        items = [_item(str(number), f"/in/IMG_{number}.jpg") for number in numbers]
        store = FakeItemStore(items)
        records = []
        for item, number in zip(items, numbers):
            is_anchor = number <= 2500
            notes = "Bank statement/transaction list" if number != 2503 else "Transfer record"
            records.append(
                statement_regroup._Record(
                    item=item,
                    fields={"category": "bank", "notes": notes, "vat": "0"},
                    kind="bank_statement" if is_anchor else "non_tax",
                    status="ok" if is_anchor else "excluded",
                )
            )
        collector = statement_regroup.Collector(enabled=True)
        collector.records = records
        bins = {"bank_statement": 5, "non_tax": 2}

        reduced = collector.apply(_ctx(store), bins)

        self.assertEqual(reduced, 0)
        self.assertEqual(bins, {"bank_statement": 6, "non_tax": 1})
        self.assertEqual(store.by_id("2501")["kind"], "bank_statement")
        self.assertEqual(store.by_id("2503")["kind"], "unknown")
        regrouped = [e for e in store.events if e["event_type"] == "item_regrouped"]
        self.assertEqual([e["payload"]["item_id"] for e in regrouped], ["2501"])

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


class EdcSettlementClassifyTests(unittest.TestCase):
    """SA-2a:EDC 结算票归堆落 ok + edc 快照事件(字段逐一对齐 sales_agg/model.py 契约)。"""

    ENTRIES = [("บริษัท ซิสเตอร์ ตัวอย่าง จำกัด", "legal"), ("Sister Makeup", "exact")]

    def setUp(self):
        for name, fake in (
            ("_resolve_own_tax_id", lambda ctx: OWN_TAX),
            ("_resolve_own_names", lambda ctx: list(self.ENTRIES)),
            ("_m1_enabled", lambda ctx: True),
        ):
            prev = getattr(classify, name)
            setattr(classify, name, fake)
            self.addCleanup(setattr, classify, name, prev)
        self.addCleanup(setattr, classify, "_ocr_image", classify._default_ocr_image)

    def test_settlement_slip_ok_with_contract_aligned_snapshot(self):
        item = _item("i1", "/in/IMG_2582.jpg")
        store = FakeItemStore([item])
        classify._ocr_image = lambda path: {
            "document_type": "other",
            "date": "2026-05-25",
            "seller_name": "SISTER MAKEUP SAPHAN SUNG , BKK",
            "subtotal": "540.00",
            "vat": "0.00",
            "total_amount": "540.00",
            "payment_method": "qr",
            "notes": "SETTLEMENT SUCCESSFUL\nHOST: THAIQR\nTID# 62608078\nBATCH# 000186",
        }

        out = classify.run(_ctx(store))

        self.assertEqual(out.payload["bins"], {"edc_settlement": 1})
        self.assertEqual(out.payload["flagged"], 0)
        row = store.by_id("i1")
        self.assertEqual(row["kind"], "edc_settlement")
        self.assertEqual(row["status"], "ok")
        self.assertIsNone(row["flag_reason"])
        evt = store.classified("i1")
        # edc 快照独立于 money(money 是银行对账候选料源,结算票混入会被 E1 双配)。
        self.assertNotIn("money", evt)
        self.assertEqual(
            evt["edc"],
            {
                "settle_date": "2026-05-25",
                "gross_amount": "540.00",
                "fee_amount": None,
                "net_amount": None,
                "batch_no": "000186",
                "terminal_id": "62608078",
            },
        )

    def test_snapshot_without_footer_leaves_anchors_empty(self):
        item = _item("i1", "/in/IMG_2595.jpg")
        store = FakeItemStore([item])
        classify._ocr_image = lambda path: {
            "document_type": "other",
            "date": "2026-05-10",
            "seller_name": "SISTER MAKEUP SAPHAN SUNG, BKK",
            "total_amount": "39375.00",
            "vat": "",
            "notes": "SETTLEMENT SUCCESSFUL",
        }

        classify.run(_ctx(store))

        edc = store.classified("i1")["edc"]
        self.assertEqual(edc["gross_amount"], "39375.00")
        self.assertEqual(edc["batch_no"], "")
        self.assertEqual(edc["terminal_id"], "")


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


class _HeartbeatStore(FakeItemStore):
    def __init__(self, items):
        super().__init__(items)
        self.renewals = []

    def renew_run_lease(self, cur, *, tenant_id, work_order_id, owner, ttl_seconds):
        self.renewals.append({"owner": owner, "ttl": ttl_seconds})
        return True


class _UnitCM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


class ClassifyHeartbeatTests(unittest.TestCase):
    """MC2-A1 ④ 心跳:按步提交模式下,每件检查点提交顺带给 run 租约续期(只续自己 owner);
    无租约料(直调/CLI)零续约,行为不变。"""

    def setUp(self):
        classify._resolve_own_tax_id = lambda ctx: OWN_TAX
        classify._resolve_own_name = lambda ctx: OWN_NAME
        classify._ocr_image = lambda path: _purchase_fields(
            invoice_no=f"IV{abs(hash(path)) % 1000}", seller=f"1{abs(hash(path)) % 10**12:012d}"
        )
        self.addCleanup(
            setattr, classify, "_resolve_own_tax_id", classify._default_resolve_own_tax_id
        )
        self.addCleanup(setattr, classify, "_resolve_own_name", classify._default_resolve_own_name)
        self.addCleanup(setattr, classify, "_ocr_image", classify._default_ocr_image)

    def _ctx(self, store, data):
        return StepContext(
            cur=None,
            tenant_id="t-1",
            work_order_id="wo-1",
            store=store,
            data=data,
            cursor_factory=_UnitCM,
        )

    def test_each_item_checkpoint_renews_lease(self):
        store = _HeartbeatStore([_item("i1", "/in/a.jpg"), _item("i2", "/in/b.jpg")])
        lease = {"owner": "run:hb", "ttl_seconds": 1800}
        classify.run(self._ctx(store, {"run_lease": dict(lease)}))
        self.assertEqual(len(store.renewals), 2)  # 逐件检查点各续一次
        self.assertEqual(store.renewals[0], {"owner": "run:hb", "ttl": 1800})

    def test_no_lease_payload_means_no_renewal(self):
        store = _HeartbeatStore([_item("i1", "/in/a.jpg")])
        classify.run(self._ctx(store, {}))
        self.assertEqual(store.renewals, [])


class _QuotaBoom(Exception):
    """名字带 quota 的假异常(ocr_quota.is_quota_error 子串判据命中)。"""


class _CostStore(FakeItemStore):
    """sum_workorder_ocr_cost 脚本化(模拟 ai_usage 台账逐步长),验成本封顶。"""

    def __init__(self, items, sums):
        super().__init__(items)
        self._sums = list(sums)
        self._i = 0

    def sum_workorder_ocr_cost(self, cur, *, tenant_id, item_ids):
        val = self._sums[min(self._i, len(self._sums) - 1)]
        self._i += 1
        return val


class ClassifyQuotaDeferTests(unittest.TestCase):
    """R1 件二 验收:撞配额退避用尽 → 该件 flagged ocr_error:quota + 整步 stuck 待续;
    续跑复位 pending 重烧到完成(不双计)。"""

    def setUp(self):
        classify._resolve_own_tax_id = lambda ctx: OWN_TAX
        classify._resolve_own_name = lambda ctx: OWN_NAME
        for k, v in (
            ("PEARNLY_WORKORDER_OCR_QUOTA_BACKOFF_SECONDS", "0"),
            ("PEARNLY_WORKORDER_OCR_QUOTA_MAX_ATTEMPTS", "3"),
            ("PEARNLY_WORKORDER_OCR_CONCURRENCY", "1"),
        ):
            os.environ[k] = v
            self.addCleanup(os.environ.pop, k, None)
        self.addCleanup(
            setattr, classify, "_resolve_own_tax_id", classify._default_resolve_own_tax_id
        )
        self.addCleanup(setattr, classify, "_resolve_own_name", classify._default_resolve_own_name)
        self.addCleanup(setattr, classify, "_ocr_image", classify._default_ocr_image)

    def test_quota_exhausted_defers_then_resume_completes(self):
        item = _item("i1", "/in/q.jpg")
        store = FakeItemStore([item])
        attempts = {"n": 0}

        def quota_ocr(path):
            attempts["n"] += 1
            raise _QuotaBoom("layer2: gateway (quota)")

        classify._ocr_image = quota_ocr
        out = classify.run(_ctx(store))

        self.assertEqual(out.status, "stuck")
        self.assertTrue(any(str(r).startswith("ocr_quota_deferred") for r in out.reasons))
        row = store.by_id("i1")
        self.assertEqual(row["status"], "flagged")
        self.assertEqual(row["flag_reason"], "ocr_error:quota")
        self.assertIsNone(store.classified("i1"))  # 无终局证据事件(免 dedupe 锁死错值)
        self.assertEqual(attempts["n"], 3)  # 首读 + 2 退避重试 = max_attempts

        # 恢复:配额过了,续跑复位 pending → 重烧成功 → 归堆完成。
        classify._ocr_image = lambda path: _purchase_fields()
        out2 = classify.run(_ctx(store))
        self.assertEqual(out2.status, "ok")
        row2 = store.by_id("i1")
        self.assertEqual(row2["status"], "ok")
        self.assertEqual(row2["kind"], "purchase_invoice")
        self.assertIsNone(row2["flag_reason"])  # 复位清了 quota 待补的 reason
        self.assertIsNotNone(store.classified("i1"))  # 这次落了终局证据


class ClassifyCostCapTests(unittest.TestCase):
    """R1 件三 验收:OCR 累计成本达 cap → 停投料、run 落 stuck ocr_cost_cap_exceeded、
    未处理件仍 pending(非 failed);续跑(预算放宽)跑完。"""

    def setUp(self):
        classify._resolve_own_tax_id = lambda ctx: OWN_TAX
        classify._resolve_own_name = lambda ctx: OWN_NAME
        for k, v in (
            ("PEARNLY_WORKORDER_OCR_COST_CAP_THB", "100"),
            ("PEARNLY_WORKORDER_OCR_CONCURRENCY", "1"),
        ):
            os.environ[k] = v
            self.addCleanup(os.environ.pop, k, None)
        classify._ocr_image = lambda path: _purchase_fields(
            invoice_no=f"IV{abs(hash(path)) % 10000}", seller=f"1{abs(hash(path)) % 10**12:012d}"
        )
        self.addCleanup(
            setattr, classify, "_resolve_own_tax_id", classify._default_resolve_own_tax_id
        )
        self.addCleanup(setattr, classify, "_resolve_own_name", classify._default_resolve_own_name)
        self.addCleanup(setattr, classify, "_ocr_image", classify._default_ocr_image)

    def _capped_ctx(self, store):
        # 封顶只在带 cursor_factory 的按步提交形态启用(预算读走独立短事务,免攥长锁死锁)。
        return StepContext(
            cur=None,
            tenant_id="t-1",
            work_order_id="wo-1",
            store=store,
            data={},
            cursor_factory=_UnitCM,
        )

    def test_cost_cap_stucks_and_leaves_rest_pending_then_resumes(self):
        items = [_item(f"i{k}", f"/in/{k}.jpg") for k in range(3)]
        # 人工 run 基线读一次(0),之后 item0→60(<100)、item1→130(>=100 停投料)。
        store = _CostStore(items, sums=[0.0, 60.0, 130.0])
        out = classify.run(self._capped_ctx(store))

        self.assertEqual(out.status, "stuck")
        self.assertIn("ocr_cost_cap_exceeded", out.reasons)
        # 未处理件留 pending(不是 failed);已处理件正常归堆。
        self.assertEqual(store.by_id("i2")["status"], "pending")
        self.assertEqual(store.by_id("i0")["status"], "ok")
        self.assertEqual(store.by_id("i1")["status"], "ok")

        # 续跑放宽预算(台账不再长)→ 剩余件跑完。
        os.environ["PEARNLY_WORKORDER_OCR_COST_CAP_THB"] = "100000"
        out2 = classify.run(self._capped_ctx(store))
        self.assertEqual(out2.status, "ok")
        self.assertEqual(store.by_id("i2")["status"], "ok")


if __name__ == "__main__":
    unittest.main()
