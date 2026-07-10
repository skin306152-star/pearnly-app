# -*- coding: utf-8 -*-
"""脸0 品牌门户接入守门(2026-07-10)。

锁三条机械事实,防回归:
  1. 根路径 `/` 出品牌门户 static/landing/portal.dc.html(不是登录页)· 带 no-cache;
     `/login` 仍出原登录页 static/dist/login.html(登录主路径没被门户顶掉)。
  2. 门户资产零外链:HTML 里的 <link stylesheet> / <script src> 全指向本地 /static/landing/vendor/。
     唯二允许的外部字符串是 window.__resources 里 React/ReactDOM 的 unpkg 键(support.js 读它
     重定向到本地副本 · 不真落 CDN)与页脚 LINE OA 联系链接(用户点击跳转 · 非资源加载)。
  3. 四张产品卡零注册入口(Zihao 2026-07-10 拍板:登录/预约/联系,不放注册按钮)。
"""

import asyncio
import re
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import pages_routes
from routes.pages_routes import router

PORTAL = Path("static/landing/portal.dc.html")


class PortalRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = FastAPI()
        app.include_router(router)
        cls.client = TestClient(app)
        cls.html = PORTAL.read_text(encoding="utf-8")

    def test_root_serves_portal_login_serves_login(self):
        self.assertEqual(asyncio.run(pages_routes.root()).path, "static/landing/portal.dc.html")
        self.assertEqual(asyncio.run(pages_routes.login_page()).path, "static/dist/login.html")

    def test_root_no_cache(self):
        resp = self.client.get("/", follow_redirects=False)
        self.assertEqual(resp.status_code, 200)
        cc = resp.headers.get("cache-control", "")
        self.assertIn("no-cache", cc)
        self.assertIn("no-store", cc)

    def test_portal_file_exists(self):
        self.assertTrue(PORTAL.is_file())

    def test_asset_links_are_local(self):
        # 所有 stylesheet / script src 必须是本地 /static/landing/vendor/ 路径(零外链资源加载)
        refs = re.findall(r'<(?:link[^>]*href|script[^>]*src)=["\']([^"\']+)["\']', self.html)
        loaded = [r for r in refs if r.endswith((".js", ".css")) or "/vendor/" in r]
        self.assertTrue(loaded, "portal 应至少引用本地 vendor 资产")
        for r in loaded:
            self.assertTrue(
                r.startswith("/static/landing/vendor/"),
                f"门户资产必须自托管在 /static/landing/vendor/,发现外链:{r}",
            )

    def test_only_expected_external_strings(self):
        # 非本地资产的 http(s) 出现处只允许:__resources 的 unpkg 键 + 页脚 LINE OA 联系链接
        externals = set(re.findall(r"https?://[^\"'\s)]+", self.html))
        # pos.pearnly.com = POS 老板后台独立域名(Zihao 2026-07-10 拍板 · PS-5 在建 · 门户四卡之一的跳转目标)
        allowed_prefixes = (
            "https://unpkg.com/react",
            "https://line.me/",
            "https://pos.pearnly.com",
        )
        for u in externals:
            self.assertTrue(
                u.startswith(allowed_prefixes),
                f"门户出现未预期外链:{u}(只许 unpkg 重定向键 + LINE OA 联系链接)",
            )

    def test_deploy_sentinels_all_filled(self):
        # {{LOGIN_AI}} 等部署占位必须全部落真值(渲染出来会变成字面量 = 死链)
        leftover = re.findall(r"\{\{[A-Z_]+\}\}", self.html)
        self.assertEqual(leftover, [], f"仍有未落值的部署占位:{leftover}")

    def test_product_cards_have_no_register_entry(self):
        # 四卡零注册入口:自助注册走登录页自带流程,门户不放注册按钮/链接
        self.assertNotIn("/register", self.html)
        self.assertNotIn("/signup", self.html)


if __name__ == "__main__":
    unittest.main()
