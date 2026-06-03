#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_dms_endpoint_routes.py

DMS 集成(2026-05-31)· 创建/更新 mrerp_dms endpoint 守门(TestClient + mock · 无真 DB)。

钉死:
  1. 凭据加密:wizard 发的明文 username_enc/password_enc 必须经 kms 加密后才落库
     (走 adapter in ENCRYPTED_CRED_ADAPTERS 路径 · 不再硬编码 == 'mrerp')。
  2. auto_push 兜底:mrerp_dms 无论前端发什么 · 落库 auto_push 必须 False
     (防发票自动推送误投 DMS)。
  3. id_card_auto_push 配置原样保留(身份证自动推送开关)。
  4. 响应不回明文凭据(_strip_endpoint_for_response 抹成 ***)。
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

_HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None
try:
    from core import kms_helper  # noqa: F401

    _HAS_KMS = True
except Exception:
    _HAS_KMS = False


@unittest.skipUnless(_HAS_FASTAPI and _HAS_KMS, "needs fastapi + kms_helper importable")
class MrerpDmsEndpointCreateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa
        from routes import erp_endpoints_routes  # noqa

        cls.app_module = app
        cls.routes = erp_endpoints_routes

    def _client(self):
        from fastapi.testclient import TestClient

        return TestClient(self.app_module.app)

    def _run_create(self, body, auto_push_allowed=True):
        """POST /api/erp/endpoints with all DB + auth + kms patched.
        Returns (response, captured_create_kwargs)."""
        captured = {}

        def _fake_create(user_id, name, adapter, config, is_default=False, auto_push=False):
            captured["config"] = config
            captured["auto_push"] = auto_push
            captured["adapter"] = adapter
            return "new-dms-id"

        def _fake_get(user_id, endpoint_id):
            return {
                "id": "new-dms-id",
                "adapter": "mrerp_dms",
                "config": dict(captured.get("config") or {}),
                "enabled": True,
                "auto_push": captured.get("auto_push", False),
            }

        app = self.app_module
        with (
            patch.object(
                self.routes,
                "get_current_user_from_request",
                return_value={"id": "u-1", "plan": "pro"},
            ),
            patch.object(self.routes, "_check_push_access", return_value=None),
            patch.object(
                self.routes,
                "_plan_permissions",
                return_value={"endpoints_limit": -1, "can_auto_push_erp": auto_push_allowed},
            ),
            patch.object(app.db, "list_erp_endpoints", return_value=[]),
            patch.object(app.db, "create_erp_endpoint", side_effect=_fake_create),
            patch.object(app.db, "get_erp_endpoint", side_effect=_fake_get),
            patch("core.kms_helper.encrypt_str", side_effect=lambda v: "ENC:" + v),
            patch("core.kms_helper.is_encrypted", side_effect=lambda v: str(v).startswith("ENC:")),
        ):
            with self._client() as client:
                r = client.post("/api/erp/endpoints", json=body)
        return r, captured

    def test_creds_encrypted_and_auto_push_forced_false(self):
        body = {
            "name": "MR.ERP DMS",
            "adapter": "mrerp_dms",
            "config": {
                "system_url": "https://www.mrerp4sme.com/dms/index.php",
                "username_enc": "dmsuser",  # plaintext from wizard
                "password_enc": "dmspass",
                "id_card_auto_push": True,
                "booking_defaults": {"booking_prefix": "PN"},
            },
            "is_default": False,
            "auto_push": True,  # even if frontend sends true...
        }
        r, captured = self._run_create(body)
        self.assertEqual(r.status_code, 200, r.text)
        cfg = captured["config"]
        # 1. credentials encrypted (not stored plaintext)
        self.assertEqual(cfg["username_enc"], "ENC:dmsuser")
        self.assertEqual(cfg["password_enc"], "ENC:dmspass")
        self.assertNotIn("dmsuser", cfg["password_enc"])
        # 2. auto_push forced False for mrerp_dms (anti-misroute)
        self.assertFalse(captured["auto_push"])
        # 3. id_card_auto_push preserved
        self.assertTrue(cfg["id_card_auto_push"])
        # 4. response strips plaintext creds
        body_out = r.json()
        out_cfg = body_out.get("config", {})
        self.assertEqual(out_cfg.get("username_enc"), "***")
        self.assertEqual(out_cfg.get("password_enc"), "***")

    def test_already_encrypted_creds_not_double_encrypted(self):
        body = {
            "name": "MR.ERP DMS",
            "adapter": "mrerp_dms",
            "config": {
                "system_url": "https://www.mrerp4sme.com/dms/index.php",
                "username_enc": "ENC:already",  # looks like ciphertext
                "password_enc": "ENC:already2",
                "id_card_auto_push": True,
            },
            "is_default": False,
            "auto_push": False,
        }
        r, captured = self._run_create(body)
        self.assertEqual(r.status_code, 200, r.text)
        # is_encrypted → True, so no re-encryption (no double ENC: prefix)
        self.assertEqual(captured["config"]["username_enc"], "ENC:already")
        self.assertEqual(captured["config"]["password_enc"], "ENC:already2")


if __name__ == "__main__":
    unittest.main()
