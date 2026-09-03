from unittest import mock

from services.erp.endpoint_identity import (
    advisory_lock_key,
    deduplicate_legacy_endpoints,
    deduplicate_legacy_specs,
    matching_mrerp_endpoint,
)


def _endpoint(endpoint_id, password="secret", **fields):
    return {
        "id": endpoint_id,
        "adapter": "mrerp",
        "config": {
            "system_url": "https://www.mrerp4sme.com/",
            "username": "account",
            "password": password,
        },
        "created_at": fields.pop("created_at", f"2026-09-0{len(endpoint_id)}T00:00:00Z"),
        **fields,
    }


def test_bound_endpoint_wins_over_unbound_duplicate():
    bound = _endpoint("bound", created_at="2026-08-28T09:21:07Z")
    duplicate = _endpoint("duplicate", created_at="2026-09-01T11:51:06Z")
    workspace = {"id": 106, "erp_endpoint_id": "bound"}

    specs = deduplicate_legacy_specs([(bound, workspace, 1, False), (duplicate, None, 0, True)])

    assert [spec[0]["id"] for spec in specs] == ["bound"]


def test_unbound_duplicates_collapse_to_latest_row():
    oldest = _endpoint("old", created_at="2026-08-01T00:00:00Z")
    newest = _endpoint("new", created_at="2026-09-01T00:00:00Z")

    result = deduplicate_legacy_endpoints([oldest, newest])

    assert [endpoint["id"] for endpoint in result] == ["new"]


def test_distinct_credentials_remain_distinct_connections():
    result = deduplicate_legacy_endpoints(
        [_endpoint("first", password="one"), _endpoint("second", password="two")]
    )

    assert [endpoint["id"] for endpoint in result] == ["first", "second"]


def test_same_login_bound_to_different_workspaces_remains_visible():
    first = _endpoint("first", _workspace_binding_ids=["10"])
    second = _endpoint("second", _workspace_binding_ids=["11"])

    result = deduplicate_legacy_endpoints([first, second])

    assert [endpoint["id"] for endpoint in result] == ["first", "second"]


def test_matching_connection_prefers_bound_active_row():
    old_unbound = _endpoint("unbound", created_at="2026-08-01T00:00:00Z")
    bound = _endpoint(
        "bound",
        created_at="2026-09-01T00:00:00Z",
        _workspace_binding_ids=["106"],
    )

    result = matching_mrerp_endpoint(
        [old_unbound, bound],
        {"username": "account", "password": "secret"},
    )

    assert result and result["id"] == "bound"


def test_encrypted_credentials_are_compared_after_resolution():
    stored = _endpoint("stored")
    stored["config"] = {"username_enc": "cipher-a", "password_enc": "cipher-b"}
    incoming = {"username_enc": "cipher-c", "password_enc": "cipher-d"}

    with mock.patch(
        "services.erp.erp_mrerp_listing._resolve_creds",
        side_effect=[("account", "secret", None), ("account", "secret", None)],
    ):
        result = matching_mrerp_endpoint([stored], incoming)

    assert result and result["id"] == "stored"


def test_lock_key_is_stable_and_scoped_by_user():
    identity = ("https://www.mrerp4sme.com", "digest")

    assert advisory_lock_key("u1", identity) == advisory_lock_key("u1", identity)
    assert advisory_lock_key("u1", identity) != advisory_lock_key("u2", identity)
