"""关系 DAL、参与方隔离与状态迁移契约。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest import mock

from services.accounting_engagement import access, lifecycle, store
from services.accounting_engagement.errors import (
    FORBIDDEN,
    PRIMARY_EXISTS,
    WORKSPACE_MISMATCH,
    EngagementError,
)


class Cursor:
    def __init__(self, *, one=None, many=None):
        self.one = one
        self.many = many or []
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.many


def row(**overrides):
    data = {
        "id": "eng-1",
        "firm_tenant_id": "firm-a",
        "merchant_tenant_id": "merchant-a",
        "status": "pending_merchant",
        "is_primary": True,
        "firm_workspace_client_id": None,
        "merchant_workspace_client_id": None,
        "merchant_accepted_at": None,
        "firm_accepted_at": None,
        "active_from": None,
    }
    data.update(overrides)
    return data


class StoreAndAccessTests(unittest.TestCase):
    def test_create_pending_requires_active_profile_and_non_firm_merchant(self):
        cursor = Cursor(one=row())
        result = store.create_pending(
            cursor,
            firm_tenant_id="firm-a",
            merchant_tenant_id="merchant-a",
            created_by_admin_user_id="admin-a",
        )
        sql, params = cursor.calls[0]
        self.assertEqual(result["id"], "eng-1")
        self.assertIn("accounting_firm_profiles", sql)
        self.assertIn("p.status = 'active'", sql)
        self.assertIn("f.status = 'active'", sql)
        self.assertIn("m.status = 'active'", sql)
        self.assertIn("m.tenant_type_v2 IS DISTINCT FROM 'f_firm'", sql)
        self.assertEqual(params, ("admin-a", "merchant-a", "firm-a"))

    def test_list_is_scoped_to_either_participant(self):
        cursor = Cursor(many=[row()])
        store.list_for_tenant(cursor, tenant_id="firm-a")
        sql, params = cursor.calls[0]
        self.assertIn("firm_tenant_id = %s::uuid OR merchant_tenant_id = %s::uuid", sql)
        self.assertEqual(params, ("firm-a", "firm-a"))

    def test_participant_and_workspace_guards(self):
        self.assertEqual(access.require_participant(row(), "firm-a"), "firm")
        self.assertEqual(access.require_participant(row(), "merchant-a"), "merchant")
        with self.assertRaises(EngagementError) as forbidden:
            access.require_participant(row(), "other")
        self.assertEqual(forbidden.exception.code, FORBIDDEN)

        cursor = Cursor(one=None)
        with self.assertRaises(EngagementError) as mismatch:
            access.require_workspace_owner(cursor, tenant_id="merchant-a", workspace_client_id=9)
        self.assertEqual(mismatch.exception.code, WORKSPACE_MISMATCH)
        self.assertEqual(cursor.calls[0][1], (9, "merchant-a"))


class LifecycleTests(unittest.TestCase):
    def test_invite_is_idempotent_for_same_firm_and_rejects_transfer_by_overwrite(self):
        existing = row()
        with mock.patch.object(store, "get_open_for_merchant", return_value=existing):
            self.assertIs(
                lifecycle.invite(
                    mock.Mock(),
                    firm_tenant_id="firm-a",
                    merchant_tenant_id="merchant-a",
                    admin_user_id="admin-a",
                ),
                existing,
            )
        with mock.patch.object(
            store, "get_open_for_merchant", return_value=row(firm_tenant_id="firm-b")
        ):
            with self.assertRaises(EngagementError) as conflict:
                lifecycle.invite(
                    mock.Mock(),
                    firm_tenant_id="firm-a",
                    merchant_tenant_id="merchant-a",
                    admin_user_id="admin-a",
                )
        self.assertEqual(conflict.exception.code, PRIMARY_EXISTS)

    def test_merchant_accept_reuses_same_confirmation(self):
        accepted = row(
            status="pending_firm",
            merchant_workspace_client_id=7,
            merchant_accepted_at=datetime.now(timezone.utc),
        )
        with mock.patch.object(store, "get_by_id", return_value=accepted):
            result = lifecycle.accept_merchant(
                mock.Mock(),
                engagement_id="eng-1",
                merchant_tenant_id="merchant-a",
                workspace_client_id=7,
            )
        self.assertIs(result, accepted)

    def test_firm_accept_checks_active_firm_and_workspace_before_activation(self):
        pending = row(
            status="pending_firm",
            merchant_workspace_client_id=7,
            merchant_accepted_at=datetime.now(timezone.utc),
        )
        activated = row(status="active", firm_workspace_client_id=8)
        with (
            mock.patch.object(store, "get_by_id", return_value=pending),
            mock.patch.object(access, "require_active_firm") as active_firm,
            mock.patch.object(access, "require_workspace_owner") as owner,
            mock.patch.object(lifecycle, "_now_sql", return_value=datetime.now(timezone.utc)),
            mock.patch.object(store, "update_fields", return_value=activated) as update,
        ):
            result = lifecycle.accept_firm(
                mock.Mock(),
                engagement_id="eng-1",
                firm_tenant_id="firm-a",
                workspace_client_id=8,
            )
        self.assertIs(result, activated)
        active_firm.assert_called_once_with(mock.ANY, tenant_id="firm-a")
        owner.assert_called_once_with(mock.ANY, tenant_id="firm-a", workspace_client_id=8)
        self.assertEqual(update.call_args.kwargs["fields"]["status"], "active")


if __name__ == "__main__":
    unittest.main()
