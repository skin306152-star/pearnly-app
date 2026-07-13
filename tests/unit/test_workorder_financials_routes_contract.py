# -*- coding: utf-8 -*-
"""N1 P0-3(报表看得到、拿不走)守门:GET /api/workorder/orders/{id}/financials/download。

锁定:①端点注册且挂进 app ②format 只认 pdf|xlsx,别的值 422 ③financials 未算到(闸关/
未到 reconcile)→ 404,不返回半截文件 ④成功路径返回真 PDF/xlsx 字节 + Content-Disposition
带客户名+账期(RFC 5987),取不到客户名诚实退回 fallback 名,不拼假名字。真实渲染在
tests/unit/test_financials_pdf.py 覆盖,这里只锁路由层的分支/鉴权/文件名契约。
"""

from __future__ import annotations

import unittest
from decimal import Decimal
from unittest import mock

from fastapi import HTTPException

from routes import workorder_financials_routes as wfr
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


class RouteContractTests(unittest.TestCase):
    def test_registered(self):
        paths = {getattr(r, "path", None) for r in financials_router.routes}
        self.assertIn("/api/workorder/orders/{work_order_id}/financials/download", paths)

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/workorder/orders/{work_order_id}/financials/download", paths)


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


if __name__ == "__main__":
    unittest.main()
