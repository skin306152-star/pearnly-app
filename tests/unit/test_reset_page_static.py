# -*- coding: utf-8 -*-
"""重置密码落地页(/reset)静态契约闸。

背景:/reset 路由长期指向不存在的 static/reset.html → 500,改密邮件/LINE 链接
(auth_password_routes 生成 {host}/reset?token=)点了即报错。修法=内联 HTML 进
routes/reset_page.py(webhook 不拾取新增 static 根文件,内联随 routes/*.py 可靠上线)。
无 jsdom · 静态锁:页面/脚本内联齐 + 4 语齐 + 接对后端端点 + 读 token + 路由内联引用。
"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PAGE = os.path.join(ROOT, "routes", "reset_page.py")
PAGES_ROUTES = os.path.join(ROOT, "routes", "pages_routes.py")

LANGS = ("zh", "th", "en", "ja")
KEYS = (
    "title",
    "sub",
    "labelNew",
    "labelConfirm",
    "submit",
    "back",
    "mismatch",
    "badLink",
    "invalidToken",
    "expired",
    "used",
    "success",
    "failed",
)


class ResetPageStatic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PAGE, "r", encoding="utf-8") as f:
            cls.page = f.read()
        with open(PAGES_ROUTES, "r", encoding="utf-8") as f:
            cls.routes = f.read()

    def test_route_serves_inline_html(self):
        # /reset 必须内联返回(非 FileResponse static 文件 · 否则 webhook 不部署 → 500)
        self.assertIn("RESET_PAGE_HTML", self.routes, "/reset 须引内联常量")
        self.assertIn("HTMLResponse(RESET_PAGE_HTML", self.routes)
        self.assertNotIn(
            'FileResponse("static/reset.html"', self.routes, "禁回退到不部署的 static 文件"
        )
        self.assertIn("RESET_PAGE_HTML", self.page)

    def test_page_structure_and_wiring(self):
        self.assertIn("r-form", self.page)
        self.assertIn("r-new", self.page)
        self.assertIn("r-confirm", self.page)
        self.assertIn("/api/auth/reset_password", self.page, "须接后端 reset_password 端点")
        self.assertIn("new_password", self.page)
        self.assertRegex(self.page, r"URLSearchParams.*token|get\(['\"]token", "须从 URL 读 token")

    def test_four_languages_complete(self):
        for lg in LANGS:
            self.assertRegex(self.page, r"\b" + lg + r"\s*:\s*\{", f"缺语言 {lg}")
        for key in KEYS:
            n = len(re.findall(r"\b" + key + r"\s*:", self.page))
            self.assertGreaterEqual(n, 4, f"i18n key {key} 不足 4 语(实得 {n})")

    def test_backend_error_codes_mapped(self):
        for code in ("invalid_token", "token_expired", "token_already_used", "password_too_short"):
            self.assertIn(code, self.page, f"未映射后端错误码 {code}")


if __name__ == "__main__":
    unittest.main()
