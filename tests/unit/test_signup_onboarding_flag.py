# -*- coding: utf-8 -*-
"""注册流打「待选业态」标记的契约守门(平台业态套餐 · docs/platform-onboarding/05)。

锁定 services/auth/signup_core._ensure_tenant_for_new_user(所有注册路径建租户的唯一汇合点):
  1. 建租户后调 store.set_needs_onboarding(..., value=True) → 新注册首进自动弹业态选择
  2. 该调用被 try/except 包裹 → 标记写失败也绝不阻塞注册(主路径安全)
真库读写行为另由 tests/e2e/_platform_pp3_dbcode.py(真 Supabase)覆盖。
"""

import inspect
import unittest

from services.auth import signup_core


class SignupOnboardingFlagContractTests(unittest.TestCase):
    def setUp(self):
        self.src = inspect.getsource(signup_core._ensure_tenant_for_new_user)

    def test_sets_needs_onboarding_true_at_tenant_creation(self):
        self.assertIn("set_needs_onboarding", self.src)
        self.assertIn("value=True", self.src)

    def test_flag_write_is_guarded(self):
        # 标记写在 try/except 内 · 失败只告警不抛(注册主路径不可因此挂掉)
        idx = self.src.index("set_needs_onboarding")
        before = self.src[:idx]
        self.assertIn("try:", before.rsplit("\n\n", 1)[-1] + before[-400:])
        self.assertIn("set_needs_onboarding skip", self.src)


if __name__ == "__main__":
    unittest.main()
