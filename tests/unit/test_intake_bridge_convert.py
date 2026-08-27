# -*- coding: utf-8 -*-
"""services/intake_bridge 单测(mock cursor · 纯编排/口径覆盖,不连库)。

覆盖:方向判定(税号锚点)/ 幂等(already_converted)/ 无方向 / 无账套 / 无行项(convert.py
编排口径),以及无票号 / 撞重复(sales_leg 自身口径)、撞重复发票(purchase_leg 自身口径)。
真实建单落库(purchase_docs posted / sales_documents issued / 商品收发存出数)由
tests/integration/test_intake_bridge_real.py 真库守。
"""

from __future__ import annotations

import copy
import unittest
from unittest import mock

import psycopg2

from core.pos_api import PosError
from services.intake_bridge import convert as convert_svc
from services.intake_bridge import purchase_leg, sales_leg
from services.intake_bridge.errors import SkipConversion

_OWN_TAX = "0105561234563"
_CP_TAX = "0107537000521"

_FIELDS = {
    "invoice_number": "INV-1001",
    "date": "2026-06-01",
    "seller_tax": _OWN_TAX,
    "buyer_tax": _CP_TAX,
    "buyer_name": "7-11",
    "total_amount": "1070",
    "subtotal": "1000",
    "vat": "70",
    "items": [{"name": "สินค้า A", "qty": "10", "price": "100"}],
}


def _history_row(fields=None, workspace_client_id=9):
    return {
        "pages": [{"fields": fields if fields is not None else copy.deepcopy(_FIELDS)}],
        "workspace_client_id": workspace_client_id,
        "posting_kind": None,
    }


class _FakeCursor:
    """按调用顺序回放 fetchone 结果;execute 只记录(SQL 顺序由被测代码决定,不重复断言
    文本,只关心"给定回放序列 → 出什么 converted/skipped")。"""

    def __init__(self, fetchone_results):
        self._results = list(fetchone_results)
        self.queries: list = []

    def execute(self, sql, params=None):
        self.queries.append(sql.strip())

    def fetchone(self):
        return self._results.pop(0) if self._results else None


class ConvertOrchestrationTests(unittest.TestCase):
    """convert.py 逐口径:方向判定 / 幂等 / 无方向 / 无账套 / 无行项。"""

    def _run(self, results, **patches):
        cur = _FakeCursor(results)
        with (
            mock.patch.object(
                purchase_leg, "book_from_history", return_value=("doc-1", "PO-1")
            ) as p_book,
            mock.patch.object(
                sales_leg, "issue_from_history", return_value=("doc-2", "INV-1001")
            ) as s_issue,
        ):
            if "purchase_side_effect" in patches:
                p_book.side_effect = patches["purchase_side_effect"]
            if "sales_side_effect" in patches:
                s_issue.side_effect = patches["sales_side_effect"]
            out = convert_svc.convert_histories(
                cur, tenant_id="t1", user_id="u1", history_ids=["h1"]
            )
        return out, cur, p_book, s_issue

    def test_purchase_direction_when_own_tax_matches_buyer(self):
        # own_tax(账套主体)== 票面买方税号 → 进项。
        results = [_history_row(), None, {"tax_id": _CP_TAX}]
        out, _cur, p_book, s_issue = self._run(results)
        self.assertEqual(out["skipped"], [])
        self.assertEqual(
            out["converted"],
            [{"history_id": "h1", "doc_type": "purchase", "doc_id": "doc-1", "doc_no": "PO-1"}],
        )
        p_book.assert_called_once()
        s_issue.assert_not_called()

    def test_sales_direction_when_own_tax_matches_seller(self):
        # own_tax == 票面卖方税号 → 销项。
        results = [_history_row(), None, {"tax_id": _OWN_TAX}]
        out, _cur, p_book, s_issue = self._run(results)
        self.assertEqual(out["skipped"], [])
        self.assertEqual(out["converted"][0]["doc_type"], "sales")
        s_issue.assert_called_once()
        p_book.assert_not_called()

    def test_already_converted_is_idempotent_skip(self):
        results = [_history_row(), {"exists": 1}]  # 幂等命中,不再查 own_tax
        out, _cur, p_book, s_issue = self._run(results)
        self.assertEqual(out["converted"], [])
        self.assertEqual(out["skipped"], [{"history_id": "h1", "reason": "already_converted"}])
        p_book.assert_not_called()
        s_issue.assert_not_called()

    def test_no_direction_when_tax_ambiguous(self):
        # own_tax 两边都不命中 → ambiguous,留人工。
        results = [_history_row(), None, {"tax_id": "0199999999999"}]
        out, *_ = self._run(results)
        self.assertEqual(out["skipped"], [{"history_id": "h1", "reason": "no_direction"}])

    def test_no_workspace_when_explicit_direction_but_no_workspace(self):
        # 显式方向不靠税号锚点,workspace 缺失时不查 own_tax(短路),但仍须挡在建单前。
        fields = dict(_FIELDS)
        fields["direction"] = "sales"
        results = [_history_row(fields=fields, workspace_client_id=None), None]
        out, *_ = self._run(results)
        self.assertEqual(out["skipped"], [{"history_id": "h1", "reason": "no_workspace"}])

    def test_no_items_when_no_lines_and_no_total(self):
        fields = {"invoice_number": "X", "date": "2026-06-01"}  # 无 items、无金额
        results = [_history_row(fields=fields), None]
        out, *_ = self._run(results)
        self.assertEqual(out["skipped"], [{"history_id": "h1", "reason": "no_items"}])

    def test_expense_without_items_but_with_total_is_not_no_items(self):
        # 无行项但有票面总额的费用票:convert.py 层不拦(留给 purchase_leg 的单行兜底建单),
        # 不是"没数据"。
        fields = {
            "invoice_number": "X",
            "date": "2026-06-01",
            "seller_tax": _CP_TAX,
            "buyer_tax": _OWN_TAX,
            "total_amount": "500",
        }
        results = [_history_row(fields=fields), None, {"tax_id": _OWN_TAX}]
        out, *_ = self._run(results)
        self.assertEqual(out["skipped"], [])
        self.assertEqual(out["converted"][0]["doc_type"], "purchase")

    def test_one_history_failure_does_not_drag_down_the_batch(self):
        # 单张 SAVEPOINT 隔离:一张失败/跳过不影响本函数继续跑完(此处单张即演示跳过路径)。
        results = [_history_row(), {"exists": 1}]
        cur = _FakeCursor(results)
        out = convert_svc.convert_histories(cur, tenant_id="t1", user_id="u1", history_ids=["h1"])
        self.assertIn("RELEASE SAVEPOINT intake_bridge_convert", cur.queries)
        self.assertIn("ROLLBACK TO SAVEPOINT intake_bridge_convert", cur.queries)
        self.assertEqual(out["skipped"][0]["reason"], "already_converted")

    def test_erp_confirmation_enqueues_snapshot_in_same_savepoint(self):
        history = _history_row()
        history.update(
            {
                "filename": "merchant-invoice.pdf",
                "source": "line_erp",
                "pdf_storage_path": "merchant/private/invoice.pdf",
            }
        )
        cur = _FakeCursor([history, None, {"tax_id": _CP_TAX}])
        with (
            mock.patch.object(purchase_leg, "book_from_history", return_value=("doc-1", "PO-1")),
            mock.patch.object(convert_svc.submission_enqueue, "enqueue_confirmed_document") as put,
        ):
            out = convert_svc.convert_histories(
                cur,
                tenant_id="t1",
                user_id="u1",
                history_ids=["h1"],
                enqueue_client_submissions=True,
            )

        self.assertEqual(out["skipped"], [])
        kwargs = put.call_args.kwargs
        self.assertEqual(kwargs["merchant_workspace_client_id"], 9)
        self.assertEqual(kwargs["source_document_type"], "purchase")
        self.assertEqual(kwargs["source_document_id"], "doc-1")
        self.assertEqual(kwargs["original_file_ref"], "ocr_history:h1")
        self.assertEqual(kwargs["snapshot"]["fields"]["invoice_number"], "INV-1001")
        self.assertEqual(kwargs["snapshot"]["pages"], history["pages"])
        enqueue_at = next(
            index
            for index, query in enumerate(cur.queries)
            if query.startswith("UPDATE purchase_docs SET ocr_history_id")
        )
        release_at = cur.queries.index("RELEASE SAVEPOINT intake_bridge_convert")
        self.assertLess(enqueue_at, release_at)

    def test_submission_failure_rolls_back_formal_document_savepoint(self):
        cur = _FakeCursor([_history_row(), None, {"tax_id": _CP_TAX}])
        with (
            mock.patch.object(purchase_leg, "book_from_history", return_value=("doc-1", "PO-1")),
            mock.patch.object(
                convert_svc.submission_enqueue,
                "enqueue_confirmed_document",
                side_effect=RuntimeError("outbox unavailable"),
            ),
        ):
            out = convert_svc.convert_histories(
                cur,
                tenant_id="t1",
                user_id="u1",
                history_ids=["h1"],
                enqueue_client_submissions=True,
            )

        self.assertEqual(out["converted"], [])
        self.assertEqual(out["skipped"][0]["reason"], "error:outbox unavailable")
        self.assertIn("ROLLBACK TO SAVEPOINT intake_bridge_convert", cur.queries)


class SalesLegTests(unittest.TestCase):
    """sales_leg.issue_from_history 自身口径:无票号 / 无行项 / 撞重复。"""

    def test_no_doc_no_skips(self):
        fields = dict(_FIELDS)
        fields["invoice_number"] = ""
        with self.assertRaises(SkipConversion) as ctx:
            sales_leg.issue_from_history(
                mock.Mock(), tenant_id="t1", workspace_client_id=9, created_by="u1", fields=fields
            )
        self.assertEqual(ctx.exception.reason, "no_doc_no")

    def test_no_items_skips(self):
        fields = dict(_FIELDS)
        fields["items"] = []
        with self.assertRaises(SkipConversion) as ctx:
            sales_leg.issue_from_history(
                mock.Mock(), tenant_id="t1", workspace_client_id=9, created_by="u1", fields=fields
            )
        self.assertEqual(ctx.exception.reason, "no_items")

    def test_unreadable_date_skips(self):
        fields = dict(_FIELDS)
        fields["date"] = "not-a-date"
        with self.assertRaises(SkipConversion) as ctx:
            sales_leg.issue_from_history(
                mock.Mock(), tenant_id="t1", workspace_client_id=9, created_by="u1", fields=fields
            )
        self.assertEqual(ctx.exception.reason, "no_date")

    def test_unique_violation_maps_to_duplicate_skip(self):
        cur = mock.Mock()
        cur.execute.side_effect = psycopg2.errors.UniqueViolation("dup")
        with self.assertRaises(SkipConversion) as ctx:
            sales_leg.issue_from_history(
                cur, tenant_id="t1", workspace_client_id=9, created_by="u1", fields=dict(_FIELDS)
            )
        self.assertEqual(ctx.exception.reason, "duplicate")


class PurchaseLegTests(unittest.TestCase):
    """purchase_leg.book_from_history 自身口径:撞重复发票(dedupe)。"""

    def test_dup_invoice_pos_error_maps_to_duplicate_skip(self):
        with (
            mock.patch.object(
                purchase_leg.settings_svc, "get_settings", return_value={"auto_stock_in": False}
            ),
            mock.patch.object(
                purchase_leg.docs_svc,
                "create_doc",
                side_effect=PosError("purchase.dup_invoice", 409),
            ),
        ):
            with self.assertRaises(SkipConversion) as ctx:
                purchase_leg.book_from_history(
                    mock.Mock(),
                    tenant_id="t1",
                    workspace_client_id=9,
                    created_by="u1",
                    fields=dict(_FIELDS),
                )
        self.assertEqual(ctx.exception.reason, "duplicate")

    def test_other_pos_error_propagates(self):
        with (
            mock.patch.object(
                purchase_leg.settings_svc, "get_settings", return_value={"auto_stock_in": False}
            ),
            mock.patch.object(
                purchase_leg.docs_svc,
                "create_doc",
                side_effect=PosError("purchase.line_invalid", 422),
            ),
        ):
            with self.assertRaises(PosError):
                purchase_leg.book_from_history(
                    mock.Mock(),
                    tenant_id="t1",
                    workspace_client_id=9,
                    created_by="u1",
                    fields=dict(_FIELDS),
                )

    def test_manual_expense_beats_judge_direction_purchase_signal(self):
        # 票面证据齐全(完整税票+VAT+买方身份)judge_direction 会判 purchase_invoice,
        # 但复核屏人工裁决 posting_item_type_manual=expense 必须优先生效(item_verdict 口径)。
        fields = dict(_FIELDS)
        fields.update({"document_type": "tax_invoice", "posting_item_type_manual": "expense"})
        captured: dict = {}

        def _fake_build_draft(_fields, *, kind, categories=None):
            captured["kind"] = kind
            return {"lines": []}

        with (
            mock.patch.object(
                purchase_leg.intake_svc, "build_draft_from_invoice", side_effect=_fake_build_draft
            ),
            mock.patch.object(
                purchase_leg.settings_svc, "get_settings", return_value={"auto_stock_in": False}
            ),
            mock.patch.object(
                purchase_leg.docs_svc, "create_doc", return_value={"doc": {"id": "doc-1"}}
            ),
            mock.patch.object(
                purchase_leg.posting_svc, "post_doc", return_value={"doc": {"doc_no": "PO-1"}}
            ),
        ):
            purchase_leg.book_from_history(
                mock.Mock(),
                tenant_id="t1",
                workspace_client_id=9,
                created_by="u1",
                fields=fields,
            )
        self.assertEqual(captured["kind"], "expense")


if __name__ == "__main__":
    unittest.main()
