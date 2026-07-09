# -*- coding: utf-8 -*-
"""compute 步守门测试(services/workorder/steps/compute.py · 任务包 §5 步 5 / §6)。

全程内存 FakeStore,不碰库。覆盖:应缴精确算对(金标)、留抵负数如实不 clamp、续跑场景
从事件流回放 reconcile 数字(ctx.data 为空)、缺 reconcile 数字 needs、上期波动检查
(有上期比出 delta / 没有上期诚实记 no_prior_period)、幂等重跑同数字。
"""

import unittest
from decimal import Decimal

from services.workorder.engine import StepContext
from services.workorder.steps import compute

# 金标常量(T0 语料盘点):应缴 = 销项税 60114.61 − 进项税 29263.28。
GOLDEN_OUTPUT_VAT = "60114.61"
GOLDEN_INPUT_VAT = "29263.28"
GOLDEN_TAX_DUE = Decimal("30851.33")


class FakeStore:
    def __init__(self, *, events=None, work_order=None, deliverables=None):
        self.events = events or []
        self.work_order = work_order or {
            "id": "wo-1",
            "workspace_client_id": 1,
            "period": "2569-05",
            "intent": "monthly_vat",
        }
        self.deliverables = deliverables or {}

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        return dict(self.work_order)

    def list_deliverables(self, cur, *, tenant_id, work_order_id):
        return list(self.deliverables.get(work_order_id, []))


def _reconcile_done_event(**overrides):
    payload = {
        "input_vat_total": GOLDEN_INPUT_VAT,
        "purchase_amount_total": "418046.86",
        "sales_amount_total": "858780.16",
        "output_vat_total": GOLDEN_OUTPUT_VAT,
        "gates": {},
    }
    payload.update(overrides)
    return {"id": 9, "step": "reconcile", "event_type": "step_done", "payload": payload}


def _ctx(store, data=None):
    return StepContext(
        cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data=data or {}
    )


def _no_prior(ctx, **kwargs):
    return None


class TaxDueTests(unittest.TestCase):
    def setUp(self):
        compute._resolve_prior_work_order_id = _no_prior
        self.addCleanup(
            setattr,
            compute,
            "_resolve_prior_work_order_id",
            compute._default_resolve_prior_work_order_id,
        )

    def test_golden_tax_due_matches_official_pp30(self):
        data = {
            "input_vat_total": GOLDEN_INPUT_VAT,
            "purchase_amount_total": "418046.86",
            "sales_amount_total": "858780.16",
            "output_vat_total": GOLDEN_OUTPUT_VAT,
        }
        out = compute.run(_ctx(FakeStore(), data=data))

        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["tax_due"]), GOLDEN_TAX_DUE)
        self.assertEqual(out.payload["sales_amount"], "858780.16")
        self.assertEqual(out.payload["output_vat"], GOLDEN_OUTPUT_VAT)
        self.assertEqual(out.payload["purchase_amount"], "418046.86")
        self.assertEqual(out.payload["input_vat"], GOLDEN_INPUT_VAT)
        self.assertEqual(out.payload["period"], "2569-05")

    def test_input_vat_exceeds_output_vat_reports_negative_not_clamped(self):
        data = {
            "input_vat_total": "500.00",
            "purchase_amount_total": "7142.86",
            "sales_amount_total": "1000.00",
            "output_vat_total": "70.00",
        }
        out = compute.run(_ctx(FakeStore(), data=data))

        self.assertEqual(out.status, "ok")
        self.assertEqual(out.payload["tax_due"], "-430.00")

    def test_resume_scenario_replays_reconcile_numbers_from_event_stream(self):
        """续跑:ctx.data 为空(重启丢内存),数字必须从 reconcile 的 step_done 回放,
        与一次跑完全一致——照 reconcile.py 自身的断点续跑范式。"""
        store = FakeStore(events=[_reconcile_done_event()])
        out = compute.run(_ctx(store, data={}))

        self.assertEqual(out.status, "ok")
        self.assertEqual(Decimal(out.payload["tax_due"]), GOLDEN_TAX_DUE)

    def test_missing_reconcile_numbers_needs(self):
        out = compute.run(_ctx(FakeStore(events=[]), data={}))

        self.assertEqual(out.status, "needs")
        self.assertTrue(any("input_vat_total" in m for m in out.missing))

    def test_rerun_yields_same_tax_due(self):
        data = {
            "input_vat_total": GOLDEN_INPUT_VAT,
            "purchase_amount_total": "418046.86",
            "sales_amount_total": "858780.16",
            "output_vat_total": GOLDEN_OUTPUT_VAT,
        }
        store = FakeStore()
        first = compute.run(_ctx(store, data=dict(data)))
        second = compute.run(_ctx(store, data=dict(data)))
        self.assertEqual(first.payload["tax_due"], second.payload["tax_due"])


class PriorPeriodCheckTests(unittest.TestCase):
    def setUp(self):
        self._reconcile_data = {
            "input_vat_total": GOLDEN_INPUT_VAT,
            "purchase_amount_total": "418046.86",
            "sales_amount_total": "858780.16",
            "output_vat_total": GOLDEN_OUTPUT_VAT,
        }

    def tearDown(self):
        compute._resolve_prior_work_order_id = compute._default_resolve_prior_work_order_id

    def test_no_prior_work_order_records_honestly(self):
        compute._resolve_prior_work_order_id = lambda ctx, **kw: None
        out = compute.run(_ctx(FakeStore(), data=self._reconcile_data))

        self.assertEqual(out.payload["prior_period_check"], {"status": "no_prior_period"})

    def test_prior_period_found_reports_delta_without_blocking(self):
        compute._resolve_prior_work_order_id = lambda ctx, **kw: "wo-prior"
        store = FakeStore(
            deliverables={
                "wo-prior": [
                    {"kind": "pp30_draft", "numbers": {"tax_due": "25000.00"}},
                ]
            }
        )
        out = compute.run(_ctx(store, data=self._reconcile_data))

        check = out.payload["prior_period_check"]
        self.assertEqual(check["status"], "compared")
        self.assertEqual(check["prior_period"], "2569-04")
        self.assertEqual(check["prior_tax_due"], "25000.00")
        self.assertEqual(Decimal(check["delta"]), GOLDEN_TAX_DUE - Decimal("25000.00"))
        # 只记录不拦:即使波动很大,步仍是 ok。
        self.assertEqual(out.status, "ok")

    def test_prior_work_order_without_pp30_deliverable_records_honestly(self):
        compute._resolve_prior_work_order_id = lambda ctx, **kw: "wo-prior"
        store = FakeStore(deliverables={"wo-prior": []})
        out = compute.run(_ctx(store, data=self._reconcile_data))

        self.assertEqual(out.payload["prior_period_check"], {"status": "no_prior_period"})

    def test_january_period_shifts_to_prior_december(self):
        compute._resolve_prior_work_order_id = lambda ctx, **kw: None
        store = FakeStore(
            work_order={
                "id": "wo-1",
                "workspace_client_id": 1,
                "period": "2569-01",
                "intent": "monthly_vat",
            }
        )
        out = compute.run(_ctx(store, data=self._reconcile_data))
        self.assertEqual(out.payload["period"], "2569-01")
        self.assertEqual(compute._shift_period("2569-01"), "2568-12")


if __name__ == "__main__":
    unittest.main()
