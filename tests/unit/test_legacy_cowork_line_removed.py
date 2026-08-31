"""Removal contract for the retired Cowork LINE product."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD_ROUTE_MODULES = (
    "routes/line_routes.py",
    "routes/line_liff_routes.py",
    "routes/client_pool_routes.py",
    "routes/admin_agent_routes.py",
    "routes/notification_routes.py",
)
OLD_SERVICE_PACKAGES = (
    "services/line_binding",
    "services/agent",
    "services/notification",
)
OLD_SERVICE_MODULES = ("services/expense/conversation.py",)
OLD_ROUTE_PATHS = (
    "/api/line/liff/auth",
    "/api/line/liff/config",
    "/liff/purchase/",
    "/api/ai/client-pool",
    "/api/admin/agent/overview",
    "/api/notifications/",
)
ACTIVE_WEBHOOKS = (
    ("routes/cowork_line_webhook_routes.py", "/api/line/webhook"),
    ("routes/line_dms_webhook_routes.py", "/api/line/dms/webhook"),
    ("routes/line_erp_routes.py", "/api/line/erp/webhook"),
)


def _python_sources(*roots: str) -> list[Path]:
    sources: list[Path] = []
    for rel in roots:
        path = ROOT / rel
        if path.is_file():
            sources.append(path)
        elif path.is_dir():
            sources.extend(sorted(path.rglob("*.py")))
    return sources


class LegacyCoworkLineRemovalTests(unittest.TestCase):
    def test_legacy_package_and_routes_are_absent(self):
        for rel in OLD_SERVICE_PACKAGES + OLD_SERVICE_MODULES:
            with self.subTest(module=rel):
                self.assertFalse((ROOT / rel).exists())
        for rel in OLD_ROUTE_MODULES:
            with self.subTest(module=rel):
                self.assertFalse((ROOT / rel).exists())

    def test_legacy_route_paths_are_absent(self):
        route_source = "\n".join(
            path.read_text(encoding="utf-8") for path in _python_sources("routes")
        )
        for path in OLD_ROUTE_PATHS:
            with self.subTest(path=path):
                self.assertNotIn(path, route_source)

    def test_production_python_has_no_legacy_import(self):
        offenders = []
        for path in _python_sources("app.py", "core", "routes", "services"):
            source = path.read_text(encoding="utf-8")
            if "services.line_binding" in source or "from services import line_binding" in source:
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_three_product_webhooks_remain_registered(self):
        registry = (ROOT / "routes/registry.py").read_text(encoding="utf-8")
        for rel, path in ACTIVE_WEBHOOKS:
            with self.subTest(route=rel):
                source = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn(path, source)
                self.assertIn(Path(rel).stem, registry)

    def test_production_python_never_references_legacy_binding_tables(self):
        offenders = []
        for path in _python_sources("app.py", "core", "routes", "services"):
            source = path.read_text(encoding="utf-8")
            if "line_bindings" in source or "line_binding_codes" in source:
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
