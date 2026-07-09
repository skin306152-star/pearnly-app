# -*- coding: utf-8 -*-
"""F5 路由行为单测(PATCH /api/history/{record_id}/posting)。

钉死:body 缺省键=不传给 DAL(model_dump(exclude_unset=True))· null=显式传 None(删键)·
值域外的字符串 → 422(不许被 DAL 静默当"清除人工裁决")· DAL 写失败(记录不存在)→ 404 ·
回流只在有实际值时调 · 422/404 时不触发回流。
"""

from __future__ import annotations

import asyncio
import unittest
from unittest import mock

from fastapi import HTTPException

from routes import history_routes
from services.ocr_history.posting_manual import PostingManualResult


def _run(coro):
    return asyncio.run(coro)


class HistoryUpdatePostingRouteTests(unittest.TestCase):
    def setUp(self):
        self._patches = [
            mock.patch.object(
                history_routes, "get_current_user_from_request", return_value={"id": "u1"}
            ),
            mock.patch.object(history_routes, "_check_history_access", return_value=7),
            mock.patch.object(history_routes, "_tid", return_value="t1"),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)

    def test_empty_body_short_circuits_without_dal_call(self):
        req = history_routes.HistoryPostingRequest()
        with mock.patch.object(history_routes, "update_history_posting_manual") as mocked_update:
            resp = _run(history_routes.history_update_posting("h1", req, mock.Mock()))
        self.assertEqual(resp, {"ok": True})
        mocked_update.assert_not_called()

    def test_only_sent_key_forwarded_to_dal(self):
        req = history_routes.HistoryPostingRequest(payment="cash")
        result = PostingManualResult(True, workspace_client_id=7, seller_tax="0105546015062")
        with mock.patch.object(
            history_routes, "update_history_posting_manual", return_value=result
        ) as mocked_update:
            with mock.patch.object(history_routes, "backflow_supplier_profile") as mocked_flow:
                _run(history_routes.history_update_posting("h1", req, mock.Mock()))
        mocked_update.assert_called_once_with("u1", "h1", "t1", payment="cash")
        mocked_flow.assert_called_once_with(
            record_id="h1",
            tenant_id="t1",
            payment="cash",
            item_type=None,
            workspace_client_id=7,
            seller_tax="0105546015062",
        )

    def test_explicit_null_forwarded_as_none(self):
        req = history_routes.HistoryPostingRequest(payment=None)
        # model_dump(exclude_unset=True) 仍会含 payment(用户显式传了 null),与"没传"不同。
        result = PostingManualResult(True)
        with mock.patch.object(
            history_routes, "update_history_posting_manual", return_value=result
        ) as mocked_update:
            with mock.patch.object(history_routes, "backflow_supplier_profile"):
                _run(history_routes.history_update_posting("h1", req, mock.Mock()))
        mocked_update.assert_called_once_with("u1", "h1", "t1", payment=None)

    def test_invalid_payment_value_raises_422(self):
        req = history_routes.HistoryPostingRequest(payment="maybe")
        with mock.patch.object(history_routes, "update_history_posting_manual") as mocked_update:
            with mock.patch.object(history_routes, "backflow_supplier_profile") as mocked_flow:
                with self.assertRaises(HTTPException) as ctx:
                    _run(history_routes.history_update_posting("h1", req, mock.Mock()))
        self.assertEqual(ctx.exception.status_code, 422)
        mocked_update.assert_not_called()
        mocked_flow.assert_not_called()

    def test_invalid_item_type_value_raises_422(self):
        req = history_routes.HistoryPostingRequest(item_type="services")
        with mock.patch.object(history_routes, "update_history_posting_manual") as mocked_update:
            with self.assertRaises(HTTPException) as ctx:
                _run(history_routes.history_update_posting("h1", req, mock.Mock()))
        self.assertEqual(ctx.exception.status_code, 422)
        mocked_update.assert_not_called()

    def test_dal_failure_raises_404_and_skips_backflow(self):
        req = history_routes.HistoryPostingRequest(payment="cash")
        with mock.patch.object(
            history_routes, "update_history_posting_manual", return_value=PostingManualResult(False)
        ):
            with mock.patch.object(history_routes, "backflow_supplier_profile") as mocked_flow:
                with self.assertRaises(HTTPException) as ctx:
                    _run(history_routes.history_update_posting("h1", req, mock.Mock()))
        self.assertEqual(ctx.exception.status_code, 404)
        mocked_flow.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
