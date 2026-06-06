# -*- coding: utf-8 -*-
"""销项商品编码唯一冲突修复守门:空白 code → NULL(可多建无编码商品)+ 重复 code → 409。"""

import unittest

import psycopg2
from fastapi import HTTPException

from core.route_helpers import translate_unique_violation
from services.sales import products as products_dal


class _CaptureCursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return {"id": "p1"}


class NormCodeTests(unittest.TestCase):
    def test_blank_code_becomes_none(self):
        self.assertIsNone(products_dal._norm_code({"code": "   "})["code"])

    def test_code_stripped(self):
        self.assertEqual(products_dal._norm_code({"code": "  ABC "})["code"], "ABC")

    def test_none_and_missing_pass_through(self):
        self.assertIsNone(products_dal._norm_code({"code": None})["code"])
        self.assertNotIn("code", products_dal._norm_code({"name_th": "x"}))

    def test_blank_code_omitted_from_insert(self):
        """空白 code 归一为 NULL → 不进 INSERT 列 → 不触唯一索引(可多建无编码商品)。"""
        cur = _CaptureCursor()
        products_dal.create_product(cur, tenant_id="t", fields={"name_th": "A", "code": "  "})
        sql = cur.calls[0][0]
        self.assertNotIn("code", sql.split("VALUES")[0])

    def test_real_code_kept_in_insert(self):
        cur = _CaptureCursor()
        products_dal.create_product(cur, tenant_id="t", fields={"name_th": "A", "code": "SKU1"})
        self.assertIn("SKU1", cur.calls[0][1])


class TranslateUniqueViolationTests(unittest.TestCase):
    def test_unique_violation_becomes_409(self):
        with self.assertRaises(HTTPException) as ctx:
            with translate_unique_violation("sales.product_code_exists"):
                raise psycopg2.errors.UniqueViolation("dup key")
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "sales.product_code_exists")

    def test_passthrough_when_no_violation(self):
        out = {}
        with translate_unique_violation("x"):
            out["ran"] = True
        self.assertTrue(out["ran"])

    def test_other_errors_not_swallowed(self):
        with self.assertRaises(ValueError):
            with translate_unique_violation("x"):
                raise ValueError("unrelated")


if __name__ == "__main__":
    unittest.main()
