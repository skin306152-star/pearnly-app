# -*- coding: utf-8 -*-
"""package 步守门测试(services/workorder/steps/package.py · 任务包 §5 步 6 / §6)。

用 tempdir 真写盘 + 内存 FakeStore(list_items/list_events/upsert_deliverable/
list_deliverables,upsert 按 kind 覆盖模拟真库唯一约束语义)。覆盖:缺
deliverables_dir → needs;五种交付物齐全、文件真落盘、numbers 快照与金标一致;
evidence_index 每个数字都能索引到事件 id 与原件路径;重跑幂等(deliverable 不重复、
文件内容不变)。
"""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from services.workorder.engine import StepContext
from services.workorder.steps import package

GOLDEN_SALES_AMOUNT = "858780.16"
GOLDEN_OUTPUT_VAT = "60114.61"
GOLDEN_PURCHASE_AMOUNT = "418046.86"
GOLDEN_INPUT_VAT = "29263.28"
GOLDEN_TAX_DUE = "30851.33"


class FakeStore:
    def __init__(self, items, events):
        self.items = items
        self.events = events
        self.deliverables: dict = {}

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)

    def upsert_deliverable(self, cur, *, tenant_id, work_order_id, kind, artifact_path, numbers):
        # 真库靠 (work_order_id, kind) 唯一约束覆盖——这里用 dict 键模拟同一语义。
        self.deliverables[kind] = {"artifact_path": artifact_path, "numbers": numbers}

    def list_deliverables(self, cur, *, tenant_id, work_order_id):
        return [{"kind": k, **v} for k, v in self.deliverables.items()]


def _purchase_item(item_id, file_ref, *, status="ok"):
    return {
        "id": item_id,
        "kind": "purchase_invoice",
        "status": status,
        "flag_reason": "amount_math_fail" if status == "flagged" else None,
        "file_ref": file_ref,
    }


def _sales_item(item_id="s1"):
    return {
        "id": item_id,
        "kind": "sales_summary",
        "status": "ok",
        "flag_reason": None,
        "file_ref": "/in/pos_may.xlsx",
    }


def _classified_evt(event_id, item_id, *, kind, money=None, sales_read=None, status="ok"):
    payload = {"item_id": item_id, "kind": kind, "status": status}
    if money:
        payload["money"] = money
    if sales_read:
        payload["sales_read"] = sales_read
    return {"id": event_id, "step": "classify", "event_type": "item_classified", "payload": payload}


def _decision_evt(event_id, item_id, decision):
    payload = {"item_id": item_id, "decision": decision, "values": {}}
    return {"id": event_id, "step": "reconcile", "event_type": "human_decision", "payload": payload}


def _reconcile_done_evt(event_id=20):
    return {
        "id": event_id,
        "step": "reconcile",
        "event_type": "step_done",
        "payload": {
            "gates": {
                "r3_bank": {"bank_statement_present": False, "note": "bank_statement_missing"}
            }
        },
    }


def _compute_done_evt(event_id=21):
    return {
        "id": event_id,
        "step": "compute",
        "event_type": "step_done",
        "payload": {
            "tax_due": GOLDEN_TAX_DUE,
            "sales_amount": GOLDEN_SALES_AMOUNT,
            "output_vat": GOLDEN_OUTPUT_VAT,
            "purchase_amount": GOLDEN_PURCHASE_AMOUNT,
            "input_vat": GOLDEN_INPUT_VAT,
            "period": "2569-05",
            "prior_period_check": {"status": "no_prior_period"},
        },
    }


def _compute_ctx_data():
    return {
        "tax_due": GOLDEN_TAX_DUE,
        "sales_amount": GOLDEN_SALES_AMOUNT,
        "output_vat": GOLDEN_OUTPUT_VAT,
        "purchase_amount": GOLDEN_PURCHASE_AMOUNT,
        "input_vat": GOLDEN_INPUT_VAT,
        "period": "2569-05",
        "prior_period_check": {"status": "no_prior_period"},
        "gates": {"r3_bank": {"bank_statement_present": False, "note": "bank_statement_missing"}},
    }


class PackageFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out_dir = str(Path(self.tmp.name) / "deliverables")

    def _ctx(self, store, *, with_ctx_data=True):
        data = {"deliverables_dir": self.out_dir}
        if with_ctx_data:
            data.update(_compute_ctx_data())
        return StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data=data)

    def _sister_makeup_store(self):
        items = [
            _purchase_item("u", "/in/undisputed.jpg"),
            _purchase_item("x", "/in/IMG_2647.jpg", status="flagged"),
            _sales_item(),
        ]
        events = [
            _classified_evt(
                1,
                "u",
                kind="purchase_invoice",
                money={
                    "subtotal": "354923.86",
                    "vat": "25194.28",
                    "total_amount": "380118.14",
                    "invoice_number": "IV001",
                    "seller_tax": "0735527000289",
                },
            ),
            _classified_evt(
                2,
                "x",
                kind="purchase_invoice",
                status="flagged",
                money={
                    "subtotal": "58128.57",
                    "vat": "4069.00",
                    "total_amount": "62197.57",
                    "invoice_number": "IV2647",
                    "seller_tax": "0735527000289",
                },
            ),
            _decision_evt(3, "x", "face_value"),
            _classified_evt(4, "s1", kind="sales_summary", sales_read={"headers": [], "rows": []}),
            _reconcile_done_evt(),
            _compute_done_evt(),
        ]
        return FakeStore(items, events)


class NeedsDeliverablesDirTests(PackageFixture):
    def test_missing_deliverables_dir_needs(self):
        store = self._sister_makeup_store()
        ctx = StepContext(
            cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data=_compute_ctx_data()
        )
        out = package.run(ctx)
        self.assertEqual(out.status, "needs")
        self.assertEqual(out.missing, ("deliverables_dir",))


class FiveDeliverablesTests(PackageFixture):
    def test_all_five_kinds_written_with_numbers_snapshot(self):
        store = self._sister_makeup_store()
        out = package.run(self._ctx(store))

        self.assertEqual(out.status, "ok")
        expected_kinds = {
            "pp30_draft",
            "ledger_workpaper",
            "bank_workpaper",
            "missing_doc_memo",
            "evidence_index",
        }
        self.assertEqual(set(store.deliverables.keys()), expected_kinds)
        for kind, row in store.deliverables.items():
            self.assertTrue(Path(row["artifact_path"]).is_file(), f"{kind} 文件未真落盘")

        pp30 = store.deliverables["pp30_draft"]["numbers"]
        self.assertEqual(pp30["tax_due"], GOLDEN_TAX_DUE)
        self.assertEqual(pp30["sales_amount"], GOLDEN_SALES_AMOUNT)
        self.assertEqual(pp30["output_vat"], GOLDEN_OUTPUT_VAT)
        self.assertEqual(pp30["purchase_amount"], GOLDEN_PURCHASE_AMOUNT)
        self.assertEqual(pp30["input_vat"], GOLDEN_INPUT_VAT)
        # pp30 同时落 JSON(结构化) + markdown(底稿)两份文件。
        self.assertTrue(Path(pp30["json_path"]).is_file())
        pp30_json = json.loads(Path(pp30["json_path"]).read_text(encoding="utf-8"))
        self.assertEqual(pp30_json["tax_due"], GOLDEN_TAX_DUE)

        ledger_md = Path(store.deliverables["ledger_workpaper"]["artifact_path"]).read_text(
            encoding="utf-8"
        )
        self.assertIn("IMG_2647.jpg", ledger_md)
        self.assertIn("undisputed.jpg", ledger_md)
        self.assertIn("face_value", ledger_md)

        bank_md = Path(store.deliverables["bank_workpaper"]["artifact_path"]).read_text(
            encoding="utf-8"
        )
        self.assertIn("missing", bank_md)
        self.assertFalse(store.deliverables["bank_workpaper"]["numbers"]["bank_statement_present"])

        memo_md = Path(store.deliverables["missing_doc_memo"]["artifact_path"]).read_text(
            encoding="utf-8"
        )
        self.assertIn("bank_statement_missing", memo_md)
        self.assertIn("IMG_2647.jpg", memo_md)
        self.assertIn("face_value", memo_md)

    def test_resume_scenario_resolves_numbers_from_event_stream(self):
        """ctx.data 为空(重启),数字必须能从 compute/reconcile 的 step_done 回放出同样结果。"""
        store = self._sister_makeup_store()
        ctx = self._ctx(store, with_ctx_data=False)
        out = package.run(ctx)

        self.assertEqual(out.status, "ok")
        self.assertEqual(store.deliverables["pp30_draft"]["numbers"]["tax_due"], GOLDEN_TAX_DUE)


class EvidenceIndexTests(PackageFixture):
    def test_every_number_indexes_to_events_and_source_files(self):
        store = self._sister_makeup_store()
        package.run(self._ctx(store))

        index_path = store.deliverables["evidence_index"]["artifact_path"]
        index = json.loads(Path(index_path).read_text(encoding="utf-8"))

        self.assertEqual(index["work_order_id"], "wo-1")
        self.assertEqual(index["period"], "2569-05")
        numbers = index["numbers"]

        for key in ("tax_due", "sales_amount", "output_vat", "purchase_amount", "input_vat"):
            self.assertIn(key, numbers)
            self.assertTrue(numbers[key]["event_ids"], f"{key} 缺支撑事件")

        # 进项税/可抵进项额同一批进项票证据:两张票的 item_classified(id 1,2)+ 裁决(id 3)。
        self.assertEqual(numbers["input_vat"]["event_ids"], [1, 2, 3])
        self.assertIn("/in/undisputed.jpg", numbers["input_vat"]["source_files"])
        self.assertIn("/in/IMG_2647.jpg", numbers["input_vat"]["source_files"])

        # 销项两个数字指向销项直读事件(id 4)。
        self.assertEqual(numbers["output_vat"]["event_ids"], [4])
        self.assertEqual(numbers["sales_amount"]["event_ids"], [4])
        self.assertIn("/in/pos_may.xlsx", numbers["output_vat"]["source_files"])

        # 应缴指向 compute 的 step_done(id 21,来自事件流,而非本次 run() 新落的 step_done——
        # package 自己不落 compute 的事件,证据必须指到 compute 那一步本身)。
        self.assertEqual(numbers["tax_due"]["event_ids"], [21])
        self.assertEqual(numbers["tax_due"]["source_files"], [])

    def test_excluded_decision_ticket_not_counted_as_supporting_evidence(self):
        items = [_purchase_item("x", "/in/IMG_2647.jpg", status="flagged"), _sales_item()]
        events = [
            _classified_evt(
                1,
                "x",
                kind="purchase_invoice",
                status="flagged",
                money={"subtotal": "58128.57", "vat": "4069.00", "total_amount": "62197.57"},
            ),
            _decision_evt(2, "x", "exclude"),
            _classified_evt(3, "s1", kind="sales_summary", sales_read={"headers": [], "rows": []}),
            _reconcile_done_evt(),
            _compute_done_evt(),
        ]
        store = FakeStore(items, events)
        package.run(self._ctx(store))

        index = json.loads(
            Path(store.deliverables["evidence_index"]["artifact_path"]).read_text(encoding="utf-8")
        )
        # 被裁决剔除的票没进合计,不该出现在 input_vat 的支撑证据里。
        self.assertNotIn(1, index["numbers"]["input_vat"]["event_ids"])
        self.assertNotIn(2, index["numbers"]["input_vat"]["event_ids"])


class SalesSourceAnnotationTests(PackageFixture):
    """销项来源标注(状态诚实条款):人工申报的销项数字必须与 POS 直读区分呈现。"""

    def test_direct_read_sales_defaults_to_direct_read_no_note(self):
        store = self._sister_makeup_store()  # 既有夹具的 sales_read 无 source 字段
        package.run(self._ctx(store))

        pp30 = store.deliverables["pp30_draft"]["numbers"]
        self.assertEqual(pp30["sales_source"], "direct_read")
        self.assertIsNone(pp30["sales_source_note"])

        pp30_md = Path(store.deliverables["pp30_draft"]["artifact_path"]).read_text(
            encoding="utf-8"
        )
        self.assertNotIn("แหล่งที่มา", pp30_md)  # direct_read 不额外提示,默认可信路径

        ledger_md = Path(store.deliverables["ledger_workpaper"]["artifact_path"]).read_text(
            encoding="utf-8"
        )
        self.assertNotIn("แหล่งที่มา", ledger_md)  # ledger 与 pp30 同一份判定,不各拼一套

        index = json.loads(
            Path(store.deliverables["evidence_index"]["artifact_path"]).read_text(encoding="utf-8")
        )
        self.assertEqual(index["numbers"]["sales_amount"]["source"], "direct_read")
        self.assertNotIn("note", index["numbers"]["sales_amount"])

    def test_manual_entry_sales_labeled_and_not_confused_with_direct_read(self):
        items = [
            _purchase_item("u", "/in/undisputed.jpg"),
            {
                "id": "s1",
                "kind": "sales_summary",
                "status": "ok",
                "flag_reason": None,
                "file_ref": None,  # 人工填销项没有票据文件(api.record_sales_summary 同口径)
            },
        ]
        events = [
            _classified_evt(
                1,
                "u",
                kind="purchase_invoice",
                money={
                    "subtotal": "354923.86",
                    "vat": "25194.28",
                    "total_amount": "380118.14",
                },
            ),
            _classified_evt(
                2,
                "s1",
                kind="sales_summary",
                sales_read={
                    "headers": ["ยอดขาย", "ภาษีขาย"],
                    "rows": [{"cells": ["858780.16", "60114.61"], "is_summary": False}],
                    "source": "manual_entry",
                    "note": "no POS export, client reported by LINE",
                },
            ),
            _reconcile_done_evt(),
            _compute_done_evt(),
        ]
        store = FakeStore(items, events)
        package.run(self._ctx(store))

        pp30 = store.deliverables["pp30_draft"]["numbers"]
        self.assertEqual(pp30["sales_source"], "manual_entry")
        self.assertEqual(pp30["sales_source_note"], "no POS export, client reported by LINE")

        pp30_md = Path(store.deliverables["pp30_draft"]["artifact_path"]).read_text(
            encoding="utf-8"
        )
        self.assertIn("กรอกเอง", pp30_md)
        self.assertIn("no POS export, client reported by LINE", pp30_md)

        ledger_md = Path(store.deliverables["ledger_workpaper"]["artifact_path"]).read_text(
            encoding="utf-8"
        )
        self.assertIn("แหล่งที่มา", ledger_md)
        self.assertIn("กรอกเอง", ledger_md)

        index = json.loads(
            Path(store.deliverables["evidence_index"]["artifact_path"]).read_text(encoding="utf-8")
        )
        sales_numbers = index["numbers"]["sales_amount"]
        self.assertEqual(sales_numbers["source"], "manual_entry")
        self.assertEqual(sales_numbers["note"], "no POS export, client reported by LINE")
        # 人工填的件没有票据文件——items 里该条 file_name 诚实给 None,不是编一个假文件名。
        self.assertEqual(sales_numbers["items"], [{"item_id": "s1", "file_name": None}])
        self.assertEqual(sales_numbers["source_files"], [])

        # 进项证据不受影响(items 逐条含 file_name)。
        purchase_items = index["numbers"]["input_vat"]["items"]
        self.assertEqual(purchase_items, [{"item_id": "u", "file_name": "undisputed.jpg"}])


class IdempotencyTests(PackageFixture):
    def test_rerun_overwrites_not_duplicates(self):
        store = self._sister_makeup_store()
        ctx1 = self._ctx(store)
        first = package.run(ctx1)
        first_files = {k: v["artifact_path"] for k, v in store.deliverables.items()}

        ctx2 = self._ctx(store)
        second = package.run(ctx2)

        self.assertEqual(first.status, second.status)
        self.assertEqual(len(store.deliverables), 5)  # 未累加
        for kind, path in first_files.items():
            self.assertEqual(store.deliverables[kind]["artifact_path"], path)
        self.assertEqual(
            store.deliverables["pp30_draft"]["numbers"]["tax_due"],
            store.deliverables["pp30_draft"]["numbers"]["tax_due"],
        )
        # 文件被覆盖为同样内容,不是追加。
        ledger_path = Path(store.deliverables["ledger_workpaper"]["artifact_path"])
        content = ledger_path.read_text(encoding="utf-8")
        self.assertEqual(content.count("IMG_2647.jpg"), 1)


if __name__ == "__main__":
    unittest.main()
