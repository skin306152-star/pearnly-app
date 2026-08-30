"""Unit contracts for the B3B3 managed live service (no database dependency)."""

import inspect
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from services.erp.shared_express_live import (
    ManagedLiveError,
    _profile_status,
    _profile_is_fresh,
    confirm_managed_live_profile,
    record_managed_heartbeat,
)


class ManagedLiveServiceTests(unittest.TestCase):
    def test_public_signatures_are_frozen(self):
        heartbeat = inspect.signature(record_managed_heartbeat)
        self.assertEqual(
            tuple(heartbeat.parameters),
            ("token", "account_set", "account_dir", "agent_version", "offline"),
        )
        self.assertEqual(
            tuple(inspect.signature(confirm_managed_live_profile).parameters),
            (
                "user",
                "endpoint_id",
                "source_workspace_id",
                "expected_generation",
                "confirm",
                "request_ip",
                "request_ua",
            ),
        )

    def test_invalid_token_is_stable_and_does_not_open_database(self):
        with (
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
            mock.patch("services.erp.shared_express_live.db.get_cursor") as cursor,
        ):
            with self.assertRaises(ManagedLiveError) as raised:
                record_managed_heartbeat(
                    "not-a-token", account_set=None, account_dir=None, agent_version=None
                )
        self.assertEqual(
            (raised.exception.code, raised.exception.status), ("erp.agent_unauthorized", 401)
        )
        cursor.assert_not_called()

    def test_profile_status_is_fail_closed(self):
        base = {
            "bound_account_set": "main",
            "bound_profile_key": "v1:key",
            "live_account_set": "main",
            "live_profile_key": "v1:key",
        }
        self.assertEqual(_profile_status(base, True), ("ready", True))
        mismatch = dict(base, live_account_set="other")
        self.assertEqual(_profile_status(mismatch, True), ("mismatch", False))
        self.assertEqual(_profile_status(base, False), ("needs_attention", False))
        self.assertEqual(
            _profile_status(dict(base, bound_account_set=None, bound_profile_key=None), True),
            ("unbound", False),
        )

    def test_observed_profile_normalizes_set_and_path_equivalents(self):
        from services.erp.shared_express_live import _observed_profile

        first = _observed_profile(" Main ", r"C:\Pearnly\Main")
        second = _observed_profile("main", r"c:/pearnly/main")
        self.assertEqual(first[0], "main")
        self.assertEqual(first[1], second[1])

    def test_confirmation_requires_explicit_boolean(self):
        with self.assertRaises(ManagedLiveError) as raised:
            confirm_managed_live_profile({}, "not-used", 1, 1, False, None, None)
        self.assertEqual(
            (raised.exception.code, raised.exception.status),
            ("erp.profile_confirmation_required", 400),
        )

    def test_database_clock_freshness_boundaries(self):
        now = datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc)
        cases = (
            (now - timedelta(seconds=179.999), True),
            (now - timedelta(seconds=180), False),
            (now + timedelta(seconds=5), True),
            (now + timedelta(seconds=5.001), False),
        )
        for seen, expected in cases:
            with self.subTest(seen=seen):
                self.assertIs(_profile_is_fresh(seen, now), expected)

    def test_online_heartbeat_uses_wall_clock_and_offline_keeps_epoch(self):
        source = inspect.getsource(record_managed_heartbeat)
        self.assertIn("agent_last_seen_at = clock_timestamp()", source)
        self.assertNotIn("agent_last_seen_at = NOW()", source)
        self.assertIn("agent_last_seen_at = to_timestamp(0)", source)


if __name__ == "__main__":
    unittest.main()
