# -*- coding: utf-8 -*-
"""异常栏下线防回潮钉(Zihao 2026-07-26 拍板:用下来毫无用处,连带全掐)。

下线不是删码:页面模块 / /api/exceptions 路由 / 历史数据全留着,靠「入口恒隐 + 路由摘表
+ 引擎开关默认关」三层断电,复活按 src/home/route-table.ts 的下线注释走。本钉盯的是
断电三层别被下一次改动悄悄接回去,以及别把该活着的东西连坐砍了(集成页「推送异常」tab、
客户知识页「管理客户规矩」入口——它俩跟异常栏是两回事,后者原先只是把按钮寄生在异常页头部)。

E2E 侧的对应闸在 tests/e2e/05-exceptions.spec.js(真浏览器验侧栏/深链/命令面板),
CI 无凭据时那条会跳过,故这里用源码级断言兜底。

断言一律走 assertTrue/assertFalse 而非 assertIn/assertNotIn:后者失败时会把整份源文件
打进报错里(几万字),CI 日志根本没法看。
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (PROJECT_ROOT / rel).read_text(encoding="utf-8")


class FrontendEntryCutTests(unittest.TestCase):
    """前端三层断电:路由表摘除 / 侧栏恒隐 / 命令面板无项。"""

    def test_route_table_drops_exceptions(self):
        text = _read("src/home/route-table.ts")
        self.assertFalse("'exceptions'," in text, "exceptions 又被加回路由清单了")
        self.assertFalse(
            "exceptions: 'loadExceptionsPage'" in text, "exceptions 又被加回 ROUTE_LOADERS 了"
        )

    def test_sidebar_item_is_hidden(self):
        text = _read("src/home/app-shell-sidebar-html.ts")
        self.assertTrue(
            '<div class="nav-item nav-sub-item" data-route="exceptions" style="display:none;">'
            in text,
            "侧栏异常栏入口的内联 display:none 没了(菜单会重新露出来)",
        )

    def test_nav_preset_no_longer_manages_exceptions(self):
        # 留在 NAV_NODES 会被 applyNavPreset 的 show(el, true) 打开,等于绕过内联 display:none。
        text = _read("src/home/nav-presets.ts")
        self.assertFalse("exceptions: '.nav-item" in text, "exceptions 又回到 NAV_NODES 了")
        self.assertFalse("'exceptions'," in text, "exceptions 又回到某个 preset 白名单了")

    def test_cmdk_module_removed(self):
        # 2026-08-26 · 顶栏搜索框 / Cmd+K 命令面板整体下线(需求批 B4):cmdk 模板模块已删、
        # main.js 不再 import、home.html 无 #cmdk-mask 空壳。命令面板里的异常栏项无从残留。
        self.assertFalse(
            (PROJECT_ROOT / "src/home/cmdk-mask-html.ts").exists(),
            "cmdk 模板模块应已删除",
        )
        text = _read("src/main.js")
        self.assertFalse("cmdk-mask-html" in text, "main.js 不再 import cmdk 模板")
        home = _read("home.html")
        self.assertFalse("cmdk-mask" in home, "home.html 不应再有精命令面板空壳")

    def test_no_stray_route_jumps(self):
        # 推送日志详情里那个 routeTo('exceptions') 分支(本就无按钮触发)已删。
        text = _read("src/home/erp-log-detail.ts")
        self.assertFalse("routeTo('exceptions')" in text, "又有地方往异常栏跳了")

    def test_badge_polling_stopped(self):
        # 入口恒隐后再每 60 秒轮询 /api/exceptions/stats 就是纯白打。
        text = _read("src/home/exceptions.ts")
        self.assertFalse("setInterval(refreshExcBadge" in text, "红点轮询又开起来了")
        self.assertFalse("setTimeout(refreshExcBadge" in text, "红点首刷又开起来了")


class BackendEngineOffTests(unittest.TestCase):
    """引擎默认不跑:不写 exceptions 表。"""

    def test_engine_disabled_without_env(self):
        from services.exceptions import exception_checks

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("EXCEPTIONS_ENGINE", None)
            self.assertFalse(exception_checks._engine_enabled())

    def test_engine_opt_in_by_env(self):
        from services.exceptions import exception_checks

        with patch.dict(os.environ, {"EXCEPTIONS_ENGINE": "1"}):
            self.assertTrue(exception_checks._engine_enabled())

    def test_hook_guards_before_any_work(self):
        # 早退必须在函数体最前面(晚一步就已经查过白名单/写过表了)。
        body = _read("services/exceptions/exception_checks.py").split(
            "async def _async_run_exception_checks", 1
        )[1]
        self.assertTrue("if not _engine_enabled():" in body, "钩子里的开关早退没了")
        guard_at = body.index("if not _engine_enabled():")
        self.assertLess(guard_at, body.index("db.insert_exception"), "早退晚于写异常表")


class NotCollateralDamageTests(unittest.TestCase):
    """下线只砍异常栏本身:这几样必须还活着。"""

    def test_exceptions_api_and_page_code_kept(self):
        # 下线≠删码:留着才能一键复活。
        self.assertTrue((PROJECT_ROOT / "routes/exceptions_routes.py").exists())
        self.assertTrue((PROJECT_ROOT / "src/home/exceptions.ts").exists())

    def test_client_rules_entry_lives_on_knowledge_page(self):
        # 「管理客户规矩」原先把按钮注入异常页头部,现在只认客户知识页「规则」tab 这一处。
        self.assertTrue("kb-open-rules" in _read("src/home/page-knowledge.ts"))
        self.assertTrue("openRulesSettings" in _read("src/home/knowledge-center.ts"))
        rules = _read("src/home/rules-settings.ts")
        self.assertTrue("window.openRulesSettings" in rules)
        self.assertFalse("page-exceptions" in rules, "规矩设置又去寄生异常页了")

    def test_erp_push_exception_tab_untouched(self):
        # 集成页的「推送异常」(ERP 推送失败修复)跟异常栏是两码事,不在下线范围。
        self.assertTrue((PROJECT_ROOT / "src/home/erp-exc-actions.ts").exists())


class GuideChapterRemovedTests(unittest.TestCase):
    """教程里讲异常栏的那一章连配图一起撤掉(教用户点一个看不见的页面 = 误导)。"""

    def test_chapter_and_shots_gone(self):
        stuck = _read("static/guide/content/stuck.json")
        self.assertFalse("exc-exceptions-page" in stuck, "教程里讲异常栏的那章又回来了")
        for lang in ("zh", "th"):
            shot = PROJECT_ROOT / f"static/guide/shots/stuck-03-exceptions.{lang}.png"
            self.assertFalse(shot.exists(), f"{shot.name} 又回来了")
        self.assertFalse("stuck-03-exceptions" in _read("scripts/_guide_shots_list.cjs"))

    def test_planned_count_followed_the_deletion(self):
        """删章要同步 index.json 的 planned:手册首页显示 done/planned,还会按差值渲染
        一条「即将推出」占位 —— 少减一下,这篇就永远像缺一章没写完。"""
        index = json.loads(_read("static/guide/content/index.json"))
        stuck_planned = next(s for s in index["sections"] if s["id"] == "stuck")["planned"]
        actual = len(json.loads(_read("static/guide/content/stuck.json"))["chapters"])
        self.assertEqual(stuck_planned, actual, "stuck 篇 planned 与实际章数对不上")


if __name__ == "__main__":
    unittest.main()
