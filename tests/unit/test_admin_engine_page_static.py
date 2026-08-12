# -*- coding: utf-8 -*-
"""超管「OCR 引擎」页(/admin/engine)前端静态契约。

这页给老板定价用,三件事一旦悄悄坏掉就会得出错的价:
  ① 四个档位的参数必须逐档独立(自部署没实测过就得是「—」,不许拿别档数字顶上);
  ② 保存必须回传完整的 overrides_by_account —— 后端「缺键 = 保留现值」,少发这个键
     就删不掉灰度账号(routes/admin_ocr_engine_routes._clean_overrides_by_account);
  ③ 售价参考线钉 ฿1.5/页,成本表把每页成本单独摊开 —— 混合均值藏差价正是本页要拆穿的。
另钉 adm-* 两语(zh+th)键齐,和三个新模块都挂在 admin.html 上且带 ?v 指纹。
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
    def test_modules_loaded_with_cache_fingerprint(self):
        for name in MODULES:
            m = re.search(rf'src="/static/admin/{re.escape(name)}\?v=(\d+)"', HTML)
            self.assertIsNotNone(m, f"{name} 没挂在 admin.html 上(或漏了 ?v 指纹)")

    def test_modules_load_before_admin_js(self):
        # admin.js 只是调用方:三个模块必须先注册好 window.AdminEngine*,顺序靠 defer 保序。
        for name in MODULES:
            self.assertLess(
                HTML.index(name), HTML.index("admin.js?v="), f"{name} 必须排在 admin.js 前面"
            )

    def test_admin_js_only_delegates(self):
        self.assertIn("window.AdminEngine.render(", ADMIN_JS)
        # 旧 KPI 五卡与「模型请求页数成本」表整区已删,壳里不许再留挂载点。
        for dead in ("adm-eng-kpis", "adm-eng-by-model", "adm-eng-mode-hint"):
            self.assertNotIn(dead, HTML, f"admin.html 仍留着已删区的 {dead}")
            self.assertNotIn(dead, ADMIN_JS, f"admin.js 仍在渲染已删区的 {dead}")

    def test_page_hosts_exist(self):
        for host in (
            "adm-eng-policy-body",
            "adm-eng-accounts",
            "adm-eng-days",
            "adm-eng-cost-body",
        ):
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


class SaveContractTests(unittest.TestCase):
    def test_save_always_sends_full_account_overrides(self):
        # 后端缺键 = 保留现值,所以删一行只能靠回传完整对象来表达。
        self.assertIn("overrides_by_account: {}", ENGINE_JS)
        self.assertRegex(ENGINE_JS, r"body\.overrides_by_account\[email\] = accounts\[i\]\.mode")

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
        self.assertNotRegex(CHARTS_JS, r"#[0-9a-fA-F]{6}\b")
        self.assertIn("--viz-over", CHARTS_JS)
        self.assertIn("--viz-under", CHARTS_JS)

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
