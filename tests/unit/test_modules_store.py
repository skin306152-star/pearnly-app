# -*- coding: utf-8 -*-
"""tenant_modules DAL 守门测试(POS 项目 · PO-A1)。

锁定:
  1. 每条语句按 tenant_id 隔离 + 全参数化(值不入 SQL 串)
  2. get_modules:DEFAULT_ENABLED 打底,显式行覆盖,覆盖 KNOWN_MODULES 全集
  3. is_enabled:显式行优先 / 默认回落 / 未知模块=关(不连库)
  4. set_module:upsert(ON CONFLICT)· 未知 module_key 抛 ValueError
"""

import json
import unittest

from services.modules import store


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall or []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    @property
    def last_sql(self):
        return self.calls[-1][0]

    @property
    def last_params(self):
        return self.calls[-1][1]


class ModulesStoreIsolationTests(unittest.TestCase):
    def test_get_modules_scopes_to_tenant_and_parameterizes(self):
        cur = FakeCursor(fetchall=[])
        store.get_modules(cur, tenant_id="t-1")
        self.assertIn("WHERE tenant_id = %s", cur.last_sql)
        self.assertEqual(cur.last_params, ("t-1",))

    def test_is_enabled_scopes_to_tenant(self):
        cur = FakeCursor(fetchone={"enabled": True})
        store.is_enabled(cur, tenant_id="t-1", module_key="pos")
        self.assertIn("tenant_id = %s AND module_key = %s", cur.last_sql)
        self.assertEqual(cur.last_params, ("t-1", "pos"))


class GetModulesDefaultsTests(unittest.TestCase):
    def test_defaults_when_no_rows(self):
        cur = FakeCursor(fetchall=[])
        out = store.get_modules(cur, tenant_id="t-1")
        # 覆盖 KNOWN_MODULES 全集
        self.assertEqual(set(out.keys()), set(store.KNOWN_MODULES))
        # 既有功能默认开 · POS/库存默认关
        self.assertTrue(out["sales"]["enabled"])
        self.assertTrue(out["recon"]["enabled"])
        self.assertFalse(out["pos"]["enabled"])
        self.assertFalse(out["inventory"]["enabled"])
        self.assertEqual(out["pos"]["config"], {})

    def test_explicit_row_overrides_default(self):
        cur = FakeCursor(
            fetchall=[
                {"module_key": "pos", "enabled": True, "config": {"tables": True}},
                {"module_key": "sales", "enabled": False, "config": {}},
            ]
        )
        out = store.get_modules(cur, tenant_id="t-1")
        self.assertTrue(out["pos"]["enabled"])
        self.assertEqual(out["pos"]["config"], {"tables": True})
        # 显式关掉的覆盖默认开
        self.assertFalse(out["sales"]["enabled"])

    def test_config_string_is_parsed(self):
        cur = FakeCursor(
            fetchall=[{"module_key": "pos", "enabled": True, "config": '{"weigh": true}'}]
        )
        out = store.get_modules(cur, tenant_id="t-1")
        self.assertEqual(out["pos"]["config"], {"weigh": True})


class IsEnabledTests(unittest.TestCase):
    def test_explicit_row_wins(self):
        cur = FakeCursor(fetchone={"enabled": True})
        self.assertTrue(store.is_enabled(cur, tenant_id="t-1", module_key="pos"))

    def test_falls_back_to_default_when_no_row(self):
        cur = FakeCursor(fetchone=None)
        self.assertFalse(store.is_enabled(cur, tenant_id="t-1", module_key="pos"))
        cur2 = FakeCursor(fetchone=None)
        self.assertTrue(store.is_enabled(cur2, tenant_id="t-1", module_key="sales"))

    def test_unknown_module_is_off_without_db(self):
        cur = FakeCursor(fetchone={"enabled": True})
        self.assertFalse(store.is_enabled(cur, tenant_id="t-1", module_key="evil"))
        self.assertFalse(cur.calls, "unknown module must not hit the DB")


class SetModuleTests(unittest.TestCase):
    def test_toggle_only_upserts_enabled(self):
        cur = FakeCursor(fetchone={"module_key": "pos", "enabled": True, "config": {}})
        out = store.set_module(cur, tenant_id="t-1", module_key="pos", enabled=True)
        self.assertIn("INSERT INTO tenant_modules", cur.last_sql)
        self.assertIn("ON CONFLICT (tenant_id, module_key)", cur.last_sql)
        self.assertEqual(cur.last_params, ("t-1", "pos", True))
        self.assertEqual(out, {"module_key": "pos", "enabled": True, "config": {}})

    def test_with_config_serializes_json_param(self):
        cur = FakeCursor(
            fetchone={"module_key": "pos", "enabled": True, "config": {"tables": True}}
        )
        store.set_module(
            cur, tenant_id="t-1", module_key="pos", enabled=True, config={"tables": True}
        )
        self.assertIn("%s::jsonb", cur.last_sql)
        # config 作为 JSON 串参数传(值不拼进 SQL)
        self.assertEqual(cur.last_params[-1], json.dumps({"tables": True}))
        self.assertNotIn("tables", cur.last_sql)

    def test_unknown_module_key_rejected(self):
        cur = FakeCursor()
        with self.assertRaises(ValueError):
            store.set_module(cur, tenant_id="t-1", module_key="evil", enabled=True)
        self.assertFalse(cur.calls, "must reject before touching the DB")


if __name__ == "__main__":
    unittest.main()
