# -*- coding: utf-8 -*-
"""coa_erp_bridge DAL 单测(services/accounting/bridge_store.py · T4a)。

内存假游标验 SQL 形状与参数化(WHERE 值全走 %s,不拼字符串)、语义钉死(coa_code 必须是
coa_preset 科目码,非法即炸不落脏行)、upsert 幂等走 ON CONFLICT 覆盖。真库侧的隔离/RLS
(A 租户桥 B 租户读不到、policy 在场)在本地 docker 库亲核,不在单测里连库。
"""

import unittest

from services.accounting import bridge_store


class FakeCursor:
    """录 execute 的 (sql, params);fetchall/rowcount 由测试预置。"""

    def __init__(self, rows=None, rowcount=0):
        self.calls = []
        self._rows = rows or []
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self._rows


class LoadBridgeTests(unittest.TestCase):
    def test_returns_code_map_and_parametrizes(self):
        cur = FakeCursor(rows=[{"coa_code": "1020", "erp_code": "1113-01"}])
        out = bridge_store.load_bridge(
            cur, tenant_id="t-1", workspace_client_id=7, erp_type="mrerp"
        )
        self.assertEqual(out, {"1020": "1113-01"})
        sql, params = cur.calls[0]
        self.assertIn("%s", sql)
        self.assertNotIn("t-1", sql)  # 值不内插进 SQL,全走参数
        self.assertEqual(params, ("t-1", 7, "mrerp"))

    def test_tuple_rows_supported(self):
        cur = FakeCursor(rows=[("5290", "5320-05")])
        out = bridge_store.load_bridge(
            cur, tenant_id="t-1", workspace_client_id=7, erp_type="mrerp"
        )
        self.assertEqual(out, {"5290": "5320-05"})

    def test_invalid_erp_type_rejected(self):
        with self.assertRaises(ValueError):
            bridge_store.load_bridge(
                FakeCursor(), tenant_id="t-1", workspace_client_id=7, erp_type="notanerp"
            )


class UpsertRowsTests(unittest.TestCase):
    def test_upsert_is_on_conflict_update(self):
        cur = FakeCursor()
        n = bridge_store.upsert_rows(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            erp_type="MrErp",  # 大小写归一
            rows=[{"coa_code": "1020", "erp_code": "1113-01", "erp_name": "เงินฝาก"}],
        )
        self.assertEqual(n, 1)
        sql, params = cur.calls[0]
        self.assertIn("ON CONFLICT (tenant_id, workspace_client_id, erp_type, coa_code)", sql)
        self.assertIn("DO UPDATE SET", sql)
        self.assertEqual(params[2], "mrerp")
        self.assertEqual(params[3], "1020")
        self.assertEqual(params[4], "1113-01")

    def test_non_preset_coa_code_fails_loud(self):
        # 语义钉死:coa_code 只认 coa_preset 27 科目码,乱码在入口就炸,不落脏行。
        with self.assertRaises(ValueError):
            bridge_store.upsert_rows(
                FakeCursor(),
                tenant_id="t-1",
                workspace_client_id=7,
                erp_type="mrerp",
                rows=[{"coa_code": "9999", "erp_code": "1113-01"}],
            )

    def test_empty_erp_code_fails_loud(self):
        with self.assertRaises(ValueError):
            bridge_store.upsert_rows(
                FakeCursor(),
                tenant_id="t-1",
                workspace_client_id=7,
                erp_type="mrerp",
                rows=[{"coa_code": "1020", "erp_code": "  "}],
            )


class DeleteAndTypesTests(unittest.TestCase):
    def test_delete_row_reports_hit(self):
        cur = FakeCursor(rowcount=1)
        hit = bridge_store.delete_row(
            cur, tenant_id="t-1", workspace_client_id=7, erp_type="mrerp", coa_code="1020"
        )
        self.assertTrue(hit)
        self.assertEqual(cur.calls[0][1], ("t-1", 7, "mrerp", "1020"))

    def test_delete_row_miss_is_false(self):
        cur = FakeCursor(rowcount=0)
        self.assertFalse(
            bridge_store.delete_row(
                cur, tenant_id="t-1", workspace_client_id=7, erp_type="mrerp", coa_code="1020"
            )
        )

    def test_list_erp_types_distinct(self):
        cur = FakeCursor(rows=[{"erp_type": "express"}, {"erp_type": "mrerp"}])
        out = bridge_store.list_erp_types(cur, tenant_id="t-1", workspace_client_id=7)
        self.assertEqual(out, ["express", "mrerp"])
        self.assertIn("DISTINCT", cur.calls[0][0])


if __name__ == "__main__":
    unittest.main()
