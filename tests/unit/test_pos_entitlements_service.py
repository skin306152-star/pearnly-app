# -*- coding: utf-8 -*-
"""services/pos/entitlements 状态机 + 上限执行 + 审计契约(不连库 · 状态化 FakeCursor)。PS-3。

覆盖验收:①grant 写行 + credit_transactions pos_buyout 审计 + balance 未动 + 联动 pos_only 业态;
②持授权卡上限(店/收银员)· 第 1 店/第 3 收银员放行、超出拦;③无授权零影响;④revoke/transfer
状态机不许非法跳转 + 留审计。apply_preset 打桩(只验被以 pos_only 调用,不测其内部)。"""

import unittest
from unittest import mock

from services.pos import entitlements as ent


class StatefulCursor:
    """按 SQL 子串分派的状态化游标:持一份 pos_entitlements 内存态,支持 grant/revoke/transfer/查询。

    可配置:store_count / ws_has_store / cashier_count / balance。记录 credit_transactions 插入
    与所有 UPDATE 语句,供断言(尤其:绝不 UPDATE tenant_credits.balance)。
    """

    def __init__(self, *, store_count=0, ws_has_store=False, cashier_count=0, balance="500.00"):
        self.rows = {}  # tenant_id -> entitlement dict
        self.store_count = store_count
        self.ws_has_store = ws_has_store
        self.cashier_count = cashier_count
        self.balance = balance
        self.credit_tx = []  # (type, amount, balance_after)
        self.executed = []  # 全部 (sql, params)
        self._last = None  # 待 fetchone 返回值

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        s = " ".join(sql.split())
        self._last = self._dispatch(s, params or ())

    def _dispatch(self, s, p):
        if "FROM pos_entitlements WHERE grant_code" in s:
            return None  # 授权码唯一探测:恒不撞
        if "count(*) AS n FROM pos_store_codes" in s:
            return {"n": self.store_count}
        if "FROM pos_store_codes WHERE tenant_id" in s and "workspace_client_id" in s:
            return {"1": 1} if self.ws_has_store else None
        if "count(*) AS n FROM pos_cashiers" in s:
            return {"n": self.cashier_count}
        if "FROM tenant_credits" in s:
            return {"b": self.balance}
        if "INSERT INTO credit_transactions" in s:
            # params: (tenant, user, type, amount, balance_after, note)
            self.credit_tx.append((p[2], p[3], p[4]))
            return None
        if "SELECT" in s and "FROM pos_entitlements WHERE tenant_id" in s:
            tid = str(p[0])
            row = self.rows.get(tid)
            if row and "AND status = 'active'" in s and row["status"] != "active":
                return None
            return dict(row) if row else None
        if "INSERT INTO pos_entitlements" in s:
            return self._upsert(s, p)
        if "UPDATE pos_entitlements SET status = 'revoked'" in s:
            tid = str(p[-1])
            self.rows[tid].update(status="revoked")
            return dict(self.rows[tid])
        if "UPDATE pos_entitlements SET status = 'transferred'" in s:
            tid = str(p[-1])
            self.rows[tid].update(status="transferred", transferred_to=str(p[0]))
            return None
        return None

    def _upsert(self, s, p):
        # grant:(tid, code, amount, store_limit, cashier_limit, granted_by, note)
        # transfer 落地:(to_tid, code, amount, store_limit, cashier_limit, granted_by, from_tid)
        tid = str(p[0])
        row = {
            "id": 1,
            "tenant_id": tid,
            "grant_code": p[1],
            "amount_paid_thb": p[2],
            "store_limit": int(p[3]),
            "cashier_limit": int(p[4]),
            "status": "active",
            "granted_by": p[5],
            "transferred_from": None,
            "transferred_to": None,
            "revoked_at": None,
            "transferred_at": None,
            "purchased_at": None,
            "note": None,
            "created_at": None,
            "updated_at": None,
        }
        self.rows[tid] = row
        return dict(row)

    def fetchone(self):
        return self._last


class GrantTests(unittest.TestCase):
    def test_grant_writes_row_audits_buyout_and_switches_biztype(self):
        cur = StatefulCursor(balance="500.00")
        with mock.patch("services.modules.presets.apply_preset") as ap:
            row = ent.grant(cur, tenant_id="t1", amount_paid_thb=1000, granted_by="earn")
        # 授权行落地 · active · 带唯一授权码
        self.assertEqual(row["status"], "active")
        self.assertTrue(row["grant_code"].startswith("POS-"))
        # 联动 pos_only 业态(PS-2 外壳)
        ap.assert_called_once()
        self.assertEqual(ap.call_args.kwargs["business_type"], "pos_only")
        # credit_transactions 记一行 pos_buyout · 金额=已付额 · balance_after=当前余额(不动余额)
        self.assertEqual(len(cur.credit_tx), 1)
        typ, amount, bal_after = cur.credit_tx[0]
        self.assertEqual(typ, "pos_buyout")
        self.assertEqual(str(amount), "1000")
        self.assertEqual(str(bal_after), "500.00")
        # 绝不 UPDATE tenant_credits.balance
        self.assertFalse(any("UPDATE tenant_credits" in (sql or "") for sql, _ in cur.executed))

    def test_grant_rejects_double_active(self):
        cur = StatefulCursor()
        cur.rows["t1"] = {"status": "active", "grant_code": "POS-X", "tenant_id": "t1"}
        with mock.patch("services.modules.presets.apply_preset"):
            with self.assertRaises(ValueError) as e:
                ent.grant(cur, tenant_id="t1", amount_paid_thb=1000)
        self.assertIn("already_active", str(e.exception))

    def test_grant_amount_is_decimal_string_not_float(self):
        cur = StatefulCursor()
        with mock.patch("services.modules.presets.apply_preset"):
            ent.grant(cur, tenant_id="t1", amount_paid_thb=1000)
        # 参数化写入用 Decimal 转字符串(禁 float 直塞)
        insert = next(p for sql, p in cur.executed if "INSERT INTO pos_entitlements" in sql)
        self.assertIsInstance(insert[2], str)


class RevokeTransferStateMachineTests(unittest.TestCase):
    def test_revoke_active_ok(self):
        cur = StatefulCursor()
        cur.rows["t1"] = {"status": "active", "grant_code": "POS-A", "tenant_id": "t1"}
        row = ent.revoke(cur, tenant_id="t1", revoked_by="earn")
        self.assertEqual(row["status"], "revoked")

    def test_revoke_non_active_rejected(self):
        cur = StatefulCursor()
        cur.rows["t1"] = {"status": "revoked", "grant_code": "POS-A", "tenant_id": "t1"}
        with self.assertRaises(ValueError) as e:
            ent.revoke(cur, tenant_id="t1")
        self.assertIn("illegal_transition", str(e.exception))

    def test_revoke_missing_rejected(self):
        cur = StatefulCursor()
        with self.assertRaises(ValueError) as e:
            ent.revoke(cur, tenant_id="ghost")
        self.assertIn("not_found", str(e.exception))

    def test_transfer_moves_active_to_target(self):
        cur = StatefulCursor()
        cur.rows["src"] = {
            "status": "active",
            "grant_code": "POS-A",
            "tenant_id": "src",
            "amount_paid_thb": "1000",
            "store_limit": 1,
            "cashier_limit": 3,
        }
        with mock.patch("services.modules.presets.apply_preset") as ap:
            row = ent.transfer(cur, from_tenant_id="src", to_tenant_id="dst", transferred_by="earn")
        self.assertEqual(cur.rows["src"]["status"], "transferred")
        self.assertEqual(row["tenant_id"], "dst")
        self.assertEqual(row["status"], "active")
        self.assertEqual(ap.call_args.kwargs["business_type"], "pos_only")

    def test_transfer_rejects_same_tenant(self):
        cur = StatefulCursor()
        with self.assertRaises(ValueError):
            ent.transfer(cur, from_tenant_id="t", to_tenant_id="t")

    def test_transfer_rejects_inactive_source(self):
        cur = StatefulCursor()
        cur.rows["src"] = {"status": "revoked", "grant_code": "POS-A", "tenant_id": "src"}
        with self.assertRaises(ValueError):
            ent.transfer(cur, from_tenant_id="src", to_tenant_id="dst")

    def test_transfer_rejects_active_target(self):
        cur = StatefulCursor()
        cur.rows["src"] = {
            "status": "active",
            "grant_code": "POS-A",
            "tenant_id": "src",
            "amount_paid_thb": "1000",
            "store_limit": 1,
            "cashier_limit": 3,
        }
        cur.rows["dst"] = {"status": "active", "grant_code": "POS-B", "tenant_id": "dst"}
        with self.assertRaises(ValueError) as e:
            ent.transfer(cur, from_tenant_id="src", to_tenant_id="dst")
        self.assertIn("target_already_active", str(e.exception))


class CheckLimitTests(unittest.TestCase):
    def _entitled(self, cur, store_limit=1, cashier_limit=3):
        cur.rows["t1"] = {
            "status": "active",
            "grant_code": "POS-A",
            "tenant_id": "t1",
            "store_limit": store_limit,
            "cashier_limit": cashier_limit,
            "amount_paid_thb": "1000",
        }

    def test_no_entitlement_never_capped(self):
        cur = StatefulCursor(store_count=99, cashier_count=99)
        res = ent.check_limit(cur, tenant_id="free", workspace_client_id=1, kind="store")
        self.assertFalse(res["entitled"])
        self.assertTrue(res["allowed"])

    def test_store_first_allowed_second_blocked(self):
        cur = StatefulCursor(store_count=0, ws_has_store=False)
        self._entitled(cur)
        first = ent.check_limit(cur, tenant_id="t1", workspace_client_id=1, kind="store")
        self.assertTrue(first["allowed"])
        cur.store_count = 1  # 已有 1 家店,再要新账套的码
        second = ent.check_limit(cur, tenant_id="t1", workspace_client_id=2, kind="store")
        self.assertFalse(second["allowed"])

    def test_store_existing_workspace_idempotent_allowed(self):
        cur = StatefulCursor(store_count=1, ws_has_store=True)  # 本账套已有码
        self._entitled(cur)
        res = ent.check_limit(cur, tenant_id="t1", workspace_client_id=1, kind="store")
        self.assertTrue(res["allowed"])  # 重复取码不算新开店

    def test_cashier_third_allowed_fourth_blocked(self):
        cur = StatefulCursor(cashier_count=2)  # 已有 2 人,建第 3 人
        self._entitled(cur, cashier_limit=3)
        third = ent.check_limit(cur, tenant_id="t1", workspace_client_id=1, kind="cashier")
        self.assertTrue(third["allowed"])
        cur.cashier_count = 3  # 已 3 人,建第 4 人
        fourth = ent.check_limit(cur, tenant_id="t1", workspace_client_id=1, kind="cashier")
        self.assertFalse(fourth["allowed"])


class ProvisionLockTests(unittest.TestCase):
    def test_default_closed_allows(self):
        # 闸关(feature flag False)→ 恒放行(全链零变化)
        cur = StatefulCursor()
        with mock.patch("core.feature_flags.pos_provision_lock_enabled_for", return_value=False):
            self.assertTrue(ent.pos_provision_allowed(cur, tenant_id="t1"))

    def test_locked_new_tenant_without_entitlement_blocked(self):
        cur = StatefulCursor()

        # 闸开 + 非存量(不早于闸开启)+ 无授权 + 无订阅 → 不放行
        def _dispatch(s, p):
            if "predates" in s:
                return {"predates": False}
            return StatefulCursor._dispatch(cur, s, p)

        with (
            mock.patch("core.feature_flags.pos_provision_lock_enabled_for", return_value=True),
            mock.patch.object(cur, "_dispatch", _dispatch),
            mock.patch("core.db.get_active_subscription", return_value=None),
        ):
            self.assertFalse(ent.pos_provision_allowed(cur, tenant_id="new"))

    def test_locked_but_existing_tenant_exempt(self):
        cur = StatefulCursor()

        def _dispatch(s, p):
            if "predates" in s:
                return {"predates": True}  # 建租户早于闸开启 → 存量豁免
            return StatefulCursor._dispatch(cur, s, p)

        with (
            mock.patch("core.feature_flags.pos_provision_lock_enabled_for", return_value=True),
            mock.patch.object(cur, "_dispatch", _dispatch),
        ):
            self.assertTrue(ent.pos_provision_allowed(cur, tenant_id="old"))


if __name__ == "__main__":
    unittest.main()
