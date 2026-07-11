# -*- coding: utf-8 -*-
"""F4 供应商过账档案 DAL 单测(services/purchase/supplier_posting.py)。

钉死:批量 IN 查询按税号索引返回;UPSERT 的 None 字段不覆盖已有值(COALESCE 语义);
correction 不许覆盖已有 user_rule 行,user_rule 可覆盖任意来源(与 expense_learned.learn 同规则);
list_profiles 按 updated_at 倒序 + limit 收口;delete_profile 幂等(删不存在返回 False 不报错)、
两维隔离(WHERE 命中 tenant_id + workspace_client_id,不靠调用方额外过滤)。
"""

import re
import unittest

from services.purchase import supplier_posting as sp

TAX_A = "0105546015062"
TAX_B = "0107561000013"
TAX_C = "0109561000024"


class _FakeCur:
    """够用的假游标:主键 (tenant, ws, seller_tax_id) 内存表 + 逐句判 SQL 分支。"""

    def __init__(self, rows=None):
        self.rows = {(r["tenant_id"], r["ws"], r["seller_tax_id"]): dict(r) for r in (rows or [])}
        self._res: list = []

    def execute(self, sql, params):
        s = " ".join(sql.split())
        if s.startswith("SELECT"):
            tenant_id, ws, tax_ids = params
            self._res = [
                r
                for (t, w, tax), r in self.rows.items()
                if t == tenant_id and w == ws and tax in tax_ids
            ]
        elif s.startswith("INSERT INTO supplier_posting_profiles"):
            tenant_id, ws, tax, payment_val, item_type_val, source, raw_payment, raw_item = params
            key = (tenant_id, ws, tax)
            existing = self.rows.get(key)
            if existing is None:
                self.rows[key] = {
                    "tenant_id": tenant_id,
                    "ws": ws,
                    "seller_tax_id": tax,
                    "default_payment": payment_val,
                    "default_item_type": item_type_val,
                    "source": source,
                }
            elif existing["source"] != "user_rule" or source == "user_rule":
                if raw_payment is not None:
                    existing["default_payment"] = payment_val
                if raw_item is not None:
                    existing["default_item_type"] = item_type_val
                existing["source"] = source
        else:
            raise AssertionError(f"unexpected SQL: {s}")

    def fetchall(self):
        return list(self._res)


class GetProfilesTests(unittest.TestCase):
    def test_batch_lookup_indexed_by_tax_id(self):
        cur = _FakeCur(
            [
                {
                    "tenant_id": "t1",
                    "ws": 1,
                    "seller_tax_id": TAX_A,
                    "default_payment": "cash",
                    "default_item_type": "",
                    "source": "correction",
                },
                {
                    "tenant_id": "t1",
                    "ws": 1,
                    "seller_tax_id": TAX_B,
                    "default_payment": "credit",
                    "default_item_type": "goods",
                    "source": "user_rule",
                },
            ]
        )
        got = sp.get_profiles(cur, tenant_id="t1", workspace_client_id=1, tax_ids=[TAX_A, TAX_B])
        self.assertEqual(set(got), {TAX_A, TAX_B})
        self.assertEqual(got[TAX_A]["default_payment"], "cash")
        self.assertEqual(got[TAX_B]["source"], "user_rule")

    def test_empty_tax_ids_skips_query(self):
        cur = _FakeCur()
        self.assertEqual(
            sp.get_profiles(cur, tenant_id="t1", workspace_client_id=1, tax_ids=[]), {}
        )


class UpsertProfileTests(unittest.TestCase):
    def _get(self, cur, tax=TAX_A):
        return cur.rows.get(("t1", 1, tax))

    def test_first_insert_defaults_missing_fields_to_empty(self):
        cur = _FakeCur()
        sp.upsert_profile(
            cur, tenant_id="t1", workspace_client_id=1, seller_tax_id=TAX_A, default_payment="cash"
        )
        row = self._get(cur)
        self.assertEqual(row["default_payment"], "cash")
        self.assertEqual(row["default_item_type"], "")

    def test_none_field_does_not_overwrite_existing_value(self):
        cur = _FakeCur(
            [
                {
                    "tenant_id": "t1",
                    "ws": 1,
                    "seller_tax_id": TAX_A,
                    "default_payment": "cash",
                    "default_item_type": "goods",
                    "source": "correction",
                }
            ]
        )
        # 只改 item_type,payment 传 None → 保留原值 'cash'
        sp.upsert_profile(
            cur,
            tenant_id="t1",
            workspace_client_id=1,
            seller_tax_id=TAX_A,
            default_item_type="expense",
        )
        row = self._get(cur)
        self.assertEqual(row["default_payment"], "cash")
        self.assertEqual(row["default_item_type"], "expense")

    def test_correction_cannot_override_user_rule(self):
        cur = _FakeCur(
            [
                {
                    "tenant_id": "t1",
                    "ws": 1,
                    "seller_tax_id": TAX_A,
                    "default_payment": "credit",
                    "default_item_type": "",
                    "source": "user_rule",
                }
            ]
        )
        sp.upsert_profile(
            cur,
            tenant_id="t1",
            workspace_client_id=1,
            seller_tax_id=TAX_A,
            default_payment="cash",
            source="correction",
        )
        row = self._get(cur)
        self.assertEqual(row["default_payment"], "credit")  # 纠错没能覆盖用户显式规则
        self.assertEqual(row["source"], "user_rule")

    def test_user_rule_overrides_any_source(self):
        cur = _FakeCur(
            [
                {
                    "tenant_id": "t1",
                    "ws": 1,
                    "seller_tax_id": TAX_A,
                    "default_payment": "credit",
                    "default_item_type": "",
                    "source": "correction",
                }
            ]
        )
        sp.upsert_profile(
            cur,
            tenant_id="t1",
            workspace_client_id=1,
            seller_tax_id=TAX_A,
            default_payment="cash",
            source="user_rule",
        )
        row = self._get(cur)
        self.assertEqual(row["default_payment"], "cash")
        self.assertEqual(row["source"], "user_rule")

    def test_blank_seller_tax_id_is_noop(self):
        cur = _FakeCur()
        sp.upsert_profile(
            cur, tenant_id="t1", workspace_client_id=1, seller_tax_id="", default_payment="cash"
        )
        self.assertEqual(cur.rows, {})


class _ListFakeCur:
    """list_profiles 用假游标:按 tenant+ws 过滤 + updated_at 倒序 + 可选 LIMIT。"""

    def __init__(self, rows):
        self.rows = list(rows)
        self._res: list = []

    def execute(self, sql, params):
        tenant_id, ws = params[0], params[1]
        limit = params[2] if len(params) > 2 else None
        res = [r for r in self.rows if r["tenant_id"] == tenant_id and r["ws"] == ws]
        res.sort(key=lambda r: r["updated_at"], reverse=True)
        self._res = res[:limit] if limit is not None else res

    def fetchall(self):
        return list(self._res)


def _row(tenant_id, ws, tax, updated_at, source="user_rule"):
    return {
        "tenant_id": tenant_id,
        "ws": ws,
        "seller_tax_id": tax,
        "default_payment": "cash",
        "default_item_type": "goods",
        "source": source,
        "updated_at": updated_at,
    }


class ListProfilesTests(unittest.TestCase):
    def test_orders_by_updated_at_desc(self):
        cur = _ListFakeCur(
            [
                _row("t1", 1, TAX_A, 1),
                _row("t1", 1, TAX_B, 3),
                _row("t1", 1, TAX_C, 2),
            ]
        )
        got = sp.list_profiles(cur, tenant_id="t1", workspace_client_id=1)
        self.assertEqual([r["seller_tax_id"] for r in got], [TAX_B, TAX_C, TAX_A])

    def test_limit_caps_result_count(self):
        cur = _ListFakeCur(
            [_row("t1", 1, TAX_A, 1), _row("t1", 1, TAX_B, 3), _row("t1", 1, TAX_C, 2)]
        )
        got = sp.list_profiles(cur, tenant_id="t1", workspace_client_id=1, limit=2)
        self.assertEqual([r["seller_tax_id"] for r in got], [TAX_B, TAX_C])

    def test_tenant_isolation(self):
        cur = _ListFakeCur([_row("t1", 1, TAX_A, 1), _row("t2", 1, TAX_B, 2)])
        got = sp.list_profiles(cur, tenant_id="t1", workspace_client_id=1)
        self.assertEqual([r["seller_tax_id"] for r in got], [TAX_A])

    def test_workspace_isolation_within_same_tenant(self):
        cur = _ListFakeCur([_row("t1", 1, TAX_A, 1), _row("t1", 2, TAX_B, 2)])
        got = sp.list_profiles(cur, tenant_id="t1", workspace_client_id=1)
        self.assertEqual([r["seller_tax_id"] for r in got], [TAX_A])


class _ListWithNamesFakeCur:
    """list_profiles_with_supplier_names 用假游标:模拟 profiles LEFT JOIN suppliers
    按 regexp_replace(非数字剥除) 后的税号比对(与 DAL 的 JOIN 条件同口径)。"""

    def __init__(self, profile_rows, supplier_rows=None):
        self.profile_rows = list(profile_rows)
        self.supplier_rows = list(supplier_rows or [])
        self._res: list = []

    def execute(self, sql, params):
        tenant_id, ws = params[0], params[1]
        limit = params[2] if len(params) > 2 else None
        res = []
        for r in self.profile_rows:
            if r["tenant_id"] != tenant_id or r["ws"] != ws:
                continue
            name = None
            for s in self.supplier_rows:
                clean = re.sub(r"\D", "", s.get("tax_id") or "")
                if s["tenant_id"] == tenant_id and s["ws"] == ws and clean == r["seller_tax_id"]:
                    name = s["name"]
                    break
            row = dict(r)
            row["supplier_name"] = name
            res.append(row)
        res.sort(key=lambda r: r["updated_at"], reverse=True)
        self._res = res[:limit] if limit is not None else res

    def fetchall(self):
        return list(self._res)


class ListProfilesWithSupplierNamesTests(unittest.TestCase):
    def test_matched_supplier_name_attached(self):
        cur = _ListWithNamesFakeCur(
            [_row("t1", 1, TAX_A, 1)],
            [{"tenant_id": "t1", "ws": 1, "tax_id": TAX_A, "name": "冰厂"}],
        )
        got = sp.list_profiles_with_supplier_names(cur, tenant_id="t1", workspace_client_id=1)
        self.assertEqual(got[0]["supplier_name"], "冰厂")

    def test_unmatched_supplier_gives_none_not_error(self):
        cur = _ListWithNamesFakeCur([_row("t1", 1, TAX_A, 1)], [])
        got = sp.list_profiles_with_supplier_names(cur, tenant_id="t1", workspace_client_id=1)
        self.assertIsNone(got[0]["supplier_name"])

    def test_dirty_formatted_supplier_tax_id_still_matches(self):
        # suppliers.tax_id 带分隔符(手录/OCR 落库格式不一)——JOIN 前剥非数字后仍应命中同一行。
        cur = _ListWithNamesFakeCur(
            [_row("t1", 1, TAX_A, 1)],
            [{"tenant_id": "t1", "ws": 1, "tax_id": "010-554-6015-062", "name": "冰厂"}],
        )
        got = sp.list_profiles_with_supplier_names(cur, tenant_id="t1", workspace_client_id=1)
        self.assertEqual(got[0]["supplier_name"], "冰厂")

    def test_cross_tenant_supplier_name_does_not_leak(self):
        # 另一租户同税号同名供应商不得被本租户档案借用(隔离闸)。
        cur = _ListWithNamesFakeCur(
            [_row("t1", 1, TAX_A, 1)],
            [{"tenant_id": "t2", "ws": 1, "tax_id": TAX_A, "name": "别家的冰厂"}],
        )
        got = sp.list_profiles_with_supplier_names(cur, tenant_id="t1", workspace_client_id=1)
        self.assertIsNone(got[0]["supplier_name"])


class _DeleteFakeCur:
    """delete_profile 用假游标:主键匹配才删 · rowcount 反映真删到没有。"""

    def __init__(self, rows):
        self.rows = {(r["tenant_id"], r["ws"], r["seller_tax_id"]): dict(r) for r in rows}
        self.rowcount = 0

    def execute(self, sql, params):
        key = tuple(params)
        if key in self.rows:
            del self.rows[key]
            self.rowcount = 1
        else:
            self.rowcount = 0

    def fetchall(self):
        return []


class DeleteProfileTests(unittest.TestCase):
    def test_deletes_matching_row_returns_true(self):
        cur = _DeleteFakeCur([_row("t1", 1, TAX_A, 1)])
        deleted = sp.delete_profile(cur, tenant_id="t1", workspace_client_id=1, seller_tax_id=TAX_A)
        self.assertTrue(deleted)
        self.assertNotIn(("t1", 1, TAX_A), cur.rows)

    def test_missing_row_is_idempotent_noop(self):
        cur = _DeleteFakeCur([])
        deleted = sp.delete_profile(cur, tenant_id="t1", workspace_client_id=1, seller_tax_id=TAX_A)
        self.assertFalse(deleted)

    def test_repeated_delete_stays_false_second_time(self):
        cur = _DeleteFakeCur([_row("t1", 1, TAX_A, 1)])
        first = sp.delete_profile(cur, tenant_id="t1", workspace_client_id=1, seller_tax_id=TAX_A)
        second = sp.delete_profile(cur, tenant_id="t1", workspace_client_id=1, seller_tax_id=TAX_A)
        self.assertTrue(first)
        self.assertFalse(second)

    def test_wrong_tenant_cannot_delete_other_tenants_row(self):
        cur = _DeleteFakeCur([_row("t1", 1, TAX_A, 1)])
        deleted = sp.delete_profile(cur, tenant_id="t2", workspace_client_id=1, seller_tax_id=TAX_A)
        self.assertFalse(deleted)
        self.assertIn(("t1", 1, TAX_A), cur.rows)

    def test_blank_seller_tax_id_short_circuits(self):
        cur = _DeleteFakeCur([_row("t1", 1, TAX_A, 1)])
        deleted = sp.delete_profile(cur, tenant_id="t1", workspace_client_id=1, seller_tax_id="  ")
        self.assertFalse(deleted)


if __name__ == "__main__":
    unittest.main(verbosity=2)
