from __future__ import annotations

import json
import unittest
from unittest import mock

from services.erp import target_catalog_evidence as evidence

REQUEST_ID = "11111111-1111-4111-8111-111111111111"
NEW_REQUEST_ID = "22222222-2222-4222-8222-222222222222"


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class _Context:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, *_args):
        return False


def _refresh(**overrides):
    return {
        "id": REQUEST_ID,
        "status": "succeeded",
        "account_set_key": "@endpoint",
        "adapter": "mrerp",
        "result_revision": 7,
        "head_status": "fresh",
        "head_revision": 7,
        "snapshot_adapter": "mrerp",
        **overrides,
    }


def _snapshot(account_sets, **overrides):
    return {
        "snapshot_id": "snapshot-7",
        "adapter": "mrerp",
        "account_sets": account_sets,
        "head_snapshot_id": "snapshot-7",
        "head_revision": 7,
        "head_status": "fresh",
        **overrides,
    }


def _validate(**overrides):
    values = {
        "tenant_id": "tenant-1",
        "user_id": "user-1",
        "endpoint_id": "endpoint-1",
        "adapter": "mrerp",
        "selected_account_set_key": "7:2",
        "bound_account_set_key": "6:1",
        "request_id": REQUEST_ID,
        "revision": 7,
    }
    values.update(overrides)
    return evidence.validate_selection(**values)


def _validate_receipt(**overrides):
    values = {
        "tenant_id": "tenant-1",
        "user_id": "user-1",
        "endpoint_id": "endpoint-1",
        "adapter": "mrerp",
        "request_id": REQUEST_ID,
        "request_revision": 7,
        "catalog_revision": 7,
    }
    values.update(overrides)
    return evidence.validate_refresh_receipt(**values)


class TargetCatalogEvidenceTests(unittest.TestCase):
    def test_refresh_receipt_matches_latest_request_and_current_snapshot(self):
        cursor = _Cursor([_refresh()])
        with mock.patch.object(evidence.db, "get_cursor_rls", return_value=_Context(cursor)):
            result = _validate_receipt()

        self.assertTrue(result["ok"])
        self.assertEqual(result["reason"], "validated_snapshot")
        self.assertEqual(len(cursor.executed), 1)
        self.assertIn("erp_target_projection_heads", cursor.executed[0][0])
        self.assertIn("ORDER BY r.requested_at DESC, r.created_at DESC", cursor.executed[0][0])

    def test_refresh_receipt_rejects_a_mixed_catalog_without_database_access(self):
        with mock.patch.object(evidence.db, "get_cursor_rls") as get_cursor:
            result = _validate_receipt(catalog_revision=8)

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "revision_mismatch")
        get_cursor.assert_not_called()

    def test_refresh_receipt_rejects_a_newer_endpoint_request(self):
        cursor = _Cursor([_refresh(id=NEW_REQUEST_ID, status="requested")])
        with mock.patch.object(evidence.db, "get_cursor_rls", return_value=_Context(cursor)):
            result = _validate_receipt()

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "refresh_superseded")

    def test_refresh_receipt_rejects_a_superseded_projection_head(self):
        cursor = _Cursor([_refresh(head_revision=8)])
        with mock.patch.object(evidence.db, "get_cursor_rls", return_value=_Context(cursor)):
            result = _validate_receipt()

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "snapshot_superseded")

    def test_bound_default_needs_no_database_proof(self):
        with mock.patch.object(evidence.db, "get_cursor_rls") as get_cursor:
            result = _validate(
                selected_account_set_key="6:1",
                request_id=None,
                revision=None,
            )

        self.assertTrue(result["ok"])
        self.assertFalse(result["proof_required"])
        self.assertEqual(result["reason"], "bound_default")
        get_cursor.assert_not_called()

    def test_express_default_compares_normalized_account_and_bound_root(self):
        with mock.patch.object(evidence.db, "get_cursor_rls") as get_cursor:
            result = _validate(
                adapter="express",
                selected_account_set_key=r"C:/68EXP/TEST/",
                bound_account_set_key=r"c:\68exp\test",
                selected_root_key=r"C:/68EXP/",
                bound_root_key=r"c:\68exp",
                request_id=None,
                revision=None,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["account_set_key"], r"c:\68exp\test")
        get_cursor.assert_not_called()

    def test_changed_bound_root_does_not_bypass_proof(self):
        result = _validate(
            adapter="express",
            selected_account_set_key=r"C:\68EXP\TEST",
            bound_account_set_key=r"C:\68EXP\TEST",
            selected_root_key=r"C:\69EXP",
            bound_root_key=r"C:\68EXP",
            request_id=None,
            revision=None,
        )

        self.assertFalse(result["ok"])
        self.assertTrue(result["proof_required"])
        self.assertEqual(result["error_code"], evidence.CATALOG_REFRESH_REQUIRED)

    def test_express_default_infers_missing_bound_root_from_account_path(self):
        with mock.patch.object(evidence.db, "get_cursor_rls") as get_cursor:
            valid = _validate(
                adapter="express",
                selected_account_set_key=r"C:\68EXP\TEST",
                bound_account_set_key=r"C:\68EXP\TEST",
                selected_root_key=r"C:\68EXP",
                bound_root_key=None,
                request_id=None,
                revision=None,
            )
            tampered = _validate(
                adapter="express",
                selected_account_set_key=r"C:\68EXP\TEST",
                bound_account_set_key=r"C:\68EXP\TEST",
                selected_root_key=r"C:\69EXP",
                bound_root_key=None,
                request_id=None,
                revision=None,
            )

        self.assertTrue(valid["ok"])
        self.assertFalse(tampered["ok"])
        self.assertEqual(tampered["error_code"], evidence.CATALOG_REFRESH_REQUIRED)
        get_cursor.assert_not_called()

    def test_non_default_requires_both_request_and_revision(self):
        for values in ({"request_id": None}, {"revision": None}):
            with self.subTest(values=values):
                result = _validate(**values)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error_code"], evidence.CATALOG_REFRESH_REQUIRED)
                self.assertEqual(result["reason"], "proof_missing")

    def test_malformed_proof_is_invalid_without_database_access(self):
        with mock.patch.object(evidence.db, "get_cursor_rls") as get_cursor:
            result = _validate(request_id="not-a-uuid", revision="wrong")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], evidence.CATALOG_REFRESH_INVALID)
        self.assertEqual(result["reason"], "proof_malformed")
        get_cursor.assert_not_called()

    def test_request_and_snapshot_are_exact_and_rls_scoped(self):
        cursor = _Cursor(
            [
                _refresh(),
                _snapshot([{"source_id": "7:2", "label": "2027"}]),
            ]
        )
        with mock.patch.object(
            evidence.db, "get_cursor_rls", return_value=_Context(cursor)
        ) as get_cursor:
            result = _validate()

        self.assertTrue(result["ok"])
        self.assertTrue(result["proof_required"])
        self.assertEqual(result["request_id"], REQUEST_ID)
        self.assertEqual(result["revision"], 7)
        get_cursor.assert_called_once_with(tenant_id="tenant-1", user_id="user-1", commit=False)
        self.assertEqual(cursor.executed[0][1], ("tenant-1", "endpoint-1", "@endpoint"))
        self.assertIn("ORDER BY requested_at DESC, created_at DESC", cursor.executed[0][0])
        self.assertEqual(cursor.executed[1][1], ("tenant-1", "endpoint-1", "@endpoint", 7))
        self.assertIn("scope_kind = 'endpoint'", cursor.executed[1][0])
        self.assertIn("erp_target_projection_snapshots", cursor.executed[1][0])
        self.assertIn("erp_target_projection_heads", cursor.executed[1][0])

    def test_request_must_be_succeeded_endpoint_scope_and_exact_revision(self):
        cases = (
            (_refresh(status="leased"), "refresh_not_succeeded"),
            (_refresh(account_set_key="7:2"), "refresh_scope_mismatch"),
            (_refresh(result_revision=8), "revision_mismatch"),
            (_refresh(adapter="express"), "adapter_mismatch"),
        )
        for row, reason in cases:
            with self.subTest(reason=reason):
                cursor = _Cursor([row])
                with mock.patch.object(
                    evidence.db, "get_cursor_rls", return_value=_Context(cursor)
                ):
                    result = _validate()
                self.assertFalse(result["ok"])
                self.assertEqual(result["error_code"], evidence.CATALOG_REFRESH_INVALID)
                self.assertEqual(result["reason"], reason)
                self.assertEqual(len(cursor.executed), 1)

    def test_newer_refresh_invalidates_an_older_successful_proof(self):
        for status in ("requested", "failed"):
            with self.subTest(status=status):
                cursor = _Cursor([_refresh(id=NEW_REQUEST_ID, status=status)])
                with mock.patch.object(
                    evidence.db, "get_cursor_rls", return_value=_Context(cursor)
                ):
                    result = _validate()

                self.assertFalse(result["ok"])
                self.assertEqual(result["error_code"], evidence.CATALOG_REFRESH_INVALID)
                self.assertEqual(result["reason"], "refresh_superseded")
                self.assertEqual(len(cursor.executed), 1)

    def test_missing_request_or_exact_snapshot_is_invalid(self):
        for rows, reason in (
            ([None], "refresh_not_found"),
            ([_refresh(), None], "snapshot_not_found"),
        ):
            with self.subTest(reason=reason):
                cursor = _Cursor(rows)
                with mock.patch.object(
                    evidence.db, "get_cursor_rls", return_value=_Context(cursor)
                ):
                    result = _validate()
                self.assertFalse(result["ok"])
                self.assertEqual(result["reason"], reason)

    def test_snapshot_must_still_be_the_fresh_current_head(self):
        cases = (
            (_snapshot([{"source_id": "7:2"}], head_status="stale"), "projection_not_fresh"),
            (_snapshot([{"source_id": "7:2"}], head_revision=8), "snapshot_superseded"),
            (
                _snapshot([{"source_id": "7:2"}], head_snapshot_id="snapshot-8"),
                "snapshot_superseded",
            ),
        )
        for snapshot, reason in cases:
            with self.subTest(reason=reason):
                cursor = _Cursor([_refresh(), snapshot])
                with mock.patch.object(
                    evidence.db, "get_cursor_rls", return_value=_Context(cursor)
                ):
                    result = _validate()
                self.assertFalse(result["ok"])
                self.assertEqual(result["reason"], reason)

    def test_snapshot_must_contain_selected_source_id(self):
        cursor = _Cursor([_refresh(), _snapshot([{"source_id": "6:1"}])])
        with mock.patch.object(evidence.db, "get_cursor_rls", return_value=_Context(cursor)):
            result = _validate()

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "account_not_found")

    def test_snapshot_choice_must_be_active(self):
        cursor = _Cursor([_refresh(), _snapshot([{"source_id": "7:2", "active": False}])])
        with mock.patch.object(evidence.db, "get_cursor_rls", return_value=_Context(cursor)):
            result = _validate()

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "account_inactive")

    def test_express_snapshot_requires_matching_root(self):
        account_sets = json.dumps(
            [
                {
                    "source_id": r"C:\69EXP\TEST",
                    "attributes": {"root": r"C:\69EXP"},
                }
            ]
        )
        cursor = _Cursor(
            [
                _refresh(adapter="express"),
                _snapshot(account_sets, adapter="express"),
            ]
        )
        with mock.patch.object(evidence.db, "get_cursor_rls", return_value=_Context(cursor)):
            result = _validate(
                adapter="express",
                selected_account_set_key=r"c:/69exp/test/",
                bound_account_set_key=r"C:\68EXP\TEST",
                selected_root_key=r"c:/69exp/",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["reason"], "validated_snapshot")

    def test_express_snapshot_can_derive_root_from_selected_account_path(self):
        cursor = _Cursor(
            [
                _refresh(adapter="express"),
                _snapshot(
                    [
                        {
                            "source_id": r"C:\69EXP\TEST",
                            "attributes": {"root": r"C:\69EXP"},
                        }
                    ],
                    adapter="express",
                ),
            ]
        )
        with mock.patch.object(evidence.db, "get_cursor_rls", return_value=_Context(cursor)):
            result = _validate(
                adapter="express",
                selected_account_set_key=r"C:\69EXP\TEST",
                bound_account_set_key=r"C:\68EXP\TEST",
                selected_root_key=None,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["root_key"], r"c:\69exp")

    def test_express_code_choice_needs_no_root_when_snapshot_has_none(self):
        cursor = _Cursor(
            [
                _refresh(adapter="express"),
                _snapshot(
                    [{"source_id": "TEST2020", "attributes": {"writable": True}}],
                    adapter="express",
                ),
            ]
        )
        with mock.patch.object(evidence.db, "get_cursor_rls", return_value=_Context(cursor)):
            result = _validate(
                adapter="express",
                selected_account_set_key="test2020",
                bound_account_set_key="main",
                selected_root_key=None,
            )

        self.assertTrue(result["ok"])
        self.assertIsNone(result["root_key"])

    def test_existing_rls_cursor_is_reused_without_opening_another(self):
        cursor = _Cursor([_refresh(), _snapshot([{"source_id": "7:2"}])])
        with mock.patch.object(evidence.db, "get_cursor_rls") as get_cursor:
            result = evidence.validate_selection(
                cursor,
                tenant_id="tenant-1",
                user_id="user-1",
                endpoint_id="endpoint-1",
                adapter="mrerp",
                selected_account_set_key="7:2",
                bound_account_set_key="6:1",
                request_id=REQUEST_ID,
                revision=7,
            )

        self.assertTrue(result["ok"])
        get_cursor.assert_not_called()

    def test_express_root_mismatch_is_invalid(self):
        cursor = _Cursor(
            [
                _refresh(adapter="express"),
                _snapshot(
                    [
                        {
                            "source_id": r"C:\69EXP\TEST",
                            "attributes": {"root": r"C:\69EXP"},
                        }
                    ],
                    adapter="express",
                ),
            ]
        )
        with mock.patch.object(evidence.db, "get_cursor_rls", return_value=_Context(cursor)):
            result = _validate(
                adapter="express",
                selected_account_set_key=r"C:\69EXP\TEST",
                bound_account_set_key=r"C:\68EXP\TEST",
                selected_root_key=r"C:\70EXP",
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "root_mismatch")

    def test_express_snapshot_choice_must_be_writable(self):
        cursor = _Cursor(
            [
                _refresh(adapter="express"),
                _snapshot(
                    [
                        {
                            "source_id": r"C:\69EXP\TEST",
                            "attributes": {"root": r"C:\69EXP", "writable": False},
                        }
                    ],
                    adapter="express",
                ),
            ]
        )
        with mock.patch.object(evidence.db, "get_cursor_rls", return_value=_Context(cursor)):
            result = _validate(
                adapter="express",
                selected_account_set_key=r"C:\69EXP\TEST",
                bound_account_set_key=r"C:\68EXP\TEST",
                selected_root_key=r"C:\69EXP",
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "account_not_writable")


if __name__ == "__main__":
    unittest.main()
