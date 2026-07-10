# -*- coding: utf-8 -*-
"""Earn 超管后台专属登录页(主域路径 /earn)入口收窄契约。

钉三条:① 页面只有账号 + 密码 + 登录,不存在 Google / LINE / 注册 / 忘记密码任何旁路,
复用主站 /api/login(零新鉴权);② 放行判据 = /api/me 的 is_super_admin,通过才落 token
进 /admin/cost,非超管有四语「无权限」文案;③ /earn 路由挂在 pages_routes 上、返回
200 + HTML + no-cache(admin.js 甩回来的落点必须常在)。

演进(2026-07-10):页面从 routes/earn_login_page.py 内联常量挪成可读源
static/earn/earn-login.html + build 压成 dist/earn-login.html(view-source 只见外壳)·
本闸改对可读源断言。"""

import asyncio
import re
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import pages_routes

# 断言对"实际服务出去的内容"生效:剥掉可读源里的开发注释(build minify 也会去掉),
# 否则注释里解释入口收窄的"Google/LINE/注册"等字样会误伤 test_no_google_no_line_no_signup。
_RAW = Path("static/earn/earn-login.html").read_text(encoding="utf-8")
EARN_LOGIN_HTML = re.sub(r"<!--.*?-->", "", _RAW, flags=re.S)


class EarnLoginPageContentTests(unittest.TestCase):
    def test_has_account_password_and_login_only(self):
        html = EARN_LOGIN_HTML
        self.assertIn('id="e-user"', html)
        self.assertIn('id="e-pw"', html)
        self.assertIn('id="e-submit"', html)
        # 账号=用户名或邮箱 · 不写死 type=email(超管账号可能不是邮箱)。
        # 对属性断言而非整行字面量:prettier 会把多属性 input 折行,行内空白不可依赖。
        user_input = re.search(r"<input[^>]*id=\"e-user\"[^>]*>", html, flags=re.S)
        self.assertIsNotNone(user_input, "缺账号输入框")
        self.assertIn('type="text"', user_input.group(0))
        self.assertIn('autocapitalize="none"', user_input.group(0))
        # 复用主站登录 API · 零新鉴权
        self.assertIn("/api/login", html)

    def test_super_admin_gate_via_api_me(self):
        # 放行判据只认 /api/me 的 is_super_admin(与 admin.js _verifySuperAdmin 同一事实源);
        # 通过 → /admin/cost;不通过 → 清 token(removeItem)不给进。
        self.assertIn("/api/me", EARN_LOGIN_HTML)
        self.assertIn("is_super_admin", EARN_LOGIN_HTML)
        self.assertIn("/admin/cost", EARN_LOGIN_HTML)
        self.assertIn("removeItem('mrpilot_token')", EARN_LOGIN_HTML)
        # 非超管四语「无权限」文案
        for text in (
            "该账号无超管权限",
            "ไม่มีสิทธิ์ผู้ดูแลระบบ",
            "no super admin access",
            "管理者権限がありません",
        ):
            self.assertIn(text, EARN_LOGIN_HTML)

    def test_no_google_no_line_no_signup_bypass(self):
        # 入口收窄:用具体旁路标记断言(避免误伤 CSS 的 --line / line-height 等无关子串)。
        low = EARN_LOGIN_HTML.lower()
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
        self.assertNotIn("注册", EARN_LOGIN_HTML)

    def test_no_forgot_password_selfservice(self):
        self.assertNotIn("/api/auth/forgot_password", EARN_LOGIN_HTML)
        for text in ("忘记密码", "ลืมรหัสผ่าน", "Forgot password", "パスワードをお忘れ"):
            self.assertNotIn(text, EARN_LOGIN_HTML)

    def test_four_languages_viewport_noindex(self):
        for lang in ("zh:", "th:", "en:", "ja:"):
            self.assertIn(lang, EARN_LOGIN_HTML)
        self.assertIn('name="viewport"', EARN_LOGIN_HTML)
        self.assertIn("noindex", EARN_LOGIN_HTML)


class EarnLoginRouteContractTests(unittest.TestCase):
    def test_earn_route_mounted(self):
        paths = {r.path for r in pages_routes.router.routes if hasattr(r, "path")}
        self.assertIn("/earn", paths)

    def test_earn_serves_html_no_cache(self):
        app = FastAPI()
        app.include_router(pages_routes.router)
        resp = TestClient(app).get("/earn", follow_redirects=False)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.headers.get("content-type", ""))
        cc = resp.headers.get("cache-control", "")
        self.assertIn("no-cache", cc)
        self.assertIn("no-store", cc)
        self.assertIn('id="e-form"', resp.text)

    def test_route_handler_serves_dist_product(self):
        # /earn 出 dist minified 产物(dist/ 部署可靠 · 源可读在 static/earn/earn-login.html)
        resp = asyncio.run(pages_routes.earn_login_page())
        self.assertEqual(resp.path, "static/dist/earn-login.html")


if __name__ == "__main__":
    unittest.main()
