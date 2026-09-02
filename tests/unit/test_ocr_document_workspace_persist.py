import unittest
from types import SimpleNamespace
from unittest import mock

from fastapi import HTTPException

from services.ocr.recognize import persist
from services.ocr.recognize import workspace_assignment


class _CursorContext:
    def __init__(self):
        self.cursor = mock.Mock()

    def __enter__(self):
        return self.cursor

    def __exit__(self, *_args):
        return False


class OcrDocumentWorkspacePersistTests(unittest.TestCase):
    def test_resolves_workspace_before_category_duplicate_and_history_insert(self):
        fields = {
            "direction": "sales",
            "seller_name": "Company B",
            "seller_tax": "0105567178203",
            "buyer_name": "Buyer",
            "buyer_tax": "0105561234563",
            "invoice_number": "INV-B-1",
            "date": "2026-09-03",
            "total_amount": "107.00",
        }
        group = {
            "invoice_fields": fields,
            "source_pages": [{"fields": fields}],
            "page_indices": [1],
        }
        decision = {
            "workspace_client_id": 22,
            "action": "created",
            "workspace_name": "Company B",
            "subject": {"tax_id": "0105567178203", "name": "Company B"},
        }
        created_tasks = []

        def close_task(coro):
            created_tasks.append(coro)
            coro.close()

        with (
            mock.patch(
                "services.ocr.invoice_grouper.group_pages_to_invoices", return_value=[group]
            ),
            mock.patch.object(persist.db, "get_archive_template", return_value=None),
            mock.patch.object(persist.db, "get_user_dup_check_enabled", return_value=True),
            mock.patch.object(persist.db, "get_cursor", return_value=_CursorContext()),
            mock.patch(
                "services.purchase.categories.get_tree", return_value=[{"name": "Sales"}]
            ) as tree,
            mock.patch("services.ocr.recognize.category_tag.resolve_tag", return_value="Sales"),
            mock.patch.object(persist.db, "get_category_for_seller", return_value=None),
            mock.patch.object(
                persist.db, "check_duplicate_invoice", return_value=None
            ) as duplicate,
            mock.patch.object(persist, "insert_ocr_history", return_value="history-b") as insert,
            mock.patch.object(
                persist.db,
                "resolve_or_create_buyer_client",
                return_value={"action": "none", "reason": "no_match"},
            ),
            mock.patch.object(persist.db, "update_history_workspace_client_id") as rebind,
            mock.patch.object(
                persist._workspace, "resolve_batch", return_value=[decision]
            ) as resolve,
            mock.patch("asyncio.create_task", side_effect=close_task),
        ):
            result = persist.persist_invoices(
                result={"pages": [{"fields": fields}], "page_count": 1, "elapsed_ms": 15},
                user={"id": "user-1", "tenant_id": "tenant-1", "plan": "free"},
                confidence="high",
                _billing={"is_exempt": True},
                _chg_kind="page",
                _chg_units=0,
                file=SimpleNamespace(filename="company-b.pdf"),
                content=b"pdf",
                file_hash="hash",
                client_id=None,
                _ws_client_id=11,
                staged=True,
                direction="sales",
                source="erp_web",
            )

        resolve.assert_called_once_with(
            [(fields, "sales")],
            mock.ANY,
            "erp_web",
            fallback_workspace_id=11,
        )
        tree.assert_called_once_with(mock.ANY, tenant_id="tenant-1", workspace_client_id=22)
        self.assertEqual(duplicate.call_args.kwargs["workspace_client_id"], 22)
        self.assertEqual(insert.call_args.kwargs["workspace_client_id"], 22)
        rebind.assert_not_called()
        self.assertEqual(
            result["workspace_assignments"],
            [
                {
                    "history_id": "history-b",
                    "workspace_id": 22,
                    "action": "created",
                    "workspace_name": "Company B",
                    "subject": {"tax_id": "0105567178203", "name": "Company B"},
                }
            ],
        )
        self.assertEqual(len(created_tasks), 1)

    def test_no_direction_existing_match_is_written_directly_to_workspace(self):
        fields = {"seller_name": "Known Company", "invoice_number": "INV-1"}
        group = {
            "invoice_fields": fields,
            "source_pages": [{"fields": fields}],
            "page_indices": [1],
        }
        with (
            mock.patch(
                "services.ocr.invoice_grouper.group_pages_to_invoices", return_value=[group]
            ),
            mock.patch.object(persist.db, "get_archive_template", return_value=None),
            mock.patch.object(persist.db, "get_user_dup_check_enabled", return_value=False),
            mock.patch.object(persist.db, "get_cursor", return_value=_CursorContext()),
            mock.patch("services.purchase.categories.get_tree", return_value=None),
            mock.patch.object(persist.db, "get_category_for_seller", return_value=None),
            mock.patch.object(persist, "insert_ocr_history", return_value="history-1") as insert,
            mock.patch.object(
                persist.db,
                "resolve_or_create_buyer_client",
                return_value={"action": "none", "reason": "no_match"},
            ),
            mock.patch.object(
                persist._workspace,
                "resolve_batch",
                return_value=[
                    {
                        "workspace_client_id": 33,
                        "action": "matched",
                        "workspace_name": "Known Company",
                    }
                ],
            ) as resolve,
            mock.patch.object(
                persist.db, "update_history_workspace_client_id", return_value=True
            ) as rebind,
            mock.patch("asyncio.create_task", side_effect=lambda coro: coro.close()),
        ):
            result = persist.persist_invoices(
                result={"pages": [{"fields": fields}], "page_count": 1, "elapsed_ms": 1},
                user={"id": "user-1", "tenant_id": "tenant-1", "plan": "free"},
                confidence="medium",
                _billing={"is_exempt": True},
                _chg_kind="page",
                _chg_units=0,
                file=SimpleNamespace(filename="legacy.pdf"),
                content=b"pdf",
                file_hash="hash",
                client_id=None,
                _ws_client_id=11,
                staged=True,
                source="cowork_web",
            )

        resolve.assert_called_once_with(
            [(fields, None)],
            mock.ANY,
            "cowork_web",
            fallback_workspace_id=11,
        )
        rebind.assert_not_called()
        self.assertEqual(insert.call_args.kwargs["workspace_client_id"], 33)
        self.assertEqual(result["workspace_assignments"][0]["workspace_id"], 33)

    def test_second_history_write_failure_compensates_before_side_effects(self):
        fields = {
            "direction": "sales",
            "seller_name": "Company B",
            "seller_tax": "0105567178203",
            "invoice_number": "INV-B-1",
        }
        groups = [
            {
                "invoice_fields": dict(fields, invoice_number=f"INV-B-{index}"),
                "source_pages": [{"fields": fields}],
                "page_indices": [index],
            }
            for index in (1, 2)
        ]
        decision = {
            "workspace_client_id": 22,
            "action": "created",
            "workspace_name": "Company B",
            "subject": {"tax_id": "0105567178203", "name": "Company B"},
        }
        with (
            mock.patch("services.ocr.invoice_grouper.group_pages_to_invoices", return_value=groups),
            mock.patch.object(persist.db, "get_archive_template", return_value=None),
            mock.patch.object(persist.db, "get_user_dup_check_enabled", return_value=False),
            mock.patch.object(persist.db, "get_cursor", return_value=_CursorContext()),
            mock.patch("services.purchase.categories.get_tree", return_value=None),
            mock.patch.object(persist.db, "get_category_for_seller", return_value=None),
            mock.patch.object(
                persist._workspace, "resolve_batch", return_value=[decision, decision]
            ),
            mock.patch.object(
                persist, "insert_ocr_history", side_effect=["history-1", RuntimeError("db")]
            ),
            mock.patch.object(persist._workspace, "cleanup_failed_batch") as cleanup,
            mock.patch.object(persist.history_postprocess, "charge_batch") as charge,
            mock.patch.object(persist.history_postprocess, "process_history") as process,
        ):
            with self.assertRaisesRegex(RuntimeError, "db"):
                persist.persist_invoices(
                    result={"pages": [{"fields": fields}], "page_count": 2, "elapsed_ms": 1},
                    user={"id": "user-1", "tenant_id": "tenant-1", "plan": "free"},
                    confidence="high",
                    _billing={"is_exempt": False},
                    _chg_kind="page",
                    _chg_units=2,
                    file=SimpleNamespace(filename="batch.pdf"),
                    content=b"pdf",
                    file_hash="hash",
                    client_id=None,
                    _ws_client_id=11,
                    staged=True,
                    direction="sales",
                    source="erp_web",
                )

        cleanup.assert_called_once_with(mock.ANY, ["history-1"], [decision, decision])
        charge.assert_not_called()
        process.assert_not_called()


class OcrWorkspaceCreatePermissionTests(unittest.TestCase):
    def test_no_direction_rejects_conflicting_seller_and_buyer_workspaces(self):
        with (
            mock.patch.object(
                workspace_assignment.db,
                "match_workspace_for_seller",
                return_value={
                    "action": "assigned",
                    "workspace_client_id": 21,
                    "workspace_name": "Seller Company",
                },
            ),
            mock.patch.object(
                workspace_assignment.db,
                "match_workspace_for_buyer",
                return_value={
                    "action": "assigned",
                    "workspace_client_id": 22,
                    "workspace_name": "Buyer Company",
                },
            ),
        ):
            with self.assertRaises(workspace_assignment.WorkspaceAssignmentError) as raised:
                workspace_assignment.resolve_batch(
                    [({"seller_name": "Seller Company", "buyer_name": "Buyer Company"}, None)],
                    {"id": "admin", "is_super_admin": True},
                    "cowork_web",
                    fallback_workspace_id=11,
                )

        self.assertEqual(raised.exception.code, "workspace_ambiguous")

    def test_no_direction_accepts_same_workspace_from_both_parties(self):
        route = {
            "action": "assigned",
            "workspace_client_id": 22,
            "workspace_name": "Company B",
        }
        with (
            mock.patch.object(
                workspace_assignment.db, "match_workspace_for_seller", return_value=route
            ),
            mock.patch.object(
                workspace_assignment.db, "match_workspace_for_buyer", return_value=route
            ),
        ):
            decisions = workspace_assignment.resolve_batch(
                [({"seller_name": "Company B", "buyer_name": "Company B"}, None)],
                {"id": "admin", "is_super_admin": True},
                "cowork_web",
                fallback_workspace_id=11,
            )

        self.assertEqual(decisions[0]["workspace_client_id"], 22)
        self.assertEqual(decisions[0]["action"], "matched")

    def test_no_direction_requires_declaration_when_no_party_matches(self):
        no_match = {"action": "none"}
        with (
            mock.patch.object(
                workspace_assignment.db, "match_workspace_for_seller", return_value=no_match
            ),
            mock.patch.object(
                workspace_assignment.db, "match_workspace_for_buyer", return_value=no_match
            ),
            mock.patch.object(
                workspace_assignment.document_assignment, "materialize_assignment"
            ) as materialize,
        ):
            with self.assertRaises(workspace_assignment.WorkspaceAssignmentError) as raised:
                workspace_assignment.resolve_batch(
                    [({"seller_name": "Unknown Company"}, None)],
                    {"id": "admin", "is_super_admin": True},
                    "cowork_web",
                    fallback_workspace_id=11,
                )

        self.assertEqual(raised.exception.code, "direction_required")
        materialize.assert_not_called()

    def test_no_direction_surfaces_workspace_lookup_failure(self):
        with (
            mock.patch.object(
                workspace_assignment.db,
                "match_workspace_for_seller",
                return_value={"action": "none", "reason": "lookup_error"},
            ),
            mock.patch.object(
                workspace_assignment.db,
                "match_workspace_for_buyer",
                return_value={"action": "none"},
            ),
        ):
            with self.assertRaises(workspace_assignment.WorkspaceAssignmentError) as raised:
                workspace_assignment.resolve_batch(
                    [({"seller_name": "Company"}, None)],
                    {"id": "admin", "is_super_admin": True},
                    "cowork_web",
                    fallback_workspace_id=11,
                )

        self.assertEqual(raised.exception.code, "workspace_lookup_failed")

    def test_no_direction_without_party_identity_is_not_assigned_to_fallback(self):
        no_match = {"action": "none"}
        with (
            mock.patch.object(
                workspace_assignment.db, "match_workspace_for_seller", return_value=no_match
            ),
            mock.patch.object(
                workspace_assignment.db, "match_workspace_for_buyer", return_value=no_match
            ),
        ):
            with self.assertRaises(workspace_assignment.WorkspaceAssignmentError) as raised:
                workspace_assignment.resolve_batch(
                    [({"invoice_number": "INV-1"}, None)],
                    {"id": "admin", "is_super_admin": True},
                    "cowork_web",
                    fallback_workspace_id=11,
                )

        self.assertEqual(raised.exception.code, "workspace_subject_missing")

    def test_assigned_scope_cannot_create_an_unassigned_workspace(self):
        authz = mock.Mock()
        authz.has.return_value = True
        authz.scope_mode = "assigned"
        with mock.patch("services.authz.resolver.resolve", return_value=authz):
            with self.assertRaises(HTTPException) as raised:
                workspace_assignment._require_create({"id": "user-1", "tenant_id": "tenant-1"})

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(raised.exception.detail, "authz.forbidden")

    def test_super_admin_create_does_not_query_membership(self):
        with mock.patch("services.authz.resolver.resolve") as resolve:
            workspace_assignment._require_create({"id": "admin", "is_super_admin": True})

        resolve.assert_not_called()

    def test_assigned_scope_cannot_route_to_an_unassigned_existing_workspace(self):
        authz = mock.Mock()
        authz.allows_workspace.return_value = False
        route = {"action": "assigned", "workspace_client_id": 22, "workspace_name": "B"}
        with (
            mock.patch("services.authz.resolver.resolve", return_value=authz),
            mock.patch.object(
                workspace_assignment.db, "match_workspace_for_seller", return_value=route
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                workspace_assignment.resolve_or_create(
                    {"seller_name": "B", "seller_tax": "0105567178203"},
                    "sales",
                    {"id": "user-1", "tenant_id": "tenant-1"},
                    "erp_web",
                )

        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.detail, "authz.not_found")

    def test_batch_is_fully_planned_before_any_workspace_create(self):
        authz = mock.Mock()
        first_plan = {
            "workspace_client_id": None,
            "action": "create",
            "workspace_name": "A",
            "subject": {"tax_id": "1", "name": "A"},
            "direction": "sales",
        }
        with (
            mock.patch.object(workspace_assignment, "_policy", return_value=authz),
            mock.patch.object(
                workspace_assignment.document_assignment,
                "prepare_assignment",
                side_effect=[
                    first_plan,
                    workspace_assignment.WorkspaceAssignmentError("workspace_ambiguous"),
                ],
            ),
            mock.patch.object(
                workspace_assignment.document_assignment, "materialize_assignment"
            ) as materialize,
        ):
            with self.assertRaises(workspace_assignment.WorkspaceAssignmentError):
                workspace_assignment.resolve_batch(
                    [({"seller_name": "A"}, "sales"), ({"seller_name": "B"}, "sales")],
                    {"id": "user-1", "tenant_id": "tenant-1"},
                    "erp_web",
                    fallback_workspace_id=11,
                )

        materialize.assert_not_called()

    def test_batch_reuses_name_only_subject_across_case_and_space_variants(self):
        authz = mock.Mock()
        plans = [
            {
                "workspace_client_id": None,
                "action": "create",
                "workspace_name": name,
                "subject": {"tax_id": "", "name": name},
                "direction": "sales",
            }
            for name in ("Company   B", " company b ")
        ]
        decision = {
            "workspace_client_id": 22,
            "action": "created",
            "workspace_name": "Company B",
            "subject": {"tax_id": "", "name": "Company B"},
        }
        with (
            mock.patch.object(workspace_assignment, "_policy", return_value=authz),
            mock.patch.object(
                workspace_assignment.document_assignment,
                "prepare_assignment",
                side_effect=plans,
            ),
            mock.patch.object(
                workspace_assignment.document_assignment,
                "materialize_assignment",
                return_value=decision,
            ) as materialize,
            mock.patch.object(workspace_assignment, "_log_created"),
        ):
            decisions = workspace_assignment.resolve_batch(
                [({"seller_name": plan["workspace_name"]}, "sales") for plan in plans],
                {"id": "user-1", "tenant_id": "tenant-1"},
                "erp_web",
                fallback_workspace_id=11,
            )

        materialize.assert_called_once()
        self.assertEqual(decisions, [decision, decision])


if __name__ == "__main__":
    unittest.main()
