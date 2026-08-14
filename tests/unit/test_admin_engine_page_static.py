# -*- coding: utf-8 -*-
"""超管「OCR 引擎」页(/admin/engine)前端静态契约。

这页给老板定价用,三件事一旦悄悄坏掉就会得出错的价:
  ① 四个档位的参数必须逐档独立(自部署没实测过就得是「—」,不许拿别档数字顶上);
  ② 账号灰度 2026-08-13 整体退役 —— 编辑区/保存键 overrides_by_account 必须删干净,
     后端见键即 400,前端残留半截就是「保存永远失败」;
  ③ 售价参考线钉 ฿1.5/页,成本表把每页成本单独摊开 —— 混合均值藏差价正是本页要拆穿的。
另钉 adm-* 两语(zh+th)键齐,和三个新模块的按需注入接线(2026-08-12 起不再挂 admin.html,
admin.js 进引擎页签才动态注入,URL 的 ?v 运行时从 admin.js 自己的 ?v 抠)。
"""

import re
import unittest
from pathlib import Path

ADMIN_DIR = Path("static/admin")
HTML = (ADMIN_DIR / "admin.html").read_text(encoding="utf-8")
I18N = (ADMIN_DIR / "admin-i18n.js").read_text(encoding="utf-8")
ENGINE_JS = (ADMIN_DIR / "admin-engine.js").read_text(encoding="utf-8")
COST_JS = (ADMIN_DIR / "admin-engine-cost.js").read_text(encoding="utf-8")
CHARTS_JS = (ADMIN_DIR / "admin-engine-charts.js").read_text(encoding="utf-8")
ADMIN_JS = (ADMIN_DIR / "admin.js").read_text(encoding="utf-8")

TIERS = ("direct35", "economy", "qwen", "selfhost")
MODULES = ("admin-engine.js", "admin-engine-cost.js", "admin-engine-charts.js")


def _lang_block(lang: str) -> str:
    """取 window.ADMIN_I18N.<lang> 那一段(两语块首尾都由 `        <lang>: {` 界定)。"""
    start = I18N.index(f"        {lang}: {{")
    rest = I18N[start:]
    end = rest.index("\n        },")
    return rest[:end]


def _eng_keys(lang: str) -> set:
    return set(re.findall(r"'(adm-eng-[a-z0-9_.-]+)':", _lang_block(lang), flags=re.I))


class EnginePageWiringTests(unittest.TestCase):
    def test_modules_injected_lazily_from_admin_js(self):
        # 2026-08-12 收编:三支引擎模块(约 36KB)改按需注入 —— 不再写死在 admin.html,
        # 引用收进 admin.js 的 _ENGINE_SCRIPTS 清单,URL 的 ?v 运行时从 admin.js 自己的 ?v 抠
        # (七个管理页签只有引擎页用它们,挂 HTML 上让另外六页白背体积)。
        for name in MODULES:
            self.assertNotIn(
                f'src="/static/admin/{name}?v=', HTML, f"{name} 不该再静态挂在 admin.html 上"
            )
            self.assertIn(name, ADMIN_JS, f"{name} 不在 admin.js 的注入清单里")

    def test_admin_js_only_delegates(self):
        self.assertIn("window.AdminEngine.render(", ADMIN_JS)
        self.assertIn("_ensureEngineScripts()", ADMIN_JS)
        # 旧 KPI 五卡与「模型请求页数成本」表整区已删,壳里不许再留挂载点。
        for dead in ("adm-eng-kpis", "adm-eng-by-model", "adm-eng-mode-hint"):
            self.assertNotIn(dead, HTML, f"admin.html 仍留着已删区的 {dead}")
            self.assertNotIn(dead, ADMIN_JS, f"admin.js 仍在渲染已删区的 {dead}")

    def test_page_hosts_exist(self):
        for host in ("adm-eng-policy-body", "adm-eng-days", "adm-eng-cost-body"):
            self.assertIn(f'id="{host}"', HTML, f"缺 {host} 挂载点")


class TierCardTests(unittest.TestCase):
    def test_every_tier_has_its_own_four_facts(self):
        zh = _lang_block("zh")
        for mode in TIERS:
            for facet in ("name", "models", "cost", "quality", "speed", "note"):
                self.assertIn(f"'adm-eng-tier-{mode}-{facet}':", zh, f"{mode} 缺 {facet} 文案")

    def test_selfhost_metrics_are_honest_dashes(self):
        # 自部署没跑过金标 —— 成本/质量/速度三项必须是占位符,不许借别档数字。
        zh = _lang_block("zh")
        for facet in ("cost", "quality", "speed"):
            m = re.search(rf"'adm-eng-tier-selfhost-{facet}': '([^']*)'", zh)
            self.assertIsNotNone(m, f"selfhost {facet} 没定义")
            self.assertEqual("—", m.group(1), f"selfhost {facet} 应为占位符 —")

    def test_qwen_tier_is_selectable(self):
        self.assertIn("{ mode: 'qwen', code: 'C' }", ENGINE_JS)
        self.assertIn("'adm-eng-opt-qwen':", _lang_block("zh"))

    def test_all_backend_policy_tasks_are_selectable(self):
        for task in ("vat_report_csv", "salesvat", "fileconv_ocr"):
            self.assertIn(f"'{task}'", ENGINE_JS)
            self.assertIn(f"'adm-eng-task-{task}':", _lang_block("zh"))
            self.assertIn(f"'adm-eng-task-{task}':", _lang_block("th"))


class SaveContractTests(unittest.TestCase):
    def test_account_gray_release_fully_removed(self):
        # 账号灰度已退役:后端见 overrides_by_account 键即 400,前端残留半截
        # (编辑区没了但保存还发键)= 这页的保存从此永远失败。
        for surface, name in ((HTML, "admin.html"), (ENGINE_JS, "admin-engine.js")):
            self.assertNotIn("overrides_by_account", surface, f"{name} 残留灰度键")
            self.assertNotIn("adm-eng-acct", surface, f"{name} 残留灰度 UI")
            self.assertNotIn("eng-acct-", surface, f"{name} 残留灰度 UI 类名")
        self.assertNotIn("adm-eng-acct", I18N, "admin-i18n.js 残留灰度文案键")

    def test_save_blocked_before_policy_loaded(self):
        self.assertIn("if (!policy) return;", ENGINE_JS)

    def test_unknown_mode_survives_round_trip(self):
        # select 渲染不出后端存的档 → 一按保存就被当「跟全局」抹掉(银行钉档真丢过)。
        self.assertIn("if (current && opts.indexOf(current) === -1) opts.push(current);", ENGINE_JS)


class CostPanelTests(unittest.TestCase):
    def test_price_reference_line_comes_from_backend(self):
        # 售价参考线走后端单源(costs 响应 price_thb_per_page,源头 pricing.PDF_TIER1_PRICE_V21);
        # 前端只留缺字段时回落 1.5 的兜底,不再硬编「当前定价」。
        self.assertRegex(COST_JS, r"const PRICE_FALLBACK = 1\.5;")
        self.assertIn("cache.price_thb_per_page", COST_JS)
        self.assertIn("priceThb", COST_JS)

    def test_unknown_pages_never_become_zero_cost(self):
        # cost_per_page 为 null 的行:表里写 —,柱图里不画。写成 0 等于说它免费。
        self.assertIn("return r.cost_per_page != null;", COST_JS)
        self.assertIn("if (n == null) return '—';", COST_JS)

    def test_unattributed_row_is_kept_separate(self):
        self.assertIn("'adm-eng-unattributed'", COST_JS)
        self.assertIn("eng-row-muted", COST_JS)

    def test_four_states_all_present(self):
        for kind in ("loading", "empty", "error"):
            self.assertIn(f"_stateBox('{kind}'", COST_JS, f"成本区缺 {kind} 态")
        # 重试按钮渲染在共享 _stateBox(admin-engine.js 单一 owner),cost 侧以 'costs' 为 retry 值
        self.assertRegex(COST_JS, r"_stateBox\('error', _t\('adm-eng-cost-fail'\), 'costs'\)")
        self.assertIn('data-eng-retry="', ENGINE_JS)

    def test_day_range_switch(self):
        self.assertIn("const DAY_OPTIONS = [7, 30, 90];", COST_JS)


class ChartLayerTests(unittest.TestCase):
    def test_echarts_is_vendored_not_cdn(self):
        # CSP 是 script-src 'self':任何 CDN 域都会被浏览器拦掉。
        self.assertIn("'/static/vendor/echarts/echarts.common.min.js'", CHARTS_JS)
        self.assertNotIn("http", CHARTS_JS.split("ECHARTS_SRC")[1][:200])
        self.assertTrue(Path("static/vendor/echarts/echarts.common.min.js").exists())

    def test_colors_come_from_tokens(self):
        # 图表配色是 admin-viz.css 的令牌,JS 里不写死 hex(裸 hex 会顶穿 ui_design_lint 棘轮)。
        # 令牌读取单源在宿主 admin.js 的 _vizTheme(暴露为 AdminHost.vizTheme),图表层只委托
        # —— 别再回到两份 _theme 各抄一套回落色的年代。
        self.assertNotRegex(CHARTS_JS, r"#[0-9a-fA-F]{6}\b")
        self.assertIn("window.AdminHost.vizTheme()", CHARTS_JS)
        self.assertIn("window.AdminHost.loadScript(", CHARTS_JS)
        for token in ("--viz-over", "--viz-under", "--viz-other"):
            self.assertIn(token, ADMIN_JS, f"宿主 _vizTheme 缺 {token} 令牌")

    def test_lib_load_failure_surfaces(self):
        self.assertIn("adm-eng-chart-fail", COST_JS)


class AdminI18nParityTests(unittest.TestCase):
    def test_engine_keys_have_zh_and_th(self):
        zh, th = _eng_keys("zh"), _eng_keys("th")
        self.assertEqual(set(), zh - th, "以下键缺泰语")
        self.assertEqual(set(), th - zh, "以下键缺中文")
        self.assertGreater(len(zh), 60)

    def test_every_data_i18n_in_engine_section_is_defined(self):
        section = HTML[HTML.index('id="page-admin-engine"') : HTML.index('id="page-admin-agent"')]
        used = set(re.findall(r'data-i18n="([^"]+)"', section))
        zh = set(re.findall(r"'([a-z0-9-]+)':", _lang_block("zh"), flags=re.I))
        self.assertEqual(set(), used - zh, "页面用到但字典里没有的键")


if __name__ == "__main__":
    unittest.main()
