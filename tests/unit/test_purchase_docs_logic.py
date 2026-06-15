# -*- coding: utf-8 -*-
"""进项单据守卫逻辑单测(docs/posting 状态机早退 · 不连真库 · docs/purchasing/02 §1)。

用极简 FakeCursor 喂状态行,验状态机在写库前正确拦截(not_draft/amount_mismatch/404)+
行校验(line_invalid)。真 DB 行为(连号/库存联动/隔离)由隔离闸 + 真账号 E2E 守。
"""

import unittest

from core.pos_api import PosError
from services.purchase import docs as docs_svc
from services.purchase import posting as posting_svc


class FakeCursor:
    """只回一行固定状态,execute 全 no-op(够测写库前的守卫早退)。"""

    def __init__(self, row):
        self._row = row
        self.rowcount = 0

    def execute(self, *a, **k):
        return None

    def fetchone(self):
        return self._row


def _post(row):
    return posting_svc.post_doc(
        FakeCursor(row),
        tenant_id="t",
        workspace_client_id=1,
        doc_id="d",
        auto_stock_in=False,
        created_by="u",
    )


class PostingGuardTests(unittest.TestCase):
    def test_post_missing_doc_404(self):
        with self.assertRaises(PosError) as e:
            _post(None)
        self.assertEqual(e.exception.code, "purchase.unexpected")

    def test_post_non_draft_blocked(self):
        with self.assertRaises(PosError) as e:
            _post({"status": "posted", "doc_kind": "expense"})
        self.assertEqual(e.exception.code, "purchase.not_draft")

    def test_pay_over_remaining_blocked(self):
        with self.assertRaises(PosError) as e:
            posting_svc.pay_doc(
                FakeCursor({"status": "posted", "net_payable": 100, "paid_amount": 0}),
                tenant_id="t",
                workspace_client_id=1,
                doc_id="d",
                amount=150,
            )
        self.assertEqual(e.exception.code, "purchase.amount_mismatch")

    def test_pay_unposted_blocked(self):
        with self.assertRaises(PosError) as e:
            posting_svc.pay_doc(
                FakeCursor({"status": "draft", "net_payable": 100, "paid_amount": 0}),
                tenant_id="t",
                workspace_client_id=1,
                doc_id="d",
                amount=10,
            )
        self.assertEqual(e.exception.code, "purchase.not_draft")

    def test_void_draft_blocked(self):
        with self.assertRaises(PosError) as e:
            posting_svc.void_doc(
                FakeCursor({"status": "draft"}),
                tenant_id="t",
                workspace_client_id=1,
                doc_id="d",
                created_by="u",
            )
        self.assertEqual(e.exception.code, "purchase.not_draft")


def _update(row):
    # 守卫在重算/写库前早退,故 data/settings 给空即可触发。
    return docs_svc.update_draft(
        FakeCursor(row),
        tenant_id="t",
        workspace_client_id=1,
        created_by="u",
        doc_id="d",
        data={},
        settings={},
    )


class UpdateDraftGuardTests(unittest.TestCase):
    """编辑只针对草稿原地改(前端 PUT 修法前提):posted/void 拒改,缺单 404。"""

    def test_update_missing_doc_404(self):
        with self.assertRaises(PosError) as e:
            _update(None)
        self.assertEqual(e.exception.code, "purchase.unexpected")

    def test_update_posted_blocked(self):
        with self.assertRaises(PosError) as e:
            _update({"status": "posted"})
        self.assertEqual(e.exception.code, "purchase.not_draft")

    def test_update_void_blocked(self):
        with self.assertRaises(PosError) as e:
            _update({"status": "void"})
        self.assertEqual(e.exception.code, "purchase.not_draft")


class LineValidationTests(unittest.TestCase):
    def test_empty_lines_invalid(self):
        with self.assertRaises(PosError):
            docs_svc._validate_lines([])

    def test_line_without_item_invalid(self):
        bad = [{"line_no": 1, "description": "", "product_id": None, "qty": 1}]
        with self.assertRaises(PosError):
            docs_svc._validate_lines(bad)

    def test_good_line_passes(self):
        ok = [{"line_no": 1, "description": "ของ", "product_id": None, "qty": 2}]
        docs_svc._validate_lines(ok)  # 不抛 = 通过


class PostAutoPayTests(unittest.TestCase):
    """PO-5 建单即付:post 时 payment_status='paid' → 自动补付款(复用 pay_doc)。"""

    def _post(self, doc):
        from unittest import mock

        captured = {}

        class Cur:
            def execute(self, *a, **k):
                return None

            def fetchone(self):
                return {
                    "status": "draft",
                    "doc_kind": "expense",
                    "net_payable": 100,
                    "paid_amount": 0,
                }

        def fake_pay(cur, **k):
            captured.update(k)
            return {**doc, "paid_amount": 100}

        with (
            mock.patch.object(posting_svc.docs_svc, "get_doc", return_value=doc),
            mock.patch.object(posting_svc.acct_hooks, "enqueue_posting", return_value=None),
            mock.patch.object(posting_svc, "pay_doc", side_effect=fake_pay),
        ):
            res = posting_svc.post_doc(
                Cur(),
                tenant_id="t",
                workspace_client_id=1,
                doc_id="D1",
                auto_stock_in=False,
                created_by="u",
            )
        return res, captured

    def test_paid_doc_auto_pays(self):
        from decimal import Decimal

        res, captured = self._post(
            {"id": "D1", "payment_status": "paid", "net_payable": 100, "paid_amount": 0}
        )
        self.assertEqual(captured.get("amount"), Decimal("100"))
        self.assertEqual(res["paid_amount"], 100)

    def test_unpaid_doc_no_auto_pay(self):
        res, captured = self._post(
            {"id": "D1", "payment_status": "unpaid", "net_payable": 100, "paid_amount": 0}
        )
        self.assertEqual(captured, {})


class PaymentStatusToggleTests(unittest.TestCase):
    """PO-5 一键改付款态:paid 付清未付额 / unpaid 撤销付款 / 非法状态拒 / 仅 posted。"""

    def _cur(self, paid_amount=0, status="posted"):
        class Cur:
            def execute(self, *a, **k):
                return None

            def fetchone(self):
                return {
                    "status": status,
                    "doc_kind": "expense",
                    "net_payable": 100,
                    "paid_amount": paid_amount,
                }

        return Cur()

    def test_bad_status_rejected(self):
        with self.assertRaises(PosError) as e:
            posting_svc.set_payment_status(
                self._cur(), tenant_id="t", workspace_client_id=1, doc_id="D", status="weird"
            )
        self.assertEqual(e.exception.code, "purchase.line_invalid")

    def test_paid_pays_remaining(self):
        from decimal import Decimal
        from unittest import mock

        cap = {}

        def fake_pay(cur, **k):
            cap.update(k)
            return {"id": "D", "payment_status": "paid"}

        with mock.patch.object(posting_svc, "pay_doc", side_effect=fake_pay):
            posting_svc.set_payment_status(
                self._cur(0), tenant_id="t", workspace_client_id=1, doc_id="D", status="paid"
            )
        self.assertEqual(cap.get("amount"), Decimal("100"))

    def test_unpaid_resets_doc(self):
        from unittest import mock

        with mock.patch.object(
            posting_svc.docs_svc,
            "get_doc",
            return_value={"id": "D", "payment_status": "unpaid", "paid_amount": 0},
        ):
            res = posting_svc.set_payment_status(
                self._cur(100), tenant_id="t", workspace_client_id=1, doc_id="D", status="unpaid"
            )
        self.assertEqual(res["payment_status"], "unpaid")

    def test_unpay_only_posted(self):
        with self.assertRaises(PosError) as e:
            posting_svc.unpay_doc(
                self._cur(status="draft"), tenant_id="t", workspace_client_id=1, doc_id="D"
            )
        self.assertEqual(e.exception.code, "purchase.not_draft")

    def test_void_chain_voids_all_partial_payments(self):
        # 多次部分付款(30 + 70 = 100)→ 撤付款应沿累计链 void 全部凭证。
        from decimal import Decimal
        from unittest import mock

        from services.accounting import hooks as acct_hooks, vouchers as jv

        store = {
            str(acct_hooks.payment_event_id("D", Decimal("100"))): {"id": "v2", "total_debit": 70},
            str(acct_hooks.payment_event_id("D", Decimal("30"))): {"id": "v1", "total_debit": 30},
        }
        voided = []

        class Cur:
            def execute(self, *a, **k):
                return None

        with (
            mock.patch.object(
                jv, "find_active_by_source", side_effect=lambda c, **k: store.get(k["source_id"])
            ),
            mock.patch.object(
                jv, "set_status", side_effect=lambda c, **k: voided.append(k["voucher_id"])
            ),
        ):
            posting_svc._void_payment_vouchers(
                Cur(), tenant_id="t", workspace_client_id=1, doc_id="D", paid=Decimal("100")
            )
        self.assertEqual(voided, ["v2", "v1"])


if __name__ == "__main__":
    unittest.main()
