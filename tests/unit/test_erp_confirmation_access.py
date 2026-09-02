# -*- coding: utf-8 -*-
"""ERP confirmation preflight contracts."""

from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from services.intake_bridge import erp_confirmation_access as access

TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
OTHER_TENANT = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
ACTOR = "11111111-1111-1111-1111-111111111111"
OTHER_ACTOR = "22222222-2222-2222-2222-222222222222"
PURCHASE_HISTORY = "cccccccc-cccc-cccc-cccc-cccccccc0001"
SALES_HISTORY = "cccccccc-cccc-cccc-cccc-cccccccc0002"
WORKSPACE = 101
OTHER_WORKSPACE = 202
OWN_TAX = "0105561234563"
COUNTERPARTY_TAX = "0107537000521"


def _row(history_id, *, actor=ACTOR, tenant=TENANT, workspace=WORKSPACE, direction=None):
    fields = {
        "items": [{"name": "Widget", "qty": "1", "price": "100"}],
        "seller_tax": COUNTERPARTY_TAX,
        "buyer_tax": OWN_TAX,
    }
    if direction:
        fields["direction"] = direction
    return {
        "id": history_id,
        "user_id": actor,
        "tenant_id": tenant,
        "workspace_client_id": workspace,
        "pages": [{"fields": fields}],
        "source": "erp_web",
    }


class _Cursor:
    def __init__(self, rows, *, workspace=None):
        self.rows = list(rows)
        self.workspace = (
            workspace if workspace is not None else {"id": WORKSPACE, "tax_id": OWN_TAX}
        )
        self.executed = []
        self._result = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if "FROM workspace_clients" in sql:
            self._result = self.workspace
        elif "FROM ocr_history" in sql:
            self._result = self.rows

    def fetchone(self):
        return self._result

    def fetchall(self):
        return self._result


class ErpConfirmationAccessTests(unittest.TestCase):
    def test_main_and_cowork_use_only_the_recognition_workspace_gate(self):
        for entry in ("main", "cowork"):
            with self.subTest(entry=entry):
                cur = mock.Mock()
                user = {"id": ACTOR, "tenant_id": TENANT, "entry": entry}
                with (
                    mock.patch.object(access.wc, "assert_workspace_in_tenant") as legacy_gate,
                    mock.patch.object(access, "preflight_confirmation") as preflight,
                    mock.patch.object(access, "require_perm") as require,
                    mock.patch.object(access, "check_workspace_scope") as check_scope,
                    mock.patch.object(access, "require_erp_portal") as entrance,
                ):
                    result = access.guard_confirmation(
                        cur, mock.sentinel.request, user, TENANT, WORKSPACE, [PURCHASE_HISTORY]
                    )
                self.assertIsNone(result)
                legacy_gate.assert_called_once_with(
                    cur, tenant_id=TENANT, workspace_client_id=WORKSPACE
                )
                preflight.assert_not_called()
                require.assert_not_called()
                check_scope.assert_not_called()
                entrance.assert_not_called()

    def test_erp_owner_mixed_workspace_batch_checks_each_group(self):
        cur = mock.Mock()
        user = {"id": ACTOR, "tenant_id": TENANT, "entry": "erp", "role": "owner"}
        purchase_preflight = access.ConfirmationPreflight(
            directions=("purchase",),
            required_permissions=("purchase.doc.create", "purchase.doc.approve"),
            history_directions=((PURCHASE_HISTORY, "purchase"),),
        )
        sales_preflight = access.ConfirmationPreflight(
            directions=("sales",),
            required_permissions=("sales.doc.create", "sales.doc.approve"),
            history_directions=((SALES_HISTORY, "sales"),),
        )
        with (
            mock.patch.object(
                access,
                "_snapshot_history_groups",
                return_value=(
                    (WORKSPACE, (PURCHASE_HISTORY,)),
                    (OTHER_WORKSPACE, (SALES_HISTORY,)),
                ),
            ),
            mock.patch.object(
                access,
                "preflight_confirmation",
                side_effect=(purchase_preflight, sales_preflight),
            ) as preflight,
            mock.patch.object(access, "require_perm", return_value=user) as require,
            mock.patch.object(access, "check_workspace_scope") as check_scope,
            mock.patch.object(access.wc, "assert_workspace_in_tenant") as legacy_gate,
        ):
            result = access.guard_confirmation(
                cur,
                mock.sentinel.request,
                user,
                TENANT,
                WORKSPACE,
                [PURCHASE_HISTORY, SALES_HISTORY],
            )
        self.assertEqual(
            result,
            access.ConfirmationBatch(
                groups=(
                    access.ConfirmationGroup(WORKSPACE, (PURCHASE_HISTORY,), purchase_preflight),
                    access.ConfirmationGroup(OTHER_WORKSPACE, (SALES_HISTORY,), sales_preflight),
                )
            ),
        )
        self.assertEqual(preflight.call_count, 2)
        self.assertEqual(
            [call.args[1] for call in require.call_args_list],
            [
                "purchase.doc.create",
                "purchase.doc.approve",
                "sales.doc.create",
                "sales.doc.approve",
            ],
        )
        self.assertEqual(
            check_scope.call_args_list,
            [
                mock.call(mock.sentinel.request, user, WORKSPACE),
                mock.call(mock.sentinel.request, user, OTHER_WORKSPACE),
            ],
        )
        legacy_gate.assert_not_called()

    def test_non_erp_entrances_keep_the_exact_recognition_path(self):
        for entry in ("pos", "ai", "dms", "daily", None, "unknown"):
            with self.subTest(entry=entry):
                cur = mock.Mock()
                user = {"id": ACTOR, "tenant_id": TENANT, "entry": entry}
                with (
                    mock.patch.object(access, "preflight_confirmation") as preflight,
                    mock.patch.object(access, "check_workspace_scope") as check_scope,
                    mock.patch.object(access.wc, "assert_workspace_in_tenant") as legacy_gate,
                ):
                    result = access.guard_confirmation(
                        cur,
                        mock.sentinel.request,
                        user,
                        TENANT,
                        WORKSPACE,
                        [PURCHASE_HISTORY],
                    )
                self.assertIsNone(result)
                legacy_gate.assert_called_once_with(
                    cur, tenant_id=TENANT, workspace_client_id=WORKSPACE
                )
                check_scope.assert_not_called()
                preflight.assert_not_called()

    def test_formal_confirmation_context_is_exactly_erp(self):
        for entry in ("main", "cowork"):
            self.assertFalse(
                access.is_shared_confirmation_context(
                    {"id": ACTOR, "tenant_id": TENANT, "entry": entry}, TENANT
                )
            )
        self.assertTrue(
            access.is_shared_confirmation_context(
                {"id": ACTOR, "tenant_id": TENANT, "entry": "erp"}, TENANT
            )
        )

    def test_erp_entry_uses_persisted_workspace_grouping_when_flag_is_off(self):
        user = {"id": ACTOR, "tenant_id": TENANT, "entry": "erp"}
        self.assertTrue(access.is_shared_confirmation_context(user, TENANT))

    def test_main_and_cowork_commit_do_not_create_formal_documents(self):
        for entry in ("main", "cowork"):
            with self.subTest(entry=entry):
                user = {"id": ACTOR, "tenant_id": TENANT, "entry": entry}
                with mock.patch.object(access.db, "get_cursor_rls") as cursor:
                    result = access.commit_shared_confirmation(
                        mock.sentinel.request, user, TENANT, [PURCHASE_HISTORY]
                    )
                self.assertIsNone(result)
                cursor.assert_not_called()

    def test_erp_missing_one_permission_stops_after_scope_before_write(self):
        user = {"id": ACTOR, "tenant_id": TENANT, "entry": "erp"}
        preflight_result = access.ConfirmationPreflight(
            directions=("purchase", "sales"),
            required_permissions=(
                "purchase.doc.create",
                "purchase.doc.approve",
                "sales.doc.create",
                "sales.doc.approve",
            ),
        )

        def _permission(_request, code):
            if code == "sales.doc.approve":
                raise HTTPException(403, detail="authz.forbidden")
            return user

        with (
            mock.patch.object(
                access,
                "_snapshot_history_groups",
                return_value=((WORKSPACE, (PURCHASE_HISTORY, SALES_HISTORY)),),
            ),
            mock.patch.object(access, "preflight_confirmation", return_value=preflight_result),
            mock.patch.object(access, "require_perm", side_effect=_permission),
            mock.patch.object(access, "check_workspace_scope") as check_scope,
            mock.patch.object(access, "require_erp_portal"),
        ):
            with self.assertRaises(HTTPException) as caught:
                access.guard_confirmation(
                    mock.Mock(),
                    mock.sentinel.request,
                    user,
                    TENANT,
                    WORKSPACE,
                    [PURCHASE_HISTORY, SALES_HISTORY],
                )
        self.assertEqual(caught.exception.status_code, 403)
        self.assertEqual(caught.exception.detail, "authz.forbidden")
        check_scope.assert_called_once_with(mock.sentinel.request, user, WORKSPACE)

    def test_erp_unassigned_workspace_is_not_found(self):
        user = {"id": ACTOR, "tenant_id": TENANT, "entry": "erp"}
        preflight_result = access.ConfirmationPreflight(
            directions=("purchase",),
            required_permissions=("purchase.doc.create", "purchase.doc.approve"),
        )
        with (
            mock.patch.object(
                access,
                "_snapshot_history_groups",
                return_value=((WORKSPACE, (PURCHASE_HISTORY,)),),
            ),
            mock.patch.object(
                access, "preflight_confirmation", return_value=preflight_result
            ) as preflight,
            mock.patch.object(access, "require_perm", return_value=user) as require,
            mock.patch.object(
                access,
                "check_workspace_scope",
                side_effect=HTTPException(404, detail="authz.not_found"),
            ),
            mock.patch.object(access, "require_erp_portal"),
        ):
            with self.assertRaises(HTTPException) as caught:
                access.guard_confirmation(
                    mock.Mock(),
                    mock.sentinel.request,
                    user,
                    TENANT,
                    WORKSPACE,
                    [PURCHASE_HISTORY],
                )
        self.assertEqual(caught.exception.status_code, 404)
        self.assertEqual(caught.exception.detail, "authz.not_found")
        preflight.assert_not_called()
        require.assert_not_called()

    def test_mixed_batch_requires_four_permissions_from_stored_directions(self):
        cur = _Cursor(
            [
                _row(PURCHASE_HISTORY, direction="purchase"),
                _row(SALES_HISTORY, direction="sales"),
            ]
        )
        result = access.preflight_confirmation(
            cur,
            tenant_id=TENANT,
            actor_id=ACTOR,
            workspace_client_id=WORKSPACE,
            history_ids=[PURCHASE_HISTORY, SALES_HISTORY],
        )
        self.assertEqual(result.directions, ("purchase", "sales"))
        self.assertEqual(
            result.required_permissions,
            (
                "purchase.doc.create",
                "purchase.doc.approve",
                "sales.doc.create",
                "sales.doc.approve",
            ),
        )
        self.assertEqual(
            result.history_directions,
            ((PURCHASE_HISTORY, "purchase"), (SALES_HISTORY, "sales")),
        )
        self.assertIn("FOR SHARE", cur.executed[0][0])
        self.assertIn("ORDER BY id FOR UPDATE", cur.executed[1][0])
        self.assertTrue(all(sql.lstrip().startswith("SELECT") for sql, _ in cur.executed))

    def test_direction_uses_canonical_tax_anchor_not_request_data(self):
        cur = _Cursor([_row(PURCHASE_HISTORY)])
        result = access.preflight_confirmation(
            cur,
            tenant_id=TENANT,
            actor_id=ACTOR,
            workspace_client_id=WORKSPACE,
            history_ids=[PURCHASE_HISTORY],
        )
        self.assertEqual(result.directions, ("purchase",))

    def test_missing_cross_tenant_and_other_actor_are_same_not_found(self):
        cases = (
            [],
            [_row(PURCHASE_HISTORY, tenant=OTHER_TENANT)],
            [_row(PURCHASE_HISTORY, actor=OTHER_ACTOR)],
        )
        for rows in cases:
            with self.subTest(rows=rows):
                with self.assertRaises(HTTPException) as caught:
                    access.preflight_confirmation(
                        _Cursor(rows),
                        tenant_id=TENANT,
                        actor_id=ACTOR,
                        workspace_client_id=WORKSPACE,
                        history_ids=[PURCHASE_HISTORY],
                    )
                self.assertEqual(caught.exception.status_code, 404)
                self.assertEqual(caught.exception.detail, "history.not_found")

    def test_snapshot_groups_mixed_workspace_batch_from_stored_attribution(self):
        cur = mock.Mock()
        cur.fetchall.return_value = [
            {"id": PURCHASE_HISTORY, "workspace_client_id": WORKSPACE},
            {"id": SALES_HISTORY, "workspace_client_id": OTHER_WORKSPACE},
        ]
        groups = access._snapshot_history_groups(
            cur,
            tenant_id=TENANT,
            actor_id=ACTOR,
            history_ids=[PURCHASE_HISTORY, SALES_HISTORY],
        )
        self.assertEqual(
            groups,
            (
                (WORKSPACE, (PURCHASE_HISTORY,)),
                (OTHER_WORKSPACE, (SALES_HISTORY,)),
            ),
        )
        sql, params = cur.execute.call_args.args
        self.assertIn("tenant_id = %s::uuid AND user_id = %s::uuid", sql)
        self.assertNotIn("FOR UPDATE", sql)
        self.assertEqual(params, ([PURCHASE_HISTORY, SALES_HISTORY], TENANT, ACTOR))

    def test_workspace_outside_tenant_or_inactive_is_not_found_before_history_lookup(self):
        cur = _Cursor([_row(PURCHASE_HISTORY)], workspace=None)
        cur.workspace = None
        with self.assertRaises(HTTPException) as caught:
            access.preflight_confirmation(
                cur,
                tenant_id=TENANT,
                actor_id=ACTOR,
                workspace_client_id=WORKSPACE,
                history_ids=[PURCHASE_HISTORY],
            )
        self.assertEqual(caught.exception.status_code, 404)
        self.assertEqual(caught.exception.detail, "authz.not_found")
        self.assertEqual(len(cur.executed), 1)
        self.assertIn("is_active = TRUE", cur.executed[0][0])

    def test_ambiguous_direction_fails_before_any_write(self):
        row = _row(PURCHASE_HISTORY)
        row["pages"][0]["fields"].update({"seller_tax": "", "buyer_tax": ""})
        cur = _Cursor([row])
        with self.assertRaises(HTTPException) as caught:
            access.preflight_confirmation(
                cur,
                tenant_id=TENANT,
                actor_id=ACTOR,
                workspace_client_id=WORKSPACE,
                history_ids=[PURCHASE_HISTORY],
            )
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(caught.exception.detail["code"], "erp.declaration_required")
        self.assertTrue(all(sql.lstrip().startswith("SELECT") for sql, _ in cur.executed))

    def test_finish_resolved_histories_binds_actor_and_workspace_on_flag_path(self):
        cur = mock.Mock()
        preflight = access.ConfirmationPreflight(
            ("purchase",),
            ("purchase.doc.create",),
            ((PURCHASE_HISTORY, "purchase"),),
        )
        with mock.patch.object(access, "_require_formal_conversion") as formal:
            access.finish_resolved_histories(
                cur, preflight, TENANT, ACTOR, WORKSPACE, [PURCHASE_HISTORY]
            )
        formal.assert_called_once_with(
            cur,
            preflight=preflight,
            tenant_id=TENANT,
            actor_id=ACTOR,
            workspace_client_id=WORKSPACE,
            history_ids=[PURCHASE_HISTORY],
        )
        sql, params = cur.execute.call_args.args
        self.assertIn("user_id = %s::uuid", sql)
        self.assertIn("workspace_client_id = %s", sql)
        self.assertEqual(params, ([PURCHASE_HISTORY], TENANT, ACTOR, WORKSPACE))

    def test_finish_resolved_histories_uses_each_persisted_workspace_group(self):
        cur = mock.Mock()
        purchase = access.ConfirmationPreflight(
            ("purchase",), (), ((PURCHASE_HISTORY, "purchase"),)
        )
        sales = access.ConfirmationPreflight(("sales",), (), ((SALES_HISTORY, "sales"),))
        batch = access.ConfirmationBatch(
            groups=(
                access.ConfirmationGroup(WORKSPACE, (PURCHASE_HISTORY,), purchase),
                access.ConfirmationGroup(OTHER_WORKSPACE, (SALES_HISTORY,), sales),
            )
        )
        with mock.patch.object(access, "_require_formal_conversion") as formal:
            access.finish_resolved_histories(
                cur,
                batch,
                TENANT,
                ACTOR,
                999,
                {PURCHASE_HISTORY, SALES_HISTORY},
            )
        self.assertEqual(
            [call.kwargs["workspace_client_id"] for call in formal.call_args_list],
            [WORKSPACE, OTHER_WORKSPACE],
        )
        self.assertEqual(
            [call.args[1] for call in cur.execute.call_args_list],
            [
                ([PURCHASE_HISTORY], TENANT, ACTOR, WORKSPACE),
                ([SALES_HISTORY], TENANT, ACTOR, OTHER_WORKSPACE),
            ],
        )

    def test_finish_resolved_histories_rejects_ids_outside_checked_batch(self):
        cur = mock.Mock()
        preflight = access.ConfirmationPreflight(
            ("purchase",), (), ((PURCHASE_HISTORY, "purchase"),)
        )
        batch = access.ConfirmationBatch(
            groups=(access.ConfirmationGroup(WORKSPACE, (PURCHASE_HISTORY,), preflight),)
        )
        with (
            mock.patch.object(access, "_require_formal_conversion") as formal,
            self.assertRaises(HTTPException) as caught,
        ):
            access.finish_resolved_histories(cur, batch, TENANT, ACTOR, WORKSPACE, [SALES_HISTORY])
        self.assertEqual(caught.exception.status_code, 404)
        formal.assert_not_called()
        cur.execute.assert_not_called()

    def test_preflight_requires_an_active_workspace(self):
        cur = _Cursor([_row(PURCHASE_HISTORY)])
        access.preflight_confirmation(
            cur,
            tenant_id=TENANT,
            actor_id=ACTOR,
            workspace_client_id=WORKSPACE,
            history_ids=[PURCHASE_HISTORY],
        )
        self.assertIn("is_active = TRUE", cur.executed[0][0])

    def test_finish_resolved_histories_keeps_legacy_update_off_flag(self):
        cur = mock.Mock()
        access.finish_resolved_histories(cur, None, TENANT, ACTOR, WORKSPACE, [PURCHASE_HISTORY])
        sql, params = cur.execute.call_args.args
        self.assertIn("user_id IN (SELECT id FROM users", sql)
        self.assertNotIn("workspace_client_id = %s", sql)
        self.assertEqual(params, ([PURCHASE_HISTORY], TENANT, TENANT))


if __name__ == "__main__":
    unittest.main()
