# -*- coding: utf-8 -*-
"""销项商品编码唯一冲突修复守门:空白 code → NULL(可多建无编码商品)+ 重复 code → 409。"""

import unittest

import psycopg2
from fastapi import HTTPException

from core.route_helpers import translate_unique_violation
from services.sales import products as products_dal


class _CaptureCursor:
    """默认无软删同码记录(revive SELECT → None)→ 走正常 INSERT 路径。"""

    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return None


class _ReviveCursor:
    """模拟存在一条已软删的同编码记录:首个 fetchone(revive SELECT)返回死记录 id。"""

    def __init__(self):
        self.calls = []
        self._n = 0

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        self._n += 1
        return {"id": "dead1"} if self._n == 1 else {"id": "dead1", "is_active": True}


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
        products_dal.create_product(
            cur, tenant_id="t", workspace_client_id=1, fields={"name_th": "A", "code": "  "}
        )
        sql = cur.calls[0][0]
        self.assertNotIn("code", sql.split("VALUES")[0])

    def test_real_code_kept_in_insert(self):
        cur = _CaptureCursor()
        products_dal.create_product(
            cur, tenant_id="t", workspace_client_id=1, fields={"name_th": "A", "code": "SKU1"}
        )
        insert = next(c for c in cur.calls if "INSERT" in c[0])
        self.assertIn("SKU1", insert[1])


class ReviveSoftDeletedTests(unittest.TestCase):
    """编码撞到已软删记录 → 复活并覆盖(不再误报"已存在"·编码可复用)。"""

    def test_recreate_revives_instead_of_insert(self):
        cur = _ReviveCursor()
        out = products_dal.create_product(
            cur, tenant_id="t", workspace_client_id=1, fields={"name_th": "新名", "code": "1"}
        )
        self.assertIn("is_active = FALSE", cur.calls[0][0])  # 先查软删同码
        self.assertIn("UPDATE products", cur.calls[1][0])  # 复活而非 INSERT
        self.assertIn("is_active = TRUE", cur.calls[1][0])
        self.assertIn("新名", cur.calls[1][1])
        self.assertFalse(any("INSERT" in c[0] for c in cur.calls))
        self.assertEqual(out["id"], "dead1")

    def test_no_code_skips_revive_query(self):
        cur = _CaptureCursor()
        products_dal.create_product(
            cur, tenant_id="t", workspace_client_id=1, fields={"name_th": "A"}
        )
        self.assertFalse(any("is_active = FALSE" in c[0] for c in cur.calls))


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
