# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/static_assets.py + users.columns.ensure_user_profile_columns
(2026-05-29 从 app.py 抽出启动期工具 · 纯搬家 0 逻辑改 · 并删 app.py 死码 _calc_trial_days_left)

锁定:
  1. static_assets 导出 read_frontend_version / purge_stale_static_gz · 安全可调不 raise。
  2. app.py 模块全局 PEARNLY_FRONTEND_VERSION 仍在(meta_aliases /api/version + admin_diagnostics 读它)
     · 且由单一来源 read_frontend_version 计算。
  3. purge_stale_static_gz / ensure_user_profile_columns 走单一来源(app 不再各拷一份)。
  4. ensure_user_profile_columns 已落 services/users/columns.py(同类 ensure_* 列归位)。
  5. 死码 _calc_trial_days_left 已删(me_routes 不再算 trial_days_left)· app 上不应再有。
"""

import unittest

from services import static_assets
from services.users import columns


class StaticAssetsContractTests(unittest.TestCase):
    def test_static_assets_exports_callable(self):
        self.assertTrue(callable(static_assets.read_frontend_version))
        self.assertTrue(callable(static_assets.purge_stale_static_gz))

    def test_read_frontend_version_safe_returns_str(self):
        # static/home.html 不在测试 cwd → 安全返 "0" · 不 raise
        v = static_assets.read_frontend_version()
        self.assertIsInstance(v, str)

    def test_purge_safe_no_raise(self):
        static_assets.purge_stale_static_gz()  # 不应 raise(目录不存在也吞)

    def test_app_single_source_and_global(self):
        import app

        self.assertIs(app.read_frontend_version, static_assets.read_frontend_version)
        self.assertIs(app.purge_stale_static_gz, static_assets.purge_stale_static_gz)
        self.assertIs(app.ensure_user_profile_columns, columns.ensure_user_profile_columns)
        # 模块全局保留(外部 meta_aliases / admin_diagnostics 依赖)
        self.assertTrue(hasattr(app, "PEARNLY_FRONTEND_VERSION"))
        self.assertIsInstance(app.PEARNLY_FRONTEND_VERSION, str)

    def test_ensure_user_profile_columns_homed_in_columns(self):
        self.assertTrue(callable(columns.ensure_user_profile_columns))

    def test_dead_calc_trial_days_left_removed(self):
        import app

        self.assertFalse(
            hasattr(app, "_calc_trial_days_left"),
            "死码 _calc_trial_days_left 应已删除",
        )


if __name__ == "__main__":
    unittest.main()
