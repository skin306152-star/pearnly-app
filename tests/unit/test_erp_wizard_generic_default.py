#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_erp_wizard_generic_default.py

P1「真正开箱即用」收尾 · §3.4 step 3(第三十二会话)守门。

锁定两件事:
  1. suggest_generic_product_code(products) 纯函数:能从商品列表里挑出一个
     收入/销售/服务类商品(多语种关键词),挑不到返 None(绝不瞎填)。
  2. /api/erp/wizard/products 路由成功时附 suggested_generic_code 键,把
     建议码透出给向导预选。

为什么要守:这是「新用户连一次就把通用商品配好」的灵魂 —— 建议逻辑挂了
用户又回到「自己去高级设置手挑」的繁琐老路,违背开箱即用目标。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_product_sync import suggest_generic_product_code  # noqa: E402


class SuggestGenericProductTests(unittest.TestCase):
    def test_empty_list_returns_none(self):
        self.assertIsNone(suggest_generic_product_code([]))
        self.assertIsNone(suggest_generic_product_code(None))  # type: ignore[arg-type]

    def test_matches_thai_income_keyword_in_name(self):
        products = [
            {"code": "P001", "name": "น้ำพริกเผา 200g"},
            {"code": "00-REV", "name": "รายได้จากการขาย"},  # รายได้ = 收入
            {"code": "P002", "name": "คุกกี้"},
        ]
        self.assertEqual(suggest_generic_product_code(products), "00-REV")

    def test_matches_english_keyword(self):
        products = [
            {"code": "A", "name": "Widget"},
            {"code": "B", "name": "General Sales Revenue"},
        ]
        self.assertEqual(suggest_generic_product_code(products), "B")

    def test_matches_chinese_keyword(self):
        products = [
            {"code": "X", "name": "定制蛋糕"},
            {"code": "Y", "name": "销售收入"},
        ]
        self.assertEqual(suggest_generic_product_code(products), "Y")

    def test_name_match_wins_over_later_category_match(self):
        # 名字命中优先于后面靠分类命中的项。
        products = [
            {"code": "NAME-HIT", "name": "income account", "category_name": "misc"},
            {"code": "CAT-HIT", "name": "random thing", "category_name": "รายได้"},
        ]
        self.assertEqual(suggest_generic_product_code(products), "NAME-HIT")

    def test_category_match_when_no_name_match(self):
        products = [
            {"code": "C1", "name": "ของแถม", "category_name": "ของขวัญ"},
            {"code": "C2", "name": "บริการพิเศษ", "category_name": "บริการ"},  # name 已命中 บริการ
        ]
        # บริการ(服务)是关键词 · C2 的 name 直接命中
        self.assertEqual(suggest_generic_product_code(products), "C2")

    def test_no_keyword_returns_none(self):
        products = [
            {"code": "Z1", "name": "Custom Cake 1kg"},
            {"code": "Z2", "name": "ขนมปังไส้ครีม", "category_name": "เบเกอรี่"},
        ]
        # ขนมปัง... 不含关键词;เบเกอรี่(烘焙)也不在表里 → None
        # 注:ขาย 不在这些字符串里。
        self.assertIsNone(suggest_generic_product_code(products))

    def test_skips_rows_without_code(self):
        products = [
            {"name": "sales revenue (no code)"},  # 命中关键词但无 code → 跳过
            {"code": "OK", "name": "service fee"},
        ]
        self.assertEqual(suggest_generic_product_code(products), "OK")


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None,
    "fastapi not installed — route-level test covered server-side.",
)
class WizardProductsRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa: F401
        import erp_routes  # noqa: F401

        cls.app_module = app
        cls.erp_routes = erp_routes

    def _client(self):
        from fastapi.testclient import TestClient

        return TestClient(self.app_module.app)

    def test_route_attaches_suggested_code_on_success(self):
        app = self.app_module
        erp_routes = self.erp_routes
        fake_listing = MagicMock(
            return_value={
                "ok": True,
                "elapsed_ms": 50,
                "products": [
                    {"code": "P9", "name": "Custom item"},
                    {"code": "00-REV", "name": "รายได้จากการขาย"},
                ],
                "error_code": None,
                "error_friendly": None,
                "raw_error": None,
            }
        )
        with (
            patch.object(
                erp_routes,
                "get_current_user_from_request",
                return_value={"id": "u", "plan": "pro"},
            ),
            patch.object(erp_routes, "_check_push_access", return_value=None),
            patch.object(app._erp, "list_mrerp_products", fake_listing),
        ):
            with self._client() as client:
                r = client.post(
                    "/api/erp/wizard/products",
                    json={"config": {"username": "u", "password": "p"}},
                )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body.get("suggested_generic_code"), "00-REV")

    def test_route_no_suggestion_key_munging_on_failure(self):
        """失败时不强行附 suggested_generic_code(前端走降级文本框)。"""
        app = self.app_module
        erp_routes = self.erp_routes
        fail_listing = MagicMock(
            return_value={
                "ok": False,
                "elapsed_ms": 0,
                "products": [],
                "error_code": "ERR_AUTH",
                "error_friendly": {"zh": "登录失败"},
                "raw_error": "auth",
            }
        )
        with (
            patch.object(
                erp_routes,
                "get_current_user_from_request",
                return_value={"id": "u", "plan": "pro"},
            ),
            patch.object(erp_routes, "_check_push_access", return_value=None),
            patch.object(app._erp, "list_mrerp_products", fail_listing),
        ):
            with self._client() as client:
                r = client.post(
                    "/api/erp/wizard/products",
                    json={"config": {"username": "bad", "password": "bad"}},
                )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertFalse(body.get("ok"))
        self.assertNotIn("suggested_generic_code", body)


if __name__ == "__main__":
    unittest.main()
