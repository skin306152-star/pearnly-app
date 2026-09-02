from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest import mock

from services.erp import line_target_catalog


class LineTargetProjectionSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.endpoint = {
            "id": "endpoint-1",
            "adapter": "mrerp",
            "enabled": True,
            "config": {"comidyear": "15", "seldb": "2"},
        }
        self.state = {
            "freshness": {
                "status": "fresh",
                "error_code": None,
                "attempted_at": datetime(2026, 9, 2, 8, 0, tzinfo=timezone.utc),
            },
            "snapshot": {
                "revision": 4,
                "account_sets_revision": 3,
                "account_sets": [
                    {
                        "source_id": "15:2",
                        "label": "New account",
                        "attributes": {"comidyear": "15", "seldb": "2"},
                    }
                ],
            },
        }

    def test_refresh_uses_projection_and_bypasses_legacy_probe_cache(self):
        with (
            mock.patch.object(
                line_target_catalog,
                "erp_target_projection_enabled_for",
                return_value=True,
            ),
            mock.patch.object(
                line_target_catalog,
                "refresh_mrerp_projection",
                return_value={"ok": True, "error_code": None},
            ) as refresh,
            mock.patch.object(line_target_catalog, "load_state", return_value=self.state),
            mock.patch.object(line_target_catalog.target_readiness, "probe_endpoint") as legacy,
        ):
            probe = line_target_catalog._projection_probe(
                self.endpoint,
                tenant_id="tenant-1",
                user_id="user-1",
                refresh=True,
            )

        self.assertTrue(probe["ok"])
        self.assertEqual(probe["companies"][0]["comidyear"], "15")
        self.assertEqual(probe["account_sets_revision"], 3)
        self.assertFalse(probe["cached"])
        refresh.assert_called_once()
        legacy.assert_not_called()

    def test_failed_master_refresh_keeps_choices_but_blocks_new_document(self):
        with (
            mock.patch.object(
                line_target_catalog,
                "erp_target_projection_enabled_for",
                return_value=True,
            ),
            mock.patch.object(
                line_target_catalog,
                "refresh_mrerp_projection",
                return_value={"ok": False, "error_code": "ERR_TECHNICAL"},
            ),
            mock.patch.object(line_target_catalog, "load_state", return_value=self.state),
        ):
            probe = line_target_catalog._projection_probe(
                self.endpoint,
                tenant_id="tenant-1",
                user_id="user-1",
                refresh=True,
            )

        self.assertFalse(probe["ok"])
        self.assertEqual(probe["error_code"], "ERR_TECHNICAL")
        self.assertEqual(probe["companies"][0]["label"], "New account")

    def test_disabled_projection_preserves_legacy_behavior(self):
        expected = {"ok": True, "companies": []}
        with (
            mock.patch.object(
                line_target_catalog,
                "erp_target_projection_enabled_for",
                return_value=False,
            ),
            mock.patch.object(
                line_target_catalog.target_readiness,
                "probe_endpoint",
                return_value=expected,
            ) as legacy,
        ):
            probe = line_target_catalog._projection_probe(
                self.endpoint,
                tenant_id="tenant-1",
                user_id="user-1",
                refresh=True,
            )
        self.assertIs(probe, expected)
        legacy.assert_called_once_with(self.endpoint, refresh=True)


if __name__ == "__main__":
    unittest.main()
