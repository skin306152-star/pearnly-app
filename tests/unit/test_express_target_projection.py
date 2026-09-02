from __future__ import annotations

import unittest
from unittest import mock

from services.erp import express_target_projection as projection


class _Cursor:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.statements = []

    def execute(self, sql, params=None):
        self.statements.append((sql, params))

    def fetchone(self):
        return self.endpoint


class _CursorContext:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, *_args):
        return False


class ExpressTargetProjectionTests(unittest.TestCase):
    def setUp(self):
        self.endpoint = {
            "id": "11111111-1111-4111-8111-111111111111",
            "tenant_id": "22222222-2222-4222-8222-222222222222",
            "owner_tenant_id": "22222222-2222-4222-8222-222222222222",
            "binding_generation": 1,
        }
        self.body = {
            "account_set": r"C:\EXPRESS\TEST",
            "account_dir": r"C:\EXPRESS\TEST",
            "account_sets": [
                {
                    "code": "TEST",
                    "name": "Test Company",
                    "path": r"C:\EXPRESS\TEST",
                    "writable": True,
                }
            ],
            "accounts": [{"code": "1100", "name": "Cash", "type": "A"}],
            "catalog": {
                "products": [{"code": "P01", "name": "Product 1", "kind": "stock"}],
                "customers": [
                    {
                        "code": "C01",
                        "name": "Customer 1",
                        "tax_id": "123",
                        "branch": "00000",
                    }
                ],
            },
            "companion_version": "1.1.70",
        }

    def _ingest(self, body):
        cursor = _Cursor(self.endpoint)
        with (
            mock.patch.object(projection.db, "get_cursor", return_value=_CursorContext(cursor)),
            mock.patch.object(
                projection,
                "publish_with_cursor",
                side_effect=[
                    {"published": True, "revision": 2},
                    {"published": True, "revision": 3},
                ],
            ) as publish,
        ):
            result = projection.ingest_express_heartbeat(self.endpoint["id"], body)
        return result, publish

    def test_catalog_heartbeat_publishes_endpoint_and_account_set_snapshots(self):
        result, publish = self._ingest(self.body)

        self.assertTrue(result["published"])
        self.assertEqual(publish.call_count, 2)
        endpoint_projection = publish.call_args_list[0].kwargs["projection"]
        account_projection = publish.call_args_list[1].kwargs["projection"]
        self.assertEqual(endpoint_projection.scope_kind, "endpoint")
        self.assertEqual(len(endpoint_projection.account_sets), 1)
        self.assertEqual(account_projection.scope_key, r"c:\express\test")
        self.assertEqual(account_projection.entity_counts["products"], 1)
        self.assertEqual(account_projection.entity_counts["customers"], 1)
        self.assertEqual(account_projection.entity_counts["accounts"], 1)
        self.assertEqual(account_projection.collector["adapter_version"], "1.1.70")

    def test_heartbeat_without_catalog_never_replaces_account_set_masters(self):
        body = {key: value for key, value in self.body.items() if key != "catalog"}
        result, publish = self._ingest(body)

        self.assertTrue(result["published"])
        self.assertEqual(publish.call_count, 1)
        self.assertEqual(publish.call_args.kwargs["projection"].scope_kind, "endpoint")

    def test_omitted_account_sets_keeps_old_companion_selected_account_compatibility(self):
        body = {key: value for key, value in self.body.items() if key != "account_sets"}
        result, publish = self._ingest(body)

        self.assertTrue(result["published"])
        self.assertEqual(publish.call_count, 2)
        endpoint_projection = publish.call_args_list[0].kwargs["projection"]
        self.assertEqual(
            [row["source_id"] for row in endpoint_projection.account_sets],
            [r"c:\express\test"],
        )

    def test_empty_reported_scan_fails_refresh_and_preserves_snapshot(self):
        body = {
            **self.body,
            "account_sets": [],
            "master_refresh_request_id": "33333333-3333-4333-8333-333333333333",
            "master_refresh_scope": "endpoint",
        }
        cursor = _Cursor(self.endpoint)
        with (
            mock.patch.object(
                projection.db,
                "get_cursor",
                return_value=_CursorContext(cursor),
            ),
            mock.patch.object(projection, "publish_with_cursor") as publish,
            mock.patch.object(
                projection,
                "record_refresh_state_with_cursor",
            ) as record_failure,
            mock.patch(
                "services.erp.target_refresh.complete_express_refresh_with_cursor",
                return_value=True,
            ) as complete,
        ):
            result = projection.ingest_express_heartbeat(self.endpoint["id"], body)

        self.assertFalse(result["published"])
        self.assertEqual(result["reason"], "account_sets_empty")
        self.assertEqual(result["error_code"], "ERR_ACCOUNT_SET_EMPTY")
        publish.assert_not_called()
        record_failure.assert_called_once_with(
            cursor,
            tenant_id=self.endpoint["tenant_id"],
            endpoint_id=self.endpoint["id"],
            account_set_key=None,
            status="error",
            observed_at=mock.ANY,
            collector={"kind": "companion", "adapter_version": "1.1.70"},
            error_code="ERR_ACCOUNT_SET_EMPTY",
        )
        complete.assert_called_once_with(
            cursor,
            request_id=body["master_refresh_request_id"],
            endpoint_id=self.endpoint["id"],
            account_set_key=r"c:\express\test",
            scope_kind="endpoint",
            error_code="ERR_ACCOUNT_SET_EMPTY",
        )

    def test_duplicate_or_uncoded_rows_are_removed_at_ingestion_boundary(self):
        body = dict(self.body)
        body["catalog"] = {
            "products": [
                {"code": "P01", "name": "First"},
                {"code": "P01", "name": "Duplicate"},
                {"name": "No code"},
            ],
            "customers": [],
        }
        _, publish = self._ingest(body)

        account_projection = publish.call_args_list[1].kwargs["projection"]
        self.assertEqual(
            [row["label"] for row in account_projection.masters["products"]], ["First"]
        )

    def test_refresh_ack_publishes_the_requested_account_not_current_profile(self):
        body = dict(self.body)
        body["account_sets"] = [
            *self.body["account_sets"],
            {
                "code": "NEW",
                "name": "New Company",
                "path": r"C:\EXPRESS\NEW",
                "writable": True,
            },
        ]
        body.update(
            {
                "master_refresh_request_id": "33333333-3333-4333-8333-333333333333",
                "master_refresh_scope": "account_set",
                "master_refresh_account_set": r"c:\express\new",
            }
        )
        with mock.patch(
            "services.erp.target_refresh.complete_express_refresh_with_cursor",
            return_value=True,
        ) as complete:
            _, publish = self._ingest(body)

        account_projection = publish.call_args_list[1].kwargs["projection"]
        self.assertEqual(account_projection.scope_key, r"c:\express\new")
        complete.assert_called_once()
        self.assertEqual(complete.call_args.kwargs["scope_kind"], "account_set")


if __name__ == "__main__":
    unittest.main()
