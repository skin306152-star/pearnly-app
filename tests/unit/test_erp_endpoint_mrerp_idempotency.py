import asyncio
import sys
from types import SimpleNamespace
from unittest import mock

from routes import erp_endpoints_routes
from services.erp import push_store


class Cursor:
    def __init__(self, *, rows=None, inserted_id=None):
        self.rows = list(rows or [])
        self.inserted_id = inserted_id
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return {"id": self.inserted_id} if self.inserted_id else None


def _config():
    return {"username": "account", "password": "secret"}


def test_create_reuses_same_mrerp_identity_under_transaction_lock():
    cursor = Cursor(
        rows=[
            {
                "id": "existing",
                "adapter": "mrerp",
                "config": _config(),
                "created_at": "2026-08-28T09:21:07Z",
                "_workspace_binding_ids": ["106"],
            }
        ]
    )

    endpoint_id = push_store.create_erp_endpoint_with_cursor(
        cursor,
        user_id="owner",
        name="MR.ERP",
        adapter="mrerp",
        config=_config(),
    )

    sql = " ".join(call[0] for call in cursor.calls)
    assert endpoint_id == "existing"
    assert "pg_advisory_xact_lock" in cursor.calls[0][0]
    assert "INSERT INTO erp_endpoints" not in sql


def test_create_inserts_when_mrerp_identity_is_new():
    cursor = Cursor(rows=[], inserted_id="new-endpoint")

    endpoint_id = push_store.create_erp_endpoint_with_cursor(
        cursor,
        user_id="owner",
        name="MR.ERP",
        adapter="mrerp",
        config=_config(),
    )

    sql = " ".join(call[0] for call in cursor.calls)
    assert endpoint_id == "new-endpoint"
    assert "pg_advisory_xact_lock" in sql
    assert "INSERT INTO erp_endpoints" in sql


def test_retry_reuses_connection_before_plan_limit_check():
    user = {"id": "owner", "plan": "free", "entry": "erp", "role": "owner"}
    endpoint = {"id": "existing", "adapter": "mrerp", "config": _config()}
    request = SimpleNamespace(headers={})
    req = erp_endpoints_routes.ErpEndpointCreate(
        name="MR.ERP",
        adapter="mrerp",
        config={"username": "account", "password": "secret"},
    )

    with (
        mock.patch.object(erp_endpoints_routes, "get_current_user_from_request", return_value=user),
        mock.patch.object(erp_endpoints_routes, "require_erp_portal"),
        mock.patch.object(erp_endpoints_routes, "_check_push_access"),
        mock.patch.object(erp_endpoints_routes.team_access, "require_endpoint_manager"),
        mock.patch.object(
            erp_endpoints_routes,
            "_plan_permissions",
            return_value={"endpoints_limit": 1, "can_auto_push_erp": True},
        ),
        mock.patch("services.erp.ssrf_guard.assert_public_config_url", new=mock.AsyncMock()),
        mock.patch.dict(
            sys.modules,
            {
                "core.kms_helper": SimpleNamespace(
                    encrypt_str=lambda value: value,
                    is_encrypted=lambda _value: False,
                )
            },
        ),
        mock.patch.object(
            erp_endpoints_routes.db,
            "find_reusable_erp_endpoint",
            return_value="existing",
        ) as find_reusable,
        mock.patch.object(erp_endpoints_routes.db, "get_erp_endpoint", return_value=endpoint),
        mock.patch.object(erp_endpoints_routes.db, "list_erp_endpoints") as list_endpoints,
        mock.patch.object(erp_endpoints_routes.db, "create_erp_endpoint") as create_endpoint,
    ):
        result = asyncio.run(erp_endpoints_routes.erp_endpoints_create(req, request))

    assert result["id"] == "existing"
    find_reusable.assert_called_once()
    list_endpoints.assert_not_called()
    create_endpoint.assert_not_called()
