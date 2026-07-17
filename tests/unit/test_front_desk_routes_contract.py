# -*- coding: utf-8 -*-
"""前门路由契约 + fail-closed 守门(routes/front_desk_routes.py · FD-0a 验收断言①闸关四端点404)。

锁:①四端点按 path+method 注册且挂进 app;②闸关(front_desk 或 m1 任一关)时四端点一律 404
(对存量用户等于不存在);③闭集外/未开放意图在 confirm 被 422 拒(桩层诚实拒,不装懂)。
闸开全链真库跑通(draft→confirm→work_order_items sha256)在 tests/integration。
"""

from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from routes import front_desk_routes as fr
from tests.unit._route_contract_fakes import route_set as _route_set

_USER = {"id": "u1", "tenant_id": "t-1"}
_EXPECTED = {
    ("POST", "/api/ai/front-desk/contracts"),
    ("POST", "/api/ai/front-desk/interpret"),
    ("POST", "/api/ai/front-desk/confirm"),
    ("GET", "/api/ai/front-desk/feed"),
}


class RouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        rs = _route_set(fr.router)
        self.assertTrue(_EXPECTED.issubset(rs), f"缺路由: {_EXPECTED - rs}")

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/ai/front-desk/contracts", paths)


class GateClosedTests(unittest.IsolatedAsyncioTestCase):
    """front_desk 闸关(m1 开但 front_desk 关)→ 四端点 404,fail-closed。"""

    def _patches(self):
        return (
            mock.patch.object(fr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                fr.feature_flags, "pearnly_ai_front_desk_enabled_for", return_value=False
            ),
        )

    async def _assert_404(self, coro):
        with self.assertRaises(HTTPException) as ctx:
            await coro
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_all_four_endpoints_404_when_gate_closed(self):
        p1, p2 = self._patches()
        with p1, p2:
            await self._assert_404(fr.get_feed(mock.Mock()))
            await self._assert_404(fr.create_contract(mock.Mock()))
            await self._assert_404(fr.interpret_goal(fr.InterpretIn(contract_id="c1"), mock.Mock()))
            await self._assert_404(
                fr.confirm_contract(
                    fr.ConfirmIn(
                        contract_id="c1",
                        workspace_client_id=7,
                        period="2569-05",
                        intent="monthly_vat",
                    ),
                    mock.Mock(),
                )
            )

    async def test_m1_closed_also_404(self):
        # authorize_pearnly_ai 内部 m1 关即抛 404(front_desk 组合闸也含 m1),此处模拟 m1 关。
        with mock.patch.object(
            fr, "authorize_pearnly_ai", side_effect=HTTPException(404, detail=fr._NOT_FOUND)
        ):
            with self.assertRaises(HTTPException) as ctx:
                await fr.get_feed(mock.Mock())
            self.assertEqual(ctx.exception.status_code, 404)


class StatusProbeTests(unittest.IsolatedAsyncioTestCase):
    """S4(2026-07-17):/status 探针不走闸 404——闸关也 200 {enabled:false},console 零噪音。"""

    async def _status(self, enabled):
        with (
            mock.patch.object(fr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                fr.feature_flags, "pearnly_ai_front_desk_enabled_for", return_value=enabled
            ),
        ):
            return await fr.get_status(mock.Mock())

    async def test_gate_closed_returns_enabled_false_not_404(self):
        self.assertEqual(await self._status(False), {"enabled": False})

    async def test_gate_open_returns_enabled_true(self):
        self.assertEqual(await self._status(True), {"enabled": True})


class DisabledIntentTests(unittest.IsolatedAsyncioTestCase):
    """闸开但确认未开放/闭集外意图 → 422(诚实拒,不装懂 · 不开工单)。"""

    async def test_confirm_rejects_disabled_intent_422(self):
        with (
            mock.patch.object(fr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                fr.feature_flags, "pearnly_ai_front_desk_enabled_for", return_value=True
            ),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await fr.confirm_contract(
                    fr.ConfirmIn(
                        contract_id="c1",
                        workspace_client_id=7,
                        period="2569-05",
                        intent="digitize",  # 在册但未开放
                    ),
                    mock.Mock(),
                )
        self.assertEqual(ctx.exception.status_code, 422)


class BadPeriodTests(unittest.IsolatedAsyncioTestCase):
    """期间必须是佛历 YYYY-MM(工单全链纪年)——公历/畸形值 422 fail-fast,不开错税期工单。"""

    async def _confirm(self, period):
        with (
            mock.patch.object(fr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                fr.feature_flags, "pearnly_ai_front_desk_enabled_for", return_value=True
            ),
        ):
            await fr.confirm_contract(
                fr.ConfirmIn(
                    contract_id="c1",
                    workspace_client_id=7,
                    period=period,
                    intent="monthly_vat",
                ),
                mock.Mock(),
            )

    async def test_confirm_rejects_gregorian_period_422(self):
        with self.assertRaises(HTTPException) as ctx:
            await self._confirm("2026-06")
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail["code"], "front_desk.bad_period")

    async def test_confirm_rejects_bad_month_422(self):
        with self.assertRaises(HTTPException) as ctx:
            await self._confirm("2569-13")
        self.assertEqual(ctx.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
