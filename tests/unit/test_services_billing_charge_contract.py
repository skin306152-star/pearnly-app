# -*- coding: utf-8 -*-
"""契约测试 · services/billing/charge(REFACTOR-B2)

E2E 闸:spec 11 + spec 16 真账号验过 charge_ocr 钱写入。本契约假游标 mock 验路径分支。
"""

import unittest
from contextlib import contextmanager
from decimal import Decimal
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
    def _gc(*a, **k):
        yield cur

    return _gc


def _all_sql(cur):
    return "\n".join(s for s, _ in cur.executed)


def _params_of(cur, sql_fragment):
    """取第一条含 sql_fragment 的 execute 的参数元组(验写入落值)。"""
    for sql, params in cur.executed:
        if sql_fragment in sql:
            return params
    raise AssertionError(f"no execute matched: {sql_fragment}")


def _quota_row(quota, used, over_rate, in_cycle=True):
    """consume_subscription_quota 锁到的订阅行。"""
    return {
        "quota": quota,
        "pages_used_this_cycle": used,
        "over_rate": Decimal(over_rate),
        "in_cycle": in_cycle,
    }


@contextmanager
def _subscribed(charge, cur):
    """订阅命中 · 假游标 —— _charge_with_subscription 与 consume 都跑真代码。"""
    with (
        mock.patch.object(charge.db, "is_user_billing_exempt", return_value=False),
        mock.patch.object(charge.db, "get_active_subscription", return_value={"plan_code": "M"}),
        mock.patch.object(charge.db, "get_cursor_rls", _ctxmgr(cur)),
    ):
        yield


class ChargeReExportTests(unittest.TestCase):
    def test_db_reexports(self):
        from core import db
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
            mock.patch.object(charge.db, "get_active_subscription", return_value=None),
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
            mock.patch.object(charge.db, "get_active_subscription", return_value=None),
            mock.patch.object(charge.db, "get_cursor_rls", _ctxmgr(cur)),
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


class SubscriptionChargeTests(unittest.TestCase):
    """付费用户的钱路:charge_ocr → _charge_with_subscription。

    套餐内免费不动余额 · 只对超额张数扣 over_rate · 订阅并发失效才回落按量。
    """

    def test_within_quota_is_free_and_skips_balance_write(self):
        from services.billing import charge

        # 剩 90 张 · 来 5 张 → billable=0 → 免费分支只读余额不加写锁
        cur = _FakeCursor(rows=[_quota_row(100, 10, "1.25"), {"b": Decimal("50.00")}, {"id": 4242}])
        with _subscribed(charge, cur):
            r = charge.charge_ocr("u1", "t1", "pdf", 5, history_id="h9")
        self.assertTrue(r["ok"])
        self.assertEqual(r["charged_thb"], 0.0)
        self.assertEqual(r["balance_after"], 50.0)
        self.assertTrue(r["subscription"])
        self.assertEqual(r["quota_pages"], 5)
        self.assertEqual(r["billable_pages"], 0)
        sql = _all_sql(cur)
        self.assertIn("UPDATE tenant_subscriptions SET pages_used_this_cycle", sql)
        self.assertNotIn("UPDATE tenant_credits SET balance_thb", sql)
        self.assertNotIn("monthly_page_usage", sql)  # 套餐用量只记在订阅行上
        # 免费也留一条 0 元 usage 流水 · pages 记全量(免费+超额)
        txn = _params_of(cur, "INSERT INTO credit_transactions")
        self.assertEqual(Decimal(txn[2]), Decimal("0"))
        self.assertEqual(txn[3], 5)
        self.assertIn("套餐内扫描", txn[5])

    def test_overage_charges_only_the_billable_pages(self):
        from services.billing import charge

        # 剩 10 张 · 来 25 张 → 15 张超额 × ฿1.25 = ฿18.75
        cur = _FakeCursor(
            rows=[_quota_row(100, 90, "1.25"), {"balance_thb": "100.00"}, {"id": 555}]
        )
        with _subscribed(charge, cur):
            r = charge.charge_ocr("u1", "t1", "pdf", 25)
        self.assertAlmostEqual(r["charged_thb"], 18.75)
        self.assertAlmostEqual(r["balance_after"], 81.25)
        self.assertEqual(r["billable_pages"], 15)
        self.assertEqual(r["quota_pages"], 25)
        self.assertIn("UPDATE tenant_credits SET balance_thb", _all_sql(cur))
        self.assertEqual(Decimal(_params_of(cur, "UPDATE tenant_credits SET")[0]), Decimal("81.25"))
        txn = _params_of(cur, "INSERT INTO credit_transactions")
        self.assertEqual(Decimal(txn[2]), Decimal("-18.75"))
        self.assertEqual(txn[3], 25)
        self.assertEqual(Decimal(txn[4]), Decimal("81.25"))
        self.assertIn("超额 15", txn[5])

    def test_overage_beyond_balance_goes_negative_not_rejected(self):
        """钉现状:超额扣费没有余额闸 · 与按量一样可扣成负(用量已发生)。"""
        from services.billing import charge

        cur = _FakeCursor(rows=[_quota_row(100, 100, "1.50"), {"balance_thb": "5.00"}, {"id": 1}])
        with _subscribed(charge, cur):
            r = charge.charge_ocr("u1", "t1", "pdf", 10)
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(r["charged_thb"], 15.0)
        self.assertAlmostEqual(r["balance_after"], -10.0)
        self.assertEqual(Decimal(_params_of(cur, "UPDATE tenant_credits SET")[0]), Decimal("-10"))

    def test_missing_credits_row_is_created_before_overage_debit(self):
        from services.billing import charge

        # 余额行不存在 → 先 INSERT 0 行再扣(rows[1]=None 模拟 FOR UPDATE 空)
        cur = _FakeCursor(rows=[_quota_row(50, 50, "1.00"), None, {"balance_thb": "0"}, {"id": 2}])
        with _subscribed(charge, cur):
            r = charge.charge_ocr("u1", "t1", "pdf", 4)
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(r["balance_after"], -4.0)
        self.assertIn("INSERT INTO tenant_credits", _all_sql(cur))

    def test_excel_units_fold_into_quota_pages(self):
        from services.billing import charge

        # 10000 字符 → doc_quota_pages = 2 张 · 额度按张数扣不是按字符
        cur = _FakeCursor(rows=[_quota_row(200, 0, "1.25"), {"b": Decimal("300.00")}, {"id": 77}])
        with _subscribed(charge, cur):
            r = charge.charge_ocr("u1", "t1", "excel", 10000)
        self.assertEqual(r["quota_pages"], 2)
        self.assertEqual(r["billable_pages"], 0)
        self.assertEqual(r["units"], 10000)
        self.assertEqual(_params_of(cur, "UPDATE tenant_subscriptions SET")[0], 2)

    def test_concurrent_expiry_falls_back_to_metered(self):
        from services.billing import charge

        # consume 读到已过期行 → 返 None → charge_ocr 落按量分支
        cur = _FakeCursor(
            rows=[
                _quota_row(100, 0, "1.50", in_cycle=False),
                {"u": 0},
                {"balance_thb": "100.00"},
                {"id": 606},
            ]
        )
        with (
            _subscribed(charge, cur),
            mock.patch.object(charge.db, "estimate_pdf_cost_thb", return_value=Decimal("2.00")),
        ):
            r = charge.charge_ocr("u1", "t1", "pdf", 2)
        self.assertTrue(r["ok"])
        self.assertNotIn("subscription", r)
        self.assertAlmostEqual(r["charged_thb"], 2.0)
        sql = _all_sql(cur)
        self.assertIn("monthly_page_usage", sql)  # 按量分支特征
        self.assertNotIn("UPDATE tenant_subscriptions", sql)  # 失效行不许再累加额度

    def test_subscription_branch_error_does_not_fall_back(self):
        """钉现状:订阅扣费抛错返 ok=False,不静默改走按量(避免双扣)。"""
        from services.billing import charge

        cur = _FakeCursor(rows=[], raise_on_exec=True)
        with _subscribed(charge, cur):
            r = charge.charge_ocr("u1", "t1", "pdf", 3)
        self.assertFalse(r["ok"])
        self.assertIn("simulated DB error", r["error"])
        self.assertNotIn("monthly_page_usage", _all_sql(cur))

    def test_exempt_user_never_reaches_subscription_branch(self):
        from services.billing import charge

        with (
            mock.patch.object(charge.db, "is_user_billing_exempt", return_value=True),
            mock.patch.object(charge.db, "get_active_subscription") as looked_up,
        ):
            r = charge.charge_ocr("u1", "t1", "pdf", 5)
        self.assertTrue(r["exempt"])
        looked_up.assert_not_called()


class SubscriptionRoutingTests(unittest.TestCase):
    """charge_ocr 的分流:get_active_subscription 也跑真代码,只喂行序列。"""

    def test_active_subscription_routes_to_subscription_charge(self):
        from services.billing import charge

        active = {
            "plan_code": "L",
            "status": "active",
            "quota": 500,
            "over_rate": Decimal("1.00"),
            "monthly_fee": Decimal("500"),
            "pages_used_this_cycle": 498,
            "auto_renew": True,
            "cycle_start": None,
            "cycle_end": None,
            "in_cycle": True,
        }
        # 剩 2 张免费 · 来 5 张 → 3 张超额 × ฿1.00
        cur = _FakeCursor(
            rows=[active, _quota_row(500, 498, "1.00"), {"balance_thb": "20.00"}, {"id": 3131}]
        )
        with (
            mock.patch.object(charge.db, "is_user_billing_exempt", return_value=False),
            mock.patch.object(charge.db, "get_cursor_rls", _ctxmgr(cur)),
        ):
            r = charge.charge_ocr("u1", "t1", "pdf", 5)
        self.assertTrue(r["subscription"])
        self.assertEqual(r["billable_pages"], 3)
        self.assertAlmostEqual(r["charged_thb"], 3.0)
        self.assertAlmostEqual(r["balance_after"], 17.0)
        self.assertEqual(r["transaction_id"], 3131)
        self.assertNotIn("monthly_page_usage", _all_sql(cur))

    def test_no_subscription_routes_to_metered(self):
        from services.billing import charge

        cur = _FakeCursor(rows=[None, {"u": 3}, {"balance_thb": "50.00"}, {"id": 8}])
        with (
            mock.patch.object(charge.db, "is_user_billing_exempt", return_value=False),
            mock.patch.object(charge.db, "estimate_pdf_cost_thb", return_value=Decimal("1.00")),
            mock.patch.object(charge.db, "get_cursor_rls", _ctxmgr(cur)),
        ):
            r = charge.charge_ocr("u1", "t1", "pdf", 1)
        self.assertTrue(r["ok"])
        self.assertNotIn("subscription", r)
        sql = _all_sql(cur)
        self.assertIn("monthly_page_usage", sql)
        self.assertNotIn("UPDATE tenant_subscriptions", sql)

    def test_subscription_read_failure_charges_subscriber_by_meter(self):
        """钉现状(⚠️已上报):读订阅表抛错被 get_active_subscription 吞成 None,
        付费用户于是被按量从余额扣钱 —— 月费白付。修掉这个行为时本用例要一起改。
        """
        from services.billing import charge

        calls = {"n": 0}

        @contextmanager
        def _first_read_fails(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:  # get_active_subscription 的读
                raise RuntimeError("subscription read timeout")
            yield cur

        cur = _FakeCursor(rows=[{"u": 0}, {"balance_thb": "300.00"}, {"id": 9}])
        with (
            mock.patch.object(charge.db, "is_user_billing_exempt", return_value=False),
            mock.patch.object(charge.db, "estimate_pdf_cost_thb", return_value=Decimal("3.00")),
            mock.patch.object(charge.db, "get_cursor_rls", _first_read_fails),
        ):
            r = charge.charge_ocr("u1", "t1", "pdf", 2)
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(r["charged_thb"], 3.0)
        self.assertNotIn("subscription", r)
        self.assertIn("monthly_page_usage", _all_sql(cur))


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
