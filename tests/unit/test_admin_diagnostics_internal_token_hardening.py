# -*- coding: utf-8 -*-
"""
危险运维端点收紧(2026-07-09 · 安全复核后加固)。

补 4 门:
  1. 错 token(header)→ 403 · 且旧的 URL query token 不再生效
  2. 对 token(header X-Internal-Token)→ 放行
  3. INTERNAL_OPS_ENABLED 关(默认)→ /internal/install-playwright 404(装作不存在)
     ·开关打开后仍要过 token 校验(而非直接放行)
  4. /internal/deploy/status 此前完全无鉴权 · 现在也要挡

真实 subprocess(pip / systemctl / tail)全部 mock 掉 · 不真跑。
GitHub webhook(/internal/deploy · HMAC 签名那条)不在本文件范围 · 见
test_admin_diagnostics_routes_contract.py 的 test_deploy_webhook_present。
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.admin_diagnostics_routes import router

FAKE_SECRET = "s3cr3t-webhook-token"


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class InternalTokenAuthTests(unittest.TestCase):
    """_require_internal_token: header 恒定时间比对 · query 不再生效 · fail-closed。"""

    def setUp(self) -> None:
        self.client = _client()
        self._env = patch.dict(
            "os.environ", {"GITHUB_WEBHOOK_SECRET": FAKE_SECRET, "INTERNAL_OPS_ENABLED": ""}
        )
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_wrong_header_token_is_403(self):
        resp = self.client.get("/internal/deploy/status", headers={"X-Internal-Token": "wrong"})
        self.assertEqual(resp.status_code, 403)

    def test_missing_token_is_403(self):
        resp = self.client.get("/internal/deploy/status")
        self.assertEqual(resp.status_code, 403)

    def test_query_string_token_no_longer_accepted(self):
        """收紧前 ?token=<secret> 能过 · 现在密钥只认 header · query 必须失效。"""
        resp = self.client.get(f"/internal/deploy/status?token={FAKE_SECRET}")
        self.assertEqual(resp.status_code, 403)

    def test_correct_header_token_passes(self):
        with patch("os.path.isfile", return_value=False):
            resp = self.client.get(
                "/internal/deploy/status", headers={"X-Internal-Token": FAKE_SECRET}
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True, "rolled_back": False})

    def test_secret_unconfigured_fails_closed(self):
        """GITHUB_WEBHOOK_SECRET 空 · 即便 header 也传空 · 必须拒绝而非放行。"""
        with patch.dict("os.environ", {"GITHUB_WEBHOOK_SECRET": ""}):
            resp = self.client.get("/internal/deploy/status", headers={"X-Internal-Token": ""})
        self.assertEqual(resp.status_code, 403)

    def test_manual_deploy_trigger_rejects_wrong_token_without_shelling_out(self):
        """错 token 必须在触发部署脚本前就被拦 · subprocess 不该被调用。"""
        with patch("subprocess.Popen") as mock_popen:
            resp = self.client.get("/internal/deploy/manual", headers={"X-Internal-Token": "wrong"})
        self.assertEqual(resp.status_code, 403)
        mock_popen.assert_not_called()

    def test_manual_deploy_trigger_accepts_correct_token(self):
        with patch("subprocess.Popen") as mock_popen:
            resp = self.client.get(
                "/internal/deploy/manual", headers={"X-Internal-Token": FAKE_SECRET}
            )
        self.assertEqual(resp.status_code, 200)
        mock_popen.assert_called_once()

    def test_deploy_log_requires_token(self):
        resp = self.client.get("/internal/deploy/log")
        self.assertEqual(resp.status_code, 403)

    def test_deploy_log_accepts_correct_token(self):
        fake_result = MagicMock(stdout="deploy ok\n")
        with patch("subprocess.run", return_value=fake_result) as mock_run:
            resp = self.client.get(
                "/internal/deploy/log", headers={"X-Internal-Token": FAKE_SECRET}
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True, "log": "deploy ok\n"})
        mock_run.assert_called_once()


class InstallPlaywrightSwitchTests(unittest.TestCase):
    """INTERNAL_OPS_ENABLED 开关:关(默认)= 404 装不存在 · 开 = 仍要过 token。"""

    def setUp(self) -> None:
        self.client = _client()

    def test_switch_off_by_default_is_404_even_with_correct_token(self):
        with patch.dict(
            "os.environ", {"GITHUB_WEBHOOK_SECRET": FAKE_SECRET, "INTERNAL_OPS_ENABLED": ""}
        ):
            resp = self.client.get(
                "/internal/install-playwright", headers={"X-Internal-Token": FAKE_SECRET}
            )
        self.assertEqual(resp.status_code, 404)

    def test_switch_off_hides_route_from_wrong_token_too(self):
        """开关关时不该泄露"路由存在但 token 错"(403)· 一律 404。"""
        with patch.dict(
            "os.environ", {"GITHUB_WEBHOOK_SECRET": FAKE_SECRET, "INTERNAL_OPS_ENABLED": "0"}
        ):
            resp = self.client.get(
                "/internal/install-playwright", headers={"X-Internal-Token": "wrong"}
            )
        self.assertEqual(resp.status_code, 404)

    def test_switch_on_still_requires_correct_token(self):
        with patch.dict(
            "os.environ", {"GITHUB_WEBHOOK_SECRET": FAKE_SECRET, "INTERNAL_OPS_ENABLED": "1"}
        ):
            with patch("subprocess.run") as mock_run:
                resp = self.client.get(
                    "/internal/install-playwright", headers={"X-Internal-Token": "wrong"}
                )
        self.assertEqual(resp.status_code, 403)
        mock_run.assert_not_called()

    def test_switch_on_correct_token_runs_full_install_flow_mocked(self):
        """开关开 + token 对 → 端点应正常跑完(pip/playwright/systemctl 全 mock)。"""
        pip_result = MagicMock(returncode=0, stdout="Successfully installed playwright", stderr="")
        browser_result = MagicMock(returncode=0, stdout="chromium downloaded", stderr="")
        verify_result = MagicMock(returncode=0, stdout="IMPORT_OK · version x", stderr="")

        with patch.dict(
            "os.environ", {"GITHUB_WEBHOOK_SECRET": FAKE_SECRET, "INTERNAL_OPS_ENABLED": "1"}
        ):
            with (
                patch(
                    "subprocess.run", side_effect=[pip_result, browser_result, verify_result]
                ) as mock_run,
                patch("subprocess.Popen") as mock_popen,
            ):
                resp = self.client.get(
                    "/internal/install-playwright", headers={"X-Internal-Token": FAKE_SECRET}
                )

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["step"], "complete")
        self.assertEqual(mock_run.call_count, 3)
        mock_popen.assert_called_once()  # restart scheduled


if __name__ == "__main__":
    unittest.main()
