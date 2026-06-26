# -*- coding: utf-8 -*-
"""B8 RLS wave3 3d 契约:钱写入/读取 DAL 必须穿租户上下文走 get_cursor_rls,且绝不 bypass。

铁律 #26 高敏:tenant_credits / credit_transactions / monthly_page_usage / ocr_cost_log 是钱表。
- charge_ocr / deduct_thb(扣费写入)→ get_cursor_rls(tenant_id=...) · bypass 必须不为 True。
- log_ocr_cost(成本记账写入)→ get_cursor_rls(tenant_id=..., user_id=...)(tenant_or_user)。
- get_billing_status_combined(扣费前余额闸)→ get_cursor_rls(tenant_id=...)。
超管聚合(get_cost_*/get_credits_*)走 owner 的 bare get_cursor(BYPASSRLS 通道),不在本契约内。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

TENANT = "11111111-1111-1111-1111-111111111111"
USER = "22222222-2222-2222-2222-222222222222"


class _Cur:
    def __init__(self, fetchone_seq=None, rowcount=1):
        self._seq = list(fetchone_seq or [])
        self.rowcount = rowcount

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._seq.pop(0) if self._seq else None


def _capture(fetchone_seq=None):
    calls = []

    @contextmanager
    def fake(*args, **kwargs):
        calls.append(kwargs)
        yield _Cur(fetchone_seq=fetchone_seq)

    return calls, fake


def _no_bypass(test, calls):
    test.assertTrue(calls, "未走 get_cursor_rls")
    for c in calls:
        test.assertNotEqual(c.get("bypass"), True, "钱路径绝不能 bypass RLS")


class ChargeRlsContract(unittest.TestCase):
    def test_charge_ocr_excel_threads_tenant_no_bypass(self):
        from services.billing import charge

        # excel 路径:单事务(SELECT FOR UPDATE 余额 → INSERT credit_transactions RETURNING id)。
        calls, fake = _capture(fetchone_seq=[{"balance_thb": "100.00"}, {"id": 1}])
        with (
            mock.patch.object(charge.db, "is_user_billing_exempt", return_value=False),
            mock.patch.object(
                charge.db,
                "estimate_excel_cost_thb",
                return_value=__import__("decimal").Decimal("0.25"),
            ),
            mock.patch.object(charge.db, "get_cursor_rls", fake),
            mock.patch("core.db.get_cursor", side_effect=AssertionError("钱写入禁用 owner 裸游标")),
        ):
            r = charge.charge_ocr(USER, TENANT, "excel", 1000)
        self.assertTrue(r["ok"])
        _no_bypass(self, calls)
        self.assertEqual(calls[0].get("tenant_id"), TENANT)

    def test_deduct_thb_threads_tenant_no_bypass(self):
        from services.billing import charge

        calls, fake = _capture(fetchone_seq=[{"balance_thb": "50.00"}, {"id": 2}])
        with (
            mock.patch.object(charge.db, "is_user_billing_exempt", return_value=False),
            mock.patch.object(charge.db, "get_cursor_rls", fake),
            mock.patch("core.db.get_cursor", side_effect=AssertionError("钱写入禁用 owner 裸游标")),
        ):
            r = charge.deduct_thb(USER, TENANT, 1.0, "rag")
        self.assertTrue(r["ok"])
        _no_bypass(self, calls)
        self.assertEqual(calls[0].get("tenant_id"), TENANT)


class CostLogRlsContract(unittest.TestCase):
    def test_log_ocr_cost_threads_tenant_and_user(self):
        from services.cost import store as cost

        calls, fake = _capture(fetchone_seq=[{"id": 9}])
        with mock.patch.object(cost.db, "get_cursor_rls", fake):
            ok = cost.log_ocr_cost(USER, TENANT, "h1", "gemini", 1, 0, 0, 0.5, 10)
        self.assertTrue(ok)
        _no_bypass(self, calls)
        self.assertEqual(calls[0].get("tenant_id"), TENANT)
        self.assertEqual(calls[0].get("user_id"), USER)


class BillingGateRlsContract(unittest.TestCase):
    def test_billing_status_combined_threads_tenant(self):
        from services.billing import account_status

        account_status._EXEMPT_CACHE[USER] = (False, __import__("time").time() + 300)
        calls, fake = _capture(fetchone_seq=[{"balance_thb": 150, "pages_used": 3}])
        with mock.patch.object(account_status.db, "get_cursor_rls", fake):
            s = account_status.get_billing_status_combined(USER, TENANT)
        self.assertTrue(s["allowed"])
        _no_bypass(self, calls)
        self.assertEqual(calls[0].get("tenant_id"), TENANT)


if __name__ == "__main__":
    unittest.main()
