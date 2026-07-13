# -*- coding: utf-8 -*-
"""工单 OCR ↔ ocr_history 识别台账双写守门(services/workorder/steps/ocr_ledger.py · MC2-A2 ②)。

脱库:验证归属解析(工单→账套 owner user)+ 双写调 insert_ocr_history 的载荷形状 + 旁路
优雅降级(无归属/解析出错→None,绝不拖垮 classify)。真 DB 写在集成/真机验,这里只锁契约。
另含 classify 集成:双写落的 ocr_history 行字段与事件流 item_classified 的钱字段同源一致。
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from typing import Any
from unittest import mock

from services.workorder.engine import StepContext
from services.workorder.steps import classify, ocr_ledger


class _Cur:
    def __init__(self, row):
        self._row = row
        self.sql = None

    def execute(self, sql, params):
        self.sql = sql
        self.params = params

    def fetchone(self):
        return self._row


@dataclass
class _Store:
    wo: Any = None
    raises: bool = False

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        if self.raises:
            raise RuntimeError("db down")
        return self.wo


def _ctx(store, cur):
    return StepContext(cur=cur, tenant_id="t-1", work_order_id="wo-1", store=store)


class ResolveOwnerTests(unittest.TestCase):
    def test_resolves_owner_from_workspace_client(self):
        ctx = _ctx(_Store(wo={"workspace_client_id": 7}), _Cur({"user_id": "u-9"}))
        owner = ocr_ledger.resolve_owner(ctx)
        self.assertEqual(owner, {"user_id": "u-9", "workspace_client_id": 7, "tenant_id": "t-1"})

    def test_none_when_no_client(self):
        ctx = _ctx(_Store(wo={"workspace_client_id": None}), _Cur(None))
        self.assertIsNone(ocr_ledger.resolve_owner(ctx))

    def test_none_when_no_owner_user(self):
        ctx = _ctx(_Store(wo={"workspace_client_id": 7}), _Cur({"user_id": None}))
        self.assertIsNone(ocr_ledger.resolve_owner(ctx))

    def test_query_error_degrades_to_none(self):
        # 归属解析失败=旁路优雅跳过,绝不上抛拖垮 classify。
        ctx = _ctx(_Store(raises=True), _Cur(None))
        self.assertIsNone(ocr_ledger.resolve_owner(ctx))


class RecordTests(unittest.TestCase):
    def test_none_owner_skips_write(self):
        self.assertIsNone(ocr_ledger.record({"id": "i1"}, {"total_amount": "107"}, None))

    def test_writes_clean_fields_and_returns_id(self):
        owner = {"user_id": "u-9", "workspace_client_id": 7, "tenant_id": "t-1"}
        item = {"id": "i1", "file_ref": "/in/a.jpg", "original_name": "a.jpg"}
        fields = {
            "total_amount": "107.00",
            "vat": "7.00",
            "_needs_review": True,
            "_ocr_engine": "v9",
        }
        with mock.patch("core.db.insert_ocr_history", return_value="h-1") as ins:
            got = ocr_ledger.record(item, fields, owner)
        self.assertEqual(got, "h-1")
        kw = ins.call_args.kwargs
        self.assertEqual(kw["user_id"], "u-9")
        self.assertEqual(kw["workspace_client_id"], 7)
        self.assertEqual(kw["tenant_id"], "t-1")
        self.assertEqual(kw["source"], "workorder_classify")
        self.assertEqual(kw["source_ref"], "i1")
        # 内部下划线字段被剥掉,只留真读值。
        self.assertEqual(kw["pages"][0]["fields"], {"total_amount": "107.00", "vat": "7.00"})

    def test_insert_failure_degrades_to_none(self):
        owner = {"user_id": "u-9", "workspace_client_id": 7, "tenant_id": "t-1"}
        with mock.patch("core.db.insert_ocr_history", side_effect=RuntimeError("boom")):
            self.assertIsNone(ocr_ledger.record({"id": "i1"}, {"total_amount": "1"}, owner))


class _ClassifyStore:
    """classify 集成用内存 store:含 get_work_order + cur 查 owner + update_item(收 ocr_history_id)。"""

    def __init__(self, items):
        self.items = items
        self.events = []

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        return {"workspace_client_id": 7}

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
        it["kind"] = kind if kind is not None else it["kind"]
        it["ocr_history_id"] = ocr_history_id

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


class ClassifyDoubleWriteIntegration(unittest.TestCase):
    """件 1 验收:classify 落库时 ocr_history_id 回填,且台账 fields 与事件流钱字段同源一致。"""

    def setUp(self):
        self._saved = {
            n: getattr(classify, n)
            for n in (
                "_ocr_image",
                "_resolve_own_tax_id",
                "_resolve_own_name",
                "_resolve_own_names",
                "_m1_enabled",
                "_record_ocr_history",
            )
        }
        self.addCleanup(lambda: [setattr(classify, n, v) for n, v in self._saved.items()])
        classify._resolve_own_tax_id = lambda ctx: "0105567178203"
        classify._resolve_own_name = lambda ctx: None
        classify._resolve_own_names = lambda ctx: []
        classify._m1_enabled = lambda ctx: False
        classify._ocr_image = lambda path: {
            "document_type": "tax_invoice",
            "buyer_tax": "0105567178203",
            "seller_tax": "0735527000289",
            "invoice_number": "IV001",
            "subtotal": "100.00",
            "vat": "7.00",
            "total_amount": "107.00",
        }
        self.records = []

        def _rec(item, fields, owner):
            self.records.append({"item": item["id"], "fields": fields, "owner": owner})
            return f"h-{item['id']}"

        classify._record_ocr_history = _rec

    def test_ocr_history_id_backfilled_and_consistent_with_event_money(self):
        store = _ClassifyStore(
            [
                {
                    "id": "i1",
                    "file_ref": "/in/a.jpg",
                    "kind": "unknown",
                    "status": "pending",
                    "flag_reason": None,
                },
            ]
        )
        # 内存模式 cur 复用整步:给个能解 owner user 的假游标(resolve_owner 查 workspace_clients)。
        cur = _Cur({"user_id": "u-9"})
        classify.run(StepContext(cur=cur, tenant_id="t-1", work_order_id="wo-1", store=store))
        # 回填:item.ocr_history_id 非空。
        self.assertEqual(store.items[0]["ocr_history_id"], "h-i1")
        # owner 由 get_work_order 解析出,双写被调一次。
        self.assertEqual(len(self.records), 1)
        self.assertEqual(self.records[0]["owner"]["workspace_client_id"], 7)
        # 一致性:台账拿到的 fields 与事件流 item_classified.money 同源同值。
        evt = next(e for e in store.events if e["event_type"] == "item_classified")
        self.assertEqual(evt["payload"]["money"]["total_amount"], "107.00")
        self.assertEqual(self.records[0]["fields"]["total_amount"], "107.00")


if __name__ == "__main__":
    unittest.main()
