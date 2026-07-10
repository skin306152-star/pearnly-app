# -*- coding: utf-8 -*-
"""POS 老板后台专属登录页(主域路径 /pos)入口收窄契约(PS-5)。

验收断言 ①的静态部分:页面只有账号(用户名或邮箱)+ 密码 + 登录,断言【不存在】Google /
LINE / 注册 / 忘记密码任何旁路(发放制账号密码问题找发号人);复用主站账号密码登录 API
(零新鉴权),4 语齐全,有 viewport。(真浏览器渲染 + 截图为动态部分,见交付报告。)

演进(2026-07-10):页面从 routes/pos_login_page.py 内联常量挪成可读源 static/pos/pos-login.html
+ build 压成 dist/pos-login.html(view-source 只见外壳)· 本闸改对可读源断言。"""

import re
import unittest
from pathlib import Path

from routes.pages_routes import router as pages_router

# 断言对"实际服务出去的内容"生效:剥掉可读源里的开发注释(build minify 也会去掉),
# 否则注释里解释入口收窄的"Google/LINE/注册"等字样会误伤 test_no_google_no_line_no_signup。
_RAW = Path("static/pos/pos-login.html").read_text(encoding="utf-8")
POS_LOGIN_HTML = re.sub(r"<!--.*?-->", "", _RAW, flags=re.S)


class PosLoginPageContentTests(unittest.TestCase):
    def test_has_email_password_and_login_only(self):
        html = POS_LOGIN_HTML
        self.assertIn('id="p-email"', html)
        self.assertIn('id="p-pw"', html)
        self.assertIn('id="p-submit"', html)
        # 复用主站邮箱密码登录 API · 零新鉴权
        self.assertIn("/api/login", html)

    def test_no_google_no_line_no_signup_bypass(self):
        # 入口收窄:不给 Google / LINE / 注册任何旁路。用具体旁路标记断言(避免误伤 CSS 的
        # --line / line-height 等无关子串):第三方登录端点、SSO 按钮、注册端点/文案都不得出现。
        low = POS_LOGIN_HTML.lower()
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
        self.assertNotIn("注册", POS_LOGIN_HTML)

    def test_no_forgot_password_selfservice(self):
        # 2026-07-10 Zihao 拍板:发放制账号不走自助找回(密码问题找发号人 → Earn 重置密码)。
        # 接口引用 + 元素 id + 四语文案都不得出现。
        self.assertNotIn("/api/auth/forgot_password", POS_LOGIN_HTML)
        self.assertNotIn("p-forgot", POS_LOGIN_HTML)
        for text in ("忘记密码", "ลืมรหัสผ่าน", "Forgot password", "パスワードをお忘れ"):
            self.assertNotIn(text, POS_LOGIN_HTML)

    def test_four_languages_and_viewport(self):
        for lang in ("zh:", "th:", "en:", "ja:"):
            self.assertIn(lang, POS_LOGIN_HTML)
        self.assertIn('name="viewport"', POS_LOGIN_HTML)
        self.assertIn("noindex", POS_LOGIN_HTML)

    def test_stores_token_like_main_site(self):
        # 登录成功按主站同款落地(localStorage['mrpilot_token']) → 进 /home 主应用
        self.assertIn("mrpilot_token", POS_LOGIN_HTML)
        self.assertIn("/home", POS_LOGIN_HTML)

    def test_old_cashier_device_redirect_guard(self):
        # 老收银设备兼容:本机存过 pos_store_token(键名与收银台 SPA 精确一致)→ 跳 /cashier。
        self.assertIn("pos_store_token", POS_LOGIN_HTML)
        self.assertIn("/cashier", POS_LOGIN_HTML)
        self.assertIn("location.replace", POS_LOGIN_HTML)


class PosLoginRouteContractTests(unittest.TestCase):
    def test_owner_login_at_pos_cashier_at_cashier(self):
        # PS-5 最终地图:/pos = 老板后台登录页;收银台 SPA 迁至 /cashier。刻意不碰根路由 /。
        paths = {r.path for r in pages_router.routes if hasattr(r, "path")}
        self.assertIn("/pos", paths)
        self.assertIn("/cashier", paths)
        self.assertIn("/cashier/{rest:path}", paths)
        self.assertNotIn("/pos-login", paths)  # 子域方案已废弃,不再有独立 /pos-login


if __name__ == "__main__":
    unittest.main()
