# -*- coding: utf-8 -*-
"""「平台业态自选板块」防回潮钉(Zihao 2026-07-11 拍板)。

背景:被邀请的 POS 商家开通即全功能可用(写死),不再有二道开关;同时下架老的
「按行业开通」自选板块——onboarding 业态卡片(PP2 window.openBusinessPicker)/
侧栏「可开启功能 →」(nav-enroll)/ 设置里的「切换业态」按钮全部物理删除,不再靠
display:none 藏起来(照 EN-9 receivables 先例:靠开关隐藏的 UI 会借尸还魂)。

apply_preset / presets.py 保留(Earn 建号仍用它写死开通;注册流默认静默套用 firm)。
needs_onboarding 标记 / 引导闭环向导(主体→账务→选套账)也保留——它服务的不只是
业态选择,新租户仍要建主体+选套账。
"""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (PROJECT_ROOT / rel).read_text(encoding="utf-8")


class BusinessPickerFileRemovedTests(unittest.TestCase):
    def test_onboarding_business_ts_deleted(self):
        self.assertFalse(
            (PROJECT_ROOT / "src/home/onboarding-business.ts").exists(),
            "onboarding-business.ts(PP2 业态选择器弹窗)又诈尸了",
        )

    def test_main_js_no_longer_imports_it(self):
        text = _read("src/main.js")
        self.assertNotIn("onboarding-business", text)


class BusinessPickerEntryPointsRemovedTests(unittest.TestCase):
    """三个入口(首登弹窗业态卡 / 侧栏可开启功能 / 设置切换业态)全砍。"""

    def test_sidebar_has_no_nav_enroll(self):
        text = _read("src/home/app-shell-sidebar-html.ts")
        self.assertNotIn("nav-enroll", text)

    def test_module_nav_no_longer_shows_enroll_or_falls_back_to_picker(self):
        text = _read("src/home/module-nav.ts")
        self.assertNotIn("nav-enroll", text)
        self.assertNotIn("openBusinessPicker", text)

    def test_nav_presets_no_longer_maps_enroll(self):
        text = _read("src/home/nav-presets.ts")
        self.assertNotIn("nav-enroll", text)

    def test_settings_switch_business_button_removed(self):
        text = _read("src/home/module-settings.ts")
        self.assertNotIn("openBusinessPicker", text)
        self.assertNotIn("modset-switch", text)
        self.assertNotIn("curBiz", text)

    def test_onboarding_flow_no_longer_has_business_type_step(self):
        text = _read("src/home/onboarding-flow.ts")
        self.assertNotIn("onboarding-business", text)
        self.assertNotIn("TYPES", text)
        self.assertNotIn("biz-pick", text)
        # 向导起步默认静默套 firm 预设,不再问用户选业态。
        self.assertIn("applyFirmPresetSilently", text)
        self.assertIn("business_type: 'firm'", text)

    def test_globals_dts_no_longer_declares_open_business_picker(self):
        text = _read("src/types/globals.d.ts")
        self.assertNotIn("openBusinessPicker", text)


class ApplyPresetStillAliveForOperationsTests(unittest.TestCase):
    """apply_preset/needs_onboarding 不能被连坐删掉:Earn 开通 + 注册流默认 firm 仍要用。"""

    def test_apply_preset_function_still_exists(self):
        from services.modules import presets

        self.assertTrue(callable(presets.apply_preset))
        self.assertTrue(presets.is_known("firm"))
        self.assertTrue(presets.is_known("pos_only"))

    def test_signup_still_flags_needs_onboarding(self):
        text = _read("services/auth/signup_core.py")
        self.assertIn("set_needs_onboarding", text)


class OrphanedI18nKeysDeletedTests(unittest.TestCase):
    """业态卡片专属文案(四语)必须清干净;仍被复用的 key(如 mod.sales/biz.firm)不能误删。"""

    ORPHANED_KEYS = (
        "onb.preset_suffix",
        "onb.will_open",
        "onb.title",
        "onb.sub",
        "onb.enter",
        "onb.owner_only",
        "onb.done",
        "onb.base",  # 精确匹配收尾引号(见下方 needle),不撞 onb.base_tag 前缀
        "onb.biz_mods",
        "onb.tag_on",
        "mod.product",
        "mod.client",
        "mod.workbench",
        "mod.ai",
        "onbf-step-biz",
        "onbf-biz-title",
        "onbf-biz-sub",
        "onbf-back",
        "biz.firm.desc",
        "biz.retail.desc",
        "biz.pharmacy.desc",
        "biz.restaurant.desc",
        "biz.service.desc",
        "biz.b2b.desc",
        "set.switch_biz",
    )

    def test_i18n_data_has_no_orphaned_keys(self):
        text = _read("static/i18n-data.js")
        for key in self.ORPHANED_KEYS:
            needle = "'" + key + "':"  # 精确带收尾引号+冒号,防止子串误撞更长的 key
            self.assertNotIn(needle, text, msg=f"i18n 键 {key} 又诈尸了")

    def test_still_used_keys_survive(self):
        # 这些 key 被 module-settings.ts(个别模块开关面板)等仍在用的功能复用,不该被连坐删掉。
        text = _read("static/i18n-data.js")
        for key in (
            "mod.sales",
            "mod.inventory",
            "mod.pos",
            "mod.expense",
            "mod.recon",
            "mod.receivable",
            "mod.knowledge",
            "onb.base_tag",
            "onb.tag_off",
            "biz.firm",
            "set.cur_biz",
            "set.biz_none",
        ):
            needle = "'" + key + "':"
            self.assertIn(needle, text, msg=f"i18n 键 {key} 被误删了")


if __name__ == "__main__":
    unittest.main()
