# -*- coding: utf-8 -*-
"""审核队列路由契约 + fail-closed 守门(routes/workorder_review_routes.py · MC1-b1）。

锁定:①四端点按 path+method 注册且挂进 app;②M1 闸关时任一端点 404(对存量用户等于不存在);
③C3 细码:每端点传给 require_perm 的 tax.filing.* 与方案闸点对齐;④批量裁决部分成功原样透传
(不整批假成功);⑤review-queue 非法 severity/period → 422。
"""

from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from core import route_helpers
from tests.unit._route_contract_fakes import FakeCur as _Cur
from tests.unit._route_contract_fakes import FakeDB as _FakeDB
from tests.unit._route_contract_fakes import route_set as _route_set


class RouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        from routes.workorder_review_routes import router

        expected = {
            ("GET", "/api/workorder/review-queue"),
            ("POST", "/api/workorder/orders/{work_order_id}/decisions:batch"),
            ("POST", "/api/workorder/orders/{work_order_id}/review-reject"),
            ("POST", "/api/workorder/orders/{work_order_id}/self-review-declare"),
            ("POST", "/api/workorder/orders/{work_order_id}/bank-recon/decide"),
        }
        self.assertTrue(
            expected.issubset(_route_set(router)), f"缺路由: {expected - _route_set(router)}"
        )

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/workorder/review-queue", paths)

    def test_registered_in_agent_registry(self):
        import json
        from pathlib import Path

        reg = json.loads(Path("docs/agent/agent_registry.json").read_text(encoding="utf-8"))
        self.assertIn("workorder_review_routes", reg)


_USER = {"id": "u1", "tenant_id": "t-1"}


class GateClosedTests(unittest.IsolatedAsyncioTestCase):
    async def test_gate_closed_hides_review_queue_as_404(self):
        from routes import workorder_review_routes as wr

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=False),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wr.get_review_queue(mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)


class QueueValidationTests(unittest.IsolatedAsyncioTestCase):
    def _open_gate(self, wr):
        return (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
        )

    async def test_invalid_severity_maps_422(self):
        from routes import workorder_review_routes as wr

        for p in self._open_gate(wr):
            self.enterContext(p)
        with self.assertRaises(HTTPException) as ctx:
            await wr.get_review_queue(mock.Mock(), severity="orange")
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "review.invalid_severity")

    async def test_invalid_period_maps_422(self):
        from routes import workorder_review_routes as wr

        for p in self._open_gate(wr):
            self.enterContext(p)
        with self.assertRaises(HTTPException) as ctx:
            await wr.get_review_queue(mock.Mock(), period="2026/5")
        self.assertEqual(ctx.exception.status_code, 422)


class BatchPassthroughTests(unittest.IsolatedAsyncioTestCase):
    async def test_partial_success_passthrough_and_advance_on_any_ok(self):
        from routes import workorder_review_routes as wr

        result = {
            "results": [
                {"item_id": "a", "ok": True, "event_id": 1},
                {"item_id": "b", "ok": False, "error": "x"},
            ],
            "ok_count": 1,
            "fail_count": 1,
            "total": 2,
        }
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr, "_load_mutable_order", return_value={"workspace_client_id": 7}),
            mock.patch.object(wr.review, "batch_decisions", return_value=result),
            mock.patch.object(wr, "_auto_advance") as adv,
        ):
            out = await wr.add_decisions_batch(
                "wo-1",
                wr.BatchDecisionsIn(decisions=[wr.DecisionIn(item_id="a", decision="face_value")]),
                mock.Mock(),
                mock.Mock(),
            )
        self.assertEqual(out["ok_count"], 1)
        self.assertEqual(out["fail_count"], 1)  # 整批不假成功,逐条如实
        adv.assert_called_once()  # 有成功件才排自驱

    async def test_no_ok_skips_advance(self):
        from routes import workorder_review_routes as wr

        result = {
            "results": [{"item_id": "b", "ok": False, "error": "x"}],
            "ok_count": 0,
            "fail_count": 1,
            "total": 1,
        }
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr, "_load_mutable_order", return_value={"workspace_client_id": 7}),
            mock.patch.object(wr.review, "batch_decisions", return_value=result),
            mock.patch.object(wr, "_auto_advance") as adv,
        ):
            await wr.add_decisions_batch(
                "wo-1",
                wr.BatchDecisionsIn(decisions=[wr.DecisionIn(item_id="b", decision="face_value")]),
                mock.Mock(),
                mock.Mock(),
            )
        adv.assert_not_called()


class PermCodeWiringTests(unittest.IsolatedAsyncioTestCase):
    """每端点传给 require_perm 的细码与方案闸点对齐(view/prepare/review/approve)。"""

    async def _perm_code_used(self, wr, coro):
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr, "_load_mutable_order", return_value={"workspace_client_id": 7}),
            mock.patch.object(wr.review, "review_queue", return_value={}),
            mock.patch.object(wr.review, "batch_decisions", return_value={"ok_count": 0}),
            mock.patch.object(wr.review, "reject_review", return_value={}),
            mock.patch.object(wr.review, "declare_self_review", return_value={}),
            mock.patch.object(wr.bank_recon_review, "record_bank_decision", return_value={"id": 1}),
            mock.patch.object(wr, "_auto_advance"),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER) as perm,
        ):
            try:
                await coro
            except Exception:
                pass
        self.assertTrue(perm.called, "端点未走 require_perm")
        return perm.call_args[0][1]

    async def test_endpoint_perm_codes(self):
        from routes import workorder_review_routes as wr

        cases = (
            (wr.get_review_queue(mock.Mock()), wr._C_VIEW),
            (
                wr.add_decisions_batch(
                    "wo-1",
                    wr.BatchDecisionsIn(
                        decisions=[wr.DecisionIn(item_id="a", decision="face_value")]
                    ),
                    mock.Mock(),
                    mock.Mock(),
                ),
                wr._C_PREPARE,
            ),
            (
                wr.reject_order_review("wo-1", wr.RejectIn(reason="fix"), mock.Mock(), mock.Mock()),
                wr._C_REVIEW,
            ),
            (wr.declare_self_review("wo-1", mock.Mock()), wr._C_APPROVE),
            (
                wr.decide_bank_recon(
                    "wo-1",
                    wr.BankReconDecideIn(
                        statement_tx_id="tx-1", action="accept", candidate_id="it-2"
                    ),
                    mock.Mock(),
                ),
                wr._C_PREPARE,
            ),
        )
        for coro, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(await self._perm_code_used(wr, coro), expected)


class BankReconDecideRouteTests(unittest.IsolatedAsyncioTestCase):
    """decide 端点接线:成功透传 event_id;冻结只读闸(_load_mutable_order 409)先于服务
    层校验;服务层拒(tx 不在 review 桶/野 candidate)照 _raise_from_api_error 翻码。"""

    def _open_gate(self):
        return (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
        )

    async def test_success_returns_event_id(self):
        from routes import workorder_review_routes as wr

        for p in self._open_gate():
            self.enterContext(p)
        with (
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr, "_load_mutable_order", return_value={"workspace_client_id": 7}),
            mock.patch.object(
                wr.bank_recon_review, "record_bank_decision", return_value={"id": 55}
            ),
        ):
            out = await wr.decide_bank_recon(
                "wo-1",
                wr.BankReconDecideIn(statement_tx_id="tx-1", action="accept", candidate_id="it-2"),
                mock.Mock(),
            )
        self.assertEqual(out, {"ok": True, "event_id": 55})

    async def test_frozen_order_rejected_before_service_call(self):
        from routes import workorder_review_routes as wr

        for p in self._open_gate():
            self.enterContext(p)
        svc = mock.Mock()
        with (
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(
                wr,
                "_load_mutable_order",
                side_effect=HTTPException(status_code=409, detail="workorder.archived_readonly"),
            ),
            mock.patch.object(wr.bank_recon_review, "record_bank_decision", svc),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wr.decide_bank_recon(
                    "wo-1",
                    wr.BankReconDecideIn(statement_tx_id="tx-1", action="reject"),
                    mock.Mock(),
                )
        self.assertEqual(ctx.exception.status_code, 409)
        svc.assert_not_called()

    async def test_tx_not_found_maps_404(self):
        from routes import workorder_review_routes as wr
        from services.workorder import api as wo_api

        for p in self._open_gate():
            self.enterContext(p)
        with (
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr, "_load_mutable_order", return_value={"workspace_client_id": 7}),
            mock.patch.object(
                wr.bank_recon_review,
                "record_bank_decision",
                side_effect=wo_api.WorkOrderApiError("workorder.bank_recon_tx_not_found"),
            ),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wr.decide_bank_recon(
                    "wo-1",
                    wr.BankReconDecideIn(statement_tx_id="tx-ghost", action="reject"),
                    mock.Mock(),
                )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_invalid_candidate_maps_422(self):
        from routes import workorder_review_routes as wr
        from services.workorder import api as wo_api

        for p in self._open_gate():
            self.enterContext(p)
        with (
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr, "_load_mutable_order", return_value={"workspace_client_id": 7}),
            mock.patch.object(
                wr.bank_recon_review,
                "record_bank_decision",
                side_effect=wo_api.WorkOrderApiError("workorder.bank_recon_candidate_invalid"),
            ),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wr.decide_bank_recon(
                    "wo-1",
                    wr.BankReconDecideIn(statement_tx_id="tx-1", action="accept", candidate_id="x"),
                    mock.Mock(),
                )
        self.assertEqual(ctx.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
