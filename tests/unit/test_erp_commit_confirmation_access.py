# -*- coding: utf-8 -*-
"""Atomic commit gate for flag-on shared ERP confirmation."""

import unittest
from unittest import mock

from fastapi import HTTPException

from services.intake_bridge import erp_confirmation_access as access

TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ACTOR = "11111111-1111-1111-1111-111111111111"
PURCHASE_HISTORY = "cccccccc-cccc-cccc-cccc-cccccccc0001"
SALES_HISTORY = "cccccccc-cccc-cccc-cccc-cccccccc0002"
WORKSPACE = 101


class _Context:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *_args):
        return False


class ErpCommitConfirmationAccessTests(unittest.TestCase):
    def test_nonshared_entries_and_disabled_shared_entries_are_legacy(self):
        cases = [
            ({"id": ACTOR, "entry": entry}, True)
            for entry in ("pos", "ai", "dms", "daily", None, "unknown")
        ]
        cases.extend(({"id": ACTOR, "entry": entry}, False) for entry in ("main", "cowork", "erp"))
        for user, enabled in cases:
            with self.subTest(entry=user["entry"], enabled=enabled):
                with (
                    mock.patch.object(
                        access,
                        "erp_shared_express_endpoint_enabled_for",
                        return_value=enabled,
                    ) as flag,
                    mock.patch.object(access.db, "get_cursor_rls") as get_cursor,
                ):
                    result = access.commit_shared_confirmation(
                        mock.sentinel.request, user, TENANT, [PURCHASE_HISTORY]
                    )
                self.assertIsNone(result)
                get_cursor.assert_not_called()
                if user["entry"] not in ("main", "cowork", "erp"):
                    flag.assert_not_called()

    def test_success_is_one_transaction_and_actor_workspace_scoped(self):
        cur = mock.Mock(rowcount=2)
        user = {"id": ACTOR, "tenant_id": TENANT, "entry": "cowork"}
        preflight = access.ConfirmationPreflight(
            directions=("purchase", "sales"),
            required_permissions=("purchase.doc.create", "sales.doc.create"),
            history_directions=(
                (PURCHASE_HISTORY, "purchase"),
                (SALES_HISTORY, "sales"),
            ),
        )
        with (
            mock.patch.object(access, "erp_shared_express_endpoint_enabled_for", return_value=True),
            mock.patch.object(access, "require_erp_portal") as entrance,
            mock.patch.object(access.db, "get_cursor_rls", return_value=_Context(cur)) as cursor,
            mock.patch.object(
                access, "_snapshot_commit_workspace", return_value=WORKSPACE
            ) as lock_batch,
            mock.patch.object(access, "_shared_preflight", return_value=preflight) as guard,
            mock.patch.object(access, "_require_formal_conversion") as formal,
        ):
            result = access.commit_shared_confirmation(
                mock.sentinel.request,
                user,
                TENANT,
                [PURCHASE_HISTORY, SALES_HISTORY],
            )
        self.assertEqual(result, 2)
        entrance.assert_called_once_with(user)
        cursor.assert_called_once_with(tenant_id=TENANT, user_id=ACTOR, commit=True)
        lock_batch.assert_called_once()
        guard.assert_called_once()
        formal.assert_called_once()
        sql, params = cur.execute.call_args.args
        self.assertIn("user_id = %s::uuid", sql)
        self.assertIn("workspace_client_id = %s", sql)
        self.assertIn("staged = TRUE", sql)
        self.assertEqual(
            params,
            ([PURCHASE_HISTORY, SALES_HISTORY], TENANT, ACTOR, WORKSPACE),
        )

    def test_permission_history_and_conversion_failures_never_update(self):
        user = {"id": ACTOR, "tenant_id": TENANT, "entry": "erp"}
        preflight = access.ConfirmationPreflight(
            ("purchase",),
            ("purchase.doc.create", "purchase.doc.approve"),
            ((PURCHASE_HISTORY, "purchase"),),
        )
        for stage in ("permission", "history", "formal"):
            with self.subTest(stage=stage):
                cur = mock.Mock(rowcount=0)

                def lock_batch(*_args, **_kwargs):
                    if stage == "history":
                        raise HTTPException(404, detail="history.not_found")
                    return WORKSPACE

                def check_access(*_args, **_kwargs):
                    if stage == "permission":
                        raise HTTPException(403, detail="authz.forbidden")
                    return preflight

                def check_formal(*_args, **_kwargs):
                    if stage == "formal":
                        raise HTTPException(
                            409,
                            detail={
                                "code": "erp.formal_document_required",
                                "history_ids": [PURCHASE_HISTORY],
                            },
                        )

                with (
                    mock.patch.object(
                        access,
                        "erp_shared_express_endpoint_enabled_for",
                        return_value=True,
                    ),
                    mock.patch.object(access, "require_erp_portal"),
                    mock.patch.object(access.db, "get_cursor_rls", return_value=_Context(cur)),
                    mock.patch.object(access, "_snapshot_commit_workspace", side_effect=lock_batch),
                    mock.patch.object(access, "_shared_preflight", side_effect=check_access),
                    mock.patch.object(
                        access, "_require_formal_conversion", side_effect=check_formal
                    ),
                ):
                    with self.assertRaises(HTTPException):
                        access.commit_shared_confirmation(
                            mock.sentinel.request, user, TENANT, [PURCHASE_HISTORY]
                        )
                cur.execute.assert_not_called()

    def test_history_lock_rejects_missing_actor_or_mixed_workspace(self):
        cases = (
            ([], [PURCHASE_HISTORY]),
            ([{"id": PURCHASE_HISTORY, "workspace_client_id": None}], [PURCHASE_HISTORY]),
            (
                [
                    {"id": PURCHASE_HISTORY, "workspace_client_id": WORKSPACE},
                    {"id": SALES_HISTORY, "workspace_client_id": WORKSPACE + 1},
                ],
                [PURCHASE_HISTORY, SALES_HISTORY],
            ),
        )
        for rows, history_ids in cases:
            with self.subTest(rows=rows):
                cur = mock.Mock()
                cur.fetchall.return_value = rows
                with self.assertRaises(HTTPException) as caught:
                    access._snapshot_commit_workspace(
                        cur,
                        tenant_id=TENANT,
                        actor_id=ACTOR,
                        history_ids=history_ids,
                    )
                self.assertEqual(caught.exception.status_code, 404)
                sql, params = cur.execute.call_args.args
                self.assertIn("tenant_id = %s::uuid AND user_id = %s::uuid", sql)
                self.assertNotIn("FOR UPDATE", sql)
                self.assertEqual(params, (history_ids, TENANT, ACTOR))

    def test_formal_document_matches_direction_actor_workspace_and_status(self):
        preflight = access.ConfirmationPreflight(
            ("purchase", "sales"),
            (),
            ((PURCHASE_HISTORY, "purchase"), (SALES_HISTORY, "sales")),
        )
        cur = mock.Mock()
        cur.fetchall.side_effect = (
            [{"history_id": PURCHASE_HISTORY}],
            [{"history_id": SALES_HISTORY}],
        )
        access._require_formal_conversion(
            cur,
            preflight=preflight,
            tenant_id=TENANT,
            actor_id=ACTOR,
            workspace_client_id=WORKSPACE,
            history_ids=[PURCHASE_HISTORY, SALES_HISTORY],
        )
        purchase_sql, purchase_params = cur.execute.call_args_list[0].args
        sales_sql, sales_params = cur.execute.call_args_list[1].args
        self.assertIn("created_by = %s::uuid AND status = 'posted'", purchase_sql)
        self.assertIn("created_by = %s::uuid AND status = 'issued'", sales_sql)
        self.assertIn("workspace_client_id = %s", purchase_sql)
        self.assertIn("seller_workspace_client_id = %s", sales_sql)
        expected_params = (TENANT, WORKSPACE, ACTOR, [PURCHASE_HISTORY, SALES_HISTORY])
        self.assertEqual(purchase_params, expected_params)
        self.assertEqual(sales_params, expected_params)

        missing = mock.Mock()
        missing.fetchall.side_effect = ([], [{"history_id": SALES_HISTORY}])
        with self.assertRaises(HTTPException) as caught:
            access._require_formal_conversion(
                missing,
                preflight=preflight,
                tenant_id=TENANT,
                actor_id=ACTOR,
                workspace_client_id=WORKSPACE,
                history_ids=[PURCHASE_HISTORY, SALES_HISTORY],
            )
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(caught.exception.detail["history_ids"], [PURCHASE_HISTORY])

    def test_status_is_read_only_and_uses_canonical_formal_records(self):
        cur = mock.Mock()
        user = {"id": ACTOR, "tenant_id": TENANT, "entry": "erp"}
        preflight = access.ConfirmationPreflight(
            ("purchase", "sales"),
            (),
            ((PURCHASE_HISTORY, "purchase"), (SALES_HISTORY, "sales")),
        )
        with (
            mock.patch.object(access, "require_erp_portal") as entrance,
            mock.patch.object(access, "_shared_preflight", return_value=preflight) as guard,
            mock.patch.object(
                access,
                "_formal_history_ids_by_direction",
                return_value={"purchase": {PURCHASE_HISTORY}, "sales": set()},
            ) as formal,
        ):
            result = access.confirmation_status(
                cur,
                mock.sentinel.request,
                user,
                TENANT,
                WORKSPACE,
                [PURCHASE_HISTORY, SALES_HISTORY],
            )
        self.assertEqual(
            result,
            {"resolved": [PURCHASE_HISTORY], "unresolved": [SALES_HISTORY]},
        )
        entrance.assert_called_once_with(user)
        self.assertFalse(guard.call_args.kwargs["lock_histories"])
        formal.assert_called_once()

    def test_preflight_reports_actor_owned_workspace_mismatch_without_leaking_workspace(self):
        cur = mock.Mock()
        cur.fetchone.return_value = {"id": WORKSPACE, "tax_id": "0105537000881"}
        cur.fetchall.return_value = [
            {
                "id": PURCHASE_HISTORY,
                "user_id": ACTOR,
                "tenant_id": TENANT,
                "workspace_client_id": WORKSPACE + 1,
                "pages": [{"fields": {}}],
                "source": "upload",
            }
        ]
        with self.assertRaises(HTTPException) as caught:
            access.preflight_confirmation(
                cur,
                tenant_id=TENANT,
                actor_id=ACTOR,
                workspace_client_id=WORKSPACE,
                history_ids=[PURCHASE_HISTORY],
                lock_histories=False,
            )
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(
            caught.exception.detail,
            {"code": "erp.workspace_mismatch", "history_ids": [PURCHASE_HISTORY]},
        )
        history_sql = cur.execute.call_args_list[1].args[0]
        self.assertNotIn("FOR UPDATE", history_sql)
        self.assertNotIn(str(WORKSPACE + 1), str(caught.exception.detail))


if __name__ == "__main__":
    unittest.main()
