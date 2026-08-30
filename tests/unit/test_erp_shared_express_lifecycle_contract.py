"""HTTP contract tests for the flag-off owner lifecycle boundary."""

from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

import routes.erp_shared_express_lifecycle_routes as route
from services.audit import store

ROOT = Path(__file__).resolve().parents[2]


def _app():
    app = FastAPI()
    app.include_router(route.router)
    return app


def _body(**extra):
    value = {
        "operation_id": str(uuid4()),
        "expected_generation": 1,
        "reason": "operator requested",
    }
    value.update(extra)
    return value


def _check_route_registered_in_erp_aggregate_and_registry():
    aggregate = (ROOT / "routes" / "erp_routes.py").read_text(encoding="utf-8")
    registry = (ROOT / "docs" / "agent" / "agent_registry.json").read_text(encoding="utf-8")
    assert "erp_shared_express_lifecycle_routes" in aggregate
    assert "_shared_lifecycle_router" in aggregate
    assert '"erp_shared_express_lifecycle_routes": "C"' in registry


def _check_flag_off_is_checked_before_endpoint_resolution(path):
    user = {"id": "u1", "tenant_id": "t1", "entry": "main", "is_super_admin": False}
    body = _body(
        **(
            {
                "target_workspace_client_id": 2,
                "confirm_target_workspace_client_id": 2,
            }
            if path == "rebind"
            else {"confirm": True} if path == "revoke" else {}
        )
    )
    with (
        patch.object(route, "get_current_user_from_request", return_value=user),
        patch.object(route, "require_perm", return_value=user),
        patch.object(route, "require_erp_portal", return_value=user),
        patch.object(route, "erp_shared_express_endpoint_enabled_for", return_value=False),
    ):
        response = TestClient(_app()).post(
            f"/api/erp/endpoints/{uuid4()}/shared/{path}",
            headers={"X-Workspace-Client-Id": "1"},
            json=body,
        )
    assert response.status_code == 404
    assert response.json()["detail"] == "erp.shared_endpoint_unavailable"


def _check_entry_and_super_admin_are_rejected_after_authentication():
    for user in (
        {"id": "u1", "tenant_id": "t1", "entry": "pos", "is_super_admin": False},
        {"id": "u1", "tenant_id": "t1", "entry": "main", "is_super_admin": True},
    ):
        with (
            patch.object(route, "get_current_user_from_request", return_value=user),
            patch.object(route, "require_perm", return_value=user),
            patch.object(route, "require_erp_portal", return_value=user),
            patch.object(route, "erp_shared_express_endpoint_enabled_for", return_value=True),
        ):
            response = TestClient(_app()).post(
                f"/api/erp/endpoints/{uuid4()}/shared/enable",
                headers={"X-Workspace-Client-Id": "1"},
                json=_body(),
            )
        assert response.status_code == 403
        assert response.json()["detail"] == "authz.entrance_scope"


def _check_models_reject_extra_and_invalid_semantic_confirmation():
    user = {"id": "u1", "tenant_id": "t1", "entry": "main", "is_super_admin": False}
    with (
        patch.object(route, "get_current_user_from_request", return_value=user),
        patch.object(route, "require_perm", return_value=user),
        patch.object(route, "require_erp_portal", return_value=user),
        patch.object(route, "erp_shared_express_endpoint_enabled_for", return_value=True),
        patch.object(route, "change_shared_express_endpoint") as service,
    ):
        response = TestClient(_app()).post(
            f"/api/erp/endpoints/{uuid4()}/shared/rebind",
            headers={"X-Workspace-Client-Id": "1"},
            json=_body(target_workspace_client_id=2, confirm_target_workspace_client_id=3),
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "erp.target_workspace_confirmation_mismatch"
    service.assert_not_called()

    with (
        patch.object(route, "get_current_user_from_request", return_value=user),
        patch.object(route, "require_perm", return_value=user),
        patch.object(route, "require_erp_portal", return_value=user),
        patch.object(route, "erp_shared_express_endpoint_enabled_for", return_value=True),
    ):
        response = TestClient(_app()).post(
            f"/api/erp/endpoints/{uuid4()}/shared/enable",
            headers={"X-Workspace-Client-Id": "1"},
            json=_body(unexpected=True),
        )
    assert response.status_code == 422


def _check_revoke_requires_explicit_confirmation():
    user = {"id": "u1", "tenant_id": "t1", "entry": "main", "is_super_admin": False}
    with (
        patch.object(route, "get_current_user_from_request", return_value=user),
        patch.object(route, "require_perm", return_value=user),
        patch.object(route, "require_erp_portal", return_value=user),
        patch.object(route, "erp_shared_express_endpoint_enabled_for", return_value=True),
        patch.object(route, "change_shared_express_endpoint") as service,
    ):
        response = TestClient(_app()).post(
            f"/api/erp/endpoints/{uuid4()}/shared/revoke",
            headers={"X-Workspace-Client-Id": "1"},
            json=_body(confirm=False),
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "erp.revoke_confirmation_required"
    service.assert_not_called()


def _check_reason_control_character_is_rejected():
    user = {"id": "u1", "tenant_id": "t1", "entry": "main", "is_super_admin": False}
    with (
        patch.object(route, "get_current_user_from_request", return_value=user),
        patch.object(route, "require_perm", return_value=user),
        patch.object(route, "require_erp_portal", return_value=user),
        patch.object(route, "erp_shared_express_endpoint_enabled_for", return_value=True),
    ):
        response = TestClient(_app()).post(
            f"/api/erp/endpoints/{uuid4()}/shared/disable",
            headers={"X-Workspace-Client-Id": "1"},
            json=_body(reason="bad\nreason"),
        )
    assert response.status_code == 422


def _check_lifecycle_audit_accepts_endpoint_and_action_details():
    store.insert_operation_log_tx(
        Mock(),
        tenant_id="tenant",
        actor_user_id="actor",
        actor_username="owner",
        actor_is_super=False,
        action="erp.endpoint.enable",
        target_type="erp_endpoint",
        target_id="endpoint",
        details={
            "operation_id": str(uuid4()),
            "endpoint_id": "endpoint",
            "action": "enable",
            "workspace_before": 1,
            "workspace_after": 1,
            "target_workspace_client_id": None,
            "expected_generation": 1,
            "actual_generation": 2,
            "generation_before": 1,
            "generation_after": 2,
            "enabled_before": False,
            "enabled_after": True,
            "shared_scope_before": True,
            "shared_scope_after": True,
            "revoked_before": False,
            "revoked_after": False,
            "reason": "owner requested",
        },
    )


class SharedExpressLifecycleContractTests(unittest.TestCase):
    def test_route_registered_in_erp_aggregate_and_registry(self):
        _check_route_registered_in_erp_aggregate_and_registry()

    def test_flag_off_is_checked_before_endpoint_resolution(self):
        for path in ("rebind", "enable", "disable", "revoke"):
            with self.subTest(path=path):
                _check_flag_off_is_checked_before_endpoint_resolution(path)

    def test_entry_and_super_admin_are_rejected_after_authentication(self):
        _check_entry_and_super_admin_are_rejected_after_authentication()

    def test_models_reject_extra_and_invalid_semantic_confirmation(self):
        _check_models_reject_extra_and_invalid_semantic_confirmation()

    def test_revoke_requires_explicit_confirmation(self):
        _check_revoke_requires_explicit_confirmation()

    def test_reason_control_character_is_rejected(self):
        _check_reason_control_character_is_rejected()

    def test_lifecycle_audit_accepts_endpoint_and_action_details(self):
        _check_lifecycle_audit_accepts_endpoint_and_action_details()
