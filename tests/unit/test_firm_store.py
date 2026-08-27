# -*- coding: utf-8 -*-
"""会计事务所 profile DAL 的租户边界契约。"""

from __future__ import annotations

import unittest

from services.firm import store


class Cursor:
    def __init__(self, *, one=None, many=None):
        self.one = one
        self.many = many or []
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.many


class FirmProfileStoreTests(unittest.TestCase):
    def test_create_requires_same_tenant_to_be_firm(self):
        row = {"tenant_id": "tenant-a", "firm_code": "PF00000001"}
        cursor = Cursor(one=row)
        result = store.create_profile(
            cursor,
            tenant_id="tenant-a",
            display_name="A Accounting",
            tax_id="0100000000001",
        )

        sql, params = cursor.calls[0]
        self.assertEqual(result, row)
        self.assertIn("FROM tenants t", sql)
        self.assertIn("t.id = %s::uuid", sql)
        self.assertIn("t.tenant_type_v2 = 'f_firm'", sql)
        self.assertIn("CASE WHEN t.status = 'active' THEN 'active' ELSE 'suspended' END", sql)
        self.assertEqual(params, ("A Accounting", "0100000000001", "tenant-a"))

    def test_create_upsert_never_changes_code_or_tax_id(self):
        cursor = Cursor(one=None)
        store.create_profile(cursor, tenant_id="tenant-a", display_name="Renamed")
        update_clause = cursor.calls[0][0].split("DO UPDATE SET", 1)[1].split("RETURNING", 1)[0]
        self.assertIn("display_name", update_clause)
        self.assertNotIn("firm_code", update_clause)
        self.assertNotIn("tax_id", update_clause)

    def test_get_is_scoped_to_tenant(self):
        cursor = Cursor(one={"tenant_id": "tenant-a"})
        store.get_profile(cursor, tenant_id="tenant-a")
        sql, params = cursor.calls[0]
        self.assertIn("WHERE tenant_id = %s::uuid", sql)
        self.assertEqual(params, ("tenant-a",))

    def test_active_list_requires_and_filters_tenant(self):
        cursor = Cursor(many=[{"tenant_id": "tenant-a"}])
        rows = store.list_active_profiles(cursor, tenant_id="tenant-a")
        sql, params = cursor.calls[0]
        self.assertEqual(rows, [{"tenant_id": "tenant-a"}])
        self.assertIn("p.tenant_id = %s::uuid", sql)
        self.assertIn("p.status = 'active'", sql)
        self.assertIn("t.status = 'active'", sql)
        self.assertEqual(params, ("tenant-a",))

    def test_active_list_cannot_be_called_without_tenant(self):
        with self.assertRaises(TypeError):
            store.list_active_profiles(Cursor())


if __name__ == "__main__":
    unittest.main()
