# -*- coding: utf-8 -*-
"""契约测试 · 订阅套餐(services/billing/subscription + pricing)

锁定钱逻辑(铁律 #26):套餐价格常量 / 文档折算 / 额度抵扣拆分 / 超额扣费 /
余额不足不能订阅。DB 路径用假游标验调用序列与分支。
"""

import unittest
from contextlib import contextmanager
from decimal import Decimal
from unittest import mock


class _FakeCursor:
    def __init__(self, rows=None, rowcount=1):
        self._rows = list(rows or [])
        self._idx = 0
        self.rowcount = rowcount
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((str(sql), params))

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


def _sub_row(**over):
    """tenant_subscriptions 行 · 默认 M 套餐已过期(in_cycle=False)。"""
    row = {
        "plan_code": "M",
        "status": "active",
        "quota": 200,
        "over_rate": Decimal("1.25"),
        "monthly_fee": Decimal("250"),
        "pages_used_this_cycle": 30,
        "auto_renew": True,
        "cycle_start": None,
        "cycle_end": None,
        "in_cycle": False,
    }
    row.update(over)
    return row


class PricingPlansLockTests(unittest.TestCase):
    """套餐目录 = Zihao 2026-06-28 拍板值 · 改价必须先改本测试。"""

    def test_plan_specs_locked(self):
        from services.billing.pricing import SUBSCRIPTION_PLANS

        self.assertEqual(SUBSCRIPTION_PLANS["S"]["quota"], 100)
        self.assertEqual(SUBSCRIPTION_PLANS["S"]["fee"], Decimal("150"))
        self.assertEqual(SUBSCRIPTION_PLANS["S"]["over_rate"], Decimal("1.50"))
        self.assertEqual(SUBSCRIPTION_PLANS["M"]["quota"], 200)
        self.assertEqual(SUBSCRIPTION_PLANS["M"]["fee"], Decimal("250"))
        self.assertEqual(SUBSCRIPTION_PLANS["M"]["over_rate"], Decimal("1.25"))
        self.assertEqual(SUBSCRIPTION_PLANS["L"]["quota"], 500)
        self.assertEqual(SUBSCRIPTION_PLANS["L"]["fee"], Decimal("500"))
        self.assertEqual(SUBSCRIPTION_PLANS["L"]["over_rate"], Decimal("1.00"))

    def test_plan_spec_lookup_case_insensitive(self):
        from services.billing.pricing import subscription_plan_spec

        self.assertEqual(subscription_plan_spec("m")["quota"], 200)
        self.assertEqual(subscription_plan_spec(" L ")["quota"], 500)
        self.assertIsNone(subscription_plan_spec("X"))
        self.assertIsNone(subscription_plan_spec(""))
        self.assertIsNone(subscription_plan_spec(None))


class DocQuotaFoldTests(unittest.TestCase):
    """文档字符成本 ÷ ฿1.50 向上取整 = 占额度张数(Zihao 拍板的折算口径)。"""

    def test_zero_chars_zero_pages(self):
        from services.billing.pricing import doc_quota_pages

        self.assertEqual(doc_quota_pages(0), 0)

    def test_10000_chars_is_two_pages(self):
        # 10000 字符 → ฿2.00 按量 → 2.00/1.50 = 1.33 → 2 张
        from services.billing.pricing import doc_quota_pages

        self.assertEqual(doc_quota_pages(10000), 2)

    def test_small_doc_is_one_page(self):
        # 5000 字符 → ฿1.00 → 1.00/1.50 = 0.67 → 1 张
        from services.billing.pricing import doc_quota_pages

        self.assertEqual(doc_quota_pages(5000), 1)

    def test_exact_one_page_boundary(self):
        # 7500 字符 → ฿1.50 → 1.50/1.50 = 1.0 → 1 张
        from services.billing.pricing import doc_quota_pages

        self.assertEqual(doc_quota_pages(7500), 1)


class OverageCostTests(unittest.TestCase):
    def test_zero_billable_zero_cost(self):
        from services.billing.subscription import overage_cost

        self.assertEqual(overage_cost(0, Decimal("1.25")), Decimal("0.00"))

    def test_overage_uses_plan_rate(self):
        from services.billing.subscription import overage_cost

        self.assertEqual(overage_cost(15, Decimal("1.25")), Decimal("18.75"))


class ConsumeQuotaTests(unittest.TestCase):
    """额度抵扣拆分:前面免费抵额度 · 超出才计 billable。"""

    def test_within_quota_no_billable(self):
        from services.billing.subscription import consume_subscription_quota

        cur = _FakeCursor(
            rows=[
                {
                    "quota": 100,
                    "pages_used_this_cycle": 10,
                    "over_rate": Decimal("1.25"),
                    "in_cycle": True,
                }
            ]
        )
        res = consume_subscription_quota(cur, "t1", 5)
        self.assertEqual(res, (0, Decimal("1.25")))
        # 周期用量累加 5(免费部分也计入)
        self.assertIn("pages_used_this_cycle = pages_used_this_cycle +", _all_sql(cur))

    def test_crossing_quota_splits(self):
        from services.billing.subscription import consume_subscription_quota

        # 剩 10 张 · 来 25 张 → 15 张超额
        cur = _FakeCursor(
            rows=[
                {
                    "quota": 100,
                    "pages_used_this_cycle": 90,
                    "over_rate": Decimal("1.25"),
                    "in_cycle": True,
                }
            ]
        )
        billable, rate = consume_subscription_quota(cur, "t1", 25)
        self.assertEqual(billable, 15)
        self.assertEqual(rate, Decimal("1.25"))

    def test_fully_exhausted_all_billable(self):
        from services.billing.subscription import consume_subscription_quota

        cur = _FakeCursor(
            rows=[
                {
                    "quota": 100,
                    "pages_used_this_cycle": 100,
                    "over_rate": Decimal("1.00"),
                    "in_cycle": True,
                }
            ]
        )
        billable, _ = consume_subscription_quota(cur, "t1", 8)
        self.assertEqual(billable, 8)

    def test_no_row_returns_none(self):
        from services.billing.subscription import consume_subscription_quota

        self.assertIsNone(consume_subscription_quota(_FakeCursor(rows=[]), "t1", 5))

    def test_out_of_cycle_returns_none(self):
        from services.billing.subscription import consume_subscription_quota

        cur = _FakeCursor(
            rows=[
                {
                    "quota": 100,
                    "pages_used_this_cycle": 0,
                    "over_rate": Decimal("1.50"),
                    "in_cycle": False,
                }
            ]
        )
        self.assertIsNone(consume_subscription_quota(cur, "t1", 5))


class SubscribeTests(unittest.TestCase):
    def test_insufficient_balance_blocks(self):
        from services.billing import subscription

        cur = _FakeCursor(rows=[{"balance_thb": "100.00"}])  # 余额 100 · L 月费 500
        with mock.patch.object(subscription.db, "get_cursor_rls", _ctxmgr(cur)):
            r = subscription.subscription_subscribe("u1", "t1", "L")
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "insufficient_balance")
        self.assertEqual(r["needed_thb"], 500.0)
        # 余额不足绝不可写 tenant_credits / tenant_subscriptions
        sql = _all_sql(cur)
        self.assertNotIn("UPDATE tenant_credits", sql)
        self.assertNotIn("INSERT INTO tenant_subscriptions", sql)

    def test_unknown_plan_rejected(self):
        from services.billing import subscription

        r = subscription.subscription_subscribe("u1", "t1", "Z")
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "unknown_plan")

    def test_subscribe_success_deducts_and_writes(self):
        from services.billing import subscription

        sub_row = {
            "plan_code": "M",
            "status": "active",
            "quota": 200,
            "over_rate": Decimal("1.25"),
            "monthly_fee": Decimal("250"),
            "pages_used_this_cycle": 0,
            "auto_renew": True,
            "cycle_start": None,
            "cycle_end": None,
        }
        cur = _FakeCursor(rows=[{"balance_thb": "500.00"}, sub_row])
        with mock.patch.object(subscription.db, "get_cursor_rls", _ctxmgr(cur)):
            r = subscription.subscription_subscribe("u1", "t1", "M")
        self.assertTrue(r["ok"])
        self.assertEqual(r["balance_after"], 250.0)  # 500 - 250
        self.assertEqual(r["subscription"]["plan_code"], "M")
        sql = _all_sql(cur)
        self.assertIn("UPDATE tenant_credits", sql)
        self.assertIn("'subscription'", sql)  # 月费流水类型
        self.assertIn("INSERT INTO tenant_subscriptions", sql)


class GetActiveSubscriptionTests(unittest.TestCase):
    def test_in_cycle_returns_sub(self):
        from services.billing import subscription

        row = {
            "plan_code": "S",
            "status": "active",
            "quota": 100,
            "over_rate": Decimal("1.50"),
            "monthly_fee": Decimal("150"),
            "pages_used_this_cycle": 40,
            "auto_renew": True,
            "cycle_start": None,
            "cycle_end": None,
            "in_cycle": True,
        }
        cur = _FakeCursor(rows=[row])
        with mock.patch.object(subscription.db, "get_cursor_rls", _ctxmgr(cur)):
            sub = subscription.get_active_subscription("t1")
        self.assertEqual(sub["plan_code"], "S")
        self.assertEqual(sub["remaining"], 60)

    def test_no_row_returns_none(self):
        from services.billing import subscription

        cur = _FakeCursor(rows=[])
        with mock.patch.object(subscription.db, "get_cursor_rls", _ctxmgr(cur)):
            self.assertIsNone(subscription.get_active_subscription("t1"))

    def test_empty_tenant_returns_none(self):
        from services.billing import subscription

        self.assertIsNone(subscription.get_active_subscription(None))

    def test_cancelled_but_in_cycle_still_active(self):
        """取消 = 到期不再续 · 当前周期额度照用(不能一取消就掉回按量)。"""
        from services.billing import subscription

        cur = _FakeCursor(rows=[_sub_row(status="cancelled", auto_renew=False, in_cycle=True)])
        with mock.patch.object(subscription.db, "get_cursor_rls", _ctxmgr(cur)):
            sub = subscription.get_active_subscription("t1")
        self.assertEqual(sub["status"], "cancelled")
        self.assertEqual(sub["remaining"], 170)
        self.assertNotIn("DELETE", _all_sql(cur))


class RenewOrExpireTests(unittest.TestCase):
    """周期已过后的惰性续订/失效 —— 付费用户扣月费的唯一入口。

    分支矩阵:并发已续 / cancelled / 关自动续订 / 余额不足 / 余额够。
    前四条都不许动 tenant_credits;最后一条必须扣费 + 重置周期。
    """

    def _renew(self, rows):
        from services.billing import subscription

        cur = _FakeCursor(rows=rows)
        with mock.patch.object(subscription.db, "get_cursor_rls", _ctxmgr(cur)):
            return subscription._renew_or_expire("t1"), cur

    def _assert_expired_without_charging(self, out, cur):
        self.assertIsNone(out)
        sql = _all_sql(cur)
        self.assertIn("DELETE FROM tenant_subscriptions", sql)
        self.assertNotIn("UPDATE tenant_credits", sql)
        self.assertNotIn("INSERT INTO credit_transactions", sql)

    def test_no_row_returns_none(self):
        out, cur = self._renew([])
        self.assertIsNone(out)
        self.assertNotIn("DELETE", _all_sql(cur))

    def test_concurrently_renewed_returns_row_without_writes(self):
        out, cur = self._renew([_sub_row(in_cycle=True)])
        self.assertEqual(out["plan_code"], "M")
        self.assertEqual(out["remaining"], 170)
        sql = _all_sql(cur)
        self.assertNotIn("DELETE", sql)
        self.assertNotIn("UPDATE tenant_credits", sql)
        self.assertNotIn("UPDATE tenant_subscriptions", sql)

    def test_cancelled_expires_and_falls_back(self):
        out, cur = self._renew([_sub_row(status="cancelled")])
        self._assert_expired_without_charging(out, cur)

    def test_auto_renew_off_expires_and_falls_back(self):
        out, cur = self._renew([_sub_row(auto_renew=False)])
        self._assert_expired_without_charging(out, cur)

    def test_insufficient_balance_expires_and_falls_back(self):
        # 余额 100 · M 月费 250 → 不够续 → 删行回落按量
        out, cur = self._renew([_sub_row(), {"balance_thb": "100.00"}])
        self._assert_expired_without_charging(out, cur)

    def test_missing_credits_row_counts_as_zero_balance(self):
        # tenant_credits 无行 → 视作 0 元 → 失效(不建行 · 不扣负)
        out, cur = self._renew([_sub_row()])
        self._assert_expired_without_charging(out, cur)

    def test_sufficient_balance_renews_and_resets_cycle(self):
        renewed = _sub_row(pages_used_this_cycle=0, in_cycle=True)
        out, cur = self._renew([_sub_row(), {"balance_thb": "600.00"}, renewed])
        self.assertEqual(out["plan_code"], "M")
        self.assertEqual(out["pages_used_this_cycle"], 0)
        self.assertEqual(out["remaining"], 200)
        sql = _all_sql(cur)
        self.assertNotIn("DELETE", sql)
        self.assertIn("UPDATE tenant_credits SET balance_thb", sql)
        self.assertIn("pages_used_this_cycle = 0", sql)
        self.assertIn("make_interval(days =>", sql)
        # 600 - 250 = 350 · 余额与流水 balance_after 必须同值
        self.assertEqual(Decimal(_params_of(cur, "UPDATE tenant_credits")[0]), Decimal("350"))
        txn = _params_of(cur, "INSERT INTO credit_transactions")
        self.assertEqual(Decimal(txn[1]), Decimal("-250"))
        self.assertEqual(Decimal(txn[2]), Decimal("350"))
        self.assertIn("Package M", txn[3])

    def test_renewal_uses_configured_cycle_days(self):
        from services.billing.pricing import SUBSCRIPTION_CYCLE_DAYS

        renewed = _sub_row(pages_used_this_cycle=0, in_cycle=True)
        _, cur = self._renew([_sub_row(), {"balance_thb": "600.00"}, renewed])
        self.assertEqual(_params_of(cur, "UPDATE tenant_subscriptions")[0], SUBSCRIPTION_CYCLE_DAYS)

    def test_db_error_returns_none(self):
        from services.billing import subscription

        @contextmanager
        def _boom(*a, **k):
            raise RuntimeError("db down")
            yield  # pragma: no cover

        with mock.patch.object(subscription.db, "get_cursor_rls", _boom):
            self.assertIsNone(subscription._renew_or_expire("t1"))

    def test_expired_row_routes_from_get_active_subscription(self):
        """接线验证:热路径读到过期行 → 真的进 _renew_or_expire 而不是直接返 None。"""
        from services.billing import subscription

        renewed = _sub_row(pages_used_this_cycle=0, in_cycle=True)
        cur = _FakeCursor(rows=[_sub_row(), _sub_row(), {"balance_thb": "600.00"}, renewed])
        with mock.patch.object(subscription.db, "get_cursor_rls", _ctxmgr(cur)):
            sub = subscription.get_active_subscription("t1")
        self.assertEqual(sub["remaining"], 200)
        self.assertIn("FOR UPDATE", _all_sql(cur))
        self.assertIn("UPDATE tenant_credits SET balance_thb", _all_sql(cur))


class CatalogAndReExportTests(unittest.TestCase):
    def test_catalog_shape(self):
        from services.billing.subscription import subscription_catalog

        cat = subscription_catalog()
        self.assertEqual([p["code"] for p in cat], ["S", "M", "L"])
        self.assertEqual(cat[1], {"code": "M", "quota": 200, "fee": 250.0, "over_rate": 1.25})

    def test_db_reexports(self):
        from core import db
        from services.billing import subscription, pricing

        for name in (
            "get_active_subscription",
            "consume_subscription_quota",
            "overage_cost",
            "subscription_subscribe",
            "subscription_cancel",
            "subscription_catalog",
        ):
            self.assertIs(getattr(db, name), getattr(subscription, name))
        for name in ("subscription_plan_spec", "doc_quota_pages", "SUBSCRIPTION_PLANS"):
            self.assertIs(getattr(db, name), getattr(pricing, name))


if __name__ == "__main__":
    unittest.main()
