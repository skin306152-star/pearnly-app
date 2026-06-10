# -*- coding: utf-8 -*-
"""
REFACTOR-C1 守门测试 · 测试中心(Test Center)从 home.js 抽到 src/home/test-center.js。

home.js 是巨石 · 无法 jsdom 单测 · 用静态文本契约锁定抽迁(防回归 / 防重复):
  1. src/home/test-center.js 存在 · 定义入口 window.loadTestCenterPage(+ _tcOnNewLog/_tcApplyVisibility)
  2. src/main.js 通过 side-effect import 引入了 test-center.js(否则 bundle 不含它 → 入口丢失)
  3. home.js 不再 *定义* 测试中心 IIFE(window.loadTestCenterPage = 已删)· 但仍保留 *调用方*
     (路由 window.loadTestCenterPage() + 错误拦截器 window._tcOnNewLog())· 防重复定义双跑
  4. home.html 仍在 home.js 之后加载 main.js bundle(加载序约束 · test-center 依赖 home.js 全局)

8 硬门槛 #4:每拆一个模块必带守门测试。
"""

import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestCenterExtractionStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # REFACTOR-C1-home-batch9g2 · home.js 巨石已彻底删除 · 读取改可选(残留断言对空串恒真)
        _home = os.path.join(ROOT, "home.js")
        cls.home_js = open(_home, "r", encoding="utf-8").read() if os.path.exists(_home) else ""
        with open(os.path.join(ROOT, "src", "main.js"), "r", encoding="utf-8") as f:
            cls.main_js = f.read()
        # REFACTOR-C1-home-batch9f · 真核心簇(含 routeTo 路由分发)已 cutover 到 core-boot.js
        # C5 迁 TS:src/home 模块现为 .ts(import 路径仍写 .js · Vite 解析 .js→.ts)
        with open(os.path.join(ROOT, "src", "home", "core-boot.ts"), "r", encoding="utf-8") as f:
            cls.core_boot_js = f.read()
        # REFACTOR-C1-home-batch9g2 · 错误拦截器(含 _tcOnNewLog 钩子)已搬到 src/home/state.ts
        with open(os.path.join(ROOT, "src", "home", "state.ts"), "r", encoding="utf-8") as f:
            cls.state_js = f.read()
        with open(os.path.join(ROOT, "src", "home", "test-center.ts"), "r", encoding="utf-8") as f:
            cls.tc_js = f.read()
        with open(os.path.join(ROOT, "home.html"), "r", encoding="utf-8") as f:
            cls.home_html = f.read()

    def test_module_defines_entry(self):
        """新模块定义测试中心入口 + 跨文件 window 钩子"""
        self.assertIn("window.loadTestCenterPage", self.tc_js)
        self.assertIn("window._tcOnNewLog", self.tc_js)
        self.assertIn("window._tcApplyVisibility", self.tc_js)

    def test_main_imports_test_center(self):
        """src/main.js side-effect import test-center.js · 否则 Vite bundle 不含它"""
        self.assertIn("./home/test-center.js", self.main_js)

    def test_home_js_no_longer_defines_test_center(self):
        """home.js 不再 *定义* 测试中心(防与 bundle 重复定义双跑)。
        注意:不能用裸 'window.loadTestCenterPage =' 判 · 它是 'window.loadTestCenterPage ===' 的前缀
        (路由 L832 typeof 检查)· 必须判定义形态 '= function' / '= async'。"""
        self.assertNotIn("window.loadTestCenterPage = function", self.home_js)
        self.assertNotIn("window.loadTestCenterPage = async", self.home_js)
        self.assertNotIn("window._tcApplyVisibility = ", self.home_js)
        # 定义形态(= function)只应出现在新模块里
        self.assertIn("window.loadTestCenterPage = function", self.tc_js)
        # 中文标题注释也应随 IIFE 移走(只在新模块里)
        self.assertNotIn("测试中心(Test Center · TC)", self.home_js)
        self.assertIn("测试中心(Test Center · TC)", self.tc_js)

    def test_home_js_keeps_callers(self):
        """调用方(路由分发 + 错误拦截器钩子)仍存在 · 经 window 调新模块入口。
        REFACTOR-C1-home-batch9f:routeTo 路由分发 → core-boot.js。
        2026-06-08:routeTo 改用 ROUTE_LOADERS 映射 + 动态 winFns[loader]() 分发(不再逐个 window.loadXxx() 字面量)·
        改为验 test-center 仍在映射表里接上其 loader。
        REFACTOR-C1-home-batch9g2:错误拦截器 IIFE(含 _tcOnNewLog 钩子)→ state.js · home.js 已删。
        2026-06-10:路由表抽到 route-table.ts(core-boot import 之)· 映射断言随迁。"""
        with open(os.path.join(ROOT, "src", "home", "route-table.ts"), "r", encoding="utf-8") as f:
            route_table = f.read()
        self.assertIn("'test-center': 'loadTestCenterPage'", route_table)
        self.assertIn("./route-table.js", self.core_boot_js)
        self.assertIn("window._tcOnNewLog(", self.state_js)

    def test_home_html_load_order(self):
        """REFACTOR-C1-home-batch9g2 · home.js 已删 · 新加载序约束:
        i18n-data.js(sync · 提供 window.I18N)必须先于 main.js bundle(state.js 第1个 import 裸读 I18N)。
        且 home.html 不再引用 home.js。"""
        self.assertNotIn(
            "/static/home.js?v=", self.home_html, "home.js 巨石应已删除 · 不再被 home.html 引用"
        )
        idx_i18n = self.home_html.find("/static/i18n-data.js?v=")
        idx_bundle = self.home_html.find("/static/dist/main.js?v=")
        self.assertGreater(idx_i18n, 0, "i18n-data.js script 标签缺失")
        self.assertGreater(idx_bundle, 0, "main.js bundle script 标签缺失")
        self.assertLess(idx_i18n, idx_bundle, "i18n-data.js 必须排在 main.js bundle 之前")


if __name__ == "__main__":
    unittest.main()
