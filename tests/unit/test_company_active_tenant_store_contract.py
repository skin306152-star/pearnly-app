# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 多公司成员/当前账套切换 DAL 抽取契约

锁定:
  1. list_user_companies / set_user_active_tenant 从 services.tenant.store 提供,
     db.py 经 re-export 暴露同一对象(billing_routes 走 db.x 零改动)。
  2. 纯结构性 0 逻辑改 + 跨域 _bkk_year_month 走 db.*:set_user_active_tenant 的越权防御
     (用户不属于该 tenant → 返 False · 不写 active_tenant_id)经 mock.patch("core.db.get_cursor") 仍生效。
"""

import unittest
from unittest import mock

from core import db
from services.tenant import store


class CompanyActiveTenantReexportContract(unittest.TestCase):
    def test_reexported_same_object(self):
        for n in ["list_user_companies", "set_user_active_tenant"]:
            self.assertTrue(hasattr(store, n), f"service missing {n}")
            self.assertIs(
                getattr(db, n), getattr(store, n), f"db.{n} not re-exporting service object"
            )


class CompanyActiveTenantBehaviorContract(unittest.TestCase):
    def _cursor(self, fetchone_ret):
        cur = mock.MagicMock()
        cur.fetchone.return_value = fetchone_ret
        ctx = mock.MagicMock()
        ctx.__enter__.return_value = cur
        ctx.__exit__.return_value = False
        return ctx, cur

    def test_set_active_rejects_non_member(self):
        # 成员校验查不到 → 返 False,不执行 UPDATE
        ctx, cur = self._cursor(None)
        with mock.patch("core.db.get_cursor", return_value=ctx):
            self.assertFalse(store.set_user_active_tenant("u1", "t-not-mine"))
        # 只执行了校验 SELECT,没有 UPDATE active_tenant_id
        sqls = " ".join(str(c.args[0]) for c in cur.execute.call_args_list)
        self.assertNotIn("UPDATE users SET active_tenant_id", sqls)

    def test_list_companies_returns_empty_on_db_error(self):
        with mock.patch("core.db.get_cursor", side_effect=RuntimeError("boom")):
            self.assertEqual(store.list_user_companies("u1"), [])


if __name__ == "__main__":
    unittest.main()
