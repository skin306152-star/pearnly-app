# -*- coding: utf-8 -*-
"""PS-3 新租户 POS 锁闸:apply_preset 门控两态 + 钥匙闸默认关(fail-closed)。

验收⑤:闸关=全链零变化(pos 照预设开);闸开且未放行=pos「预备但锁定」(不真开)。
锁闸是加限功能 → 判据异常一律 fail-open(绝不把 pos 从既有客户锁没)。"""

import unittest
from unittest import mock

from core import feature_flags
from services.modules import presets


class ApplyPresetLockGatingTests(unittest.TestCase):
    def _run(self, *, allowed):
        """跑 apply_preset(retail 含 pos),把 store DAL 全打桩,返回 {module: enabled} 快照。"""
        calls = {}

        def _set_module(cur, *, tenant_id, module_key, enabled, config=None):
            calls[module_key] = enabled

        with (
            mock.patch.object(presets.store, "set_module", _set_module),
            mock.patch.object(presets.store, "set_business_type"),
            mock.patch.object(presets.store, "set_needs_onboarding"),
            mock.patch.object(presets.store, "get_modules", return_value={}),
            mock.patch.object(presets, "_pos_provision_allowed", return_value=allowed),
        ):
            presets.apply_preset(object(), tenant_id="t1", business_type="retail")
        return calls

    def test_lock_open_and_not_allowed_locks_pos(self):
        calls = self._run(allowed=False)
        self.assertFalse(calls["pos"])  # 预备但锁定:pos 不真开
        self.assertTrue(calls["inventory"])  # 其余预设模块不受影响

    def test_allowed_opens_pos_as_usual(self):
        calls = self._run(allowed=True)
        self.assertTrue(calls["pos"])  # 放行(闸关/存量/授权/订阅)→ 与历史一致

    def test_provision_allowed_fail_open(self):
        # 判据抛异常 → _pos_provision_allowed 吞掉返 True(fail-open · 不误伤既有客户)
        with mock.patch(
            "services.pos.entitlements.pos_provision_allowed", side_effect=RuntimeError("boom")
        ):
            self.assertTrue(presets._pos_provision_allowed(object(), "t1"))


class FeatureFlagDefaultClosedTests(unittest.TestCase):
    def test_lock_flag_delegates_with_correct_key(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=True
        ) as m:
            self.assertTrue(feature_flags.pos_provision_lock_enabled_for("t1"))
        m.assert_called_once_with(feature_flags.POS_PROVISION_LOCK_KEY, "t1")

    def test_lock_flag_fail_closed_on_exception(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user",
            side_effect=RuntimeError("db down"),
        ):
            self.assertFalse(feature_flags.pos_provision_lock_enabled_for("t1"))


if __name__ == "__main__":
    unittest.main()
