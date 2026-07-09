# -*- coding: utf-8 -*-
"""F4 供应商过账档案 DAL 单测(services/purchase/supplier_posting.py)。

钉死:批量 IN 查询按税号索引返回;UPSERT 的 None 字段不覆盖已有值(COALESCE 语义);
correction 不许覆盖已有 user_rule 行,user_rule 可覆盖任意来源(与 expense_learned.learn 同规则)。
"""

import unittest

from services.purchase import supplier_posting as sp

TAX_A = "0105546015062"
TAX_B = "0107561000013"


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
