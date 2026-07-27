# -*- coding: utf-8 -*-
"""前门路由契约 + fail-closed 守门(routes/front_desk_routes.py · FD-0a 验收断言①闸关四端点404)。

锁:①四端点按 path+method 注册且挂进 app;②闸关(front_desk 或 m1 任一关)时四端点一律 404
(对存量用户等于不存在);③闭集外/未开放意图在 confirm 被 422 拒(桩层诚实拒,不装懂);
④带料建合同先过余额闸(与工单补料端点同一条:不够跑 402,一个字节都没读)。
闸开全链真库跑通(draft→confirm→work_order_items sha256)在 tests/integration。
"""

from __future__ import annotations

import os
import unittest
from unittest import mock

from fastapi import HTTPException

from routes import front_desk_routes as fr
from services.workorder.steps import ocr_balance
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


class _FakeUpload:
    """总台上传替身:read 被调过就说明闸没拦住(料读完落盘建单之后再说「没钱」= 白读)。"""

    def __init__(self, filename="a.jpg"):
        self.filename = filename
        self.reads = 0

    async def read(self, _limit=None):
        self.reads += 1
        return b"\x89PNG\r\n"


class _NoopCursor:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


class BalanceGateTests(unittest.IsolatedAsyncioTestCase):
    """总台带料建合同 = /ai 第二条入料路径,与工单补料端点共用同一条余额闸,行为不许分叉。"""

    def setUp(self):
        os.environ[ocr_balance._FLAG_ENV] = "1"
        self.addCleanup(os.environ.pop, ocr_balance._FLAG_ENV, None)

    async def _post(self, upload, status):
        with (
            mock.patch.object(fr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                fr.feature_flags, "pearnly_ai_front_desk_enabled_for", return_value=True
            ),
            mock.patch.object(fr.contract_store, "ensure_once", lambda: None),
            mock.patch.object(fr.db, "get_cursor", _NoopCursor),
            mock.patch.object(ocr_balance, "_billing_status", lambda uid, tid: dict(status)),
            mock.patch.object(ocr_balance, "_estimate", lambda used, pages: 1.5),
            mock.patch.object(ocr_balance, "resolve_billing_user", lambda cur, tid, cid: "u-owner"),
        ):
            return await fr.create_contract(
                mock.Mock(),
                workspace_client_id=7,
                period=None,
                intent=None,
                files=[upload],
            )

    async def test_insufficient_balance_blocks_before_reading_any_byte(self):
        upload = _FakeUpload()
        with self.assertRaises(HTTPException) as ctx:
            await self._post(upload, {"allowed": False, "balance_thb": 0.0})
        self.assertEqual(ctx.exception.status_code, 402)
        self.assertEqual(ctx.exception.detail["code"], "insufficient_balance")
        self.assertEqual(upload.reads, 0)  # 一个字节都没读

    async def test_exempt_account_is_not_blocked(self):
        # 放行即进段一读文件(下游 create_draft 未打桩会抛,但闸已经放过去了 = 本例要的信号)。
        upload = _FakeUpload()
        with self.assertRaises(Exception) as ctx:
            await self._post(upload, {"allowed": False, "is_exempt": True})
        self.assertNotIsInstance(ctx.exception, HTTPException)
        self.assertEqual(upload.reads, 1)


if __name__ == "__main__":
    unittest.main()
