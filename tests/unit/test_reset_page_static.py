# -*- coding: utf-8 -*-
"""重置密码落地页(/reset)静态契约闸。

背景:/reset 路由长期指向不存在的 static/reset.html → 500,改密邮件/LINE 链接
(auth_password_routes 生成 {host}/reset?token=)点了即报错。本次补齐 reset.html +
reset.js。无 jsdom · 静态锁:页面/脚本存在 + 4 语齐 + 接对后端端点 + 读 token。
"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HTML = os.path.join(ROOT, "static", "reset.html")
JS = os.path.join(ROOT, "static", "reset.js")

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
        with open(HTML, "r", encoding="utf-8") as f:
            cls.html = f.read()
        with open(JS, "r", encoding="utf-8") as f:
            cls.js = f.read()

    def test_files_exist_and_wired(self):
        self.assertIn("/static/reset.js", self.html, "reset.html 须引 reset.js")
        self.assertIn("r-form", self.html)
        self.assertIn("r-new", self.html)
        self.assertIn("r-confirm", self.html)

    def test_posts_to_reset_endpoint(self):
        self.assertIn("/api/auth/reset_password", self.js, "须接后端 reset_password 端点")
        self.assertIn("new_password", self.js)
        self.assertRegex(self.js, r"URLSearchParams.*token|get\(['\"]token", "须从 URL 读 token")

    def test_four_languages_complete(self):
        for lg in LANGS:
            self.assertRegex(self.js, r"\b" + lg + r"\s*:\s*\{", f"缺语言 {lg}")
        # 每个 key 至少出现 4 次(4 语各一)
        for key in KEYS:
            n = len(re.findall(r"\b" + key + r"\s*:", self.js))
            self.assertGreaterEqual(n, 4, f"i18n key {key} 不足 4 语(实得 {n})")

    def test_backend_error_codes_mapped(self):
        for code in ("invalid_token", "token_expired", "token_already_used", "password_too_short"):
            self.assertIn(code, self.js, f"未映射后端错误码 {code}")


if __name__ == "__main__":
    unittest.main()
