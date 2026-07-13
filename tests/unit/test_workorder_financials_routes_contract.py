# -*- coding: utf-8 -*-
"""N1 P0-3(报表看得到、拿不走)+ 交付物下载守门(routes/workorder_financials_routes.py)。

覆盖两组端点:①GET .../financials/download(月度报表 PDF/Excel)②GET .../deliverables、
GET .../deliverables/{kind}(交付物清单/单件下载)——两组同属"下载已生成产物",2026-07
拆分时并进同一文件,鉴权/归属校验共用 routes/workorder_routes.py 的 _authorize/_load_order。

锁定:①端点注册且挂进 app ②financials/download:format 只认 pdf|xlsx,别的值 422;
financials 未算到(闸关/未到 reconcile)→ 404,不返回半截文件;成功路径返回真 PDF/xlsx
字节 + Content-Disposition 带客户名+账期(RFC 5987),取不到客户名诚实退回 fallback 名,
不拼假名字 ③deliverables/{kind}:未登记的 kind → 404,不碰磁盘 ④C3:两个端点传给
require_perm 的细码是 tax.filing.view。真实渲染在 tests/unit/test_financials_pdf.py 覆盖,
这里只锁路由层的分支/鉴权/文件名契约。
"""

from __future__ import annotations

import unittest
from decimal import Decimal
from unittest import mock

from fastapi import HTTPException

from core import route_helpers
from routes import workorder_financials_routes as wfr
from routes import workorder_routes as wr
from routes.workorder_financials_routes import router as financials_router
from services.accounting import workorder_financials, workorder_shadow_adapter

_USER = {"id": "u1", "tenant_id": "t-1"}
_WO = {"id": "wo-1", "workspace_client_id": 7, "period": "2569-05"}


def _golden_detail():
    shadow = workorder_shadow_adapter.build_shadow(
        purchase_entries=[{"net": Decimal("1000"), "vat": Decimal("70"), "grand": Decimal("1070")}],
        sales_amount=Decimal("5000"),
        output_vat=Decimal("350"),
        period="2569-05",
    )
    fin = workorder_financials.build_financials(shadow.as_gate_payload(), period="2569-05")
    return {"financials": fin}


class _CM:
    def __enter__(self):
        return mock.Mock()

    def __exit__(self, *a):
        return False


class _FakeDB:
    def get_cursor(self, commit=False):
        return _CM()


_DELIVERABLE_PATHS = (
    "/api/workorder/orders/{work_order_id}/deliverables",
    "/api/workorder/orders/{work_order_id}/deliverables/{kind}",
)


class RouteContractTests(unittest.TestCase):
    def test_registered(self):
        paths = {getattr(r, "path", None) for r in financials_router.routes}
        self.assertIn("/api/workorder/orders/{work_order_id}/financials/download", paths)
        for p in _DELIVERABLE_PATHS:
            self.assertIn(p, paths)

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/workorder/orders/{work_order_id}/financials/download", paths)
        for p in _DELIVERABLE_PATHS:
            self.assertIn(p, paths)


class DownloadBehaviorTests(unittest.IsolatedAsyncioTestCase):
    def _wire(self):
        return (
            mock.patch.object(wfr, "_authorize", return_value=(_USER, "t-1")),
            mock.patch.object(wfr, "_load_order", return_value=dict(_WO)),
            mock.patch.object(wfr, "db", _FakeDB()),
        )

    async def test_bad_format_is_422(self):
        with self.assertRaises(HTTPException) as ctx:
            await wfr.download_financials_report("wo-1", mock.Mock(), format="docx", lang="th")
        self.assertEqual(ctx.exception.status_code, 422)

    async def test_no_financials_yet_is_404(self):
        p1, p2, p3 = self._wire()
        with (
            p1,
            p2,
            p3,
            mock.patch.object(wfr.api, "order_detail", return_value={"financials": None}),
            mock.patch.object(wfr, "_client_name_for_order", return_value="Sister Makeup"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wfr.download_financials_report("wo-1", mock.Mock(), format="pdf", lang="th")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_pdf_success_filename_has_client_and_period(self):
        p1, p2, p3 = self._wire()
        with (
            p1,
            p2,
            p3,
            mock.patch.object(wfr.api, "order_detail", return_value=_golden_detail()),
            mock.patch.object(wfr, "_client_name_for_order", return_value="Sister Makeup"),
        ):
            resp = await wfr.download_financials_report(
                "wo-1", mock.Mock(), format="pdf", lang="th"
            )
        self.assertEqual(resp.media_type, "application/pdf")
        self.assertTrue(bytes(resp.body).startswith(b"%PDF"))
        disp = resp.headers["content-disposition"]
        self.assertIn("2569-05", disp)
        # RFC 5987:泰文原名走 filename*=UTF-8''<percent-encoded>,不是裸塞进 filename=。
        self.assertIn("filename*=UTF-8''", disp)
        self.assertIn("financials_wo-1.pdf", disp)  # ASCII fallback

    async def test_xlsx_success(self):
        p1, p2, p3 = self._wire()
        with (
            p1,
            p2,
            p3,
            mock.patch.object(wfr.api, "order_detail", return_value=_golden_detail()),
            mock.patch.object(wfr, "_client_name_for_order", return_value="Sister Makeup"),
        ):
            resp = await wfr.download_financials_report(
                "wo-1", mock.Mock(), format="xlsx", lang="th"
            )
        self.assertEqual(
            resp.media_type,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertGreater(len(resp.body), 100)

    async def test_client_name_lookup_failure_falls_back_honestly(self):
        # 客户名查不到(边缘态)不拼假名字——文件名退回 financials_<period>。
        p1, p2, p3 = self._wire()
        with (
            p1,
            p2,
            p3,
            mock.patch.object(wfr.api, "order_detail", return_value=_golden_detail()),
            mock.patch.object(wfr, "_client_name_for_order", return_value=""),
        ):
            resp = await wfr.download_financials_report(
                "wo-1", mock.Mock(), format="pdf", lang="th"
            )
        disp = resp.headers["content-disposition"]
        self.assertIn("financials_2569-05.pdf", disp)


class DeliverablesGuardTests(unittest.IsolatedAsyncioTestCase):
    """GET .../deliverables/{kind}:未登记的 kind → 404,短路不碰磁盘。"""

    async def test_unregistered_kind_is_404_without_touching_disk(self):
        wo = {"workspace_client_id": 7}
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wfr, "db", _FakeDB()),
            # _client_name_for_order 仍定义在 workorder_routes.py,持独立 db 名字绑定
            # (见 test_workorder_deliverable_filename_contract.py 同款注记)。
            mock.patch.object(wr, "db", _FakeDB()),
            mock.patch.object(wr.store, "get_work_order", return_value=wo),
            mock.patch.object(wfr.api, "deliverable_artifact_path", return_value=None),
            mock.patch.object(wfr.storage, "resolve_within_order") as resolve,
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wfr.download_deliverable("wo-1", "pp30_draft", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)
        resolve.assert_not_called()  # 未登记就短路,不进磁盘解析


class DeliverablesPermCodeTests(unittest.IsolatedAsyncioTestCase):
    """C3 拍板2 闸点表落地:list_order_deliverables / download_deliverable 传给
    require_perm 的细码须为 tax.filing.view(同 _C_VIEW)。做法同
    test_workorder_routes_contract.PermCodeWiringTests:只需 _authorize 成功即可捕获
    传入的码,之后无论下游怎么炸都不影响本测试目的。"""

    async def _perm_code_used(self, coro):
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wfr, "db", _FakeDB()),
            mock.patch.object(wr, "db", _FakeDB()),
            mock.patch.object(wr.store, "get_work_order", return_value={"workspace_client_id": 7}),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER) as perm,
        ):
            try:
                await coro
            except Exception:
                pass
        self.assertTrue(perm.called, "端点未走 require_perm")
        return perm.call_args[0][1]

    async def test_endpoint_perm_codes_match_gate_table(self):
        cases = (
            (wfr.list_order_deliverables("wo-1", mock.Mock()), wfr._C_VIEW),
            (wfr.download_deliverable("wo-1", "pp30_draft", mock.Mock()), wfr._C_VIEW),
        )
        for coro, expected in cases:
            with self.subTest(expected=expected):
                got = await self._perm_code_used(coro)
                self.assertEqual(got, expected)


if __name__ == "__main__":
    unittest.main()
