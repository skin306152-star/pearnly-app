# -*- coding: utf-8 -*-
"""对外页面「外壳闸」:每个公开路由吐的 HTML 必须是 minified 外壳(≤3 行)。

Zihao 2026-07-10 点名:老页面早整改过 view-source 成品化,新页面必须跟上同一范式 ——
源码可读地放 src/ 或 static/<域>/,Vite/html-minifier build 出单行 dist 产物,浏览器
view-source 只见外壳。本闸真发请求验响应字节的物理行数,任何新页面裸发多行源码即红,
逼其并入 build 管线(见 scripts/build-html-minify.mjs)。
"""

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.pages_routes import router

# 全部返回 HTML 外壳的对外路由(/admin 是 301 → 用落地的 /admin/cost)。
SHELL_ROUTES = [
    "/",
    "/login",
    "/home",
    "/admin/cost",
    "/pos",
    "/earn",
    "/cashier",
    "/console",
    "/invite/x",
    "/ai",
    "/reset",
    "/terms",
    "/privacy",
]

MAX_LINES = 3  # minified 外壳 · 留 3 行余量(实测均为 1 行)


class PageShellMinifiedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = FastAPI()
        app.include_router(router)
        cls.client = TestClient(app)

    def test_public_routes_serve_minified_shell(self):
        for path in SHELL_ROUTES:
            with self.subTest(path=path):
                resp = self.client.get(path, follow_redirects=False)
                self.assertEqual(resp.status_code, 200, f"{path} → {resp.status_code}")
                lines = resp.text.count("\n") + 1
                self.assertLessEqual(
                    lines,
                    MAX_LINES,
                    f"{path} 吐了 {lines} 行 · 对外页面须 build 成 minified 外壳"
                    f"(源保持可读 · 见 scripts/build-html-minify.mjs)",
                )

    def test_no_readable_internal_comments_leaked(self):
        # 外壳不得残留 HTML 内部注释(<!-- ... -->)· 中文排期/接入注释更是硬红。
        for path in SHELL_ROUTES:
            with self.subTest(path=path):
                resp = self.client.get(path, follow_redirects=False)
                self.assertNotIn("<!--", resp.text, f"{path} 残留 HTML 注释(应被 minify 去除)")


if __name__ == "__main__":
    unittest.main()
