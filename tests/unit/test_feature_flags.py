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


if __name__ == "__main__":
    unittest.main()
