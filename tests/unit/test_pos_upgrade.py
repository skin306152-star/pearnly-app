# -*- coding: utf-8 -*-
"""POS 小票升级正式税票纯逻辑守门测试(POS 项目 · PO-B4)。

不连库的纯逻辑:买方块映射(party_type→type · head→hq)、开票日期解析、已升级/不存在的
短路防呆、回填 UPDATE 的参数化形状。建草稿/取连号/冻结的重流程由 _e2e_po_b4 真库覆盖。"""

import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

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
    """开票日必须按曼谷日历日(固定时刻断言,禁 now();UTC 口径会在 0:00–7:00 窗口错桶)。"""

    def test_bangkok_day_rolls_over_utc_evening(self):
        # UTC 6/7 23:30 = 曼谷 6/8 06:30 → 票面日必须是 6/8(UTC 口径给 6/7 即为 bug)。
        d = upgrade._resolve_issue_date(datetime(2026, 6, 7, 23, 30, tzinfo=timezone.utc))
        self.assertEqual(d.isoformat(), "2026-06-08")

    def test_month_boundary_first_day_before_7am(self):
        # UTC 7/31 17:30 = 曼谷 8/1 00:30 → 归 8 月(旧 UTC 口径盖 7/31:VAT 期错位+月号段错桶)。
        d = upgrade._resolve_issue_date(datetime(2026, 7, 31, 17, 30, tzinfo=timezone.utc))
        self.assertEqual(d.isoformat(), "2026-08-01")

    def test_year_boundary_new_year_before_7am(self):
        # UTC 12/31 18:00 = 曼谷次年 1/1 01:00 → 归新年(旧口径盖 12/31 即跨年错桶)。
        d = upgrade._resolve_issue_date(datetime(2026, 12, 31, 18, 0, tzinfo=timezone.utc))
        self.assertEqual(d.isoformat(), "2027-01-01")

    def test_same_day_inside_bangkok_window(self):
        # 曼谷白天售出(UTC 上午)不跨日:两口径同日,守恒不回归。
        d = upgrade._resolve_issue_date(datetime(2026, 6, 8, 4, 0, tzinfo=timezone.utc))
        self.assertEqual(d.isoformat(), "2026-06-08")

    def test_aware_non_utc_offset_normalized(self):
        # 非 UTC 的 tz-aware(如 +9)也按曼谷折算:东京 8/1 01:30 = 曼谷 7/31 23:30。
        tokyo = timezone(timedelta(hours=9))
        d = upgrade._resolve_issue_date(datetime(2026, 8, 1, 1, 30, tzinfo=tokyo))
        self.assertEqual(d.isoformat(), "2026-07-31")

    def test_naive_treated_as_bangkok_local(self):
        # naive 视为已是曼谷值(同 dates.iso_bangkok 约定),日期原样取。
        d = upgrade._resolve_issue_date(datetime(2026, 8, 1, 0, 30))
        self.assertEqual(d.isoformat(), "2026-08-01")

    def test_none_falls_back_to_bangkok_today(self):
        with patch.object(upgrade, "bangkok_today", return_value=date(2026, 8, 1)):
            d = upgrade._resolve_issue_date(None)
        self.assertEqual(d.isoformat(), "2026-08-01")


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


class SaveBuyerClientTests(unittest.TestCase):
    """买方档存回客户管理:已有档复用不覆盖 · 税号校验位不合法/无操作人不建档。"""

    _BUYER = {
        "type": "company",
        "name": "ACME",
        "address": "BKK",
        "tax_id": "0107544000108",
        "branch_type": "hq",
    }

    def test_existing_client_reused_no_create(self):
        cur = _Cur(ones=[{"id": 77}])
        with patch("core.db.create_client") as create:
            cid = upgrade._save_buyer_client(
                cur, tenant_id="t", created_by="u", buyer=dict(self._BUYER)
            )
        self.assertEqual(cid, 77)
        create.assert_not_called()
        sql, params = cur.calls[0]
        self.assertIn("FROM clients WHERE tenant_id = %s AND tax_id = %s", sql)
        self.assertEqual(params, ("t", "0107544000108"))

    def test_new_client_created_with_buyer_fields(self):
        cur = _Cur(ones=[None])
        with patch("core.db.create_client", return_value=88) as create:
            cid = upgrade._save_buyer_client(
                cur,
                tenant_id="t",
                created_by="u",
                buyer={**self._BUYER, "branch_type": "branch", "branch_no": "00002"},
            )
        self.assertEqual(cid, 88)
        create.assert_called_once_with(
            "u",
            "t",
            "ACME",
            tax_id="0107544000108",
            address="BKK",
            party_type="company",
            branch="00002",
        )

    def test_checksum_invalid_tax_id_not_saved(self):
        cur = _Cur()
        cid = upgrade._save_buyer_client(
            cur, tenant_id="t", created_by="u", buyer={**self._BUYER, "tax_id": "1234567890123"}
        )
        self.assertIsNone(cid)
        self.assertEqual(cur.calls, [])  # 连查重都不查,直接不存

    def test_missing_operator_not_saved(self):
        cid = upgrade._save_buyer_client(
            _Cur(), tenant_id="t", created_by=None, buyer=dict(self._BUYER)
        )
        self.assertIsNone(cid)


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
