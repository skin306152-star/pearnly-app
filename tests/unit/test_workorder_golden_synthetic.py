# -*- coding: utf-8 -*-
"""工单制 L1 合成金标全链路测试(M0 任务包 §6 · CI 每次 push 必跑)。

不碰真库/真 OCR/真语料:内存 FakeStore(work_orders/items/events/deliverables 四表
语义)驱动 engine.run_work_order(ctx, handlers=real_handlers()) 跑完整条流水线
(intake→sort→classify→reconcile→compute→package)。合成语料在 tempdir 现造:openpyxl
造一份销项汇总表,文件名信号造一份银行单,3 张"进项票"靠 patch classify._ocr_image
免真 OCR(1 正常 / 1 与正常票同票号→duplicate / 1 金额自洽性报警→amount_math_fail)。

只 patch 两处"真库/真钱"入口:classify._resolve_own_tax_id(锚点查询要连真库)、
classify._ocr_image(真调是付费 OCR);compute._resolve_prior_work_order_id 也 patch
掉(默认实现直接对 cur 发 SQL,FakeStore 场景没有真游标)。其余全部走生产代码路径——
sort 的文件名/表头判定、classify 的销项直读(真 parse_table)、reconcile 的四道闸、
compute 的减法、package 的五件套落盘、evidence 的证据索引,零 mock。
"""

from __future__ import annotations

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from typing import Optional

import openpyxl

from services.workorder import engine
from services.workorder.engine import StepContext, StepResult
from services.workorder.steps import classify, compute
from services.workorder.steps import real_handlers

OWN_TAX = "0105567178203"
OTHER_TAX = "0735527000289"

GOOD_NET, GOOD_VAT, GOOD_TOTAL = Decimal("1000.00"), Decimal("70.00"), Decimal("1070.00")
DISPUTED_NET = Decimal("500.00")
DISPUTED_FACE_VAT, DISPUTED_TOTAL = Decimal("45.00"), Decimal("545.00")
DISPUTED_RECALC_VAT = Decimal("35.00")
SALES_AMOUNT, OUTPUT_VAT = Decimal("10000.00"), Decimal("700.00")


class FakeStore:
    """work_orders/items/events/deliverables 四表的内存实现,语义对齐真 store.py:
    add_item/upsert_deliverable 按幂等键覆盖,work_order_events 只追加。"""

    def __init__(self):
        self._item_seq = 0
        self._evt_seq = 0
        self.work_orders: dict = {}
        self.items: list = []
        self.events: list = []
        self.deliverables: dict = {}

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        wo = self.work_orders.get(work_order_id)
        return dict(wo) if wo else None

    def set_status(self, cur, *, tenant_id, work_order_id, status, current_step=None):
        wo = self.work_orders[work_order_id]
        wo["status"] = status
        if current_step is not None:
            wo["current_step"] = current_step

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
        self._evt_seq += 1
        row = {
            "id": self._evt_seq,
            "tenant_id": tenant_id,
            "work_order_id": work_order_id,
            "step": step,
            "event_type": event_type,
            "payload": payload or {},
            "actor": actor,
        }
        self.events.append(row)
        return dict(row)

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events if e["work_order_id"] == work_order_id]

    def add_item(
        self,
        cur,
        *,
        tenant_id,
        work_order_id,
        source,
        kind="unknown",
        file_ref=None,
        original_name=None,
        ocr_history_id=None,
        status="pending",
        flag_reason=None,
        dedupe_key=None,
    ):
        if dedupe_key is not None:
            for it in self.items:
                if it["work_order_id"] == work_order_id and it["dedupe_key"] == dedupe_key:
                    return dict(it)
        self._item_seq += 1
        row = {
            "id": f"item-{self._item_seq}",
            "tenant_id": tenant_id,
            "work_order_id": work_order_id,
            "source": source,
            "kind": kind,
            "file_ref": file_ref,
            "original_name": original_name,
            "ocr_history_id": ocr_history_id,
            "status": status,
            "flag_reason": flag_reason,
            "dedupe_key": dedupe_key,
            "_seq": self._item_seq,
        }
        self.items.append(row)
        return dict(row)

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        rows = [it for it in self.items if it["work_order_id"] == work_order_id]
        if status is not None:
            rows = [it for it in rows if it["status"] == status]
        return [dict(it) for it in sorted(rows, key=lambda r: r["_seq"])]

    def update_item(self, cur, *, tenant_id, item_id, status=None, kind=None, flag_reason=None):
        it = next(i for i in self.items if i["id"] == item_id)
        for col, val in (("status", status), ("kind", kind), ("flag_reason", flag_reason)):
            if val is not None:
                it[col] = val

    def next_deliverable_version(self, cur, *, tenant_id, work_order_id):
        return (
            self.current_deliverable_version(cur, tenant_id=tenant_id, work_order_id=work_order_id)
            + 1
        )

    def current_deliverable_version(self, cur, *, tenant_id, work_order_id):
        bucket = self.deliverables.get(work_order_id, {})
        return max((r.get("version", 1) for r in bucket.values()), default=0)

    def upsert_deliverable(
        self, cur, *, tenant_id, work_order_id, kind, version=1, artifact_path=None, numbers=None
    ):
        # kind->最新版本行(读侧 DISTINCT ON (kind) 取最新);inner bucket 按 kind 键便于断言。
        bucket = self.deliverables.setdefault(work_order_id, {})
        bucket[kind] = {
            "kind": kind,
            "version": version,
            "artifact_path": artifact_path,
            "numbers": numbers or {},
        }
        return dict(bucket[kind])

    def list_deliverables(self, cur, *, tenant_id, work_order_id):
        bucket = self.deliverables.get(work_order_id, {})
        return [{"kind": k, **v} for k, v in bucket.items()]


def _purchase_fields(*, seller, buyer, invoice_no, subtotal, vat, total, warnings=None):
    fields = {
        "document_type": "tax_invoice",
        "seller_tax": seller,
        "buyer_tax": buyer,
        "invoice_number": invoice_no,
        "subtotal": str(subtotal),
        "vat": str(vat),
        "total_amount": str(total),
    }
    if warnings:
        fields["_validation_warnings"] = warnings
    return fields


def _write_sales_summary_xlsx(path: Path) -> None:
    """合成销项汇总表:表头 ยอดขาย/ภาษีขาย + 一条数据行 + 一条应被跳过的合计行。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["วันที่", "ยอดขาย", "ภาษีขาย"])
    ws.append(["01/05/2569", str(SALES_AMOUNT), str(OUTPUT_VAT)])
    ws.append(["รวม", str(SALES_AMOUNT), str(OUTPUT_VAT)])
    wb.save(path)


class _Corpus:
    """一份合成语料 + FakeStore + 假 OCR 入口的装配件,每个测试各建一份互不干扰。"""

    def __init__(self, tmp: Path):
        self.dir = tmp / "intake"
        self.dir.mkdir()
        self.out_dir = tmp / "out"
        self.store = FakeStore()
        self.tenant_id = "t-1"
        self.work_order_id = "wo-1"
        self.store.work_orders[self.work_order_id] = {
            "id": self.work_order_id,
            "tenant_id": self.tenant_id,
            "workspace_client_id": 1,
            "period": "2569-05",
            "intent": "monthly_vat",
            "status": "collecting",
            "current_step": None,
        }

        self.p_ok = self.dir / "invoice_ok.jpg"
        self.p_dup = self.dir / "invoice_dup.jpg"
        self.p_fail = self.dir / "invoice_mathfail.jpg"
        self.p_sales = self.dir / "sales_summary.xlsx"
        self.p_bank = self.dir / "kbank_statement_may.csv"

        self.p_ok.write_bytes(b"jpeg-ok")
        self.p_dup.write_bytes(b"jpeg-dup")
        self.p_fail.write_bytes(b"jpeg-fail")
        _write_sales_summary_xlsx(self.p_sales)
        self.p_bank.write_bytes(b"date,amount\n")

        # 重复票:与正常票同税号+票号+含税合计(票面级指纹相同),但文件字节不同——
        # 验证的是 classify 的内容级查重,不是 intake 的文件级去重。
        self.ocr_map = {
            str(self.p_ok): _purchase_fields(
                seller=OTHER_TAX,
                buyer=OWN_TAX,
                invoice_no="IV100",
                subtotal=GOOD_NET,
                vat=GOOD_VAT,
                total=GOOD_TOTAL,
            ),
            str(self.p_dup): _purchase_fields(
                seller=OTHER_TAX,
                buyer=OWN_TAX,
                invoice_no="IV100",
                subtotal=GOOD_NET,
                vat=GOOD_VAT,
                total=GOOD_TOTAL,
            ),
            str(self.p_fail): _purchase_fields(
                seller=OTHER_TAX,
                buyer=OWN_TAX,
                invoice_no="IV999",
                subtotal=DISPUTED_NET,
                vat=DISPUTED_FACE_VAT,
                total=DISPUTED_TOTAL,
                warnings=["VAT 45.00 与净额 500.00 不平(应为 7% = 35.00,自洽性报警)"],
            ),
        }

    def intake_files(self) -> list:
        return [
            str(self.p_ok),
            str(self.p_dup),
            str(self.p_fail),
            str(self.p_sales),
            str(self.p_bank),
        ]

    def ctx(self, **data_extra) -> StepContext:
        data = {"deliverables_dir": str(self.out_dir)}
        data.update(data_extra)
        return StepContext(
            cur=None,
            tenant_id=self.tenant_id,
            work_order_id=self.work_order_id,
            store=self.store,
            data=data,
        )

    def first_run_ctx(self) -> StepContext:
        return self.ctx(intake_files=self.intake_files())

    def item_by_file(self, path: Path) -> dict:
        return next(it for it in self.store.items if it["file_ref"] == str(path))

    def decide(self, decision: str, values: Optional[dict] = None) -> None:
        flagged = self.item_by_file(self.p_fail)
        self.store.append_event(
            None,
            tenant_id=self.tenant_id,
            work_order_id=self.work_order_id,
            step="reconcile",
            event_type="human_decision",
            payload={"item_id": flagged["id"], "decision": decision, "values": values or {}},
            actor="user:cli",
        )

    def pp30_numbers(self) -> dict:
        return self.store.deliverables[self.work_order_id]["pp30_draft"]["numbers"]


class _GoldenSyntheticTestCase(unittest.TestCase):
    """统一 patch/restore 两处真库/真 OCR 入口 + compute 的上期查询(需要真游标)。"""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.corpus = _Corpus(Path(tmp.name))

        classify._resolve_own_tax_id = lambda ctx: OWN_TAX
        classify._resolve_own_name = lambda ctx: None
        classify._ocr_image = lambda path: self.corpus.ocr_map[path]
        compute._resolve_prior_work_order_id = lambda ctx, **kw: None
        self.addCleanup(
            setattr, classify, "_resolve_own_tax_id", classify._default_resolve_own_tax_id
        )
        self.addCleanup(setattr, classify, "_resolve_own_name", classify._default_resolve_own_name)
        self.addCleanup(setattr, classify, "_ocr_image", classify._default_ocr_image)
        self.addCleanup(
            setattr,
            compute,
            "_resolve_prior_work_order_id",
            compute._default_resolve_prior_work_order_id,
        )

    def _run(self, ctx=None, handlers=None):
        ctx = ctx or self.corpus.ctx()
        return engine.run_work_order(ctx, handlers=handlers or real_handlers())


class StuckOnUnresolvedFlaggedTicketTests(_GoldenSyntheticTestCase):
    def test_first_run_stops_at_reconcile_on_unresolved_math_fail_ticket(self):
        out = self._run(self.corpus.first_run_ctx())

        self.assertFalse(out.completed)
        self.assertEqual(out.stopped_at, "reconcile")
        self.assertTrue(any("amount_math_fail" in r for r in out.result.reasons))
        self.assertTrue(any("无人工裁决" in r for r in out.result.reasons))

        fail_item = self.corpus.item_by_file(self.corpus.p_fail)
        self.assertEqual(fail_item["status"], "flagged")
        self.assertEqual(fail_item["flag_reason"], "amount_math_fail")


class FaceValueDecisionTests(_GoldenSyntheticTestCase):
    def test_face_value_decision_completes_at_disputed_face_amount(self):
        self._run(self.corpus.first_run_ctx())
        self.corpus.decide("face_value")

        out = self._run()

        self.assertTrue(out.completed)
        numbers = self.corpus.pp30_numbers()
        self.assertEqual(Decimal(numbers["input_vat"]), GOOD_VAT + DISPUTED_FACE_VAT)
        self.assertEqual(Decimal(numbers["tax_due"]), OUTPUT_VAT - (GOOD_VAT + DISPUTED_FACE_VAT))


class RecalcDecisionTests(_GoldenSyntheticTestCase):
    def test_recalc_decision_completes_at_a_different_total_than_face_value(self):
        self._run(self.corpus.first_run_ctx())
        self.corpus.decide("recalc", values={"vat": str(DISPUTED_RECALC_VAT)})

        out = self._run()

        self.assertTrue(out.completed)
        numbers = self.corpus.pp30_numbers()
        self.assertEqual(Decimal(numbers["input_vat"]), GOOD_VAT + DISPUTED_RECALC_VAT)
        self.assertNotEqual(
            Decimal(numbers["input_vat"]), GOOD_VAT + DISPUTED_FACE_VAT
        )  # 两条裁决路径终值确实不同


class DuplicateExclusionTests(_GoldenSyntheticTestCase):
    def test_duplicate_ticket_excluded_and_not_double_counted(self):
        self._run(self.corpus.first_run_ctx())

        dup = self.corpus.item_by_file(self.corpus.p_dup)
        self.assertEqual(dup["kind"], "duplicate")
        self.assertEqual(dup["status"], "excluded")
        self.assertTrue(dup["flag_reason"].startswith("duplicate_of:"))
        # 第一张(正常票)不受影响,仍正常归堆,不因后到的重复票被牵连。
        self.assertEqual(self.corpus.item_by_file(self.corpus.p_ok)["kind"], "purchase_invoice")

        self.corpus.decide("face_value")
        self._run()

        reconcile_done = next(
            e
            for e in self.corpus.store.events
            if e["step"] == "reconcile" and e["event_type"] == "step_done"
        )
        # R1 只数了 2 张(正常票 + 争议票),重复票没进合计。
        self.assertEqual(reconcile_done["payload"]["gates"]["r1_input_vat"]["counted"], 2)


class IdempotencyTests(_GoldenSyntheticTestCase):
    def test_rerun_after_completion_does_not_grow_events_or_deliverables(self):
        self._run(self.corpus.first_run_ctx())
        self.corpus.decide("face_value")
        self._run()

        events_after = len(self.corpus.store.events)
        numbers_after = dict(self.corpus.pp30_numbers())

        out2 = self._run()

        self.assertTrue(out2.completed)
        self.assertEqual(len(self.corpus.store.events), events_after)
        self.assertEqual(self.corpus.pp30_numbers(), numbers_after)


class ResumeAfterClassifyCutTests(_GoldenSyntheticTestCase):
    def test_forced_pause_right_after_classify_then_resume_reaches_same_final_numbers(self):
        """人为在 classify 后、reconcile 真正跑之前切断(模拟进程在此刻被杀),验证续跑
        重建出的最终数字与常规流程(自然卡在 reconcile 待裁决 → 裁决 → 续跑)完全一致——
        断点续跑不因切断的时间点不同而改变结果。"""
        paused = {"once": False}
        handlers = dict(real_handlers())
        real_reconcile = handlers["reconcile"]

        def _pause_once_then_real(ctx):
            if not paused["once"]:
                paused["once"] = True
                return StepResult.needs(["manual_pause_after_classify"])
            return real_reconcile(ctx)

        handlers["reconcile"] = _pause_once_then_real

        out1 = self._run(self.corpus.first_run_ctx(), handlers=handlers)
        self.assertFalse(out1.completed)
        self.assertEqual(out1.stopped_at, "reconcile")
        self.assertEqual(out1.result.missing, ("manual_pause_after_classify",))
        for step in ("intake", "sort", "classify"):
            done = [
                e
                for e in self.corpus.store.events
                if e["step"] == step and e["event_type"] == engine.EVT_DONE
            ]
            self.assertEqual(len(done), 1, f"{step} 不该因人为暂停被重做")

        out2 = self._run(handlers=handlers)
        self.assertFalse(out2.completed)
        self.assertEqual(out2.stopped_at, "reconcile")  # 真正的卡点:待裁决

        self.corpus.decide("face_value")
        out3 = self._run(handlers=handlers)

        self.assertTrue(out3.completed)
        numbers = self.corpus.pp30_numbers()
        self.assertEqual(Decimal(numbers["input_vat"]), GOOD_VAT + DISPUTED_FACE_VAT)


class DeliverablePackageTests(_GoldenSyntheticTestCase):
    def test_five_deliverables_written_and_evidence_index_traceable(self):
        self._run(self.corpus.first_run_ctx())
        self.corpus.decide("face_value")
        out = self._run()

        self.assertTrue(out.completed)
        bucket = self.corpus.store.deliverables[self.corpus.work_order_id]
        expected_kinds = {
            "pp30_draft",
            "ledger_workpaper",
            "bank_workpaper",
            "missing_doc_memo",
            "evidence_index",
        }
        self.assertEqual(set(bucket.keys()), expected_kinds)
        for kind, row in bucket.items():
            self.assertTrue(Path(row["artifact_path"]).is_file(), f"{kind} 未真落盘")

        index = json.loads(Path(bucket["evidence_index"]["artifact_path"]).read_text("utf-8"))
        for key in ("tax_due", "sales_amount", "output_vat", "purchase_amount", "input_vat"):
            self.assertIn(key, index["numbers"])
            self.assertTrue(index["numbers"][key]["event_ids"], f"{key} 缺可回溯事件")

        self.assertIn(str(self.corpus.p_ok), index["numbers"]["input_vat"]["source_files"])
        self.assertIn(str(self.corpus.p_fail), index["numbers"]["input_vat"]["source_files"])
        self.assertIn(str(self.corpus.p_sales), index["numbers"]["output_vat"]["source_files"])


if __name__ == "__main__":
    unittest.main()
