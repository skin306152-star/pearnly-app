# -*- coding: utf-8 -*-
"""推送定位器的单据兜底(services/agent/doc_fallback)· 图先话后盲区根治契约。

铁三条:① 只有 push_to_erp 开兜底(查状态纯读不许插载体行);② 多命中/故障不猜
维持 not_found;③ 载体行按 source_ref 幂等复用。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.agent import doc_fallback as f
from services.agent.contracts import AgentContext

_CTX = AgentContext(user={"id": "u-1", "plan": "credits"}, tenant_id="t-1", workspace_client_id=84)

_DOC = {
    "id": "d-1",
    "doc_no": "INV-9",
    "doc_date": "2026-07-01",
    "has_vat": False,
    "subtotal": "100",
    "vat_amount": "0",
    "grand_total": "100",
    "source": "line",
    "status": "posted",
}
_DETAIL = {
    "doc": _DOC,
    "supplier": {"name": "ร้าน A", "tax_id": ""},
    "lines": [{"description": "x", "qty": "1", "unit_price": "100", "line_total": "100"}],
}


def _cm(cur):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cur)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


class TestCarrierFields(unittest.TestCase):
    def test_fields_shape_matches_push_machinery(self):
        fields = f.carrier_fields_from_doc(_DETAIL)
        self.assertEqual(fields["invoice_number"], "INV-9")
        self.assertEqual(fields["date"], "2026-07-01")
        self.assertEqual(fields["total_amount"], "100")
        self.assertEqual(fields["document_type"], "receipt")  # 无 VAT 单
        self.assertEqual(fields["items"][0]["subtotal"], "100")

    def test_vat_doc_marks_tax_invoice(self):
        detail = {**_DETAIL, "doc": {**_DOC, "has_vat": True}}
        self.assertEqual(f.carrier_fields_from_doc(detail)["document_type"], "tax_invoice")


class TestLocate(unittest.TestCase):
    def _run(self, docs, existing_carrier=None, keyword=None):
        cur = MagicMock()
        cur.fetchone.return_value = {"id": existing_carrier} if existing_carrier else None
        with (
            patch.object(f.db, "get_cursor_rls", return_value=_cm(cur)),
            patch("services.purchase.docs.list_docs", return_value={"docs": docs}),
            patch("services.purchase.docs.get_doc", return_value=_DETAIL),
            patch.object(f.db, "insert_ocr_history", return_value="hid-new") as ins,
        ):
            out = f.locate_pushable_doc(_CTX, keyword)
        return out, ins

    def test_single_image_doc_builds_carrier(self):
        out, ins = self._run([_DOC])
        self.assertEqual(out["id"], "hid-new")
        self.assertEqual(out["invoice_no"], "INV-9")
        ins.assert_called_once()
        self.assertEqual(ins.call_args.kwargs["source_ref"], "purchase_doc:d-1")
        self.assertEqual(ins.call_args.kwargs["pages"][0]["fields"]["total_amount"], "100")

    def test_existing_carrier_reused_not_reinserted(self):
        out, ins = self._run([_DOC], existing_carrier="hid-old")
        self.assertEqual(out["id"], "hid-old")
        ins.assert_not_called()

    def test_manual_docs_excluded(self):
        out, _ = self._run([{**_DOC, "source": "manual"}])
        self.assertIsNone(out)

    def test_keyword_multi_hit_never_guesses(self):
        out, _ = self._run([_DOC, {**_DOC, "id": "d-2"}], keyword="ร้าน")
        self.assertIsNone(out)

    def test_any_crash_keeps_not_found(self):
        with patch.object(f.db, "get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertIsNone(f.locate_pushable_doc(_CTX, None))


class TestLocatorGating(unittest.TestCase):
    def test_status_query_never_triggers_fallback(self):
        # 查状态是纯读——零命中时绝不许走会插载体行的兜底。
        from services.agent.executor import AgentToolset

        ts = AgentToolset()
        with (
            patch("services.agent.executor.db.list_ocr_history", return_value={"items": []}),
            patch("services.agent.doc_fallback.locate_pushable_doc") as loc,
            patch(
                "services.agent.executor._plan_permissions",
                return_value={"can_push_erp": True, "can_view_history": True},
            ),
        ):
            res = ts.get_push_status(_CTX, keyword="x")
        self.assertEqual(res.error_code, "history_not_found")
        loc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
