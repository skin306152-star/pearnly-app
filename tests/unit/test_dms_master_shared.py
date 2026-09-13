"""Shared DMS master scope, refresh coalescing, and periodic orchestration."""

import unittest
from unittest import mock

from services.erp import dms_master_refresh as refresh
from services.erp import dms_master_shared as shared
from services.erp import dms_masters_cache as cache


def _ep(endpoint_id="e1", tenant="t1", admin="boss"):
    return {
        "id": endpoint_id,
        "user_id": "u1",
        "_dms_cache_tenant_id": tenant,
        "config": {"admin_username": admin, "admin_password": "secret"},
    }


_MASTERS = {key: [] for key in cache._COMPLETE_KEYS}
_MASTERS["cars"] = [["c1", "DMX", "D-Max"]]


class SharedScopeTests(unittest.TestCase):
    def test_same_tenant_admin_share_and_different_tenant_isolated(self):
        first = shared.cache_scope_id(_ep("one", "tenant-a"))
        second = shared.cache_scope_id(_ep("two", "tenant-a"))
        isolated = shared.cache_scope_id(_ep("three", "tenant-b"))
        self.assertEqual(first, second)
        self.assertNotEqual(first, isolated)

    def test_missing_admin_retains_endpoint_scope(self):
        endpoint = _ep("sales", "tenant-a")
        endpoint["config"] = {}
        self.assertEqual(shared.cache_scope_id(endpoint), "sales")
        self.assertFalse(shared.is_shared_scope(endpoint))

    def test_fresh_snapshot_avoids_lock_and_dms(self):
        cached = {"masters": _MASTERS, "age_seconds": 20}
        with (
            mock.patch.object(cache, "_read", return_value=cached),
            mock.patch.object(shared, "_acquire") as acquire,
            mock.patch.object(cache, "_fetch_masters_via_login") as fetch,
        ):
            self.assertIs(shared.get_session_masters(_ep()), _MASTERS)
        acquire.assert_not_called()
        fetch.assert_not_called()

    def test_stale_snapshot_refreshes_once_and_preserves_current_car_paints(self):
        old = {
            "masters": {
                **_MASTERS,
                "paints_by_car": {"c1": [["p1", "", "Red"]], "deleted": [["p2"]]},
                "paints_refreshed_at": {"c1": 123, "deleted": 456},
            },
            "age_seconds": 100,
        }
        reads = [old, old]
        with (
            mock.patch.object(cache, "_read", side_effect=lambda _key: reads.pop(0)),
            mock.patch.object(shared, "_acquire", return_value="owner") as acquire,
            mock.patch.object(shared, "_release") as release,
            mock.patch.object(cache, "_fetch_masters_via_login", return_value=_MASTERS) as fetch,
            mock.patch.object(cache, "_write") as write,
        ):
            result = shared.get_session_masters(_ep())
        acquire.assert_called_once()
        fetch.assert_called_once()
        release.assert_called_once()
        self.assertEqual(result["paints_by_car"], {"c1": [["p1", "", "Red"]]})
        self.assertNotIn("deleted", result["paints_refreshed_at"])
        write.assert_called_once()

    def test_incomplete_refresh_fails_closed_without_replacing_good_cache(self):
        stale = {"masters": _MASTERS, "age_seconds": 100}
        with (
            mock.patch.object(cache, "_read", return_value=stale),
            mock.patch.object(shared, "_acquire", return_value="owner"),
            mock.patch.object(shared, "_release"),
            mock.patch.object(cache, "_fetch_masters_via_login", return_value={"cars": []}),
            mock.patch.object(cache, "_write") as write,
        ):
            self.assertEqual(shared.get_session_masters(_ep()), {})
        write.assert_not_called()

    def test_paint_refresh_does_not_touch_whole_bundle_timestamp(self):
        base = {"masters": dict(_MASTERS), "age_seconds": 10}
        with (
            mock.patch.object(cache, "_read", return_value=base),
            mock.patch.object(shared, "_acquire", return_value="owner"),
            mock.patch.object(shared, "_release"),
            mock.patch.object(cache, "_fetch_paints_via_login", return_value=[]) as fetch,
            mock.patch.object(cache, "_write") as write,
        ):
            self.assertEqual(shared.get_session_paints(_ep(), "c1"), [])
        fetch.assert_called_once()
        self.assertFalse(write.call_args.kwargs["touch_refreshed_at"])
        self.assertIn("c1", write.call_args.args[1]["paints_refreshed_at"])


class RefreshOrchestrationTests(unittest.TestCase):
    def test_owner_admin_is_shared_with_member_and_scope_is_deduplicated(self):
        rows = [
            {
                "id": "owner-ep",
                "user_id": "owner",
                "_dms_cache_tenant_id": "tenant",
                "_role": "owner",
                "config": {"admin_username": "boss", "admin_password": "secret"},
            },
            {
                "id": "member-ep",
                "user_id": "member",
                "_dms_cache_tenant_id": "tenant",
                "_role": "member",
                "config": {},
            },
        ]
        with mock.patch.object(refresh, "_rows", return_value=rows):
            endpoints = refresh.shared_endpoints()
        self.assertEqual([row["id"] for row in endpoints], ["owner-ep"])

    def test_sweep_only_enqueues_stale_scope(self):
        endpoints = [_ep("fresh"), _ep("stale", admin="other")]
        with (
            mock.patch.object(refresh, "shared_endpoints", return_value=endpoints),
            mock.patch.object(refresh, "needs_refresh", side_effect=[False, True]),
            mock.patch("services.cloud_tasks.dispatch.enqueue", return_value="task") as enqueue,
        ):
            result = refresh.sweep()
        self.assertEqual(result, {"checked": 2, "queued": 1})
        enqueue.assert_called_once_with("dms.masters_refresh", "stale")


if __name__ == "__main__":
    unittest.main()
