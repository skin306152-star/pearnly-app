# -*- coding: utf-8 -*-
"""入口定壳(pearnly_entry)防回潮钉(Zihao 2026-07-12 拍板 · 2026-08-26 主控架构定版)。

背景:/login 与 /pos 登录成功都落 /home,壳过去只按租户 business_type 标签决定
(module-nav.ts)、退出分流(login-url.ts)也读同一标签——入口和所见完全脱钩,
mrerp 撞车(从 /pos 登录却看见会计壳)。修复:登录成功时写入口记号
localStorage['pearnly_entry']='pos'|'main',module-nav/login-url 优先读它;
无记号的老会话才回落原 business_type 判据(行为零变化)。

★ 2026-07-16 升级(各是各的):壳的权威 entry 改由后端按 token.entry 经 /api/me/modules
下发(module-nav apply 收 data.entry),localStorage['pearnly_entry'] 降级为纯 pre-auth 提示
(登录页选择用,登出即清)。串壳根治:功能跟着 token 走,不跟浏览器猜。preboot/loginUrl 仍
读提示选登录页(pre-auth 无 token 的先天矛盾,读不到 token.entry 只能靠持久提示)——不变。

★ 2026-08-26 主控架构定版(/cowork canonical 主壳 + /erp 专属登录门):
  · /cowork 完全复用主站登录 UI(serve static/dist/login.html · 未登录直接呈现,浏览器地址
    就是 /cowork,不再跳 /login?entry=)。
  · /erp 是独立 ERP 专属登录门(serve static/dist/erp.html · erp_portal 邀请制),不复用
    主站 login.html(按 /ai /dms /pos 独立入口范式各自成门)。
  · /login 服务端 302 → /cowork(默认;仅同源内部绝对 next 放行)· OAuth 失败回跳沿用旧行为(不新增展示层)。
  · landing.js(按 pathname 定入口;已有 token → 按 token entry/local entry 校正壳(层1),
    jump 内部 /home?canonical=;home.html 最早 preboot 读 canonical 并把可见 pathname
    归一为 /cowork|/erp 后继续 home app)。erp.html 头部 boot 同款层1 串壳校正。
  · login-url.ts 退出/401 回 /cowork|/erp,绝不露 /login?entry。
  · module-nav 按 /api/me/modules 的 data.entry 再校正一层(层2 · 权威)。

这份测试是源文件级"读文件断言"钉子,不跑浏览器,锁这些源头不被静默削掉。
"""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (PROJECT_ROOT / rel).read_text(encoding="utf-8")


class LandingEntryRoutingTests(unittest.TestCase):
    """2026-08-26 · landing.js：入口由 pathname 决定 + 存量 token 校正壳(层1)。"""

    def test_entry_derived_from_pathname(self):
        text = _read("static/landing/landing.js")
        self.assertIn("location.pathname === '/erp' ? 'erp' : 'cowork'", text)

    def test_existing_token_redirects_to_internal_canonical(self):
        # 已有 token → jump 内部 /home?canonical=,不再渲染登录页(读入口槽 + legacy 迁移收养)。
        text = _read("static/landing/landing.js")
        self.assertIn("readSlotToken", text)
        self.assertIn("legacyMigratable", text)
        self.assertIn("'/home?canonical=' + _pathEntry", text)

    def test_canonical_for_maps_erp_else_cowork(self):
        text = _read("static/landing/landing.js")
        self.assertIn("canonicalAfterLogin(entry, isSuperAdmin)", text)
        self.assertIn("entry === 'erp' ? 'erp' : 'cowork'", text)

    def test_canoniical_after_login_defaults_cowork(self):
        # 登录成功落 /home?canonical=cowork(erp 落 /home?canonical=erp;超管 /admin/cost)。
        text = _read("static/landing/landing.js")
        self.assertIn("canonicalAfterLogin", text)
        self.assertIn("return '/admin/cost'", text)
        self.assertIn("'/home?canonical=' + (entry === 'erp' ? 'erp' : 'cowork')", text)

    def test_signup_lands_on_cowork_canonical(self):
        text = _read("static/landing/landing.js")
        self.assertIn("'/home?canonical=' + _entry", text)

    def test_login_writes_entry_from_pathname(self):
        text = _read("static/landing/landing.js")
        self.assertIn("localStorage.setItem('pearnly_entry', _entry)", text)
        self.assertIn("pearnly_entry", text)

    def test_no_oauth_error_new_ui_or_copy(self):
        # 2026-08-27 · 严格复用旧 cowork 登录:本批多带的 OAuth 错误新 UI(surfaceOAuthError)与
        # signinFailed 新文案已删(/login 302 透传 OAuth 失败提示属旧行为,不新增展示层)。
        text = _read("static/landing/landing.js")
        self.assertNotIn("surfaceOAuthError", text)
        self.assertNotIn("signinFailed", text)
        dict_text = _read("static/landing/landing-i18n.js")
        self.assertNotIn("signinFailed", dict_text)


class HomePrebootCanonicalTests(unittest.TestCase):
    """2026-08-26 · home.html 最早 preboot 读 canonical 并归一可见 pathname。"""

    def test_preboot_reads_canonical(self):
        text = _read("home.html")
        self.assertIn("canonical=(cowork|erp)", text)

    def test_preboot_normalizes_pathname_via_replace_state(self):
        text = _read("home.html")
        self.assertIn("history.replaceState", text)
        self.assertIn("location.pathname==='/home'", text)

    def test_preboot_sets_pearnly_entry(self):
        text = _read("home.html")
        self.assertIn("localStorage.setItem('pearnly_entry',_slot)", text)

    def test_preboot_gate_never_uses_login_entry_query(self):
        # 门(零 token)落 canonical 主壳,绝不露 /login?entry=。槽由 pathname/canonical 决定。
        text = _read("home.html")
        self.assertNotIn("'/login?entry", text)
        self.assertIn("location.replace(_slot==='pos'?'/pos'", text)
        self.assertIn("_slot==='erp'?'/erp':'/cowork'", text)

    def test_preboot_defaults_to_cowork(self):
        text = _read("home.html")
        self.assertIn("_slot==='erp'?'/erp':'/cowork'", text)


class LoginUrlEntryPriorityTests(unittest.TestCase):
    def test_entry_checked_before_business_type_fallback(self):
        # 2026-08-27 入口级会话隔离:入口优先 session.entry()(pathname/canonical),再回落 window._entry,
        # 业态标签只作最后兜底。
        text = _read("src/home/login-url.ts")
        entry_pos_idx = text.find("entry === 'pos'")
        fallback_idx = text.find("_businessType === 'pos_only'")
        self.assertGreater(entry_pos_idx, -1, "loginUrl 没读 entry==='pos'")
        self.assertGreater(fallback_idx, -1, "loginUrl 丢了业态回落判据")
        self.assertLess(entry_pos_idx, fallback_idx, "entry 判据必须先于业态回落判据")

    def test_cold_boot_seeds_entry_from_localstorage(self):
        text = _read("src/home/login-url.ts")
        self.assertIn("window.session.entry()", text)
        self.assertIn("window._entry", text)

    def test_dms_entry_routes_to_dms(self):
        text = _read("src/home/login-url.ts")
        dms_idx = text.find("entry === 'dms'")
        fallback_idx = text.find("_businessType === 'pos_only'")
        self.assertGreater(dms_idx, -1, "loginUrl 没读 entry==='dms'")
        self.assertLess(dms_idx, fallback_idx, "dms 判据必须先于业态回落判据")

    def test_cowork_main_return_cowork_not_login(self):
        # 2026-08-26 主控:退出/401 回 /cowork|/erp,绝不露 /login?entry=。
        text = _read("src/home/login-url.ts")
        self.assertNotIn("return '/login?entry", text)
        self.assertIn("entry === 'cowork') return '/cowork'", text)
        self.assertIn("entry === 'main') return '/cowork'", text)

    def test_erp_entry_returns_erp(self):
        text = _read("src/home/login-url.ts")
        self.assertIn("entry === 'erp') return '/erp'", text)


class LoginEntryPointsWriteEntryMarkTests(unittest.TestCase):
    def test_pos_login_page_writes_pos_entry_mark(self):
        text = _read("static/pos/pos-login.html")
        self.assertIn("localStorage.setItem('pearnly_entry', 'pos')", text)

    def test_main_site_login_reads_pathname_entry(self):
        # 2026-08-26 · 主站登录页落地 canonical 主壳:登录入口(entry)由 pathname 决定,
        # 不再读 /login?entry=。
        text = _read("static/landing/landing.js")
        self.assertNotIn("URLSearchParams(window.location.search).get('entry')", text)
        self.assertIn("localStorage.setItem('pearnly_entry', _entry)", text)
        self.assertIn("canonicalAfterLogin", text)


class RouteToEntryGuardTests(unittest.TestCase):
    """Phase3 各是各的 · core-boot.ts:routeTo 跨壳深链回落当前入口首页(纯 UX 守卫)。"""

    def test_route_to_applies_entry_guard(self):
        text = _read("src/home/core-boot.ts")
        self.assertIn("_entryGuardRoute", text)
        self.assertIn("route = _entryGuardRoute(route)", text)

    def test_route_table_declares_entry_route_sets(self):
        text = _read("src/home/route-table.ts")
        self.assertIn("POS_ENTRY_ROUTES", text)
        self.assertIn("MAIN_ENTRY_ROUTES", text)
        self.assertIn("COWORK_ALLOWED_ROUTES", text)
        self.assertIn("ERP_ALLOWED_ROUTES", text)

    def test_core_boot_guards_cowork_erp(self):
        text = _read("src/home/core-boot.ts")
        self.assertIn("entry === 'cowork'", text)
        self.assertIn("entry === 'erp'", text)
        self.assertIn("!COWORK_ALLOWED_ROUTES.has(route)", text)
        self.assertIn("!ERP_ALLOWED_ROUTES.has(route)", text)
        self.assertIn("location.pathname === '/cowork'", text)
        self.assertIn("location.pathname === '/erp'", text)


class ModuleNavAuthoritativeEntryTests(unittest.TestCase):
    """★ 各是各的:壳的权威 entry 来自服务器(/api/me/modules 的 data.entry)。"""

    def test_uses_server_authoritative_entry(self):
        text = _read("src/home/module-nav.ts")
        self.assertIn("data.entry", text)
        self.assertIn("window._entry = entry ||", text)

    def test_reads_pearnly_entry_from_localstorage(self):
        text = _read("src/home/module-nav.ts")
        self.assertIn("localStorage.getItem('pearnly_entry')", text)
        self.assertIn("window._entry", text)

    def test_pos_entry_guarded_by_pos_module_enabled(self):
        text = _read("src/home/module-nav.ts")
        self.assertIn("entry === 'pos'", text)
        self.assertIn("posEnabled", text)
        self.assertIn("return posEnabled ? POS_PRESET : original", text)

    def test_layer2_corrects_canonical_pathname(self):
        # 层2 校正(权威 data.entry):主壳 canonical 与可见 pathname 不符 → 归一 URL。
        text = _read("src/home/module-nav.ts")
        self.assertIn(
            "shellEntry === 'erp' || shellEntry === 'cowork' || shellEntry === 'main'", text
        )
        self.assertIn("location.pathname !== want", text)
        self.assertIn("window.location.replace(want + location.search + location.hash)", text)

    def test_module_nav_dispatches_cowork_erp(self):
        text = _read("src/home/module-nav.ts")
        self.assertIn("COWORK_PRESET", text)
        self.assertIn("ERP_PRESET", text)
        self.assertIn("entry === 'cowork'", text)
        self.assertIn("entry === 'erp'", text)


class GlobalsDeclareEntryTests(unittest.TestCase):
    def test_window_entry_declared(self):
        text = _read("src/types/globals.d.ts")
        self.assertIn("_entry?: string", text)


class CoworkErpNavPresetTests(unittest.TestCase):
    """2026-08-26 · cowork(协同工作台主壳)/erp(erp_portal 邀请制敏感门)nav preset 拍板。"""

    def test_nav_nodes_has_master(self):
        text = _read("src/home/nav-presets.ts")
        self.assertIn("master: '[data-collapsible=\"master\"]'", text)

    def test_cowork_preset_menu_only(self):
        text = _read("src/home/nav-presets.ts")
        self.assertIn("COWORK_PRESET", text)
        for key in ["'dashboard'", "'cowork'", "'master'", "'guide'"]:
            self.assertIn(key, text)

    def test_erp_preset_menu_only_no_guide(self):
        text = _read("src/home/nav-presets.ts")
        self.assertIn("ERP_PRESET", text)
        for key in ["'dashboard'", "'firmGoods'", "'purchases'", "'sales'", "'master'"]:
            self.assertIn(key, text)

    def test_firm_and_pos_presets_keep_master(self):
        text = _read("src/home/nav-presets.ts")
        self.assertIn("'master',\n        'sales',", text)  # FIRM_PRESET
        self.assertIn("'purchases', 'sales', 'master']", text)  # POS_PRESET


class CoworkErpEntryGuardTests(unittest.TestCase):
    """2026-08-26 · cowork/erp 跨壳深链隔离(各是各的 · 纯 UX;后端 _check 真边界)。"""

    def test_portal_route_guards_are_explicit_allowlists(self):
        text = _read("src/home/route-table.ts")
        cowork = text.split("export const COWORK_ALLOWED_ROUTES", 1)[1].split(
            "export const ERP_ALLOWED_ROUTES", 1
        )[0]
        erp = text.split("export const ERP_ALLOWED_ROUTES", 1)[1].split("// route", 1)[0]
        for route in (
            "dashboard",
            "dms-intake",
            "history",
            "push-logs",
            "reconcile",
            "clients",
            "company",
            "guide",
        ):
            self.assertIn(f"'{route}'", cowork)
        for route in (
            "dashboard",
            "stock-card",
            "purchase",
            "sales-invoices",
            "clients",
            "company",
        ):
            self.assertIn(f"'{route}'", erp)
        self.assertNotIn("'guide'", erp)
        self.assertNotIn("'stock-card'", cowork)


class CoworkErpPageRoutesTests(unittest.TestCase):
    """2026-08-26 主控拍板:/cowork 完全复用主站老登录 UI(serve static/dist/login.html,
    禁复制);/erp 是独立 ERP 专属登录门(serve static/dist/erp.html · erp_portal 邀请制),
    不复用 login.html 复用那套带 Google/LINE/注册旁路的通用页。/login 服务端 302 到 /cowork。

    旧的"复用 home.html"口径已随主控架构推翻:登录态由 landing.js(或 erp.html boot)按 token
    跳内部 /home?canonical= 承接,主壳未登录即登录页,禁复制业务 DOM。"""

    def test_pages_routes_serve_cowork_login_shell(self):
        text = _read("routes/pages_routes.py")
        self.assertIn('"/cowork"', text)
        # /cowork 主壳未登录直接呈现主站同一套登录 UI(复用老 login.html)。
        self.assertIn('return FileResponse("static/dist/login.html", headers=_NO_CACHE)', text)

    def test_pages_routes_serve_erp_dedicated_gate(self):
        text = _read("routes/pages_routes.py")
        self.assertIn('"/erp"', text)
        # /erp 独立 ERP 门,不复用 login.html(serve 专属 erp.html)。
        self.assertIn('return FileResponse("static/dist/erp.html", headers=_NO_CACHE)', text)

    def test_erp_gate_is_standalone_login_only(self):
        # ERP 门只留账号+密码一条路(POST entry=erp),零新增 ERP 业务前端/API:
        # 不复用主站 login.html(不带 Google/LINE/注册旁路)、不复制 home DOM。
        text = _read("static/erp/erp.html")
        self.assertIn("entry: 'erp'", text)
        self.assertIn("/api/login", text)
        self.assertNotIn("data-sso", text)  # 无 Google/LINE SSO 旁路
        self.assertIn("pearnly_entry', 'erp'", text)

    def test_erp_gate_corrects_shell_by_token_entry(self):
        # 层1 串壳校正:仅 erp 槽(mrpilot_token_erp)或 legacy entry=erp 才进 /home?canonical=erp;
        # pos/main/cowork token 一律留住登录页(不跳走)。
        text = _read("static/erp/erp.html")
        self.assertIn("legacyEntryFromJwt", text)
        self.assertIn("'/home?canonical=erp'", text)
        self.assertIn("localStorage.getItem('mrpilot_token_erp')", text)

    def test_login_route_redirects_to_cowork(self):
        text = _read("routes/pages_routes.py")
        self.assertIn("_safe_internal_next", text)
        self.assertIn("RedirectResponse(url=target, status_code=302)", text)
        self.assertIn('_safe_internal_next(next) or "/cowork"', text)
        # 2026-08-27 · 严格复用旧登录:不再为 OAuth 失败回跳新增透传层(oauth_error 参数不在
        # /login 签名里)。
        self.assertNotIn("oauth_error", text)

    def test_no_cowork_erp_subpath_catchall(self):
        # 路由走 hash,pathname 恒为 /cowork 或 /erp → 不设 {rest:path} 子路径(最小实现)。
        text = _read("routes/pages_routes.py")
        self.assertNotIn("/cowork/{rest:path}", text)
        self.assertNotIn("/erp/{rest:path}", text)


if __name__ == "__main__":
    unittest.main()
