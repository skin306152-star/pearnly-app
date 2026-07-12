# -*- coding: utf-8 -*-
"""入口定壳(pearnly_entry)防回潮钉(Zihao 2026-07-12 拍板)。

背景:/login 与 /pos 登录成功都落 /home,壳过去只按租户 business_type 标签决定
(module-nav.ts)、退出分流(login-url.ts)也读同一标签——入口和所见完全脱钩,
mrerp 撞车(从 /pos 登录却看见会计壳)。修复:登录成功时写入口记号
localStorage['pearnly_entry']='pos'|'main',module-nav/login-url 优先读它;
无记号的老会话才回落原 business_type 判据(行为零变化)。

这份测试是源文件级"读文件断言"钉子,不跑浏览器,只锁四个源头不被静默削掉:
①module-nav.ts 读 pearnly_entry + pos 模块护栏 ②login-url.ts entry 优先判据
③pos-login.html 写 'pos' 记号 ④主站登录源(landing.js)写 'main' 记号。
"""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (PROJECT_ROOT / rel).read_text(encoding="utf-8")


class ModuleNavEntryRoutingTests(unittest.TestCase):
    def test_reads_pearnly_entry_from_localstorage(self):
        text = _read("src/home/module-nav.ts")
        self.assertIn("localStorage.getItem('pearnly_entry')", text)
        self.assertIn("window._entry", text)

    def test_pos_entry_guarded_by_pos_module_enabled(self):
        # entry='pos' 没开 pos 模块要忽略入口回落,不能无条件给 POS 壳。
        text = _read("src/home/module-nav.ts")
        self.assertIn("window._entry || '') === 'pos'", text)
        self.assertIn("posEnabled", text)

    def test_no_dedicated_main_entry_branch(self):
        # /simplify 2026-07-13 收口:entry='main' 曾有专属分支,证实与 businessType 三段
        # ternary(original)恒同值(纯冗余,两条分支返回值逐场景相等)→ 已删。resolvePreset
        # 只应对 'pos' 特判,'main'/无 entry 一律走 original 回落——这条钉子防它又被加回来。
        text = _read("src/home/module-nav.ts")
        self.assertNotIn("entry === 'main'", text)

    def test_no_entry_falls_back_to_business_type_unchanged(self):
        # 无 entry(老会话)完全回落 business_type 判据,行为零变化。
        text = _read("src/home/module-nav.ts")
        self.assertIn("无 entry", text)


class LoginUrlEntryPriorityTests(unittest.TestCase):
    def test_entry_checked_before_business_type_fallback(self):
        text = _read("src/home/login-url.ts")
        entry_pos_idx = text.find("window._entry === 'pos'")
        entry_main_idx = text.find("window._entry === 'main'")
        fallback_idx = text.find("_businessType === 'pos_only'")
        self.assertGreater(entry_pos_idx, -1, "loginUrl 没读 window._entry==='pos'")
        self.assertGreater(entry_main_idx, -1, "loginUrl 没读 window._entry==='main'")
        self.assertGreater(fallback_idx, -1, "loginUrl 丢了业态回落判据")
        self.assertLess(entry_pos_idx, fallback_idx, "entry 判据必须先于业态回落判据")
        self.assertLess(entry_main_idx, fallback_idx, "entry 判据必须先于业态回落判据")


class LoginEntryPointsWriteEntryMarkTests(unittest.TestCase):
    def test_pos_login_page_writes_pos_entry_mark(self):
        text = _read("static/pos/pos-login.html")
        self.assertIn("localStorage.setItem('pearnly_entry', 'pos')", text)

    def test_main_site_login_writes_main_entry_mark(self):
        text = _read("static/landing/landing.js")
        self.assertIn("localStorage.setItem('pearnly_entry', 'main')", text)


class GlobalsDeclareEntryTests(unittest.TestCase):
    def test_window_entry_declared(self):
        text = _read("src/types/globals.d.ts")
        self.assertIn("_entry?: string", text)


if __name__ == "__main__":
    unittest.main()
