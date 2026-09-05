"""Cloud delivery safety: persist-first, fixed dispatch, and no blind side-effect replay."""

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi import HTTPException
from starlette.requests import Request

from services.cloud_tasks import dispatch, registry, routes, store


class DispatchTests(unittest.TestCase):
    def test_persisted_task_survives_transport_failure(self):
        with (
            patch.object(store, "insert", return_value="saved") as insert,
            patch.object(dispatch, "deliver", side_effect=RuntimeError("network unavailable")),
        ):
            self.assertEqual(
                dispatch.enqueue("workorder.advance", "tenant", "order", "owner"), "saved"
            )
        insert.assert_called_once_with(
            "workorder.advance", {"args": ("tenant", "order", "owner"), "kwargs": {}}
        )

    def test_serving_roles_cannot_create_transport_schema(self):
        for role in ("web", "worker"):
            with (
                self.subTest(role=role),
                patch.dict(os.environ, PEARNLY_RUNTIME_ROLE=role),
                patch.object(store, "get_cursor") as cursor,
            ):
                with self.assertRaisesRegex(RuntimeError, "requires_release_job"):
                    store.ensure_table()
                cursor.assert_not_called()

    def test_unknown_handler_never_persists(self):
        with patch.object(store, "insert") as insert:
            with self.assertRaises(ValueError):
                dispatch.enqueue("os.system", "echo rejected")
        insert.assert_not_called()

    def test_cloud_spawn_never_constructs_local_coroutine(self):
        function = Mock()
        with (
            patch.dict(os.environ, PEARNLY_RUNTIME_ROLE="worker"),
            patch.object(dispatch, "enqueue", return_value="id") as enqueue,
        ):
            dispatch.spawn("dms.image", function, {"tenant_id": "t"}, "u", "message")
        function.assert_not_called()
        enqueue.assert_called_once_with("dms.image", {"tenant_id": "t"}, "u", "message")

    def test_binary_payload_rejected_before_database(self):
        with patch.object(store, "get_cursor") as cursor:
            with self.assertRaises(TypeError):
                store.insert("dms.image", {"content": b"private bytes"})
        cursor.assert_not_called()

    def test_cloud_pdf_failure_does_not_undo_completed_ocr_response(self):
        from routes.ocr_recognize_routes import _schedule_pdf_backfill

        with (
            patch.dict(os.environ, PEARNLY_RUNTIME_ROLE="worker"),
            patch(
                "services.ocr.pdf_backfill.generate_and_save_pdf", side_effect=OSError("storage")
            ),
        ):
            _schedule_pdf_backfill({"id": "user", "tenant_id": "tenant"}, b"image", [], ["id"])

    def test_registry_resolves_only_code_owned_functions(self):
        for name, (module, attribute) in registry.HANDLERS.items():
            with self.subTest(name=name):
                imported = __import__(module, fromlist=[attribute])
                self.assertTrue(callable(getattr(imported, attribute)))


class DeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_completed_duplicate_does_not_execute(self):
        with (
            patch.object(store, "claim", return_value={"status": "succeeded"}),
            patch.object(registry, "execute", new_callable=AsyncMock) as execute,
        ):
            result = await routes.run_delivery(routes.Delivery(task_id=uuid4()))
        self.assertEqual(result["status"], "succeeded")
        execute.assert_not_called()

    async def test_concurrent_delivery_is_retryable_without_execution(self):
        with (
            patch.object(store, "claim", return_value={"status": "running"}),
            patch.object(registry, "execute", new_callable=AsyncMock) as execute,
        ):
            with self.assertRaises(HTTPException) as error:
                await routes.run_delivery(routes.Delivery(task_id=uuid4()))
        self.assertEqual(error.exception.status_code, 409)
        execute.assert_not_called()

    async def test_execution_error_recorded_and_not_blindly_retried(self):
        task_id = uuid4()
        row = {"handler": "erp.auto_push", "payload": {"args": [], "kwargs": {}}}
        with (
            patch.object(store, "claim", return_value=row),
            patch.object(
                registry,
                "execute",
                new_callable=AsyncMock,
                side_effect=RuntimeError("remote uncertain"),
            ),
            patch.object(store, "finish") as finish,
        ):
            result = await routes.run_delivery(routes.Delivery(task_id=task_id))
        self.assertEqual(result, {"status": "failed"})
        finish.assert_called_once_with(str(task_id), "failed", "RuntimeError")

    async def test_cancelled_execution_is_uncertain(self):
        task_id = uuid4()
        with (
            patch.object(
                store,
                "claim",
                return_value={"handler": "erp.auto_push", "payload": {"args": [], "kwargs": {}}},
            ),
            patch.object(
                registry, "execute", new_callable=AsyncMock, side_effect=asyncio.CancelledError
            ),
            patch.object(store, "finish") as finish,
        ):
            with self.assertRaises(asyncio.CancelledError):
                await routes.run_delivery(routes.Delivery(task_id=task_id))
        finish.assert_called_once_with(str(task_id), "uncertain", "request_cancelled")

    async def test_internal_route_requires_worker_and_matching_secret(self):
        request = Request({"type": "http", "headers": [(b"x-pearnly-task-key", b"expected")]})
        with patch.dict(
            os.environ, PEARNLY_RUNTIME_ROLE="web", PEARNLY_TASK_SHARED_SECRET="expected"
        ):
            with self.assertRaises(HTTPException) as error:
                await routes.require_task_caller(request)
            self.assertEqual(error.exception.status_code, 404)
        with patch.dict(
            os.environ, PEARNLY_RUNTIME_ROLE="worker", PEARNLY_TASK_SHARED_SECRET="different"
        ):
            with self.assertRaises(HTTPException) as error:
                await routes.require_task_caller(request)
            self.assertEqual(error.exception.status_code, 403)
        with patch.dict(
            os.environ, PEARNLY_RUNTIME_ROLE="worker", PEARNLY_TASK_SHARED_SECRET="expected"
        ):
            await routes.require_task_caller(request)


if __name__ == "__main__":
    unittest.main()
