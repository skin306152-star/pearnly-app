# -*- coding: utf-8 -*-
"""POS Google Sheet 留档设置路由契约(老板后台 · 按账套隔离)· 复用 pos_payment_routes 同款守门。"""

import inspect
import unittest
from unittest.mock import patch

from starlette.requests import Request


def _request():
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/pos/admin/sheets-settings",
            "query_string": b"",
            "headers": [],
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


class _CursorCtx:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb):
        return False


class RoutesContractTests(unittest.TestCase):
    def test_router_registers_get_put(self):
        from routes.pos_sheets_routes import router

        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(
            got,
            {
                ("GET", "/api/pos/admin/sheets-settings"),
                ("PUT", "/api/pos/admin/sheets-settings"),
            },
        )

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/pos/admin/sheets-settings", paths)

    def test_owner_and_module_gated(self):
        from routes import pos_sheets_routes

        src = inspect.getsource(pos_sheets_routes)
        self.assertIn('require_perm_pos(request, "pos.admin.manage")', src)
        self.assertIn('assert_module_enabled(cur, tid, "pos")', src)
        self.assertIn("require_workspace", src)

    def test_registered_in_agent_registry_as_app_exclusive(self):
        import json
        from pathlib import Path

        registry = json.loads(
            (Path(__file__).resolve().parents[2] / "docs/agent/agent_registry.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(registry.get("pos_sheets_routes"), "C")


class GetRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_merges_credential_and_settings(self):
        from routes import pos_sheets_routes as psr

        with (
            patch.object(
                psr,
                "require_perm_pos",
                return_value={"tenant_id": "t-1", "workspace_client_id": 7},
            ),
            patch.object(psr.db, "get_cursor_rls", return_value=_CursorCtx()),
            patch.object(psr, "assert_module_enabled"),
            patch.object(psr, "require_workspace"),
            patch.object(
                psr.google_store,
                "get_credential",
                return_value={"google_email": "a@b.com"},
            ),
            patch.object(
                psr.svc,
                "get_settings",
                return_value={"spreadsheet_id": "SS1", "tab_name": "POS", "enabled": True},
            ),
        ):
            body = await psr.api_get_sheets_settings(_request(), workspace_client_id=7)

        self.assertTrue(body["ok"])
        self.assertEqual(
            body["data"],
            {
                "spreadsheet_id": "SS1",
                "tab_name": "POS",
                "enabled": True,
                "connected": True,
                "email": "a@b.com",
            },
        )

    async def test_not_connected_shows_empty_email(self):
        from routes import pos_sheets_routes as psr

        with (
            patch.object(
                psr,
                "require_perm_pos",
                return_value={"tenant_id": "t-1", "workspace_client_id": 7},
            ),
            patch.object(psr.db, "get_cursor_rls", return_value=_CursorCtx()),
            patch.object(psr, "assert_module_enabled"),
            patch.object(psr, "require_workspace"),
            patch.object(psr.google_store, "get_credential", return_value=None),
            patch.object(
                psr.svc,
                "get_settings",
                return_value={"spreadsheet_id": "", "tab_name": "POS", "enabled": False},
            ),
        ):
            body = await psr.api_get_sheets_settings(_request(), workspace_client_id=7)

        self.assertFalse(body["data"]["connected"])
        self.assertEqual(body["data"]["email"], "")


if __name__ == "__main__":
    unittest.main()
