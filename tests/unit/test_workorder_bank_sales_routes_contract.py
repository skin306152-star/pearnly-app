# -*- coding: utf-8 -*-
"""银行倒推销项路由契约 + fail-closed 守门(routes/workorder_bank_sales_routes.py · SA-3a)。

锁定:①两端点按 path+method 注册且挂进 app;②双闸 fail-closed——M1 闸关 404、SA-3a 闸
(pearnly_ai_bank_sales_suggest)关 404 且大脑一步不跑;③两端点传给 require_perm 的细码
= tax.filing.create(_C_PREPARE);④decide 野指纹 → 404 结构化码。引擎/大脑/人裁的业务
逻辑守门在 test_bank_sales_*,本套只钉路由层契约。
"""

from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from core import route_helpers
from routes.workorder_bank_sales_routes import router as bank_sales_router
from tests.unit._route_contract_fakes import FakeCur as _Cur
from tests.unit._route_contract_fakes import FakeDB as _FakeDB
from tests.unit._route_contract_fakes import route_set as _route_set

_USER = {"id": "u1", "tenant_id": "t-1"}
_RUN_PATH = "/api/workorder/orders/{work_order_id}/bank-sales/run"
_DECIDE_PATH = "/api/workorder/orders/{work_order_id}/bank-sales/decide"


class RouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        rs = _route_set(bank_sales_router)
        expected = {("POST", _RUN_PATH), ("POST", _DECIDE_PATH)}
        self.assertTrue(expected.issubset(rs), f"缺路由: {expected - rs}")


class RouterMountedTests(unittest.TestCase):
    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn(_RUN_PATH, paths)
        self.assertIn(_DECIDE_PATH, paths)


class GateClosedTests(unittest.IsolatedAsyncioTestCase):
    """双闸 fail-closed:任一闸关,两端点对外等于不存在(404),引擎/大脑一步不跑。"""

    async def test_m1_gate_closed_hides_routes_as_404(self):
        from routes import workorder_bank_sales_routes as wbs

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=False),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wbs.run_bank_sales("wo-1", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_sa3a_gate_closed_is_404_and_brain_never_runs(self):
        from routes import workorder_bank_sales_routes as wbs

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wbs, "pearnly_ai_bank_sales_suggest_enabled_for", return_value=False),
            mock.patch.object(wbs.bank_sales_brain, "run") as brain_run,
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wbs.run_bank_sales("wo-1", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "workorder.not_found")
        brain_run.assert_not_called()

    async def test_sa3a_gate_closed_hides_decide_as_404(self):
        from routes import workorder_bank_sales_routes as wbs

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wbs, "pearnly_ai_bank_sales_suggest_enabled_for", return_value=False),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wbs.decide_bank_sales(
                    "wo-1",
                    wbs.BankSalesDecideIn(fingerprint="2569-05-01|100|0", verdict="sales"),
                    mock.Mock(),
                )
        self.assertEqual(ctx.exception.status_code, 404)


def _open_gate_patches(wbs, wr):
    """双闸开 + 鉴权/归属/事务全假件短路(照 test_workorder_routes_contract 范式)。"""
    return (
        mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
        mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
        mock.patch.object(wbs, "pearnly_ai_bank_sales_suggest_enabled_for", return_value=True),
        mock.patch.object(wr, "check_workspace_scope", return_value=None),
        mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
        mock.patch.object(wbs, "db", _FakeDB(_Cur())),
        mock.patch.object(wr, "db", _FakeDB(_Cur())),
        mock.patch.object(wr.store, "get_work_order", return_value={"workspace_client_id": 7}),
    )


class PermCodeWiringTests(unittest.IsolatedAsyncioTestCase):
    """C3 细码:run/decide 都是制单动作,传给 require_perm 的码 = tax.filing.create。"""

    async def _perm_code_used(self, coro):
        from routes import workorder_bank_sales_routes as wbs
        from routes import workorder_routes as wr

        with (
            mock.patch.object(route_helpers, "require_perm", return_value=_USER) as perm,
            mock.patch.object(wbs.bank_sales_brain, "run", return_value={"enabled": True}),
            mock.patch.object(
                wbs.bank_sales_review, "record_bank_sales_decision", return_value={"id": 1}
            ),
        ):
            for p in _open_gate_patches(wbs, wr):
                self.enterContext(p)
            await coro
        self.assertTrue(perm.called, "端点未走 require_perm")
        return perm.call_args[0][1]

    async def test_run_and_decide_use_prepare_code(self):
        from routes import workorder_bank_sales_routes as wbs

        cases = (
            wbs.run_bank_sales("wo-1", mock.Mock()),
            wbs.decide_bank_sales(
                "wo-1",
                wbs.BankSalesDecideIn(fingerprint="2569-05-01|100|0", verdict="sales"),
                mock.Mock(),
            ),
        )
        for coro in cases:
            with self.subTest(coro=coro):
                self.assertEqual(await self._perm_code_used(coro), wbs._C_PREPARE)


class RunEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_gate_open_passes_brain_summary_through(self):
        from routes import workorder_bank_sales_routes as wbs
        from routes import workorder_routes as wr

        summary = {"enabled": True, "asked": 2, "logged": 2, "failed": 0}
        with (
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wbs.bank_sales_brain, "run", return_value=summary) as brain_run,
        ):
            for p in _open_gate_patches(wbs, wr):
                self.enterContext(p)
            out = await wbs.run_bank_sales("wo-1", mock.Mock())
        self.assertEqual(out, {"ok": True, **summary})
        self.assertEqual(brain_run.call_args.kwargs["tenant_id"], "t-1")
        self.assertEqual(brain_run.call_args.kwargs["work_order_id"], "wo-1")


class DecideWildFingerprintTests(unittest.IsolatedAsyncioTestCase):
    async def test_wild_fingerprint_maps_404(self):
        # 真服务层跑:无银行流水事件 → 指纹不存在 → bank_sales_row_not_found → 404。
        from routes import workorder_bank_sales_routes as wbs
        from routes import workorder_routes as wr

        with (
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wbs.bank_sales_review.store, "list_events", return_value=[]),
        ):
            for p in _open_gate_patches(wbs, wr):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await wbs.decide_bank_sales(
                    "wo-1",
                    wbs.BankSalesDecideIn(fingerprint="9999|0|0", verdict="sales"),
                    mock.Mock(),
                )
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "workorder.bank_sales_row_not_found")


if __name__ == "__main__":
    unittest.main()
