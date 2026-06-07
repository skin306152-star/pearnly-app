# -*- coding: utf-8 -*-
"""POS 小票升级正式税票纯逻辑守门测试(POS 项目 · PO-B4)。

不连库的纯逻辑:买方块映射(party_type→type · head→hq)、开票日期解析、已升级/不存在的
短路防呆、回填 UPDATE 的参数化形状。建草稿/取连号/冻结的重流程由 _e2e_po_b4 真库覆盖。"""

import unittest
from datetime import datetime, timezone

from core.pos_api import PosError
from services.pos import sales_store, upgrade


class _Cur:
    def __init__(self, ones=None):
        self.calls = []
        self._ones = list(ones or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None

    def fetchall(self):
        return []


class BuyerMappingTests(unittest.TestCase):
    def test_party_type_and_branch_mapping(self):
        b = upgrade._to_buyer(
            {
                "party_type": "company",
                "name": "ACME",
                "tax_id": "0105556000001",
                "branch_type": "head",
                "branch_no": "00000",
                "address": "BKK",
            }
        )
        self.assertEqual(b["type"], "company")
        self.assertEqual(b["branch_type"], "hq")  # head → hq
        self.assertEqual(b["name"], "ACME")

    def test_defaults_to_company(self):
        b = upgrade._to_buyer(None)
        self.assertEqual(b["type"], "company")
        self.assertIsNone(b["name"])

    def test_branch_value_passthrough(self):
        b = upgrade._to_buyer({"party_type": "individual", "branch_type": "branch"})
        self.assertEqual(b["type"], "individual")
        self.assertEqual(b["branch_type"], "branch")


class IssueDateTests(unittest.TestCase):
    def test_datetime_to_utc_date(self):
        d = upgrade._resolve_issue_date(datetime(2026, 6, 7, 23, 30, tzinfo=timezone.utc))
        self.assertEqual(d.isoformat(), "2026-06-07")

    def test_none_falls_back_to_today(self):
        d = upgrade._resolve_issue_date(None)
        self.assertEqual(d.year >= 2026, True)


class GuardTests(unittest.TestCase):
    def test_not_found_raises_404(self):
        cur = _Cur(ones=[None])  # get_sale → None
        with self.assertRaises(PosError) as ctx:
            upgrade.upgrade_to_full_tax_invoice(
                cur, tenant_id="t", workspace_client_id=9, sale_id="s", buyer={}
            )
        self.assertEqual(ctx.exception.http_status, 404)

    def test_already_upgraded_raises_409(self):
        sale = {
            "id": "s",
            "sale_type": "sale",
            "status": "completed",
            "full_invoice_id": "doc-1",
        }
        cur = _Cur(ones=[sale])
        with self.assertRaises(PosError) as ctx:
            upgrade.upgrade_to_full_tax_invoice(
                cur, tenant_id="t", workspace_client_id=9, sale_id="s", buyer={}
            )
        self.assertEqual(ctx.exception.code, "pos.already_upgraded")
        self.assertEqual(ctx.exception.http_status, 409)

    def test_void_sale_not_upgradable(self):
        sale = {"id": "s", "sale_type": "sale", "status": "void", "full_invoice_id": None}
        cur = _Cur(ones=[sale])
        with self.assertRaises(PosError) as ctx:
            upgrade.upgrade_to_full_tax_invoice(
                cur, tenant_id="t", workspace_client_id=9, sale_id="s", buyer={}
            )
        self.assertEqual(ctx.exception.http_status, 404)


class BackfillTests(unittest.TestCase):
    def test_set_full_invoice_id_parameterized_with_tenant(self):
        cur = _Cur()
        sales_store.set_full_invoice_id(cur, tenant_id="t", sale_id="s", doc_id="doc-1")
        self.assertEqual(len(cur.calls), 1)
        sql, params = cur.calls[0]
        self.assertIn("UPDATE pos_sales SET full_invoice_id", sql)
        self.assertIn("WHERE tenant_id = %s AND id = %s", sql)
        self.assertEqual(params, ("doc-1", "t", "s"))


if __name__ == "__main__":
    unittest.main()
