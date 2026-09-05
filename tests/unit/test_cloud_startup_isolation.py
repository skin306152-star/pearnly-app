"""Cloud instance creation must not execute VM migration or recovery effects."""

import os
import unittest
from unittest.mock import Mock, patch


class CloudStartupIsolationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cloud_startup_only_validates_schema_and_does_not_spawn_tasks(self):
        from services import startup

        for role in ("web", "worker"):
            with self.subTest(role=role):
                database = Mock()
                with (
                    patch.dict(os.environ, {"PEARNLY_RUNTIME_ROLE": role}),
                    patch.object(startup, "db", database),
                    patch.object(startup, "_boot_schema_ddl") as ddl,
                    patch.object(startup, "ensure_user_profile_columns") as profile,
                    patch.object(startup, "ensure_playwright_installed") as playwright,
                    patch.object(startup.asyncio, "create_task") as spawn,
                    patch(
                        "services.erp.shared_express_readiness.initialize_serving_schema"
                    ) as verify,
                    patch("builtins.open") as disk,
                ):
                    result = await startup.run_startup()
                self.assertEqual(result, {"email_task": None, "erp_retry_task": None})
                self.assertEqual(database.mock_calls, [])
                verify.assert_called_once_with()
                for effect in (ddl, profile, playwright, spawn, disk):
                    effect.assert_not_called()

    async def test_cloud_schema_validation_failure_blocks_startup(self):
        from services import startup

        with (
            patch.dict(os.environ, PEARNLY_RUNTIME_ROLE="worker"),
            patch(
                "services.erp.shared_express_readiness.initialize_serving_schema",
                side_effect=RuntimeError("missing ERP guard"),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "missing ERP guard"):
                await startup.run_startup()


if __name__ == "__main__":
    unittest.main()
