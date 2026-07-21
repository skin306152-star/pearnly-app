# -*- coding: utf-8 -*-
"""守门测试 · Express 记账画像路由(推送前预览 + 画像确认)。

钉死:
  - 非 express 端点 → gate=na(不猜、不假装有预览)。
  - express 端点 + 上报目录 + 有行项目 → 返回真 gate + 画像(预览 items 走真推送同一拍平)。
  - 画像确认校验 posting_mode(非法值 400)· 合法值合并进 config.posting_profile。

无真 DB:mock 掉 get_erp_endpoint / get_ocr_history_detail / _merge_config。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None,
    "fastapi not installed",
)
class PostingPreviewRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa: F401
        from routes import erp_posting_preview_routes as pp_routes  # noqa: F401

        cls.app_module = app
        cls.pp = pp_routes

    def _client(self):
        from fastapi.testclient import TestClient

        return TestClient(self.app_module.app)

    def _history(self, *names):
        """构造带行项目的历史记录(pages[].fields.items 结构 · 真推送读这里)。"""
        return {
            "id": "h-1",
            "pages": [{"fields": {"items": [{"name": n} for n in names]}}],
        }

    def _run_preview(self, body, *, endpoint, history=None):
        app = self.app_module
        pp = self.pp
        with (
            patch.object(pp, "get_current_user_from_request", return_value={"id": "u"}),
            patch.object(pp, "_check_push_access", return_value=None),
            patch.object(pp, "_tid", return_value="t-1"),
            patch.object(app.db, "get_erp_endpoint", return_value=endpoint),
            patch.object(app.db, "get_ocr_history_detail", return_value=history),
        ):
            with self._client() as client:
                return client.post("/api/erp/posting-preview", json=body)

    def test_non_express_returns_na(self):
        r = self._run_preview(
            {"history_ids": ["h-1"], "endpoint_id": "ep-1"},
            endpoint={"id": "ep-1", "adapter": "mrerp", "config": {}},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json(), {"gate": "na", "reason": "not_express"})

    def test_endpoint_not_found_404(self):
        r = self._run_preview({"history_ids": ["h-1"], "endpoint_id": "nope"}, endpoint=None)
        self.assertEqual(r.status_code, 404, r.text)

    def test_express_returns_real_gate(self):
        # 骨架精确命中(空格/声调无关)→ reuse;零库存主档 → 画像 non_stock 已定 → gate ok。
        endpoint = {
            "id": "ep-1",
            "adapter": "express",
            "config": {
                "reported_products": [{"code": "P1", "name": "น้ำแข็งหลอด", "kind": "non_stock"}],
                "catalog_fingerprint": {"stock_master_count": 0},
            },
        }
        r = self._run_preview(
            {"history_ids": ["h-1"], "endpoint_id": "ep-1"},
            endpoint=endpoint,
            history=self._history("น้ำแข็ง หลอด"),
        )
        self.assertEqual(r.status_code, 200, r.text)
        b = r.json()
        self.assertEqual(b["gate"], "ok")
        self.assertEqual(b["profile"]["posting_mode"], "non_stock")
        self.assertFalse(b["profile"]["needs_confirm"])
        self.assertEqual(b["summary"]["reuse"], 1)
        self.assertEqual(b["items"][0]["status"], "reuse")

    def test_express_missing_history_skips(self):
        # 历史查不到 → 跳过该单不炸;无行 → gate 落 ok(空批)。
        r = self._run_preview(
            {"history_ids": ["gone"], "endpoint_id": "ep-1"},
            endpoint={"id": "ep-1", "adapter": "express", "config": {}},
            history=None,
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["items"], [])


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None,
    "fastapi not installed",
)
class PostingProfileWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa: F401
        from routes import erp_posting_preview_routes as pp_routes  # noqa: F401

        cls.app_module = app
        cls.pp = pp_routes

    def _client(self):
        from fastapi.testclient import TestClient

        return TestClient(self.app_module.app)

    _UNSET = object()

    def _run_profile(self, body, *, endpoint=_UNSET, merge=None):
        app = self.app_module
        pp = self.pp
        if endpoint is self._UNSET:
            endpoint = {"id": "ep-1", "adapter": "express"}
        merge = merge if merge is not None else MagicMock(return_value=True)
        with (
            patch.object(pp, "get_current_user_from_request", return_value={"id": "u"}),
            patch.object(pp, "_check_push_access", return_value=None),
            patch.object(app.db, "get_erp_endpoint", return_value=endpoint),
            patch.object(pp, "_merge_config", merge),
        ):
            with self._client() as client:
                return client.post("/api/erp/posting-profile", json=body), merge

    def test_valid_mode_persists(self):
        r, merge = self._run_profile(
            {"endpoint_id": "ep-1", "posting_mode": "non_stock", "inventory_usage": "none"}
        )
        self.assertEqual(r.status_code, 200, r.text)
        b = r.json()
        self.assertTrue(b["ok"])
        self.assertEqual(b["posting_profile"]["posting_mode"], "non_stock")
        # config.posting_profile 键合并进去(而非顶层散写)。
        patch_arg = merge.call_args.args[1]
        self.assertEqual(patch_arg["posting_profile"]["inventory_usage"], "none")

    def test_bad_mode_rejected(self):
        r, merge = self._run_profile({"endpoint_id": "ep-1", "posting_mode": "sideways"})
        self.assertEqual(r.status_code, 400, r.text)
        merge.assert_not_called()

    def test_non_express_rejected(self):
        r, merge = self._run_profile(
            {"endpoint_id": "ep-1", "posting_mode": "non_stock"},
            endpoint={"id": "ep-1", "adapter": "mrerp"},
        )
        self.assertEqual(r.status_code, 400, r.text)
        merge.assert_not_called()

    def test_endpoint_not_found_404(self):
        r, merge = self._run_profile(
            {"endpoint_id": "gone", "posting_mode": "non_stock"}, endpoint=None
        )
        self.assertEqual(r.status_code, 404, r.text)
        merge.assert_not_called()


if __name__ == "__main__":
    unittest.main()
