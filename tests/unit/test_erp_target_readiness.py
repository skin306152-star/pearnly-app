from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest
from unittest import mock

from services.erp import target_readiness
from services.erp import line_target_projection as erp_target_projection


class ErpTargetReadinessTests(unittest.TestCase):
    def test_master_refresh_requires_companion_protocol_1_1_76(self):
        self.assertFalse(erp_target_projection.supports_master_refresh(None))
        self.assertFalse(erp_target_projection.supports_master_refresh("1.1.75"))
        self.assertTrue(erp_target_projection.supports_master_refresh("1.1.76"))
        self.assertTrue(erp_target_projection.supports_master_refresh("1.2.0"))

    def test_mrerp_probe_is_cached_and_keeps_rich_response_shape(self):
        endpoint = {
            "id": "mrerp-1",
            "user_id": "owner-1",
            "adapter": "mrerp",
            "enabled": True,
            "config": {"username_enc": "cipher", "password_enc": "cipher"},
        }
        result = {
            "ok": True,
            "companies": [{"id": "company-1", "name": "Main"}],
            "elapsed_ms": 12,
        }
        target_readiness.clear_probe_cache()
        with mock.patch(
            "services.erp.erp_push.test_mrerp_endpoint",
            return_value=result,
        ) as probe:
            first = target_readiness.probe_endpoint(endpoint)
            second = target_readiness.probe_endpoint(endpoint)

        self.assertEqual(first["companies"], result["companies"])
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        probe.assert_called_once()

    def test_legacy_express_uses_companion_heartbeat_and_is_selectable(self):
        now = datetime.now(timezone.utc)
        endpoint = {
            "id": "express-1",
            "name": "Express Main",
            "adapter": "express",
            "enabled": True,
            "binding_generation": 0,
            "server_now": now,
            "config": {
                "agent_token_hash": "hash",
                "agent_last_seen_at": (now - timedelta(seconds=20)).isoformat(),
                "account_set": "69EXP",
            },
        }
        probe = target_readiness.probe_endpoint(endpoint, refresh=True)
        target = erp_target_projection.legacy_target(
            endpoint,
            {"id": 7, "name": "Main", "erp_endpoint_id": "express-1"},
            binding_count=1,
            probe=probe,
        )

        self.assertTrue(probe["ok"])
        self.assertEqual(target["connection_state"], "online")
        self.assertTrue(target["selectable"])
        self.assertEqual(target["mode_options"], ["stock", "service"])
        self.assertFalse(target["managed"])
        self.assertEqual(target["label"], "Express Main · 69EXP")
        self.assertEqual(target["account_set_label"], "69EXP")
        self.assertNotIn("agent_token_hash", repr(target))

    def test_mrerp_target_shows_the_mapped_account_set_name(self):
        endpoint = {
            "id": "mrerp-1",
            "name": "MR.ERP",
            "adapter": "mrerp",
            "enabled": True,
            "config": {
                "username_enc": "cipher",
                "password_enc": "cipher",
                "comidyear": "15",
                "seldb": "2",
            },
        }
        probe = {
            "ok": True,
            "companies": [{"label": "Sister Makeup 2026", "comidyear": "15", "seldb": "2"}],
        }
        target = erp_target_projection.legacy_target(
            endpoint,
            {"id": 7, "name": "Sister Makeup", "erp_endpoint_id": "mrerp-1"},
            binding_count=1,
            probe=probe,
        )

        self.assertEqual(target["label"], "MR.ERP · Sister Makeup 2026")
        self.assertEqual(target["account_set_label"], "Sister Makeup 2026")

    def test_mrerp_target_blocks_when_saved_account_set_is_no_longer_available(self):
        endpoint = {
            "id": "mrerp-1",
            "adapter": "mrerp",
            "enabled": True,
            "config": {
                "username_enc": "cipher",
                "password_enc": "cipher",
                "comidyear": "15",
                "seldb": "2",
            },
        }
        target = erp_target_projection.legacy_target(
            endpoint,
            {"id": 7, "name": "Sister Makeup", "erp_endpoint_id": "mrerp-1"},
            binding_count=1,
            probe={
                "ok": True,
                "companies": [{"label": "Other", "comidyear": "6", "seldb": "1"}],
            },
        )

        self.assertFalse(target["selectable"])
        self.assertEqual(target["block_reason"], "account_set_unavailable")
        self.assertFalse(target["ready_checks"]["profile_matches"])

    def test_express_heartbeat_is_not_cached_and_offline_target_is_blocked(self):
        now = datetime.now(timezone.utc)
        endpoint = {
            "id": "express-1",
            "adapter": "express",
            "enabled": True,
            "binding_generation": 0,
            "server_now": now,
            "config": {
                "agent_token_hash": "hash",
                "agent_last_seen_at": (now - timedelta(seconds=20)).isoformat(),
                "account_set": "69EXP",
            },
        }
        self.assertTrue(target_readiness.probe_endpoint(endpoint)["ok"])
        endpoint["config"]["agent_last_seen_at"] = (now - timedelta(minutes=5)).isoformat()
        probe = target_readiness.probe_endpoint(endpoint)
        status = target_readiness.endpoint_status(endpoint, probe=probe)

        self.assertFalse(status["ready"])
        self.assertEqual(status["connection_state"], "offline")
        self.assertEqual(status["block_reason"], "companion_offline")
