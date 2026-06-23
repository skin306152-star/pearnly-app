#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""守门测试 · Express 自治级别路由(PATCH /express-autonomy)。

只合并 config.autonomy(manual/standard/auto·大小写/空白归一)· 不碰其它 config 键 ·
档位非法 400 · 非 express 端点 400。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core import db  # noqa: E402,F401 · 先 import db 避免 partial-init 循环


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None,
    "fastapi not installed",
)
class ExpressAutonomyRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa: F401
        from routes import erp_endpoints_routes as erp_routes

        cls.app_module = app
        cls.erp_routes = erp_routes

    def _client(self):
        from fastapi.testclient import TestClient

        return TestClient(self.app_module.app)

    def _run(self, body, *, adapter="express", update_ok=True):
        app = self.app_module
        erp_routes = self.erp_routes
        ep = {
            "id": "ep-1",
            "adapter": adapter,
            "config": {"account_set": "DATAT", "ar_acc": "11-02-01-00"},
        }
        update_ep = MagicMock(return_value=update_ok)
        with (
            patch.object(erp_routes, "get_current_user_from_request", return_value={"id": "u"}),
            patch.object(erp_routes, "_check_push_access", return_value=None),
            patch.object(app.db, "get_erp_endpoint", return_value=ep),
            patch.object(app.db, "update_erp_endpoint", update_ep),
        ):
            with self._client() as client:
                r = client.patch("/api/erp/endpoints/ep-1/express-autonomy", json=body)
        return r, update_ep

    def test_valid_level_merges_config(self):
        r, update_ep = self._run({"autonomy": "manual"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["autonomy"], "manual")
        cfg = update_ep.call_args.kwargs["config"]
        self.assertEqual(cfg["autonomy"], "manual")
        # 不碰其它 config 键
        self.assertEqual(cfg["account_set"], "DATAT")
        self.assertEqual(cfg["ar_acc"], "11-02-01-00")

    def test_normalizes_case_and_space(self):
        r, _ = self._run({"autonomy": " AUTO "})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["autonomy"], "auto")

    def test_invalid_level_rejected(self):
        r, update_ep = self._run({"autonomy": "bogus"})
        self.assertEqual(r.status_code, 400, r.text)
        update_ep.assert_not_called()

    def test_non_express_rejected(self):
        r, update_ep = self._run({"autonomy": "manual"}, adapter="mrerp")
        self.assertEqual(r.status_code, 400, r.text)
        update_ep.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
