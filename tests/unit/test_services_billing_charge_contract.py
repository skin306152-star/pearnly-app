# -*- coding: utf-8 -*-
"""契约测试 · services/billing/charge(REFACTOR-B2)

E2E 闸:spec 11 + spec 16 真账号验过 charge_ocr 钱写入。本契约假游标 mock 验路径分支。
"""

import unittest
from contextlib import contextmanager
from unittest import mock


class _FakeCursor:
    def __init__(self, rows=None, raise_on_exec=False):
        # rows 是按 execute 顺序返的列表 · 每个 fetchone 拿下一个
        self._rows = list(rows or [])
        self._idx = 0
        self._raise = raise_on_exec
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self._raise:
            raise RuntimeError("simulated DB error")

    def fetchone(self):
        if self._idx < len(self._rows):
            r = self._rows[self._idx]
            self._idx += 1
            return r
        return None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ctxmgr(cur):
    @contextmanager
    def _gc(commit=False):
        yield cur

    return _gc


class ChargeReExportTests(unittest.TestCase):
    def test_db_reexports(self):
        import db
        from services.billing import charge

        for name in ("charge_ocr", "_excel_char_count_estimate", "charge_ocr_async"):
            self.assertTrue(hasattr(charge, name))
            self.assertIs(getattr(db, name), getattr(charge, name))


class ChargeOcrBranchTests(unittest.TestCase):
    def test_no_tenant_returns_error(self):
        from services.billing import charge

        r = charge.charge_ocr("u1", None, "pdf", 1)
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "no_tenant")

    def test_exempt_user_returns_ok_zero_no_db_write(self):
        from services.billing import charge

        with mock.patch.object(charge.db, "is_user_billing_exempt", return_value=True):
            r = charge.charge_ocr("u1", "t1", "pdf", 5, history_id="h1")
        self.assertTrue(r["ok"])
        self.assertEqual(r["charged_thb"], 0.0)
        self.assertTrue(r["exempt"])

    def test_unknown_kind_returns_error(self):
        from services.billing import charge

        with mock.patch.object(charge.db, "is_user_billing_exempt", return_value=False):
            r = charge.charge_ocr("u1", "t1", "bogus", 5)
        self.assertFalse(r["ok"])
        self.assertIn("unknown_kind:bogus", r["error"])

    def test_zero_cost_returns_ok_no_db_write(self):
        """0 字符 Excel → cost=0 → 不应写流水"""
        from services.billing import charge

        with (
            mock.patch.object(charge.db, "is_user_billing_exempt", return_value=False),
            mock.patch.object(charge.db, "estimate_excel_cost_thb", return_value=0),
        ):
            r = charge.charge_ocr("u1", "t1", "excel", 0)
        self.assertTrue(r["ok"])
        self.assertEqual(r["charged_thb"], 0.0)

    def test_excel_happy_path_charges(self):
        from services.billing import charge

        # rows 按 fetchone 顺序返(UPDATE 不 fetchone · 跳过):
        #  1) FOR UPDATE balance_thb → fetchone 100
        #  2) UPDATE tenant_credits SET balance → 不 fetchone(跳)
        #  3) INSERT credit_transactions RETURNING id → fetchone 7777
        cur = _FakeCursor(rows=[{"balance_thb": "100.00"}, {"id": 7777}])
        from decimal import Decimal

        with (
            mock.patch.object(charge.db, "is_user_billing_exempt", return_value=False),
            mock.patch.object(charge.db, "estimate_excel_cost_thb", return_value=Decimal("0.25")),
            mock.patch.object(charge.db, "get_cursor", _ctxmgr(cur)),
        ):
            r = charge.charge_ocr("u1", "t1", "excel", 1000, description="test")
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(r["charged_thb"], 0.25)
        self.assertAlmostEqual(r["balance_after"], 99.75)
        self.assertEqual(r["transaction_id"], 7777)
        # 验执行了 SELECT FOR UPDATE + UPDATE + INSERT(无 monthly_page_usage UPSERT · 因为 excel)
        sqls = [e[0] for e in cur.executed]
        self.assertTrue(any("FOR UPDATE" in s for s in sqls))
        self.assertTrue(any("UPDATE tenant_credits SET balance_thb" in s for s in sqls))
        self.assertTrue(any("INSERT INTO credit_transactions" in s for s in sqls))
        self.assertFalse(any("monthly_page_usage" in s for s in sqls))


class ExcelCharCountTests(unittest.TestCase):
    def test_empty_bytes_returns_zero(self):
        from services.billing.charge import _excel_char_count_estimate

        self.assertEqual(_excel_char_count_estimate(b"", "any.xlsx"), 0)
        self.assertEqual(_excel_char_count_estimate(None, "any.xlsx"), 0)

    def test_csv_decode_path(self):
        from services.billing.charge import _excel_char_count_estimate

        content = b"a,b,c\n1,2,3\n"
        self.assertEqual(_excel_char_count_estimate(content, "x.csv"), len(content))
        self.assertEqual(_excel_char_count_estimate(content, "x.tsv"), len(content))
        self.assertEqual(_excel_char_count_estimate(content, "x.txt"), len(content))

    def test_xlsx_invalid_bytes_falls_back_to_byte_estimate(self):
        from services.billing.charge import _excel_char_count_estimate

        # openpyxl 加载假 xlsx 字节会抛 → 降级 len(file_bytes)//4
        bogus = b"\x00" * 400
        n = _excel_char_count_estimate(bogus, "x.xlsx")
        self.assertEqual(n, 100)  # 400//4

    def test_unknown_extension_returns_zero(self):
        from services.billing.charge import _excel_char_count_estimate

        self.assertEqual(_excel_char_count_estimate(b"data", "x.unknown"), 0)


class ChargeOcrAsyncTests(unittest.TestCase):
    def test_wraps_charge_ocr_returns_none(self):
        from services.billing import charge

        with mock.patch.object(charge, "charge_ocr", return_value={"ok": True}):
            ret = charge.charge_ocr_async("u1", "t1", "pdf", 1)
        self.assertIsNone(ret)

    def test_swallows_exception(self):
        from services.billing import charge

        with mock.patch.object(charge, "charge_ocr", side_effect=RuntimeError("boom")):
            # 不抛 · log 即可
            ret = charge.charge_ocr_async("u1", "t1", "pdf", 1)
        self.assertIsNone(ret)

    def test_logs_warning_on_failure(self):
        from services.billing import charge

        with (
            mock.patch.object(charge, "charge_ocr", return_value={"ok": False, "error": "bad"}),
            mock.patch.object(charge.logger, "warning") as warned,
        ):
            charge.charge_ocr_async("u1", "t1", "pdf", 1)
        warned.assert_called_once()


if __name__ == "__main__":
    unittest.main()
