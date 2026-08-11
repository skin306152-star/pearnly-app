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


@unittest.skipUnless(_HAS_FASTAPI and _HAS_KMS, "needs fastapi + kms_helper importable")
class MrerpDmsEndpointPatchPreserveTests(unittest.TestCase):
    """PATCH 整包替换 config 的防丢层(2026-08-12)。

    向导表单从不携带钉死顾问(booking_defaults.advisor_* = 提成归属出路)、
    id_card_auto_push 与凭据密文——整包替换会把它们静默抹掉(G-QA7 战役实锤
    归属漂移的代价)。钉死:缺席=保留,显式携带(含空串)=按来值;非 DMS
    adapter 不受此层影响。
    """

    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa
        from routes import erp_endpoints_routes  # noqa

        cls.app_module = app
        cls.routes = erp_endpoints_routes

    def _run_patch(self, body, existing):
        from unittest.mock import AsyncMock

        from services.erp import ssrf_guard

        captured = {}

        def _fake_update(user_id, endpoint_id, **fields):
            captured.update(fields)
            return True

        app = self.app_module
        with (
            patch.object(
                self.routes,
                "get_current_user_from_request",
                return_value={"id": "u-1", "plan": "pro"},
            ),
            patch.object(self.routes, "_check_push_access", return_value=None),
            patch.object(app.db, "get_erp_endpoint", return_value=dict(existing)),
            patch.object(app.db, "update_erp_endpoint", side_effect=_fake_update),
            patch.object(ssrf_guard, "assert_public_config_url", new=AsyncMock()),
            patch("core.kms_helper.encrypt_str", side_effect=lambda v: "ENC:" + v),
            patch("core.kms_helper.is_encrypted", side_effect=lambda v: str(v).startswith("ENC:")),
        ):
            with self._client() as client:
                r = client.patch("/api/erp/endpoints/ep-1", json=body)
        return r, captured

    def _client(self):
        from fastapi.testclient import TestClient

        return TestClient(self.app_module.app)

    _EXISTING_DMS = {
        "id": "ep-1",
        "adapter": "mrerp_dms",
        "enabled": True,
        "config": {
            "system_url": "https://www.mrerp4sme.com/dms/index.php",
            "username_enc": "ENC:old-u",
            "password_enc": "ENC:old-p",
            "admin_username_enc": "ENC:old-au",
            "admin_password_enc": "ENC:old-ap",
            "id_card_auto_push": True,
            "booking_defaults": {
                "booking_prefix": "ZX",
                "advisor_id": "42",
                "advisor_name": "เถ้าแก่",
            },
        },
    }

    def test_wizard_shape_patch_keeps_pin_flags_and_creds(self):
        # 向导保存的真实形状:只有 system_url + 新账密 + booking_prefix。
        body = {
            "config": {
                "system_url": "https://www.mrerp4sme.com/dms/index.php",
                "username_enc": "new-u",
                "password_enc": "new-p",
                "booking_defaults": {"booking_prefix": "PN"},
            }
        }
        r, captured = self._run_patch(body, self._EXISTING_DMS)
        self.assertEqual(r.status_code, 200, r.text)
        cfg = captured["config"]
        self.assertEqual(
            cfg["booking_defaults"],
            {"booking_prefix": "PN", "advisor_id": "42", "advisor_name": "เถ้าแก่"},
        )
        self.assertTrue(cfg["id_card_auto_push"])
        self.assertEqual(cfg["admin_username_enc"], "ENC:old-au")
        self.assertEqual(cfg["admin_password_enc"], "ENC:old-ap")
        self.assertEqual(cfg["username_enc"], "ENC:new-u")  # 新明文照旧走加密

    def test_explicit_values_still_win_including_clear(self):
        body = {
            "config": {
                "system_url": "https://www.mrerp4sme.com/dms/index.php",
                "id_card_auto_push": False,
                "booking_defaults": {"booking_prefix": "PN", "advisor_id": ""},
            }
        }
        r, captured = self._run_patch(body, self._EXISTING_DMS)
        self.assertEqual(r.status_code, 200, r.text)
        cfg = captured["config"]
        self.assertEqual(cfg["booking_defaults"]["advisor_id"], "")  # 显式清空生效
        self.assertFalse(cfg["id_card_auto_push"])
        self.assertEqual(cfg["username_enc"], "ENC:old-u")  # 未携带仍保留

    def test_non_dms_adapter_keeps_wholesale_replace(self):
        existing = {
            "id": "ep-1",
            "adapter": "mrerp",
            "enabled": True,
            "config": {"token": "T", "custom_flag": 1},
        }
        body = {"config": {"token": "***"}}
        r, captured = self._run_patch(body, existing)
        self.assertEqual(r.status_code, 200, r.text)
        cfg = captured["config"]
        self.assertEqual(cfg["token"], "T")  # *** 占位保留是既有行为
        self.assertNotIn("custom_flag", cfg)  # 非 DMS 不做缺席保留,整包替换语义不变


if __name__ == "__main__":
    unittest.main()
