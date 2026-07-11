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
from services.workorder.steps import package, pp30_form

GOLDEN_SALES_AMOUNT = "858780.16"
GOLDEN_OUTPUT_VAT = "60114.61"
GOLDEN_PURCHASE_AMOUNT = "418046.86"
GOLDEN_INPUT_VAT = "29263.28"
GOLDEN_TAX_DUE = "30851.33"

GOLDEN_PP30_FORM = pp30_form.build(
    sales_amount=GOLDEN_SALES_AMOUNT,
    output_vat=GOLDEN_OUTPUT_VAT,
    purchase_amount=GOLDEN_PURCHASE_AMOUNT,
    input_vat=GOLDEN_INPUT_VAT,
)


class FakeStore:
    def __init__(self, items, events):
        self.items = items
        self.events = events
        self.deliverables: dict = {}  # kind -> 最新版本行(保持既有按 kind 断言)
        self.all_writes: list = []  # (kind, version, artifact_path):跨版本落盘留痕
        self._max_version = 0

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)

    def next_deliverable_version(self, cur, *, tenant_id, work_order_id):
        return self._max_version + 1

    def current_deliverable_version(self, cur, *, tenant_id, work_order_id):
        return self._max_version

    def upsert_deliverable(
        self, cur, *, tenant_id, work_order_id, kind, version=1, artifact_path, numbers
    ):
        # 真库靠 (tenant, wo, kind, version) 唯一约束:同版本覆盖、换版本新增。这里 kind->最新
        # 版本行保持既有按 kind 断言,all_writes 留全版本痕迹供版本化断言。
        self._max_version = max(self._max_version, version)
        self.deliverables[kind] = {
            "kind": kind,
            "version": version,
            "artifact_path": artifact_path,
            "numbers": numbers,
        }
        self.all_writes.append((kind, version, artifact_path))

    def list_deliverables(self, cur, *, tenant_id, work_order_id):
        return [dict(v) for v in self.deliverables.values()]

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        # 未绑客户(pnd_prep 的边界分支):这批夹具都不测 WHT RD Prep,让 pnd_prep.build()
        # 在查客户前就短路返回,ctx.cur=None 也不会被真的 execute() 到。
        return None


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


def _ambiguous_item(item_id, file_ref, *, status="flagged"):
    """方向不明票(kind=unknown/flag_reason=direction_ambiguous),等人工 assign_kind 裁定。"""
    return {
        "id": item_id,
        "kind": "unknown",
        "status": status,
        "flag_reason": "direction_ambiguous",
        "file_ref": file_ref,
    }


def _sales_direction_item(item_id, file_ref, *, status="flagged"):
    """自家==卖方的方向票(kind=unknown/flag_reason=sales_direction_unhandled)——G1R2 黑洞形态:
    过去既不进 R1、又不被出包闸拦,无裁决照样出包。"""
    return {
        "id": item_id,
        "kind": "unknown",
        "status": status,
        "flag_reason": "sales_direction_unhandled",
        "file_ref": file_ref,
    }


def _waive_evt(event_id, item_id, reason, actor="user:audit"):
    """人工豁免事件(带 reason + actor,供守恒闸放行 + 备忘留痕)。"""
    payload = {"item_id": item_id, "decision": "waive", "reason": reason}
    return {
        "id": event_id,
        "step": "reconcile",
        "event_type": "human_decision",
        "payload": payload,
        "actor": actor,
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


def _assign_kind_evt(event_id, item_id, kind):
    """方向裁决事件(与普通 decision 事件结构不同:带 kind,不带 values)。"""
    payload = {"item_id": item_id, "decision": "assign_kind", "kind": kind}
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
            "pp30_form": GOLDEN_PP30_FORM,
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
        "pp30_form": GOLDEN_PP30_FORM,
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

        # 快照带全字段 ภ.พ.30 契约,逐字段 = 官方申报数;markdown 底稿逐行渲染(含诚实置 0 行)。
        form_amounts = pp30_form.amounts(pp30["pp30_form"])
        self.assertEqual(form_amounts["purchase_creditable"], GOLDEN_PURCHASE_AMOUNT)
        self.assertEqual(form_amounts["input_vat"], GOLDEN_INPUT_VAT)
        self.assertEqual(form_amounts["total_payable"], GOLDEN_TAX_DUE)
        pp30_md = Path(pp30["json_path"]).with_name("pp30_draft.md").read_text(encoding="utf-8")
        self.assertIn("ยอดขายที่ต้องเสียภาษี", pp30_md)  # 应税销售额(派生行)
        self.assertIn("เงินเพิ่ม", pp30_md)  # 加算金(本期无源诚实置 0 行)

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


class DirectionAssignedEvidenceTests(PackageFixture):
    """方向不明票(direction_ambiguous)经人工 assign_kind 裁定后,证据索引不能漏它——
    裁进项的必须现身 input_vat 的 event_ids/source_files/items;裁非税的必须不现身。"""

    def _money(self):
        return {"subtotal": "1000.00", "vat": "70.00", "total_amount": "1070.00"}

    def test_direction_assigned_purchase_ticket_included_in_input_vat_evidence(self):
        items = [
            _purchase_item("u", "/in/undisputed.jpg"),
            _ambiguous_item("d", "/in/deposit_offset.jpg"),
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
                },
            ),
            _classified_evt(2, "d", kind="unknown", status="flagged", money=self._money()),
            _assign_kind_evt(3, "d", "purchase_invoice"),
            _classified_evt(4, "s1", kind="sales_summary", sales_read={"headers": [], "rows": []}),
            _reconcile_done_evt(),
            _compute_done_evt(),
        ]
        store = FakeStore(items, events)
        package.run(self._ctx(store))

        index = json.loads(
            Path(store.deliverables["evidence_index"]["artifact_path"]).read_text(encoding="utf-8")
        )
        input_vat = index["numbers"]["input_vat"]
        # 事件 id 含方向票的 item_classified(2)与 assign_kind 裁决(3)本身。
        self.assertEqual(input_vat["event_ids"], [1, 2, 3])
        self.assertIn("/in/deposit_offset.jpg", input_vat["source_files"])
        self.assertIn({"item_id": "d", "file_name": "deposit_offset.jpg"}, input_vat["items"])

    def test_direction_assigned_non_tax_ticket_excluded_from_input_vat_evidence(self):
        items = [
            _purchase_item("u", "/in/undisputed.jpg"),
            _ambiguous_item("n", "/in/non_tax_candidate.jpg"),
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
                },
            ),
            _classified_evt(2, "n", kind="unknown", status="flagged", money=self._money()),
            _assign_kind_evt(3, "n", "non_tax"),
            _classified_evt(4, "s1", kind="sales_summary", sales_read={"headers": [], "rows": []}),
            _reconcile_done_evt(),
            _compute_done_evt(),
        ]
        store = FakeStore(items, events)
        package.run(self._ctx(store))

        index = json.loads(
            Path(store.deliverables["evidence_index"]["artifact_path"]).read_text(encoding="utf-8")
        )
        input_vat = index["numbers"]["input_vat"]
        self.assertEqual(input_vat["event_ids"], [1])
        self.assertNotIn("/in/non_tax_candidate.jpg", input_vat["source_files"])


class AssignKindMemoTests(PackageFixture):
    """备忘的方向裁决渲染:不许直出内部动作名 "assign_kind",要换成裁定结果的人话。"""

    def test_assign_kind_decision_renders_human_label_not_literal(self):
        items = [
            _purchase_item("u", "/in/undisputed.jpg"),
            _ambiguous_item("d", "/in/deposit_offset.jpg"),
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
                },
            ),
            _classified_evt(
                2,
                "d",
                kind="unknown",
                status="flagged",
                money={"subtotal": "1000.00", "vat": "70.00", "total_amount": "1070.00"},
            ),
            _assign_kind_evt(3, "d", "purchase_invoice"),
            _classified_evt(4, "s1", kind="sales_summary", sales_read={"headers": [], "rows": []}),
            _reconcile_done_evt(),
            _compute_done_evt(),
        ]
        store = FakeStore(items, events)
        package.run(self._ctx(store))

        memo_md = Path(store.deliverables["missing_doc_memo"]["artifact_path"]).read_text(
            encoding="utf-8"
        )
        self.assertNotIn("assign_kind", memo_md)
        self.assertIn("ซื้อ (进项)", memo_md)
        self.assertIn("deposit_offset.jpg", memo_md)


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


class ConservationGateTests(PackageFixture):
    """守恒硬闸:每件必须有明确终态,待裁决>0 → package stuck 逐件点名,绝不出包。
    G1R2 根治:一张 sales_direction_unhandled 无裁决的票,修前照样出包(先红),现在必 stuck。"""

    def _store_with_undecided_direction(self):
        items = [
            _purchase_item("u", "/in/undisputed.jpg"),
            _sales_direction_item("x", "/in/6d001f06_sales.jpg"),
            _sales_item(),
        ]
        events = [
            _classified_evt(
                1,
                "u",
                kind="purchase_invoice",
                money={"subtotal": "354923.86", "vat": "25194.28", "total_amount": "380118.14"},
            ),
            _classified_evt(2, "x", kind="unknown", status="flagged", money=None),
            _classified_evt(3, "s1", kind="sales_summary", sales_read={"headers": [], "rows": []}),
            _reconcile_done_evt(),
            _compute_done_evt(),
        ]
        return FakeStore(items, events)

    def test_undecided_sales_direction_ticket_blocks_package_and_names_it(self):
        store = self._store_with_undecided_direction()
        out = package.run(self._ctx(store))
        self.assertEqual(out.status, "stuck")
        self.assertTrue(any("6d001f06_sales.jpg" in r for r in out.reasons))
        self.assertTrue(any("sales_direction_unhandled" in r for r in out.reasons))
        # stuck 即不出包:交付物一件未落。
        self.assertEqual(store.deliverables, {})

    def test_assigning_direction_unblocks_package(self):
        # 同一张票裁 assign_sales(归销项材料)后守恒成立 → 正常出包。
        store = self._store_with_undecided_direction()
        store.events.insert(-2, _assign_kind_evt(9, "x", "sales_doc"))
        out = package.run(self._ctx(store))
        self.assertEqual(out.status, "ok")
        self.assertEqual(len(store.deliverables), 5)


class WaiveTests(PackageFixture):
    """豁免通道:waive 后守恒放行可出包,但备忘必须留痕(谁豁免·为何·哪张文件)。"""

    def _store_with_waived_direction(self):
        items = [
            _purchase_item("u", "/in/undisputed.jpg"),
            _sales_direction_item("x", "/in/lost_original.jpg"),
            _sales_item(),
        ]
        events = [
            _classified_evt(
                1,
                "u",
                kind="purchase_invoice",
                money={"subtotal": "354923.86", "vat": "25194.28", "total_amount": "380118.14"},
            ),
            _classified_evt(2, "x", kind="unknown", status="flagged", money=None),
            _classified_evt(3, "s1", kind="sales_summary", sales_read={"headers": [], "rows": []}),
            _waive_evt(4, "x", "客户 LINE 确认为个人杂支·原件遗失", actor="user:77"),
            _reconcile_done_evt(),
            _compute_done_evt(),
        ]
        return FakeStore(items, events)

    def test_waived_ticket_lets_package_ship_with_memo_trace(self):
        store = self._store_with_waived_direction()
        out = package.run(self._ctx(store))
        self.assertEqual(out.status, "ok")
        self.assertEqual(len(store.deliverables), 5)

        memo = store.deliverables["missing_doc_memo"]
        memo_md = Path(memo["artifact_path"]).read_text(encoding="utf-8")
        # 谁豁免 + 为何 + 哪张文件,三者齐现。
        self.assertIn("user:77", memo_md)
        self.assertIn("客户 LINE 确认为个人杂支·原件遗失", memo_md)
        self.assertIn("lost_original.jpg", memo_md)
        self.assertEqual(memo["numbers"]["waived_count"], 1)


class VersioningTests(PackageFixture):
    """交付物版本化(C-2 · 验收断言 2):未冻结重跑=新版本、v1 文件逐字节未动、读侧取最新版。"""

    def test_rerun_creates_new_version_leaving_v1_untouched(self):
        store = self._sister_makeup_store()
        first = package.run(self._ctx(store))
        self.assertEqual(first.status, "ok")
        self.assertEqual(first.payload["deliverable_version"], 1)
        # v1 五件真落盘在 {base}/v1/,记录逐字节快照。
        v1_paths = {kind: path for kind, ver, path in store.all_writes if ver == 1}
        self.assertEqual(len(v1_paths), 5)
        v1_bytes = {k: Path(p).read_bytes() for k, p in v1_paths.items()}
        for p in v1_paths.values():
            self.assertEqual(Path(p).parent.name, "v1")

        second = package.run(self._ctx(store))
        self.assertEqual(second.payload["deliverable_version"], 2)
        v2_paths = {kind: path for kind, ver, path in store.all_writes if ver == 2}
        self.assertEqual(len(v2_paths), 5)

        # v1 文件逐字节未动(重跑不覆盖旧版本)。
        for kind, path in v1_paths.items():
            self.assertTrue(Path(path).is_file(), f"{kind} v1 文件被删")
            self.assertEqual(Path(path).read_bytes(), v1_bytes[kind], f"{kind} v1 被改写")
        # v2 是不同物理文件(落在 v2/ 段),与 v1 路径不同。
        for kind in v1_paths:
            self.assertNotEqual(v1_paths[kind], v2_paths[kind])
            self.assertIn("v2", str(Path(v2_paths[kind]).parent.name))
        # 读侧默认取最新版 = v2。
        latest = {
            d["kind"]: d
            for d in store.list_deliverables(None, tenant_id="t-1", work_order_id="wo-1")
        }
        self.assertEqual(len(latest), 5)
        for kind in v1_paths:
            self.assertEqual(latest[kind]["version"], 2)
            self.assertEqual(latest[kind]["artifact_path"], v2_paths[kind])


if __name__ == "__main__":
    unittest.main()
