# -*- coding: utf-8 -*-
"""OCR 跨单去重(R2B · 钱路径)· ocr_reuse 纯装配层 + classify 复用集成。

锁契约:哈希取回、闸字段完整性判据、严格作用域(跨客户/无归属不复用)、复用零 OCR + 事件标
ocr_reused_from、复用路仍双写台账。真库集成(同文件先后进两单)在真机验,这里用注入替身锁逻辑
——复用路径绝不触 _ocr_image(付费调用),从而零 ai_usage(成本落点在 _ocr_safe 的 OCR 调用)。
"""

from __future__ import annotations

import unittest

from services.workorder.engine import StepContext
from services.workorder.steps import classify, ocr_reuse


def _page(fields, *, warnings=None, needs=False, band="high", engine="vX", drop=None):
    page = {
        "fields": dict(fields),
        "is_copy": False,
        "is_duplicate": False,
        "_validation_warnings": list(warnings or []),
        "_needs_review": needs,
        "_confidence_band": band,
        "_ocr_engine": engine,
    }
    if drop:
        page.pop(drop, None)  # 造「老记录缺闸字段」
    return page


class FileHashOfTests(unittest.TestCase):
    def test_strips_file_prefix(self):
        self.assertEqual(ocr_reuse.file_hash_of({"dedupe_key": "file:abc123"}), "abc123")

    def test_non_file_prefix_none(self):
        self.assertIsNone(ocr_reuse.file_hash_of({"dedupe_key": "manual:sales"}))
        self.assertIsNone(ocr_reuse.file_hash_of({}))


class RebuildFieldsTests(unittest.TestCase):
    def test_rebuilds_business_and_gate_fields(self):
        page = _page(
            {"seller_tax": "07355", "vat": "7.00"}, warnings=["低置信"], needs=True, band="mid"
        )
        got = ocr_reuse.rebuild_fields(page)
        self.assertEqual(got["seller_tax"], "07355")
        self.assertEqual(got["_validation_warnings"], ["低置信"])
        self.assertTrue(got["_needs_review"])
        self.assertEqual(got["_confidence_band"], "mid")
        self.assertEqual(got["_ocr_engine"], "vX")

    def test_missing_gate_key_not_reusable(self):
        # 老记录 / 主站散单台账缺闸字段 → None(不复用,照常 OCR,诚实不吞报警)。
        self.assertIsNone(ocr_reuse.rebuild_fields(_page({"vat": "7"}, drop="_confidence_band")))
        self.assertIsNone(ocr_reuse.rebuild_fields(_page({"vat": "7"}, drop="_needs_review")))
        self.assertIsNone(ocr_reuse.rebuild_fields(None))


class ResolveTests(unittest.TestCase):
    _OWNER = {"user_id": "u-9", "workspace_client_id": 7, "tenant_id": "t-1"}

    def test_no_owner_returns_empty(self):
        self.assertEqual(ocr_reuse.resolve([{"id": "i1"}], None, finder=lambda **k: None), {})

    def test_non_file_item_skipped(self):
        calls = []
        ocr_reuse.resolve(
            [{"id": "i1", "dedupe_key": "manual:x"}],
            self._OWNER,
            finder=lambda **k: calls.append(k),
        )
        self.assertEqual(calls, [])  # 无 file: 哈希 → 不查库

    def test_hit_with_complete_gate_is_reusable(self):
        rec = {"id": "h-1", "pages": [_page({"vat": "7.00"})]}
        got = ocr_reuse.resolve(
            [{"id": "i1", "dedupe_key": "file:h"}], self._OWNER, finder=lambda **k: rec
        )
        self.assertEqual(got["i1"]["history_id"], "h-1")
        self.assertEqual(got["i1"]["fields"]["vat"], "7.00")

    def test_scope_is_strict_same_workspace(self):
        seen = {}
        ocr_reuse.resolve(
            [{"id": "i1", "dedupe_key": "file:h"}],
            self._OWNER,
            finder=lambda **k: seen.update(k),
        )
        self.assertEqual(seen["workspace_client_id"], 7)
        self.assertEqual(seen["tenant_id"], "t-1")

    def test_incomplete_gate_not_reused(self):
        rec = {"id": "h-1", "pages": [_page({"vat": "7"}, drop="_validation_warnings")]}
        got = ocr_reuse.resolve(
            [{"id": "i1", "dedupe_key": "file:h"}], self._OWNER, finder=lambda **k: rec
        )
        self.assertEqual(got, {})

    def test_finder_error_degrades_to_no_hit(self):
        def _boom(**k):
            raise RuntimeError("db down")

        got = ocr_reuse.resolve([{"id": "i1", "dedupe_key": "file:h"}], self._OWNER, finder=_boom)
        self.assertEqual(got, {})  # 查库失败=未命中,照常 OCR


class StreamTests(unittest.TestCase):
    def test_original_order_reused_and_ocr_interleave(self):
        images = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        reused = {"b": {"fields": {"x": 1}, "history_id": "h-b"}}

        def _ocr_gen(batch):  # 生产 factory 回吐生成器(有 .close(),供收尾取消在飞 OCR)
            for it in batch:
                yield it, {"ocr": it["id"].upper()}

        got = list(ocr_reuse.stream(images, reused, _ocr_gen))
        self.assertEqual(
            [(it["id"], reused_from) for it, _, reused_from in got],
            [("a", None), ("b", "h-b"), ("c", None)],
        )
        self.assertEqual(got[1][1], {"x": 1})  # b 直接给缓存 fields


class _ReuseStore:
    """classify 复用集成用内存 store。"""

    def __init__(self, items):
        self.items = items
        self.events = []

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        return {"workspace_client_id": 7}

    def reset_quota_deferred_items(self, cur, *, tenant_id, work_order_id, flag_reason):
        return 0

    def sum_workorder_ocr_cost(self, cur, *, tenant_id, item_ids):
        return 0.0

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]

    def update_item(
        self,
        cur,
        *,
        tenant_id,
        item_id,
        status=None,
        kind=None,
        flag_reason=None,
        ocr_history_id=None,
    ):
        it = next(i for i in self.items if i["id"] == item_id)
        it["status"] = status
        if kind is not None:
            it["kind"] = kind

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
        return self.events[-1]


class ClassifyReuseIntegration(unittest.TestCase):
    """件一验收 1-3:复用零 OCR + 事件标 ocr_reused_from / 跨客户不串 / 缺闸字段不复用。"""

    _CACHED_FIELDS = {
        "seller_tax": "0735527000289",
        "buyer_tax": "0105567178203",
        "invoice_number": "IV001",
        "subtotal": "100.00",
        "vat": "7.00",
        "total_amount": "107.00",
    }

    def setUp(self):
        names = (
            "_resolve_own_tax_id",
            "_resolve_own_name",
            "_resolve_own_names",
            "_m1_enabled",
            "_resolve_history_owner",
            "_record_ocr_history",
            "_find_ocr_by_hash",
            "_ocr_image",
        )
        saved = {n: getattr(classify, n) for n in names}
        self.addCleanup(lambda: [setattr(classify, n, v) for n, v in saved.items()])
        classify._resolve_own_tax_id = lambda ctx: "0105567178203"
        classify._resolve_own_name = lambda ctx: None
        classify._resolve_own_names = lambda ctx: []
        classify._m1_enabled = lambda ctx: False
        classify._resolve_history_owner = lambda ctx: {
            "user_id": "u",
            "workspace_client_id": 7,
            "tenant_id": "t-1",
        }
        classify._record_ocr_history = lambda item, fields, owner: f"h-{item['id']}"
        self.ocr_calls = []
        classify._ocr_image = lambda path: self.ocr_calls.append(path) or dict(self._CACHED_FIELDS)

    def _run(self, finder):
        classify._find_ocr_by_hash = finder
        store = _ReuseStore(
            [
                {
                    "id": "i1",
                    "file_ref": "/in/a.jpg",
                    "dedupe_key": "file:hh",
                    "kind": "unknown",
                    "status": "pending",
                    "flag_reason": None,
                }
            ]
        )
        classify.run(StepContext(cur=object(), tenant_id="t-1", work_order_id="wo-1", store=store))
        return store

    def _cached_record(self, **page_kw):
        return {"id": "h-cached", "pages": [_page(self._CACHED_FIELDS, **page_kw)]}

    def test_reuse_zero_ocr_and_event_marked(self):
        store = self._run(finder=lambda **k: self._cached_record())
        self.assertEqual(self.ocr_calls, [])  # 复用件绝不触 OCR(零 ai_usage)
        evt = next(e for e in store.events if e["event_type"] == "item_classified")
        self.assertEqual(evt["payload"]["ocr_reused_from"], "h-cached")
        self.assertEqual(store.items[0]["kind"], "purchase_invoice")  # 照常归堆

    def test_cross_client_miss_falls_back_to_ocr(self):
        # 严格作用域下跨客户查不到 → finder 返 None → 照常 OCR,事件不标复用。
        store = self._run(finder=lambda **k: None)
        self.assertEqual(self.ocr_calls, ["/in/a.jpg"])
        evt = next(e for e in store.events if e["event_type"] == "item_classified")
        self.assertNotIn("ocr_reused_from", evt["payload"])

    def test_stale_record_missing_gate_not_reused(self):
        store = self._run(finder=lambda **k: self._cached_record(drop="_confidence_band"))
        self.assertEqual(self.ocr_calls, ["/in/a.jpg"])  # 缺闸字段 → 照常 OCR


if __name__ == "__main__":
    unittest.main()
