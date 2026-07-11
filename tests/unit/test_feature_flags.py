# -*- coding: utf-8 -*-
"""WP2 · core.feature_flags.agent_enabled_for · 消费侧默认关 + 委托 store。"""

import unittest
from unittest import mock

from core import feature_flags


class AgentEnabledForTests(unittest.TestCase):
    def test_delegates_to_store_with_agent_key(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=True
        ) as m:
            self.assertTrue(feature_flags.agent_enabled_for("u1"))
            m.assert_called_once_with(feature_flags.AGENT_ENABLED_KEY, "u1")

    def test_store_false_propagates(self):
        with mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False):
            self.assertFalse(feature_flags.agent_enabled_for("u1"))

    def test_store_raises_fails_closed(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user",
            side_effect=RuntimeError("boom"),
        ):
            self.assertFalse(feature_flags.agent_enabled_for("u1"))


class PearnlyAiM1EnabledForTests(unittest.TestCase):
    """M1-B2 客户建档收严闸:按账套主体归属判定,不按单个操作人。"""

    def test_tenant_id_takes_priority_over_user_id(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=True
        ) as m:
            self.assertTrue(feature_flags.pearnly_ai_m1_enabled_for("t1", "u1"))
            m.assert_called_once_with(feature_flags.PEARNLY_AI_M1_KEY, "t1")

    def test_falls_back_to_user_id_when_no_tenant(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=True
        ) as m:
            self.assertTrue(feature_flags.pearnly_ai_m1_enabled_for(None, "u1"))
            m.assert_called_once_with(feature_flags.PEARNLY_AI_M1_KEY, "u1")

    def test_defaults_closed_no_setting_row(self):
        with mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False):
            self.assertFalse(feature_flags.pearnly_ai_m1_enabled_for("t1", "u1"))

    def test_store_raises_fails_closed(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user",
            side_effect=RuntimeError("boom"),
        ):
            self.assertFalse(feature_flags.pearnly_ai_m1_enabled_for("t1", "u1"))


class PearnlyAiSodEnabledForTests(unittest.TestCase):
    """C3 · 工单 SoD 强制闸:按 tenant 判定,默认关(现状单人流不变)。"""

    def test_delegates_to_store_with_sod_key_and_tenant(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=True
        ) as m:
            self.assertTrue(feature_flags.pearnly_ai_sod_enabled_for("t-1"))
            m.assert_called_once_with(feature_flags.PEARNLY_AI_SOD_KEY, "t-1")

    def test_defaults_closed_no_setting_row(self):
        with mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False):
            self.assertFalse(feature_flags.pearnly_ai_sod_enabled_for("t-1"))

    def test_store_raises_fails_closed(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user",
            side_effect=RuntimeError("boom"),
        ):
            self.assertFalse(feature_flags.pearnly_ai_sod_enabled_for("t-1"))


class PearnlyAiClientPoolEnabledForTests(unittest.TestCase):
    """D2 · LINE 待问客户池闸:按 tenant 判定,默认关(现状 webhook 用户码流不变)。"""

    def test_delegates_to_store_with_client_pool_key_and_tenant(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=True
        ) as m:
            self.assertTrue(feature_flags.pearnly_ai_client_pool_enabled_for("t-1"))
            m.assert_called_once_with(feature_flags.PEARNLY_AI_CLIENT_POOL_KEY, "t-1")

    def test_defaults_closed_no_setting_row(self):
        with mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False):
            self.assertFalse(feature_flags.pearnly_ai_client_pool_enabled_for("t-1"))

    def test_none_tenant_is_closed(self):
        with mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False):
            self.assertFalse(feature_flags.pearnly_ai_client_pool_enabled_for(None))

    def test_store_raises_fails_closed(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user",
            side_effect=RuntimeError("boom"),
        ):
            self.assertFalse(feature_flags.pearnly_ai_client_pool_enabled_for("t-1"))


class PearnlyAiBankReconEnabledForTests(unittest.TestCase):
    """E1 · 工单银行对账逐笔对平闸:按 tenant 判定,默认关(R3 现状存在性判定不变)。"""

    def test_delegates_to_store_with_bank_recon_key_and_tenant(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=True
        ) as m:
            self.assertTrue(feature_flags.pearnly_ai_bank_recon_enabled_for("t-1"))
            m.assert_called_once_with(feature_flags.PEARNLY_AI_BANK_RECON_KEY, "t-1")

    def test_defaults_closed_no_setting_row(self):
        with mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False):
            self.assertFalse(feature_flags.pearnly_ai_bank_recon_enabled_for("t-1"))

    def test_store_raises_fails_closed(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user",
            side_effect=RuntimeError("boom"),
        ):
            self.assertFalse(feature_flags.pearnly_ai_bank_recon_enabled_for("t-1"))


class PearnlyAiShadowDraftEnabledForTests(unittest.TestCase):
    """F1 · 工单影子底稿闸:按 tenant 判定,默认关(reconcile 现状 gates 无 r5_shadow 键)。"""

    def test_delegates_to_store_with_shadow_key_and_tenant(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=True
        ) as m:
            self.assertTrue(feature_flags.pearnly_ai_shadow_draft_enabled_for("t-1"))
            m.assert_called_once_with(feature_flags.PEARNLY_AI_SHADOW_DRAFT_KEY, "t-1")

    def test_defaults_closed_no_setting_row(self):
        with mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False):
            self.assertFalse(feature_flags.pearnly_ai_shadow_draft_enabled_for("t-1"))

    def test_store_raises_fails_closed(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user",
            side_effect=RuntimeError("boom"),
        ):
            self.assertFalse(feature_flags.pearnly_ai_shadow_draft_enabled_for("t-1"))


if __name__ == "__main__":
    unittest.main()
