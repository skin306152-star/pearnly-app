"""Service-level CAS and idempotency tests without a test-only adapter."""

from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest

from services.erp import shared_express_lifecycle as lifecycle


class Cursor:
    def __init__(self, endpoint, source, target=None):
        self.endpoint = dict(endpoint)
        self.source = dict(source)
        self.target = dict(target or {})
        self.last = ""
        self.rowcount = 0
        self.sql = []

    def execute(self, query, params=()):
        self.last = query
        self.sql.append((query, params))
        if query.lstrip().upper().startswith("UPDATE WORKSPACE_CLIENTS"):
            self.rowcount = 1
        elif query.lstrip().upper().startswith("UPDATE ERP_ENDPOINTS"):
            self.rowcount = 1
            self.endpoint["binding_generation"] += 1
            if "enabled = %s" in query:
                self.endpoint["enabled"] = bool(params[0])
            elif "workspace_client_id = %s" in query:
                self.endpoint["workspace_client_id"] = params[0]
            elif "revoked_at" in query:
                self.endpoint.update(
                    {
                        "workspace_client_id": None,
                        "shared_scope": False,
                        "enabled": False,
                        "revoked_at": "now",
                        "revoked_by": params[0],
                    }
                )
        else:
            self.rowcount = -1

    def fetchone(self):
        sql = self.last.lower()
        if "operation_logs" in sql:
            return None
        if "from users" in sql:
            return {"id": "actor"}
        if sql.startswith("update erp_endpoints"):
            return dict(self.endpoint)
        if "from erp_endpoints" in sql:
            return dict(self.endpoint)
        if "current_setting" in sql:
            return {"matches": True}
        if "set local" in sql:
            return None
        if "update workspace_clients" in sql:
            return None
        return None

    def fetchall(self):
        sql = self.last.lower()
        if "from workspace_clients" in sql:
            return [self.source, self.target] if self.target else [self.source]
        return []


class CursorContext:
    def __init__(self, cursor):
        self.cursor = cursor
        self.committed = False

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, tb):
        self.committed = exc_type is None
        return False


def _fixture(enabled=False):
    endpoint = {
        "id": "11111111-1111-4111-8111-111111111111",
        "user_id": "creator",
        "tenant_id": "tenant",
        "adapter": "express",
        "config": {},
        "enabled": enabled,
        "shared_scope": True,
        "workspace_client_id": 1,
        "binding_generation": 1,
        "revoked_at": None,
        "revoked_by": None,
        "name": "Express",
    }
    source = {"id": 1, "tenant_id": "tenant", "is_active": True, "erp_endpoint_id": endpoint["id"]}
    target = {"id": 2, "tenant_id": "tenant", "is_active": True, "erp_endpoint_id": None}
    return endpoint, source, target


def test_enable_cas_returns_safe_response_and_audits_once():
    endpoint, source, target = _fixture()
    cursor = Cursor(endpoint, source, target)
    context = CursorContext(cursor)
    user = {"id": "actor", "tenant_id": "tenant", "username": "owner"}
    authz = SimpleNamespace(membership_id="m1", role_key="owner", has=lambda code: True)
    op = str(uuid4())
    with (
        patch.object(lifecycle.db, "get_cursor_rls", return_value=context),
        patch.object(lifecycle, "lifecycle_schema_ready", return_value=True),
        patch.object(lifecycle, "resolve", return_value=authz),
        patch.object(lifecycle, "enable_shared_express_lifecycle_access", return_value=True),
        patch.object(lifecycle, "endpoint_has_managed_activity", return_value=False),
        patch.object(lifecycle, "insert_operation_log_tx") as audit,
    ):
        response = lifecycle.change_shared_express_endpoint(
            user=user,
            endpoint_id=endpoint["id"],
            action="enable",
            operation_id=op,
            expected_generation=1,
            source_workspace_id=1,
        )
    assert response["enabled"] is True
    assert response["generation"] == 2
    assert response["changed"] is True
    assert set(response) == {
        "ok",
        "endpoint_id",
        "workspace_client_id",
        "generation",
        "enabled",
        "shared_scope",
        "revoked",
        "lifecycle",
        "changed",
        "operation_id",
    }
    audit.assert_called_once()
    assert audit.call_args.kwargs["details"]["target_workspace_client_id"] is None
    assert context.committed


def test_stale_generation_is_409_without_audit():
    endpoint, source, target = _fixture(enabled=True)
    cursor = Cursor(endpoint, source, target)
    context = CursorContext(cursor)
    authz = SimpleNamespace(membership_id="m1", role_key="owner", has=lambda code: True)
    with (
        patch.object(lifecycle.db, "get_cursor_rls", return_value=context),
        patch.object(lifecycle, "lifecycle_schema_ready", return_value=True),
        patch.object(lifecycle, "resolve", return_value=authz),
        patch.object(lifecycle, "enable_shared_express_lifecycle_access", return_value=True),
        patch.object(lifecycle, "endpoint_has_managed_activity", return_value=False),
        patch.object(lifecycle, "insert_operation_log_tx") as audit,
    ):
        with pytest.raises(lifecycle.HTTPException) as exc:
            lifecycle.change_shared_express_endpoint(
                user={"id": "actor", "tenant_id": "tenant"},
                endpoint_id=endpoint["id"],
                action="disable",
                operation_id=str(uuid4()),
                expected_generation=2,
                source_workspace_id=1,
            )
    assert exc.value.status_code == 409
    assert exc.value.detail == "erp.endpoint_stale_generation"
    audit.assert_not_called()
    assert context.committed is False


@pytest.mark.parametrize(("action", "enabled"), [("enable", True), ("disable", False)])
def test_same_state_enable_disable_is_idempotent_even_when_busy(action, enabled):
    endpoint, source, target = _fixture(enabled=enabled)
    cursor = Cursor(endpoint, source, target)
    context = CursorContext(cursor)
    authz = SimpleNamespace(membership_id="m1", role_key="owner", has=lambda code: True)
    with (
        patch.object(lifecycle.db, "get_cursor_rls", return_value=context),
        patch.object(lifecycle, "lifecycle_schema_ready", return_value=True),
        patch.object(lifecycle, "resolve", return_value=authz),
        patch.object(lifecycle, "enable_shared_express_lifecycle_access", return_value=True),
        patch.object(lifecycle, "endpoint_has_managed_activity", return_value=True) as busy,
        patch.object(lifecycle, "insert_operation_log_tx") as audit,
    ):
        response = lifecycle.change_shared_express_endpoint(
            user={"id": "actor", "tenant_id": "tenant"},
            endpoint_id=endpoint["id"],
            action=action,
            operation_id=str(uuid4()),
            expected_generation=1,
            source_workspace_id=1,
        )
    assert response["changed"] is False
    assert response["enabled"] is enabled
    busy.assert_not_called()
    audit.assert_not_called()
    assert context.committed


def test_replay_requires_same_request_shape_and_reconstructs_safe_response():
    cursor = Cursor({}, {}, {})
    op = str(uuid4())
    cursor.fetchone = lambda: {
        "details": {
            "operation_id": op,
            "endpoint_id": "endpoint",
            "action": "disable",
            "workspace_before": 1,
            "workspace_after": 1,
            "target_workspace_client_id": None,
            "expected_generation": 3,
            "generation_after": 4,
            "enabled_after": False,
            "shared_scope_after": True,
            "revoked_after": False,
            "reason": "stop",
        }
    }
    response = lifecycle._operation_replay(
        cursor,
        tenant_id="tenant",
        actor_id="actor",
        operation_id=op,
        endpoint_id="endpoint",
        action="disable",
        source_workspace_id=1,
        target_workspace_id=None,
        expected_generation=3,
        reason="stop",
    )
    assert response["changed"] is True
    assert response["generation"] == 4
    assert response["enabled"] is False
    assert cursor.sql[0][1] == ("tenant", op)


def test_replay_conflicts_across_actors_and_request_shapes():
    op = str(uuid4())
    details = {
        "operation_id": op,
        "endpoint_id": "endpoint",
        "action": "disable",
        "workspace_before": 1,
        "workspace_after": 1,
        "target_workspace_client_id": None,
        "expected_generation": 3,
        "generation_after": 4,
        "enabled_after": False,
        "shared_scope_after": True,
        "revoked_after": False,
        "reason": "stop",
    }

    def replay_cursor(actor):
        cursor = Cursor({}, {}, {})
        cursor.fetchone = lambda: {"actor_user_id": actor, "details": details}
        return cursor

    response = lifecycle._operation_replay(
        replay_cursor("actor-a"),
        tenant_id="tenant",
        actor_id="actor-a",
        operation_id=op,
        endpoint_id="endpoint",
        action="disable",
        source_workspace_id=1,
        target_workspace_id=None,
        expected_generation=3,
        reason="stop",
    )
    assert response["operation_id"] == op

    with pytest.raises(lifecycle.LifecycleError, match="operation_id_conflict"):
        lifecycle._operation_replay(
            replay_cursor("actor-a"),
            tenant_id="tenant",
            actor_id="actor-b",
            operation_id=op,
            endpoint_id="endpoint",
            action="disable",
            source_workspace_id=1,
            target_workspace_id=None,
            expected_generation=3,
            reason="stop",
        )


def test_duplicate_active_endpoint_pointer_is_rejected_before_mutation():
    endpoint, source, target = _fixture()
    target["erp_endpoint_id"] = endpoint["id"]
    cursor = Cursor(endpoint, source, target)
    context = CursorContext(cursor)
    authz = SimpleNamespace(membership_id="m1", role_key="owner", has=lambda code: True)
    with (
        patch.object(lifecycle.db, "get_cursor_rls", return_value=context),
        patch.object(lifecycle, "lifecycle_schema_ready", return_value=True),
        patch.object(lifecycle, "resolve", return_value=authz),
        patch.object(lifecycle, "enable_shared_express_lifecycle_access", return_value=True),
        patch.object(lifecycle, "endpoint_has_managed_activity", return_value=False),
        patch.object(lifecycle, "insert_operation_log_tx") as audit,
    ):
        with pytest.raises(lifecycle.HTTPException) as exc:
            lifecycle.change_shared_express_endpoint(
                user={"id": "actor", "tenant_id": "tenant"},
                endpoint_id=endpoint["id"],
                action="disable",
                operation_id=str(uuid4()),
                expected_generation=1,
                source_workspace_id=1,
            )
    assert exc.value.detail == "erp.endpoint_workspace_conflict"
    audit.assert_not_called()


def test_rebind_allows_target_already_pointing_to_same_endpoint():
    endpoint, source, target = _fixture()
    target["erp_endpoint_id"] = endpoint["id"]
    cursor = Cursor(endpoint, source, target)
    context = CursorContext(cursor)
    authz = SimpleNamespace(membership_id="m1", role_key="owner", has=lambda code: True)
    with (
        patch.object(lifecycle.db, "get_cursor_rls", return_value=context),
        patch.object(lifecycle, "lifecycle_schema_ready", return_value=True),
        patch.object(lifecycle, "resolve", return_value=authz),
        patch.object(lifecycle, "enable_shared_express_lifecycle_access", return_value=True),
        patch.object(lifecycle, "endpoint_has_managed_activity", return_value=False),
        patch.object(lifecycle, "insert_operation_log_tx"),
    ):
        response = lifecycle.change_shared_express_endpoint(
            user={"id": "actor", "tenant_id": "tenant"},
            endpoint_id=endpoint["id"],
            action="rebind",
            operation_id=str(uuid4()),
            expected_generation=1,
            source_workspace_id=1,
            target_workspace_id=2,
        )
    assert response["workspace_client_id"] == 2
    assert response["generation"] == 2


def test_audit_failure_does_not_commit_lifecycle_transaction():
    endpoint, source, target = _fixture()
    cursor = Cursor(endpoint, source, target)
    context = CursorContext(cursor)
    authz = SimpleNamespace(membership_id="m1", role_key="owner", has=lambda code: True)
    with (
        patch.object(lifecycle.db, "get_cursor_rls", return_value=context),
        patch.object(lifecycle, "lifecycle_schema_ready", return_value=True),
        patch.object(lifecycle, "resolve", return_value=authz),
        patch.object(lifecycle, "enable_shared_express_lifecycle_access", return_value=True),
        patch.object(lifecycle, "endpoint_has_managed_activity", return_value=False),
        patch.object(lifecycle, "insert_operation_log_tx", side_effect=RuntimeError("audit down")),
    ):
        with pytest.raises(RuntimeError, match="audit down"):
            lifecycle.change_shared_express_endpoint(
                user={"id": "actor", "tenant_id": "tenant"},
                endpoint_id=endpoint["id"],
                action="enable",
                operation_id=str(uuid4()),
                expected_generation=1,
                source_workspace_id=1,
            )
    assert context.committed is False


def test_operation_replay_lookup_happens_after_advisory_and_owner_checks():
    endpoint, source, target = _fixture()
    cursor = Cursor(endpoint, source, target)
    context = CursorContext(cursor)
    authz = SimpleNamespace(membership_id="m1", role_key="owner", has=lambda code: True)
    events = []
    replay_response = {
        "ok": True,
        "endpoint_id": endpoint["id"],
        "workspace_client_id": 1,
        "generation": 2,
        "enabled": True,
        "shared_scope": True,
        "revoked": False,
        "lifecycle": "managed",
        "changed": True,
        "operation_id": str(uuid4()),
    }
    with (
        patch.object(lifecycle.db, "get_cursor_rls", return_value=context),
        patch.object(lifecycle, "lifecycle_schema_ready", return_value=True),
        patch.object(lifecycle, "resolve", return_value=authz),
        patch.object(
            lifecycle,
            "lock_endpoint_binding",
            side_effect=lambda *args: events.append("advisory"),
        ),
        patch.object(
            lifecycle,
            "_operation_replay",
            side_effect=lambda *args, **kwargs: (events.append("replay") or replay_response),
        ),
    ):
        result = lifecycle.change_shared_express_endpoint(
            user={"id": "actor", "tenant_id": "tenant"},
            endpoint_id=endpoint["id"],
            action="disable",
            operation_id=str(uuid4()),
            expected_generation=1,
            source_workspace_id=1,
        )
    assert result == replay_response
    assert events == ["advisory", "replay"]


def test_known_operation_conflicts_before_missing_endpoint_visibility_check():
    endpoint, source, target = _fixture(enabled=True)
    op = str(uuid4())
    details = {
        "operation_id": op,
        "endpoint_id": endpoint["id"],
        "action": "disable",
        "workspace_before": 1,
        "workspace_after": 1,
        "target_workspace_client_id": None,
        "expected_generation": 1,
        "generation_after": 2,
        "enabled_after": False,
        "shared_scope_after": True,
        "revoked_after": False,
        "reason": "stop",
    }

    class ReplayCursor(Cursor):
        def fetchone(self):
            if "operation_logs" in self.last.lower():
                return {"actor_user_id": "actor", "details": details}
            return super().fetchone()

    cursor = ReplayCursor(endpoint, source, target)
    context = CursorContext(cursor)
    authz = SimpleNamespace(membership_id="m1", role_key="owner", has=lambda code: True)
    with (
        patch.object(lifecycle.db, "get_cursor_rls", return_value=context),
        patch.object(lifecycle, "lifecycle_schema_ready", return_value=True),
        patch.object(lifecycle, "resolve", return_value=authz),
        patch.object(lifecycle, "lock_endpoint_binding"),
    ):
        with pytest.raises(lifecycle.HTTPException) as exc:
            lifecycle.change_shared_express_endpoint(
                user={"id": "actor", "tenant_id": "tenant"},
                endpoint_id="22222222-2222-4222-8222-222222222222",
                action="disable",
                operation_id=op,
                expected_generation=1,
                source_workspace_id=1,
                reason="stop",
            )
    assert exc.value.status_code == 409
    assert exc.value.detail == "erp.operation_id_conflict"
    assert context.committed is False
    assert not any("UPDATE " in query.upper() for query, _ in cursor.sql)


@pytest.mark.parametrize(
    ("constraint", "expected"),
    [
        (
            "uq_operation_logs_erp_endpoint_lifecycle_operation",
            "erp.operation_id_conflict",
        ),
        ("uq_erp_endpoints_shared_express_workspace", "erp.workspace_endpoint_conflict"),
        ("unrelated_constraint", None),
    ],
)
def test_unique_violation_mapping_is_constraint_specific(constraint, expected):
    error = RuntimeError("duplicate")
    error.pgcode = "23505"
    error.diag = SimpleNamespace(constraint_name=constraint)
    assert lifecycle._integrity_error_code(error) == expected
