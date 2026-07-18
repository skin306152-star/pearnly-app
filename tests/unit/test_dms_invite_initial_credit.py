# -*- coding: utf-8 -*-
"""波1 · DMS 计费搬家后的余额闸钱路径契约(不碰真库)。

发号侧不再送额度(见 test_admin_dms_routes_contract),新邀请号开箱余额 0 → 身份证识别被
余额闸 402 恒拦;老板须进 /dms 门户「套餐与余额」页自助充值(topup)或订阅套餐才放行。
两段锁死这条搬家后的链路:
  1. grant_credits(canonical 记账口 · 现由 topup / 超管审核走)· 加余额 + 落
     credit_transactions 台账行,Decimal 计价,不手写裸 UPDATE 余额(铁律 #26)。
  2. get_billing_status_combined:余额 0 + 无订阅 → allowed=False(insufficient_balance);
     充值到正额后 → allowed=True。老板自助补齐余额 → 本闸开,链路闭合。
psycopg2 打桩(charge/account_status 顶/尾 import core.db 会拉起连接池)。
"""

from __future__ import annotations

import sys
import types
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

if "psycopg2" not in sys.modules:
    fake_pg = types.ModuleType("psycopg2")
    fake_pg.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("stub"))
    fake_pg.Error = Exception
    fake_pg.OperationalError = Exception
    fake_pg.extras = types.ModuleType("psycopg2.extras")
    fake_pg.extras.RealDictCursor = object
    fake_pg.extras.DictCursor = object
    fake_pg.extras.execute_values = lambda *a, **k: None
    fake_pg.extras.Json = lambda x: x
    fake_pg.pool = types.ModuleType("psycopg2.pool")

    class _StubPool:
        def __init__(self, *a, **k):
            pass

        def getconn(self):
            raise RuntimeError("stub")

        def putconn(self, *a, **k):
            pass

        def closeall(self):
            pass

    fake_pg.pool.ThreadedConnectionPool = _StubPool
    fake_pg.pool.SimpleConnectionPool = _StubPool
    fake_pg.sql = types.ModuleType("psycopg2.sql")
    fake_pg.sql.SQL = lambda s: s
    fake_pg.sql.Identifier = lambda s: s
    sys.modules["psycopg2"] = fake_pg
    sys.modules["psycopg2.extras"] = fake_pg.extras
    sys.modules["psycopg2.pool"] = fake_pg.pool
    sys.modules["psycopg2.sql"] = fake_pg.sql


from services.billing import account_status  # noqa: E402
from services.billing import charge  # noqa: E402


class _RecCursor:
    """记录 execute 的 SQL/参数;fetchone 顺序吐预置行。"""

    def __init__(self, fetchone_rows):
        self.executed = []
        self._rows = list(fetchone_rows)

    def execute(self, sql, params=None):
        self.executed.append((sql, list(params) if params else []))

    def fetchone(self):
        return self._rows.pop(0) if self._rows else None


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class GrantCreditsHelperTests(unittest.TestCase):
    """canonical「加余额」记账口:upsert 余额 + 台账行 · Decimal · 返加后余额。"""

    def _grant(self, **over):
        cur = _RecCursor([{"balance_thb": "300.00"}])
        kwargs = dict(
            tenant_id="t-1",
            user_id="u-1",
            amount_thb=Decimal("150"),
            txn_type="topup",
            description="客户充值到账 · #1001",
        )
        kwargs.update(over)
        ret = charge.grant_credits(cur, **kwargs)
        return cur, ret

    def test_upserts_balance_and_writes_ledger(self):
        cur, ret = self._grant()
        self.assertEqual(len(cur.executed), 2)
        upsert_sql, upsert_params = cur.executed[0]
        self.assertIn("INSERT INTO tenant_credits", upsert_sql)
        self.assertIn("ON CONFLICT", upsert_sql)
        self.assertIn("balance_thb = tenant_credits.balance_thb +", upsert_sql)
        # tenant_id + amount + amount(加值出现两次:INSERT 值 + ON CONFLICT 累加)。
        self.assertEqual(upsert_params, ["t-1", "150", "150"])
        ledger_sql, ledger_params = cur.executed[1]
        self.assertIn("INSERT INTO credit_transactions", ledger_sql)
        self.assertIn("topup", [str(p) for p in ledger_params])
        # balance_after = RETURNING 拿到的加后余额(不是本地算的)。
        self.assertIn("300.00", [str(p) for p in ledger_params])
        self.assertIn("客户充值到账 · #1001", [str(p) for p in ledger_params])

    def test_returns_decimal_post_balance(self):
        _, ret = self._grant()
        self.assertEqual(ret, Decimal("300.00"))
        self.assertIsInstance(ret, Decimal)

    def test_amount_is_decimal_not_float(self):
        # float 输入也归一成 Decimal 字符串(不带 float 噪声)。
        cur, _ = self._grant(amount_thb=150.0)
        self.assertEqual(cur.executed[0][1], ["t-1", "150.0", "150.0"])

    def test_null_user_id_becomes_none(self):
        cur, _ = self._grant(user_id=None)
        # credit_transactions.user_id 参数为 None(而非字符串 "None")。
        self.assertIsNone(cur.executed[1][1][1])


class BillingGateOpensAfterGrantTests(unittest.TestCase):
    """新邀请号开箱余额 0 + 无订阅 → 402;老板自助充值到正额后 → allowed=True(闸放行)。"""

    def _status(self, balance):
        cur = _RecCursor([{"balance_thb": balance, "pages_used": 0, "sub_pages_used": 0}])
        with (
            mock.patch.object(account_status, "is_user_billing_exempt", return_value=False),
            mock.patch.object(account_status.db, "get_cursor_rls", lambda *a, **k: _CM(cur)),
            mock.patch.object(account_status.db, "active_sub_usage_join_sql", lambda *a, **k: ""),
            mock.patch.object(account_status.db, "get_active_subscription", return_value=None),
        ):
            return account_status.get_billing_status_combined("u-1", "t-1")

    def test_granted_balance_allows(self):
        st = self._status(Decimal("150"))
        self.assertTrue(st["allowed"])
        self.assertFalse(st["is_exempt"])
        self.assertEqual(st["balance_thb"], 150.0)

    def test_zero_balance_blocks(self):
        # 新邀请号开箱 0 余额 · 无订阅 → 拦(402 · 需老板自助充值/订阅才放行)。
        st = self._status(Decimal("0"))
        self.assertFalse(st["allowed"])
        self.assertEqual(st["error_code"], "insufficient_balance")


if __name__ == "__main__":
    unittest.main()
