# -*- coding: utf-8 -*-
"""进项单据守卫逻辑单测(docs/posting 状态机早退 · 不连真库 · docs/purchasing/02 §1)。

用极简 FakeCursor 喂状态行,验状态机在写库前正确拦截(not_draft/amount_mismatch/404)+
行校验(line_invalid)。真 DB 行为(连号/库存联动/隔离)由隔离闸 + 真账号 E2E 守。
"""

import unittest

from core.pos_api import PosError
from services.purchase import correct as correct_svc
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


class _SqlCur:
    """记 SQL + 可控 rowcount;fetchall=[]、fetchone 给安全聚合默认(够测 SQL 守卫)。"""

    def __init__(self, rowcount=1):
        self.rowcount = rowcount
        self.sql: list = []

    def execute(self, sql, params=None):
        self.sql.append(sql)

    def fetchall(self):
        return []

    def fetchone(self):
        return {"goods_total": 0, "expense_total": 0, "vat_claimable": 0, "unpaid_total": 0}


class DiscardDocTests(unittest.TestCase):
    def test_discard_draft_sets_discarded_and_frees_dedupe(self):
        cur = _SqlCur(rowcount=1)
        correct_svc.discard_doc(cur, tenant_id="t", workspace_client_id=1, doc_id="D1")
        sql = cur.sql[0]
        self.assertIn("status = 'discarded'", sql)
        self.assertIn("dedupe_key = NULL", sql)  # 释放查重指纹
        self.assertIn("AND status = 'draft'", sql)  # 仅 draft 可软删

    def test_discard_non_draft_raises_not_draft(self):
        cur = _SqlCur(rowcount=0)  # 无行被改 = 非 draft
        with self.assertRaises(PosError) as e:
            correct_svc.discard_doc(cur, tenant_id="t", workspace_client_id=1, doc_id="D1")
        self.assertEqual(e.exception.code, "purchase.not_draft")


class DiscardedInvisibilityTests(unittest.TestCase):
    """★软删对所有活跃口径隐形:列表/查重/月汇总/明细 的 SQL 均排除 discarded。"""

    def test_list_docs_excludes_discarded(self):
        cur = _SqlCur()
        docs_svc.list_docs(cur, tenant_id="t", workspace_client_id=1)
        self.assertTrue(any("d.status <> 'discarded'" in s for s in cur.sql))

    def test_find_by_dedupe_excludes_discarded(self):
        cur = _SqlCur()
        docs_svc.find_by_dedupe(cur, tenant_id="t", workspace_client_id=1, dedupe_key="k")
        self.assertIn("status <> 'discarded'", cur.sql[0])

    def test_month_summary_and_detail_posted_only(self):
        from services.expense import line_qa

        cur = _SqlCur()
        line_qa.month_summary(cur, tenant_id="t", workspace_client_id=1)
        line_qa.month_detail(cur, tenant_id="t", workspace_client_id=1)
        self.assertTrue(
            all("d.status = 'posted'" in s for s in cur.sql)
        )  # posted-only → discarded 不入

    def test_recent_line_docs_excludes_discarded(self):
        from services.purchase import line_docs

        cur = _SqlCur()
        line_docs.find_recent_line_docs(cur, tenant_id="t", workspace_client_id=1, limit=5)
        self.assertIn("status IN ('posted', 'draft')", cur.sql[0])  # discarded 不在其中


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


class VoidReversalTests(unittest.TestCase):
    """作废完整对冲(docs/purchasing/03):撤付款凭证 + 作废做账主凭证 + 反库存 + status=void。"""

    def _void(self, *, paid_amount):
        from unittest import mock

        calls = []

        class Cur:
            def execute(self, *a, **k):
                return None

            def fetchone(self):
                return {
                    "status": "posted",
                    "doc_kind": "expense",
                    "net_payable": 100,
                    "paid_amount": paid_amount,
                }

            def fetchall(self):
                return []

        with (
            mock.patch.object(
                posting_svc,
                "_void_payment_vouchers",
                side_effect=lambda *a, **k: calls.append(("pay", k.get("strict"))),
            ),
            mock.patch.object(
                posting_svc.acct_hooks,
                "void_for_source",
                side_effect=lambda *a, **k: calls.append(("voucher", k.get("source_type"))),
            ),
            mock.patch.object(
                posting_svc, "_reverse_stock", side_effect=lambda *a, **k: calls.append(("stock",))
            ),
            mock.patch.object(
                posting_svc.docs_svc, "get_doc", return_value={"id": "D", "status": "void"}
            ),
        ):
            res = posting_svc.void_doc(
                Cur(), tenant_id="t", workspace_client_id=1, doc_id="D", created_by="u"
            )
        return res, calls

    def test_paid_doc_full_reversal(self):
        res, calls = self._void(paid_amount=100)
        self.assertIn(("pay", True), calls)  # 撤付款走 strict
        self.assertIn(("voucher", "purchase"), calls)  # 作废做账主凭证
        self.assertIn(("stock",), calls)  # 反库存
        self.assertEqual(res["status"], "void")

    def test_unpaid_doc_skips_payment_void(self):
        _res, calls = self._void(paid_amount=0)
        self.assertNotIn(("pay", True), calls)  # 未付不撤付款
        self.assertIn(("voucher", "purchase"), calls)  # 仍作废做账主凭证
        self.assertIn(("stock",), calls)


class StrictPaymentVoidTests(unittest.TestCase):
    """strict=True(void_doc 用):每张付款凭证走 seam void_or_reverse(开放期 void/已结期红冲),不吞错。"""

    def test_strict_dispatches_each_to_void_or_reverse(self):
        from decimal import Decimal
        from unittest import mock

        from services.accounting import hooks as acct_hooks
        from services.accounting import vouchers as jv

        store = {
            str(acct_hooks.payment_event_id("D", Decimal("100"))): {"id": "v1", "total_debit": 100},
        }
        handled = []

        class Cur:
            def execute(self, *a, **k):
                return None

        with (
            mock.patch.object(
                jv, "find_active_by_source", side_effect=lambda c, **k: store.get(k["source_id"])
            ),
            mock.patch.object(
                posting_svc.acct_hooks,
                "void_or_reverse",
                side_effect=lambda *a, **k: handled.append(k["voucher_id"]),
            ),
        ):
            posting_svc._void_payment_vouchers(
                Cur(),
                tenant_id="t",
                workspace_client_id=1,
                doc_id="D",
                paid=Decimal("100"),
                strict=True,
                created_by="u",
            )
        self.assertEqual(handled, ["v1"])

    def test_strict_propagates_errors(self):
        from decimal import Decimal
        from unittest import mock

        from services.accounting import hooks as acct_hooks
        from services.accounting import vouchers as jv

        store = {
            str(acct_hooks.payment_event_id("D", Decimal("100"))): {"id": "v1", "total_debit": 100},
        }

        class Cur:
            def execute(self, *a, **k):
                return None

        with (
            mock.patch.object(
                jv, "find_active_by_source", side_effect=lambda c, **k: store.get(k["source_id"])
            ),
            mock.patch.object(
                posting_svc.acct_hooks,
                "void_or_reverse",
                side_effect=PosError("acct.period_closed", 409),
            ),
            self.assertRaises(PosError) as e,
        ):
            posting_svc._void_payment_vouchers(
                Cur(),
                tenant_id="t",
                workspace_client_id=1,
                doc_id="D",
                paid=Decimal("100"),
                strict=True,
                created_by="u",
            )
        self.assertEqual(e.exception.code, "acct.period_closed")


class CorrectDocTests(unittest.TestCase):
    """更正(docs/purchasing/03)= 作废原单(完整对冲)+ 克隆成可改新草稿,顺序固定。"""

    def test_void_then_clone(self):
        from unittest import mock

        seq = []

        class Cur:
            def execute(self, *a, **k):
                return None

        with (
            mock.patch.object(
                correct_svc.posting_svc, "void_doc", side_effect=lambda *a, **k: seq.append("void")
            ),
            mock.patch.object(
                correct_svc,
                "clone_as_draft",
                side_effect=lambda *a, **k: (seq.append("clone") or {"doc": {"id": "NEW"}}),
            ),
        ):
            res = correct_svc.correct_doc(
                Cur(), tenant_id="t", workspace_client_id=1, doc_id="D", created_by="u"
            )
        self.assertEqual(seq, ["void", "clone"])  # 先作废后克隆(原子)
        self.assertEqual(res["doc"]["id"], "NEW")

    def test_clone_none_raises(self):
        from unittest import mock

        class Cur:
            def execute(self, *a, **k):
                return None

        with (
            mock.patch.object(correct_svc.posting_svc, "void_doc", return_value={}),
            mock.patch.object(correct_svc, "clone_as_draft", return_value=None),
            self.assertRaises(PosError) as e,
        ):
            correct_svc.correct_doc(
                Cur(), tenant_id="t", workspace_client_id=1, doc_id="D", created_by="u"
            )
        self.assertEqual(e.exception.code, "purchase.unexpected")


if __name__ == "__main__":
    unittest.main()
