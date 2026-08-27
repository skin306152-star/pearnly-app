# -*- coding: utf-8 -*-
"""ERP 专属登录门(/erp)入口收窄契约(2026-08-26)。

与 POS/Earn 登录门同构:页面只有账号(用户名或邮箱)+ 密码 + 登录,断言【不存在】Google /
LINE / 注册 / 忘记密码任何旁路;复用主站账号密码登录 API(零新鉴权 · POST entry='erp'),
4 语齐全,有 viewport。真浏览器渲染为动态部分(见交付报告)。

与 POS 门的差异(本测试如实描述真实行为):
  · POS 登录成功落 /home;ERP 落 /home?canonical=erp(由 home.html preboot 归一为 /erp)。
  · ERP 页头 boot 做串壳校正(读 token entry,层1):非 erp 入口 token 立即跳回自己的
    canonical 主壳 —— 故本页有 location.replace(这不是劫持,是按 entry 分流)。
  · 是否获 erp_portal 邀请由后端 /api/login 的 login_entrance_allowed 裁决(fail-closed),
    本页零新增准入逻辑,照实显示后端返回的错误。

演进(2026-08-26):新增 static/erp/erp.html + build 压成 dist/erp.html(view-source 只见外壳)。
"""

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from routes.pages_routes import router as pages_router

# 断言对"实际服务出去的内容"生效:剥掉可读源里的开发注释(build minify 也会去掉),
# 否则注释里解释入口收窄的"Google/LINE/注册"等字样会误伤 test_no_google_no_line_no_signup。
_RAW = Path("static/erp/erp.html").read_text(encoding="utf-8")
ERP_LOGIN_HTML = re.sub(r"<!--.*?-->", "", _RAW, flags=re.S)


class ErpLoginPageContentTests(unittest.TestCase):
    def test_has_email_password_and_login_only(self):
        html = ERP_LOGIN_HTML
        self.assertIn('id="p-email"', html)
        self.assertIn('id="p-pw"', html)
        self.assertIn('id="p-submit"', html)
        # 复用主站账号密码登录 API · 零新鉴权
        self.assertIn("/api/login", html)
        # ERP 门 POST entry='erp',请求后端按 erp_portal 邀请闸裁决。
        self.assertIn("entry: 'erp'", html)

    def test_no_google_no_line_no_signup_bypass(self):
        # 入口收窄:不给 Google / LINE / 注册 / OAuth 任何旁路。用具体旁路标记断言(避免误伤
        # CSS 的 --line / line-height 等无关子串):第三方登录端点、SSO 按钮、注册端点都不得出现。
        low = ERP_LOGIN_HTML.lower()
        for banned in (
            "google",
            "/api/auth/line",
            "/api/auth/google",
            "line/start",
            "data-sso",
            "oauth",
            "signup",
            "/api/auth/signup",
        ):
            self.assertNotIn(banned, low)
        self.assertNotIn("注册", ERP_LOGIN_HTML)

    def test_no_forgot_password_selfservice(self):
        # 发放制账号不走自助找回(密码问题找发号人 → Earn 重置)。
        self.assertNotIn("/api/auth/forgot_password", ERP_LOGIN_HTML)
        self.assertNotIn("p-forgot", ERP_LOGIN_HTML)
        for text in ("忘记密码", "ลืมรหัสผ่าน", "Forgot password", "パスワードをお忘れ"):
            self.assertNotIn(text, ERP_LOGIN_HTML)

    def test_four_languages_and_viewport(self):
        for lang in ("zh:", "th:", "en:", "ja:"):
            self.assertIn(lang, ERP_LOGIN_HTML)
        self.assertIn('name="viewport"', ERP_LOGIN_HTML)
        self.assertIn("noindex", ERP_LOGIN_HTML)

    def test_inline_script_has_valid_javascript_syntax(self):
        script = ERP_LOGIN_HTML.split("<script>", 1)[1].split("</script>", 1)[0]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", encoding="utf-8") as handle:
            handle.write(script)
            handle.flush()
            result = subprocess.run(
                ["node", "--check", handle.name],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_stores_token_and_lands_on_erp_canonical(self):
        # 登录成功按主站同款落地(localStorage['mrpilot_token'])→ 进 /home?canonical=erp,
        # 由 home.html preboot 把可见 pathname 归一为 /erp(POS 落 /home,ERP 落 /home?canonical=erp)。
        self.assertIn("mrpilot_token", ERP_LOGIN_HTML)
        self.assertIn("'/home?canonical=erp'", ERP_LOGIN_HTML)
        self.assertIn("pearnly_entry', 'erp'", ERP_LOGIN_HTML)

    def test_shell_correction_by_token_entry(self):
        # 层1 串壳校正:先看 erp 槽(mrpilot_token_erp);无则读 legacy mrpilot_token 的 JWT entry,
        # 仅当 entry==='erp' 才收养进 /home?canonical=erp;pos/main/cowork token(无 erp 槽)一律
        # 留住登录页(不跳走)。2026-08-27 改为入口级 token 槽 + legacy 迁移判据。
        self.assertIn("localStorage.getItem('mrpilot_token_erp')", ERP_LOGIN_HTML)
        self.assertIn("legacyEntryFromJwt", ERP_LOGIN_HTML)
        self.assertIn("'/home?canonical=erp'", ERP_LOGIN_HTML)

    def test_no_erp_business_api_or_dom(self):
        # 本页只是登录门:不新增 ERP 业务 API、不复制 home 业务 DOM(无 home SPA 的 page-* 壳)。
        self.assertNotIn("page-", ERP_LOGIN_HTML)
        for endpoint in ("/api/erp/endpoints", "/api/erp/logs", "/api/erp/bridge"):
            self.assertNotIn(endpoint, ERP_LOGIN_HTML)


class ErpLoginRouteContractTests(unittest.TestCase):
    def test_erp_dedicated_gate_route(self):
        paths = {r.path for r in pages_router.routes if hasattr(r, "path")}
        self.assertIn("/erp", paths)
        # 路由走 hash,不设 {rest:path} 子路径(最小实现 · 与 /cowork 同)。
        self.assertNotIn("/erp/{rest:path}", paths)

    def test_erp_route_serves_dedicated_gate_not_login_shim(self):
        import asyncio

        from routes import pages_routes

        self.assertEqual(asyncio.run(pages_routes.erp_page()).path, "static/dist/erp.html")
        # /cowork 才复用主站 login.html(ERP 不复用)。
        self.assertEqual(asyncio.run(pages_routes.cowork_page()).path, "static/dist/login.html")


if __name__ == "__main__":
    unittest.main()
