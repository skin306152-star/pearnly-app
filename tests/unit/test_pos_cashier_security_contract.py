import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.pages_routes import router

ROOT = Path(__file__).resolve().parents[2]


class PosCashierSecurityContractTests(unittest.TestCase):
    def test_cashier_has_strict_script_policy(self):
        app = FastAPI()
        app.include_router(router)
        response = TestClient(app).get("/cashier")
        policy = response.headers["content-security-policy"]
        script = next(part for part in policy.split(";") if "script-src" in part)
        self.assertIn("script-src 'self'", script)
        self.assertNotIn("'unsafe-inline'", script)
        self.assertNotIn("'unsafe-eval'", script)

    def test_cashier_does_not_load_platform_token(self):
        source = (ROOT / "static/pos/pos.js").read_text(encoding="utf-8")
        self.assertNotIn("localStorage.getItem('mrpilot_token')", source)
        self.assertNotIn("pearnly_active_workspace_client_id", source)
        self.assertIn("state.token = null", source)

    def test_cashier_worker_uses_pos_allowlist(self):
        source = (ROOT / "static/pos/cashier-sw.js").read_text(encoding="utf-8")
        self.assertIn("isCashierAsset(url.pathname)", source)
        self.assertIn("pathname === '/static/dist/pos.js'", source)
        self.assertNotIn("url.pathname.startsWith('/api/')", source)


if __name__ == "__main__":
    unittest.main()
