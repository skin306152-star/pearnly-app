# -*- coding: utf-8 -*-
"""REFACTOR-D2 覆盖补强 · services/erp/mappings_store.py 数据层行为契约

用假游标截 SQL/params,验证 4 类映射(客户/科目/税码/商品)CRUD 的:
  - erp_type 白名单 / tax_kind 白名单 校验(非法值短路返回 None)。
  - 必填校验、字段长度截断、strip/lower 归一化。
  - 客户映射 upsert 先校验 client 属于 tenant(SELECT 没命中 → None)。
  - restrict_client_ids 三态(None=不限 / [] = 空 / [...] = ANY 过滤)。
  - 商品名归一化 helper、批量查映射、bundle 聚合。
  - 删除走 (id, tenant_id) scope;异常分支吞掉 → 安全默认值。

不触真实 DB / 计费。
"""

import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core import db  # noqa: E402,F401
from services.erp import mappings_store as store  # noqa: E402


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None, rowcount=0, fetchone_seq=None):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []
        self.rowcount = rowcount
        self._fetchone_seq = list(fetchone_seq) if fetchone_seq is not None else None

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        if self._fetchone_seq is not None:
            return self._fetchone_seq.pop(0) if self._fetchone_seq else None
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    @property
    def last_sql(self):
        return self.calls[-1][0] if self.calls else ""

    @property
    def last_params(self):
        return self.calls[-1][1] if self.calls else None

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


class FakeCM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


# list/upsert client mapping 走 get_cursor_rls(穿 tenant);其余 CRUD 仍 get_cursor。两路同挂同一 fake。
def patch_cursor(cur):
    cm = lambda *a, **k: FakeCM(cur)  # noqa: E731

    @contextmanager
    def _both():
        with (
            mock.patch.object(store.db, "get_cursor", cm),
            mock.patch.object(store.db, "get_cursor_rls", cm),
        ):
            yield

    return _both()


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    @contextmanager
    def _both():
        with (
            mock.patch.object(store.db, "get_cursor", factory),
            mock.patch.object(store.db, "get_cursor_rls", factory),
        ):
            yield

    return _both()


# ─────────────────────── 校验常量 + 归一化 helper ───────────────────────
class ConstantsAndNormTests(unittest.TestCase):
    def test_valid_sets(self):
        self.assertIn("xero", store.ERP_TYPES_VALID)
        self.assertIn("mrerp", store.ERP_TYPES_VALID)
        self.assertIn("vat_7", store.PEARNLY_TAX_KINDS_VALID)
        self.assertIn("wht_3", store.PEARNLY_TAX_KINDS_VALID)

    def test_product_norm_strips_punct_and_lowercases(self):
        n = store._product_name_norm_for_db
        self.assertEqual(n("  Hello-World / Co.  "), "helloworldco")
        self.assertEqual(n("A&B (test)"), "abtest")

    def test_product_norm_empty(self):
        self.assertEqual(store._product_name_norm_for_db(""), "")
        self.assertEqual(store._product_name_norm_for_db(None), "")

    def test_product_norm_truncates_256(self):
        self.assertLessEqual(len(store._product_name_norm_for_db("x" * 1000)), 256)


# ─────────────────────── 客户映射 CRUD ───────────────────────
class ListClientMappingsTests(unittest.TestCase):
    def test_no_tenant_empty(self):
        self.assertEqual(store.list_erp_client_mappings(""), [])

    def test_restrict_none_no_any_filter(self):
        cur = FakeCursor(fetchall=[{"id": "m1"}])
        with patch_cursor(cur):
            out = store.list_erp_client_mappings("t1", restrict_client_ids=None)
        self.assertEqual(out, [{"id": "m1"}])
        self.assertNotIn("ANY", cur.last_sql)

    def test_restrict_empty_returns_empty_without_query(self):
        with patch_cursor_raises(AssertionError("no query")):
            self.assertEqual(store.list_erp_client_mappings("t1", restrict_client_ids=[]), [])

    def test_restrict_list_adds_any_filter_and_casts_ints(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            store.list_erp_client_mappings("t1", restrict_client_ids=["5", "6"])
        self.assertIn("m.client_id = ANY(%s)", cur.last_sql)
        # 字符串被转 int
        self.assertEqual(cur.last_params, ["t1", [5, 6]])

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(store.list_erp_client_mappings("t1"), [])


class UpsertClientMappingTests(unittest.TestCase):
    def test_required_fields_none(self):
        self.assertIsNone(store.upsert_erp_client_mapping("", 1, "xero", "C", "n", "u"))
        self.assertIsNone(store.upsert_erp_client_mapping("t1", 1, "xero", "", "n", "u"))

    def test_invalid_erp_type_none(self):
        self.assertIsNone(store.upsert_erp_client_mapping("t1", 1, "sap", "C", "n", "u"))

    def test_client_not_in_tenant_returns_none(self):
        # 第一次 fetchone(ownership check)→ None → 直接返回 None,不 INSERT
        cur = FakeCursor(fetchone_seq=[None])
        with patch_cursor(cur):
            out = store.upsert_erp_client_mapping("t1", 99, "xero", "C", "n", "u")
        self.assertIsNone(out)
        self.assertNotIn("INSERT INTO erp_client_mappings", cur.all_sql())

    def test_happy_path_returns_id(self):
        # ownership check 命中,然后 INSERT RETURNING id
        cur = FakeCursor(fetchone_seq=[{"?": 1}, {"id": "m-new"}])
        with patch_cursor(cur):
            out = store.upsert_erp_client_mapping("t1", 5, "XERO", " C001 ", "note", "u1")
        self.assertEqual(out, "m-new")
        # erp_type 被 lower;erp_code 被 strip
        insert_call = [c for c in cur.calls if "INSERT INTO erp_client_mappings" in c[0]][0]
        self.assertIn("xero", insert_call[1])
        self.assertIn("C001", insert_call[1])

    def test_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(store.upsert_erp_client_mapping("t1", 5, "xero", "C", "n", "u"))


class DeleteClientMappingTests(unittest.TestCase):
    def test_missing_args_false(self):
        self.assertFalse(store.delete_erp_client_mapping("", "m1"))
        self.assertFalse(store.delete_erp_client_mapping("t1", ""))

    def test_scoped_delete_true(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(store.delete_erp_client_mapping("t1", "m1"))
        self.assertIn("id = %s AND tenant_id = %s", cur.last_sql)
        self.assertEqual(cur.last_params, ("m1", "t1"))

    def test_rowcount_zero_false(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(store.delete_erp_client_mapping("t1", "m1"))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(store.delete_erp_client_mapping("t1", "m1"))


# ─────────────────────── 科目映射 CRUD ───────────────────────
class AccountMappingTests(unittest.TestCase):
    def test_list_no_tenant_empty(self):
        self.assertEqual(store.list_erp_account_mappings(""), [])

    def test_list_returns_rows(self):
        cur = FakeCursor(fetchall=[{"id": "a1"}])
        with patch_cursor(cur):
            self.assertEqual(store.list_erp_account_mappings("t1"), [{"id": "a1"}])
        self.assertEqual(cur.last_params, ("t1",))

    def test_upsert_invalid_erp_type_none(self):
        self.assertIsNone(store.upsert_erp_account_mapping("t1", "bad", "cat", "C", "N", "n", "u"))

    def test_upsert_missing_cat_or_code_none(self):
        # category 空白 → 校验后 cat="" → None
        self.assertIsNone(store.upsert_erp_account_mapping("t1", "xero", "  ", "C", "N", "n", "u"))
        self.assertIsNone(
            store.upsert_erp_account_mapping("t1", "xero", "cat", "  ", "N", "n", "u")
        )

    def test_upsert_happy(self):
        cur = FakeCursor(fetchone={"id": "a-new"})
        with patch_cursor(cur):
            out = store.upsert_erp_account_mapping(
                "t1", "Xero", "rent", "4000", "Rent", "note", "u1"
            )
        self.assertEqual(out, "a-new")
        self.assertIn("xero", cur.last_params)

    def test_upsert_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(
                store.upsert_erp_account_mapping("t1", "xero", "c", "C", "N", "n", "u")
            )

    def test_delete_scoped(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(store.delete_erp_account_mapping("t1", "a1"))
        self.assertEqual(cur.last_params, ("a1", "t1"))

    def test_delete_missing_args_false(self):
        self.assertFalse(store.delete_erp_account_mapping("", "a1"))


# ─────────────────────── 税码映射 CRUD ───────────────────────
class TaxMappingTests(unittest.TestCase):
    def test_list_no_tenant_empty(self):
        self.assertEqual(store.list_erp_tax_mappings(""), [])

    def test_upsert_invalid_tax_kind_none(self):
        # erp_type 合法但 tax_kind 不在白名单
        self.assertIsNone(store.upsert_erp_tax_mapping("t1", "xero", "vat_99", "C", "n", "u"))

    def test_upsert_invalid_erp_type_none(self):
        self.assertIsNone(store.upsert_erp_tax_mapping("t1", "bad", "vat_7", "C", "n", "u"))

    def test_upsert_empty_code_none(self):
        self.assertIsNone(store.upsert_erp_tax_mapping("t1", "xero", "vat_7", "  ", "n", "u"))

    def test_upsert_happy(self):
        cur = FakeCursor(fetchone={"id": "tx-new"})
        with patch_cursor(cur):
            out = store.upsert_erp_tax_mapping("t1", "xero", "vat_7", "OUTPUT2", "n", "u1")
        self.assertEqual(out, "tx-new")
        self.assertIn("vat_7", cur.last_params)

    def test_upsert_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(store.upsert_erp_tax_mapping("t1", "xero", "vat_7", "C", "n", "u"))

    def test_delete_scoped(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(store.delete_erp_tax_mapping("t1", "tx1"))
        self.assertEqual(cur.last_params, ("tx1", "t1"))


# ─────────────────────── 商品映射 CRUD ───────────────────────
class ProductMappingTests(unittest.TestCase):
    def test_list_no_tenant_empty(self):
        self.assertEqual(store.list_erp_product_mappings(""), [])

    def test_list_all_vs_single_erp(self):
        cur = FakeCursor(fetchall=[{"id": "p1"}])
        with patch_cursor(cur):
            store.list_erp_product_mappings("t1")
        self.assertEqual(cur.last_params, ("t1",))
        cur2 = FakeCursor(fetchall=[])
        with patch_cursor(cur2):
            store.list_erp_product_mappings("t1", erp_type="XERO")
        # erp_type 被 lower
        self.assertEqual(cur2.last_params, ("t1", "xero"))

    def test_upsert_invalid_erp_type_none(self):
        self.assertIsNone(store.upsert_erp_product_mapping("t1", "bad", "item", "C", "N", "n", "u"))

    def test_upsert_empty_norm_none(self):
        # item_name 全是会被归一化抹掉的标点 → norm 空 → None
        self.assertIsNone(
            store.upsert_erp_product_mapping("t1", "xero", "  -- // ", "C", "N", "n", "u")
        )

    def test_upsert_empty_code_none(self):
        self.assertIsNone(
            store.upsert_erp_product_mapping("t1", "xero", "Widget", "  ", "N", "n", "u")
        )

    def test_upsert_happy_includes_norm(self):
        cur = FakeCursor(fetchone={"id": "p-new"})
        with patch_cursor(cur):
            out = store.upsert_erp_product_mapping(
                "t1", "xero", "Widget-A", "WID1", "Widget A", "note", "u1"
            )
        self.assertEqual(out, "p-new")
        # 归一化形式进 params
        self.assertIn("widgeta", cur.last_params)

    def test_upsert_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(
                store.upsert_erp_product_mapping("t1", "xero", "W", "C", "N", "n", "u")
            )

    def test_delete_scoped(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(store.delete_erp_product_mapping("t1", "p1"))
        self.assertEqual(cur.last_params, ("p1", "t1"))

    def test_delete_missing_args_false(self):
        self.assertFalse(store.delete_erp_product_mapping("t1", ""))


class FindProductMappingsBatchTests(unittest.TestCase):
    def test_missing_args_empty_dict(self):
        self.assertEqual(store.find_erp_product_mappings_batch("", "xero", ["a"]), {})
        self.assertEqual(store.find_erp_product_mappings_batch("t1", "", ["a"]), {})
        self.assertEqual(store.find_erp_product_mappings_batch("t1", "xero", []), {})

    def test_all_norms_empty_returns_empty(self):
        # 全是会被归一化抹空的名字 → norms 空 → {} (不查 DB)
        with patch_cursor_raises(AssertionError("no query")):
            self.assertEqual(
                store.find_erp_product_mappings_batch("t1", "xero", ["  --  ", "//"]),
                {},
            )

    def test_returns_keyed_by_norm(self):
        cur = FakeCursor(
            fetchall=[
                {
                    "item_name": "Widget A",
                    "item_name_norm": "widgeta",
                    "erp_code": "WID1",
                    "erp_name": "Widget A",
                }
            ]
        )
        with patch_cursor(cur):
            out = store.find_erp_product_mappings_batch("t1", "XERO", ["Widget-A"])
        self.assertIn("widgeta", out)
        self.assertEqual(out["widgeta"]["erp_code"], "WID1")
        # erp_type lower + norms 进 params
        self.assertEqual(cur.last_params[1], "xero")
        self.assertEqual(cur.last_params[2], ["widgeta"])

    def test_null_erp_name_becomes_empty_string(self):
        cur = FakeCursor(
            fetchall=[
                {
                    "item_name": "X",
                    "item_name_norm": "x",
                    "erp_code": "C",
                    "erp_name": None,
                }
            ]
        )
        with patch_cursor(cur):
            out = store.find_erp_product_mappings_batch("t1", "xero", ["X"])
        self.assertEqual(out["x"]["erp_name"], "")

    def test_exception_empty_dict(self):
        with patch_cursor_raises():
            self.assertEqual(store.find_erp_product_mappings_batch("t1", "xero", ["X"]), {})


class MrerpBundleTests(unittest.TestCase):
    def test_no_tenant_empty_shape(self):
        out = store.get_mrerp_mappings_bundle("")
        self.assertEqual(out, {"clients": [], "accounts": [], "taxes": [], "products": []})

    def test_aggregates_four_lists(self):
        with (
            mock.patch.object(store, "list_erp_client_mappings", return_value=[{"c": 1}]),
            mock.patch.object(store, "list_erp_account_mappings", return_value=[{"a": 1}]),
            mock.patch.object(store, "list_erp_tax_mappings", return_value=[{"t": 1}]),
            mock.patch.object(store, "list_erp_product_mappings", return_value=[{"p": 1}]),
        ):
            out = store.get_mrerp_mappings_bundle("t1")
        self.assertEqual(out["clients"], [{"c": 1}])
        self.assertEqual(out["accounts"], [{"a": 1}])
        self.assertEqual(out["taxes"], [{"t": 1}])
        self.assertEqual(out["products"], [{"p": 1}])

    def test_exception_returns_empty_shape(self):
        with mock.patch.object(store, "list_erp_client_mappings", side_effect=RuntimeError("x")):
            out = store.get_mrerp_mappings_bundle("t1")
        self.assertEqual(out, {"clients": [], "accounts": [], "taxes": [], "products": []})


if __name__ == "__main__":
    unittest.main()
