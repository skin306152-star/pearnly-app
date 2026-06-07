#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""平台业态套餐 · 真账号 E2E(env-gated · docs/platform-onboarding/03)。

跑真 FastAPI app + 真 DB + 真账号(owner),全程走 HTTP 信封,验:
  1. GET /api/me/modules:信封 + 7 模块全集(含 receivable)+ gateable + business_type 键
  2. PUT /api/me/onboarding:各业态预设翻出正确模块组合 + 回写 business_type
  3. PUT /api/me/modules/{key}:toggle 关→开可逆(关=隐藏不删的可观测代理)
  4. 错误路径:未知业态 platform.unknown_business_type / 未知模块 platform.unknown_module

无 DB / 无凭据 = clean skip(不让 CI 红)。tearDown 把账号模块态恢复原样(自清理)。

跑法:
    export PEARNLY_INTEGRATION_DB=1
    export DATABASE_URL=postgresql://...
    export PEARNLY_E2E_USER=... PEARNLY_E2E_PASS=...
    python -m unittest tests.integration.test_platform_onboarding_integration -v
"""

from __future__ import annotations

import unittest

import unittest as _unittest

from services.modules import presets, store
from tests.integration._helpers import (
    auth_header,
    get_test_client,
    require_db,
    require_test_user,
)


class PlatformOnboardingE2E(unittest.TestCase):
    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = self._login(creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"])
        self.h = auth_header(self.token)
        # 捕获原始态以便 tearDown 恢复(自清理 · 不污染 e2e 账号)
        self._original = self._get_view()

    def tearDown(self) -> None:
        orig = getattr(self, "_original", None)
        if not orig:
            return
        bt = orig.get("business_type")
        if bt and presets.is_known(bt):
            self.client.put("/api/me/onboarding", json={"business_type": bt}, headers=self.h)
        for key, flag in (orig.get("modules") or {}).items():
            self.client.put(
                f"/api/me/modules/{key}",
                json={"enabled": bool(flag.get("enabled"))},
                headers=self.h,
            )

    # ── helpers ──────────────────────────────────────────────
    def _login(self, username: str, password: str) -> str:
        """登录拿 token(主登录 /api/login · 返 {token,user})· 失败 SkipTest 不红 CI。"""
        try:
            resp = self.client.post(
                "/api/login", json={"username": username, "password": password}
            )
        except Exception as e:  # noqa: BLE001
            raise _unittest.SkipTest(f"/api/login 不可达:{e}")
        if resp.status_code != 200:
            raise _unittest.SkipTest(f"/api/login 返 {resp.status_code}:{resp.text[:200]}")
        token = resp.json().get("token")
        if not token:
            raise _unittest.SkipTest(f"/api/login 没返 token:{resp.text[:200]}")
        return token

    def _get_view(self) -> dict:
        resp = self.client.get("/api/me/modules", headers=self.h)
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertTrue(body.get("ok"), body)
        return body["data"]

    def _onboard(self, business_type: str):
        return self.client.put(
            "/api/me/onboarding", json={"business_type": business_type}, headers=self.h
        )

    # ── tests ────────────────────────────────────────────────
    def test_get_modules_shape(self):
        data = self._get_view()
        self.assertEqual(set(data["modules"].keys()), set(store.KNOWN_MODULES))
        self.assertIn("receivable", data["modules"])
        self.assertEqual(set(data["gateable"]), set(store.KNOWN_MODULES))
        self.assertIn("business_type", data)

    def test_onboarding_firm_preset(self):
        body = self._onboard("firm").json()
        self.assertTrue(body.get("ok"), body)
        mods = body["data"]["modules"]
        self.assertEqual(body["data"]["business_type"], "firm")
        for on in ("sales", "expense", "recon", "knowledge"):
            self.assertTrue(mods[on]["enabled"], f"firm 应开 {on}")
        for off in ("inventory", "pos", "receivable"):
            self.assertFalse(mods[off]["enabled"], f"firm 应关 {off}")

    def test_onboarding_retail_preset(self):
        body = self._onboard("retail").json()
        self.assertTrue(body.get("ok"), body)
        mods = body["data"]["modules"]
        self.assertEqual(body["data"]["business_type"], "retail")
        for on in ("sales", "inventory", "pos"):
            self.assertTrue(mods[on]["enabled"], f"retail 应开 {on}")
        for off in ("expense", "recon", "receivable", "knowledge"):
            self.assertFalse(mods[off]["enabled"], f"retail 应关 {off}")

    def test_switch_business_type_overwrites(self):
        self._onboard("firm")
        body = self._onboard("service").json()
        mods = body["data"]["modules"]
        self.assertEqual(body["data"]["business_type"], "service")
        self.assertTrue(mods["expense"]["enabled"])
        # firm 开过的 recon/knowledge,切到 service 后应被关
        self.assertFalse(mods["recon"]["enabled"])
        self.assertFalse(mods["knowledge"]["enabled"])

    def test_toggle_module_off_then_on(self):
        off = self.client.put(
            "/api/me/modules/inventory", json={"enabled": False}, headers=self.h
        ).json()
        self.assertTrue(off.get("ok"), off)
        self.assertFalse(self._get_view()["modules"]["inventory"]["enabled"])
        on = self.client.put(
            "/api/me/modules/inventory", json={"enabled": True}, headers=self.h
        ).json()
        self.assertTrue(on.get("ok"), on)
        self.assertTrue(self._get_view()["modules"]["inventory"]["enabled"])

    def test_unknown_business_type_envelope_error(self):
        resp = self._onboard("casino")
        self.assertEqual(resp.status_code, 400, resp.text)
        body = resp.json()
        self.assertFalse(body.get("ok"))
        self.assertEqual(body["error"]["code"], "platform.unknown_business_type")

    def test_unknown_module_toggle_404(self):
        resp = self.client.put(
            "/api/me/modules/evil", json={"enabled": True}, headers=self.h
        )
        self.assertEqual(resp.status_code, 404, resp.text)
        body = resp.json()
        self.assertFalse(body.get("ok"))
        self.assertEqual(body["error"]["code"], "platform.unknown_module")


if __name__ == "__main__":
    unittest.main()
