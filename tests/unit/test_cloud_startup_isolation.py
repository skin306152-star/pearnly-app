"""Cloud instance creation must not execute VM migration or recovery effects."""

import os
import unittest
from unittest.mock import Mock, patch


class CloudStartupIsolationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cloud_startup_does_not_call_database_or_spawn_background_tasks(self):
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
                    patch.object(startup.asyncio, "to_thread") as threaded,
                    patch("builtins.open") as disk,
                ):
                    result = await startup.run_startup()
                self.assertEqual(result, {"email_task": None, "erp_retry_task": None})
                self.assertEqual(database.mock_calls, [])
                for effect in (ddl, profile, playwright, spawn, threaded, disk):
                    effect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
