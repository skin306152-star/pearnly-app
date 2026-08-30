# -*- coding: utf-8 -*-
"""Required transaction-local ERP lifecycle audit contracts."""

from __future__ import annotations

import unittest
from unittest import mock

from core import db as _db  # noqa: F401  # complete DAL re-exports before importing the store
from services.audit import store


class TransactionalAuditTests(unittest.TestCase):
    def test_uses_caller_cursor_without_commit_or_error_swallowing(self):
        cur = mock.Mock()

        store.insert_operation_log_tx(
            cur,
            tenant_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            actor_user_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            actor_username="owner@example.com",
            actor_is_super=False,
            action="erp.endpoint.bind",
            target_type="erp_endpoint",
            target_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
            target_name="Office Express",
            details={
                "workspace_client_id": 7,
                "generation_before": 1,
                "generation_after": 2,
                "profile_changed": True,
            },
        )

        cur.execute.assert_called_once()
        self.assertNotIn("commit", cur.execute.call_args.args[0].lower())

        cur.execute.side_effect = RuntimeError("audit unavailable")
        with self.assertRaisesRegex(RuntimeError, "audit unavailable"):
            store.insert_operation_log_tx(
                cur,
                tenant_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                actor_user_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                actor_username="owner@example.com",
                actor_is_super=False,
                action="erp.endpoint.revoke",
                target_type="erp_endpoint",
                target_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
                details={"workspace_client_id": 7},
            )

    def test_rejects_unknown_and_sensitive_detail_keys(self):
        allowed = {
            "workspace_client_id": 7,
            "generation_before": 1,
            "generation_after": 2,
            "enabled_before": True,
            "enabled_after": False,
            "shared_scope_before": True,
            "shared_scope_after": False,
            "profile_changed": False,
            "reason": "owner_request",
        }
        store.insert_operation_log_tx(
            mock.Mock(),
            tenant_id="tenant",
            actor_user_id="actor",
            actor_username="owner",
            actor_is_super=False,
            action="erp.endpoint.disable",
            target_type="erp_endpoint",
            target_id="endpoint",
            details=allowed,
        )

        for key in (
            "token",
            "token_hash",
            "token_tail",
            "raw_path",
            "account_dir",
            "profile_key",
            "catalog",
            "device",
            "unexpected",
        ):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    store.insert_operation_log_tx(
                        mock.Mock(),
                        tenant_id="tenant",
                        actor_user_id="actor",
                        actor_username="owner",
                        actor_is_super=False,
                        action="erp.endpoint.bind",
                        target_type="erp_endpoint",
                        target_id="endpoint",
                        details={key: "secret"},
                    )

        for details in (
            {"reason": {"token": "secret"}},
            {"generation_after": True},
            {"profile_changed": {"secret": "value"}},
        ):
            with self.subTest(details=details):
                with self.assertRaises(ValueError):
                    store.insert_operation_log_tx(
                        mock.Mock(),
                        tenant_id="tenant",
                        actor_user_id="actor",
                        actor_username="owner",
                        actor_is_super=False,
                        action="erp.endpoint.bind",
                        target_type="erp_endpoint",
                        target_id="endpoint",
                        details=details,
                    )

    def test_rejects_missing_required_identity(self):
        with self.assertRaises(ValueError):
            store.insert_operation_log_tx(
                mock.Mock(),
                tenant_id="",
                actor_user_id="actor",
                actor_username="owner",
                actor_is_super=False,
                action="erp.endpoint.bind",
                target_type="erp_endpoint",
                target_id="endpoint",
            )
        with self.assertRaises(ValueError):
            store.insert_operation_log_tx(
                mock.Mock(),
                tenant_id="tenant",
                actor_user_id="actor",
                actor_username="owner",
                actor_is_super=False,
                action="erp.endpoint.bind",
                target_type="erp_endpoint",
                target_id="",
            )


if __name__ == "__main__":
    unittest.main()
