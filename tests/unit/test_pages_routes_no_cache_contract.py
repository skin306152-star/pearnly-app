# -*- coding: utf-8 -*-
"""页面外壳 no-cache 契约闸。

根治"改了源码 view-source 还看旧版":SPA 外壳(home/console/invite/admin/pos…)
必须带 no-cache,否则浏览器缓存旧壳 → 内部 ?v= bump 失效。本闸用 TestClient
真发请求验响应头(等价 curl -I),防回归。
"""

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.pages_routes import router, _NO_CACHE

# 返回静态 HTML 外壳、且文件在仓库内存在的页面入口(reset.html 不入仓,单独豁免)
SHELL_ROUTES = ["/", "/login", "/home", "/console", "/invite/x", "/terms", "/privacy"]


class NoCacheContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = FastAPI()
        app.include_router(router)
        cls.client = TestClient(app)

    def test_constant_matches_home_spec(self):
        # 锚定常量值与 /home 历史口径一致
        self.assertEqual(_NO_CACHE["Cache-Control"], "no-cache, no-store, must-revalidate")
        self.assertEqual(_NO_CACHE["Pragma"], "no-cache")

    def test_shell_routes_send_no_cache(self):
        for path in SHELL_ROUTES:
            with self.subTest(path=path):
                resp = self.client.get(path, follow_redirects=False)
                self.assertEqual(resp.status_code, 200, f"{path} → {resp.status_code}")
                cc = resp.headers.get("cache-control", "")
                self.assertIn("no-cache", cc, f"{path} 缺 no-cache: {cc!r}")
                self.assertIn("no-store", cc, f"{path} 缺 no-store: {cc!r}")
                self.assertEqual(resp.headers.get("pragma"), "no-cache", f"{path} 缺 Pragma")

    def test_admin_redirect_then_shell_no_cache(self):
        # /admin → 301 /admin/cost;落地 SPA 外壳须 no-cache
        resp = self.client.get("/admin/cost", follow_redirects=False)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("no-cache", resp.headers.get("cache-control", ""))

    def test_pos_shell_no_cache(self):
        resp = self.client.get("/pos", follow_redirects=False)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("no-cache", resp.headers.get("cache-control", ""))


if __name__ == "__main__":
    unittest.main()
