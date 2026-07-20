# -*- coding: utf-8 -*-
"""人工填销项(W4)端到端形状契约:api.record_sales_summary 落的 item_classified 事件,
reconcile 的 _replay_sales_reads / aggregate_sales **原样回放解锁 R2**——证明引擎/steps
不改一行也能吃到人工销项。全程内存 FakeStore,不碰库/OCR/密钥。

若 record_sales_summary 产出的 sales_read 形状与 reconcile 消费契约有半点错位,这个测试
会红——它是「事件形状以 reconcile 回放为准」这条约束的机械守门。
"""

import unittest
from decimal import Decimal

from services.workorder import api, evidence
from services.workorder.engine import StepContext
from services.workorder.steps import reconcile
from tests.unit._workorder_fakes import WorkOrderFakeStoreBase

# 金标(T0 官方申报数):销售额 / 销项税 → 应缴 = 60114.61 − 进项 29263.28 = 30851.33。
GOLDEN_SALES_AMOUNT = Decimal("858780.16")
GOLDEN_OUTPUT_VAT = Decimal("60114.61")


class _RecordingStore(WorkOrderFakeStoreBase):
    """record_sales_summary 需要的 store 替身:add_item(幂等)继承共享基类,append_event
    新增即并入 self.events——reconcile.run() 靠 list_events() 立刻看到,验回放解锁。"""

    def __init__(self):
        super().__init__()
        self.events = []

    def _on_event_appended(self, row):
        self.events.append(row)

    # reconcile.run 用到的读侧
    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(i) for i in self.items if status is None or i["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]


def _purchase_item(store):
    """一张 ok 进项票 + 其票面金额事件(让 R1 有可算内容,好让 R2 被真正触达)。"""
    item = store.add_item(
        None,
        tenant_id="t-1",
        work_order_id="wo-1",
        source="upload",
        kind="purchase_invoice",
        status="ok",
        dedupe_key="doc:pi-1",
    )
    store.append_event(
        None,
        tenant_id="t-1",
        work_order_id="wo-1",
        step="classify",
        event_type="item_classified",
        payload={
            "item_id": item["id"],
            "kind": "purchase_invoice",
            "status": "ok",
            "money": {
                "subtotal": "1000.00",
                "vat": "70.00",
                "total_amount": "1070.00",
                "invoice_number": "IV-1",
                "seller_tax": "0735527000289",
            },
        },
    )


def _ctx(store):
    return StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data={})


class ManualSalesUnlocksR2Tests(unittest.TestCase):
    def setUp(self):
        # record_sales_summary 走 api 模块级 store(add_item/append_event);注入内存替身,
        # reconcile 那侧读同一份 store(ctx.store),两侧共享事件流才能验回放解锁。
        self.store = _RecordingStore()
        self._orig = api.store
        api.store = self.store
        self.addCleanup(setattr, api, "store", self._orig)

    def _record(self, sales, vat, note="", source_label=None):
        api.record_sales_summary(
            None,
            tenant_id="t-1",
            work_order_id="wo-1",
            sales_amount=sales,
            output_vat=vat,
            note=note,
            actor="user:9",
            source_label=source_label,
        )

    def test_missing_sales_summary_blocks_r2(self):
        """人工填之前:无销项直读源 → reconcile 停在 needs(['sales_summary'])。"""
        _purchase_item(self.store)
        out = reconcile.run(_ctx(self.store))
        self.assertEqual(out.status, "needs")
        self.assertEqual(out.missing, ("sales_summary",))

    def test_manual_entry_unlocks_r2_with_golden_totals(self):
        """人工填销项后:同一 store 再跑 reconcile → R2 解锁,销售额/销项税 = 金标。"""
        _purchase_item(self.store)
        self._record(
            str(GOLDEN_SALES_AMOUNT),
            str(GOLDEN_OUTPUT_VAT),
            note="ยื่นเอง · แนบสรุปยอดขายจากธนาคาร",
        )
        out = reconcile.run(_ctx(self.store))
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["sales_amount_total"]), GOLDEN_SALES_AMOUNT)
        self.assertEqual(Decimal(out.payload["output_vat_total"]), GOLDEN_OUTPUT_VAT)

    def test_refill_latest_value_wins_no_double_count(self):
        """先填错(翻倍)再改正:latest-wins 覆盖,不重复计入 → 只认最新的金标值。"""
        _purchase_item(self.store)
        self._record("1717560.32", "120229.22")
        self._record(str(GOLDEN_SALES_AMOUNT), str(GOLDEN_OUTPUT_VAT))
        out = reconcile.run(_ctx(self.store))
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["sales_amount_total"]), GOLDEN_SALES_AMOUNT)
        self.assertEqual(Decimal(out.payload["output_vat_total"]), GOLDEN_OUTPUT_VAT)


class MultiSourceManualSalesTests(ManualSalesUnlocksR2Tests):
    """多来源销项:一个月的销项常来自多张表(自开票 / 7-11 / Big C),必须能并存相加。

    继承上面的 setUp/_record(同一份 store 替身与录入口),只加多来源用例——单来源的
    向后兼容断言仍由父类那几条守住。
    """

    def test_three_sources_coexist_and_sum(self):
        _purchase_item(self.store)
        self._record("100000.00", "7000.00", source_label="ใบกำกับเอง")
        self._record("200000.00", "14000.00", source_label="7-11")
        self._record("300000.00", "21000.00", source_label="Big C")
        out = reconcile.run(_ctx(self.store))
        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["sales_amount_total"]), Decimal("600000.00"))
        self.assertEqual(Decimal(out.payload["output_vat_total"]), Decimal("42000.00"))
        self.assertEqual(len([i for i in self.store.items if i["kind"] == "sales_summary"]), 3)

    def test_same_source_refill_overwrites_not_adds(self):
        _purchase_item(self.store)
        self._record("100000.00", "7000.00", source_label="7-11")
        self._record("111111.11", "7777.78", source_label="7-11")
        self._record("200000.00", "14000.00", source_label="Big C")
        out = reconcile.run(_ctx(self.store))
        self.assertEqual(Decimal(out.payload["sales_amount_total"]), Decimal("311111.11"))
        self.assertEqual(len([i for i in self.store.items if i["kind"] == "sales_summary"]), 2)

    def test_unlabeled_shares_the_legacy_slot(self):
        """不带来源 = 现状那一条固定槽:重填覆盖,不新开件。"""
        _purchase_item(self.store)
        self._record("100000.00", "7000.00")
        self._record("200000.00", "14000.00")
        out = reconcile.run(_ctx(self.store))
        self.assertEqual(Decimal(out.payload["sales_amount_total"]), Decimal("200000.00"))
        self.assertEqual(len([i for i in self.store.items if i["kind"] == "sales_summary"]), 1)

    def test_blank_label_is_the_legacy_slot(self):
        """路由默认传空串,必须等价于不带来源(不许开出一条 `manual:sales_summary:` 幽灵槽)。"""
        _purchase_item(self.store)
        self._record("100000.00", "7000.00")
        self._record("200000.00", "14000.00", source_label="   ")
        self.assertEqual(len([i for i in self.store.items if i["kind"] == "sales_summary"]), 1)

    def test_label_recorded_on_payload_for_audit(self):
        _purchase_item(self.store)
        self._record("100000.00", "7000.00", source_label=" 7-11  สาขาบางนา ")
        read = self.store.events[-1]["payload"]["sales_read"]
        self.assertEqual(read["source_label"], "7-11 สาขาบางนา")
        self.assertEqual(read["source"], "manual_entry")

    def test_overlong_label_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as cm:
            self._record("1.00", "0.07", source_label="x" * 61)
        self.assertEqual(cm.exception.code, "workorder.sales_summary_source_too_long")


class SalesSourceInfoTests(unittest.TestCase):
    """evidence.sales_source_info 的 direct_read / manual_entry / mixed 判定不被多来源打乱。"""

    @staticmethod
    def _classified(*sources):
        return {
            f"i{n}": {
                "payload": {
                    "kind": "sales_summary",
                    "status": "ok",
                    "sales_read": {"source": src} if src else {},
                }
            }
            for n, src in enumerate(sources)
        }

    def test_two_manual_sources_still_manual(self):
        info = evidence.sales_source_info(self._classified("manual_entry", "manual_entry"), {})
        self.assertEqual(info["source"], "manual_entry")

    def test_manual_plus_direct_read_is_mixed(self):
        info = evidence.sales_source_info(self._classified("manual_entry", None), {})
        self.assertEqual(info["source"], "mixed")

    def test_direct_read_only(self):
        info = evidence.sales_source_info(self._classified(None, None), {})
        self.assertEqual(info["source"], "direct_read")


if __name__ == "__main__":
    unittest.main()
