"""Prevent instance startup from mutating tasks owned by another instance."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock


class RuntimeEnvironmentTest(unittest.TestCase):
    def test_platform_config_wins_over_secret_file(self):
        from services.cloud_runtime.entrypoint import load_environment

        with tempfile.TemporaryDirectory() as directory:
            secret = Path(directory) / "env"
            secret.write_text("PEARNLY_RUNTIME_ROLE=worker\nSAMPLE_SECRET=example\n")
            with patch.dict(
                os.environ,
                {"PEARNLY_RUNTIME_ROLE": "web", "PEARNLY_RUNTIME_ENV_FILE": str(secret)},
                clear=True,
            ):
                self.assertEqual(load_environment(), "web")
                self.assertEqual(os.environ["PEARNLY_RUNTIME_ROLE"], "web")
                self.assertEqual(os.environ["SAMPLE_SECRET"], "example")

    def test_missing_secret_fails_closed(self):
        from services.cloud_runtime.entrypoint import load_environment

        with patch.dict(
            os.environ,
            {"PEARNLY_RUNTIME_ROLE": "web", "PEARNLY_RUNTIME_ENV_FILE": "/missing/runtime.env"},
        ):
            with self.assertRaises(RuntimeError):
                load_environment()


class ProxyTest(unittest.IsolatedAsyncioTestCase):
    async def test_web_does_not_expose_task_execution(self):
        from services.cloud_runtime.proxy import WorkerProxy

        app = AsyncMock()
        send = AsyncMock()
        scope = {"type": "http", "path": "/internal/cloud-tasks/run"}
        await WorkerProxy(app, "web")(scope, AsyncMock(), send)
        app.assert_not_awaited()
        self.assertEqual(send.call_args_list[0].args[0]["status"], 404)

    async def test_legacy_deploy_is_disabled_on_both_roles(self):
        from services.cloud_runtime.proxy import WorkerProxy

        for role in ("web", "worker"):
            app, send = AsyncMock(), AsyncMock()
            await WorkerProxy(app, role)(
                {"type": "http", "path": "/internal/deploy/manual"}, AsyncMock(), send
            )
            app.assert_not_awaited()
            self.assertEqual(send.call_args_list[0].args[0]["status"], 410)

    async def test_ordinary_web_route_keeps_application_authentication(self):
        from services.cloud_runtime.proxy import WorkerProxy

        app = AsyncMock()
        await WorkerProxy(app, "web")({"type": "http", "path": "/api/me"}, AsyncMock(), AsyncMock())
        app.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
