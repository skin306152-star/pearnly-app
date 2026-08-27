"""ERP 与 Cowork 产品边界守门。

两套入口共享平台底座，但不建立商户与事务所关系，也不投递单据副本。
Alembic 0104/0105 是已部署迁移历史，不属于运行时接线。
"""

from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from routes import admin_erp_routes, history_routes, registry
from services import background_loops, startup
from services.intake_bridge import convert

ROOT = Path(__file__).resolve().parents[2]


class ErpCoworkIndependenceContractTests(unittest.TestCase):
    def test_relationship_runtime_modules_are_removed(self):
        removed = (
            ROOT / "routes" / "accounting_engagement_routes.py",
            ROOT / "services" / "accounting_engagement",
            ROOT / "services" / "client_submission",
        )
        for path in removed:
            self.assertFalse(path.exists(), str(path))

    def test_erp_invite_has_no_firm_binding_input_or_route(self):
        self.assertEqual(
            set(admin_erp_routes.InviteBody.model_fields),
            {"username_or_email", "password"},
        )
        paths = {route.path for route in admin_erp_routes.router.routes}
        self.assertNotIn("/api/admin/erp/firms", paths)
        self.assertNotIn("firm_tenant_id", inspect.getsource(admin_erp_routes.erp_invite))

    def test_confirmed_documents_never_enqueue_cowork_delivery(self):
        history_source = inspect.getsource(history_routes.ocr_convert_documents)
        convert_source = inspect.getsource(convert)
        self.assertNotIn("client_submission", history_source)
        self.assertNotIn("client_submission", convert_source)
        self.assertNotIn("enqueue_client_submissions", history_source)

    def test_startup_and_recovery_have_no_delivery_worker(self):
        self.assertNotIn("accounting_engagement", inspect.getsource(startup._boot_schema_ddl))
        recovery_source = inspect.getsource(background_loops.run_recovery_tick)
        self.assertNotIn("client_submission", recovery_source)
        self.assertFalse(hasattr(background_loops, "run_client_submission_tick"))

    def test_relationship_router_is_not_registered(self):
        self.assertFalse(hasattr(registry, "accounting_engagement_router"))
        self.assertNotIn(
            "accounting_engagement_router",
            {getattr(router, "__name__", "") for router in registry.ROUTERS},
        )


if __name__ == "__main__":
    unittest.main()
