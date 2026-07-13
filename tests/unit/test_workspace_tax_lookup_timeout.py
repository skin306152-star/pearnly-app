# -*- coding: utf-8 -*-
"""
tests/unit/test_workspace_tax_lookup_timeout.py

MC1-b0(2026-07-13)· /ai 建客户模态复用主站税号带出端点(routes/workspace_routes.py::
workspace_tax_lookup),该端点已有 tests/unit/test_workspace_routes_contract.py::
TaxLookupBehaviorTests 覆盖命中(回填)与 not_found(查不到)两态。这里补第三态:
services.rd.rd_api.lookup_vat 对 RD SOAP 超时/网络失败诚实降级返 {ok:False,
error:"rd_unreachable"}(不抛异常,见 services/rd/rd_api.py::_soap_post 的
requests.Timeout 分支),路由层原样透传 ok:false,不吞错、不假装成功。
"""

from __future__ import annotations

import unittest
from unittest import mock


class TaxLookupTimeoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_rd_unreachable_degrades_honestly(self):
        from routes import workspace_routes as wr

        with (
            mock.patch.object(wr, "require_perm", return_value={"id": "u1"}),
            mock.patch(
                "services.rd.rd_api.lookup_vat",
                return_value={"ok": False, "error": "rd_unreachable"},
            ),
        ):
            out = await wr.workspace_tax_lookup("0105546015062", mock.Mock(), branch=0)
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "rd_unreachable")

    async def test_route_never_raises_on_downstream_timeout(self):
        """外呼超时不应该变成一个 500——诚实降级是返回 ok:false,不是抛异常断请求。"""
        from routes import workspace_routes as wr

        with (
            mock.patch.object(wr, "require_perm", return_value={"id": "u1"}),
            mock.patch(
                "services.rd.rd_api.lookup_vat",
                return_value={"ok": False, "error": "rd_unreachable"},
            ),
        ):
            out = await wr.workspace_tax_lookup("0105546015062", mock.Mock(), branch=0)
        self.assertIsInstance(out, dict)
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
