# -*- coding: utf-8 -*-
"""业态预设守门测试(平台业态套餐 · docs/platform-onboarding/02)。

锁定:
  1. 6 canonical 业态都有预设 · 每个都含 sales · 只用 KNOWN_MODULES 里的 key
  2. apply_preset:翻全部 7 模块(预设内=开 / 外=关)· 记录 business_type · 不动 config
  3. 未知 business_type 抛 ValueError(路由翻 platform.unknown_business_type)
"""

import unittest

from services.modules import presets, store


class FakeCursor:
    """记录 set_module / set_business_type 的调用,模拟 RETURNING。"""

    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        # set_module 的 RETURNING:回一个合法行(enabled 由最后一次 params 推不出,给占位)
        return {"module_key": "x", "enabled": True, "config": {}}

    def fetchall(self):
        return []


class PresetTableTests(unittest.TestCase):
    def test_six_canonical_business_types_plus_pos_only(self):
        self.assertEqual(
            set(presets.BUSINESS_PRESETS.keys()),
            {"firm", "retail", "pharmacy", "restaurant", "service", "b2b", "pos_only"},
        )

    def test_every_preset_includes_sales_and_only_known_keys(self):
        for biz, keys in presets.BUSINESS_PRESETS.items():
            self.assertIn("sales", keys, f"{biz} 必含 sales(平台主线)")
            for k in keys:
                self.assertIn(k, store.KNOWN_MODULES, f"{biz} 用了非法 module_key {k}")

    def test_is_known(self):
        self.assertTrue(presets.is_known("retail"))
        self.assertFalse(presets.is_known("casino"))

    def test_pos_only_opens_five_modules(self):
        # Zihao 2026-07-11 拍板:被邀请的 POS 商家开通即全功能可用(写死),不再有二道开关。
        # 五模块覆盖 POS 老板后台壳(nav-presets.ts POS_PRESET)暴露的全部功能;
        # knowledge/recon/receivable 不在壳内,仍不开。
        self.assertEqual(
            set(presets.BUSINESS_PRESETS["pos_only"]),
            {"pos", "inventory", "sales", "expense", "accounting"},
        )


class ApplyPresetTests(unittest.TestCase):
    def test_unknown_business_type_raises_before_db(self):
        cur = FakeCursor()
        with self.assertRaises(ValueError):
            presets.apply_preset(cur, tenant_id="t-1", business_type="casino")
        self.assertFalse(cur.calls, "未知业态必须在碰库前拒绝")

    def test_toggles_all_seven_modules_per_preset(self):
        cur = FakeCursor()
        presets.apply_preset(cur, tenant_id="t-1", business_type="firm")
        # 收集对每个 module 的 set_module enabled 入参(INSERT INTO tenant_modules ... enabled)
        toggled = {}
        for sql, params in cur.calls:
            if "INSERT INTO tenant_modules" in sql and params and len(params) >= 3:
                # set_module(config=None) 形态:params = (tenant, module_key, enabled)
                if params[1] in store.KNOWN_MODULES:
                    toggled[params[1]] = params[2]
        # firm 预设:sales/expense/recon/knowledge 开;inventory/pos/receivable 关
        self.assertEqual(toggled["sales"], True)
        self.assertEqual(toggled["expense"], True)
        self.assertEqual(toggled["recon"], True)
        self.assertEqual(toggled["knowledge"], True)
        self.assertEqual(toggled["inventory"], False)
        self.assertEqual(toggled["pos"], False)
        self.assertEqual(toggled["receivable"], False)
        # 覆盖了全部 7 个
        self.assertEqual(set(toggled.keys()), set(store.KNOWN_MODULES))

    def test_records_business_type_sentinel(self):
        cur = FakeCursor()
        presets.apply_preset(cur, tenant_id="t-1", business_type="retail")
        sentinel_writes = [
            params
            for sql, params in cur.calls
            if params and store._BUSINESS_TYPE_KEY in (params or ())
        ]
        self.assertTrue(sentinel_writes, "apply_preset 必须记录 business_type 哨兵行")

    def test_clears_needs_onboarding_flag(self):
        # onboarding 完成 → 清「待选业态」哨兵行(值置 False),前端不再自动弹
        cur = FakeCursor()
        presets.apply_preset(cur, tenant_id="t-1", business_type="retail")
        cleared = [
            params
            for sql, params in cur.calls
            if params and store._NEEDS_ONBOARDING_KEY in (params or ())
        ]
        self.assertTrue(cleared, "apply_preset 必须清 needs_onboarding 哨兵行")
        # 写入的值是 {"value": false}(置 False)
        import json as _json

        self.assertEqual(cleared[-1][-1], _json.dumps({"value": False}))

    def test_config_not_touched(self):
        # set_module(config=None) → 走只翻 enabled 的 SQL 分支(无 %s::jsonb)
        cur = FakeCursor()
        presets.apply_preset(cur, tenant_id="t-1", business_type="retail")
        module_writes = [
            sql
            for sql, params in cur.calls
            if "INSERT INTO tenant_modules" in sql and params and params[1] in store.KNOWN_MODULES
        ]
        for sql in module_writes:
            self.assertNotIn("config = EXCLUDED.config", sql, "apply_preset 不该改 config")


if __name__ == "__main__":
    unittest.main()
