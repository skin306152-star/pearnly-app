# -*- coding: utf-8 -*-
"""
REFACTOR-WA 覆盖补强 · services/workspace/store.py 行为单测(账套主体 DAL · 非高敏)

补真实行为/边界/错误分支覆盖(原仅 test_workspace_store_contract 锁结构 · 行为覆盖 ~33%):
create/get/list/update/archive/list_enriched/bind_endpoint/get_endpoint_id 的
SQL 形状 + 参数(trim/截断/None 归一)+ 返回 + tenant vs user 隔离两路径 +
空守卫(name 空 / restrict_ids=[] / 无更新字段)+ 异常吞咽兜底 + enriched 异常退基础列表。
全部用 FakeCursor mock(隔离确定 · 不打真实 DB · 不触发任何外部)。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401  · 先 import db 完成,避免 dal_reexports partial-init 循环
from services.workspace import store as ws


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None, rowcount=0):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    @property
    def last_sql(self):
        return self.calls[-1][0] if self.calls else ""

    @property
    def last_params(self):
        return self.calls[-1][1] if self.calls else None

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def patch_cursor(cur):
    cur.cm_kwargs = []

    def factory(*a, **k):
        cur.cm_kwargs.append(k)
        return _CM(cur)

    return mock.patch.object(ws.db, "get_cursor", factory)


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return mock.patch.object(ws.db, "get_cursor", factory)


class CreateTests(unittest.TestCase):
    def test_empty_name_returns_none_without_db(self):
        with patch_cursor_raises():
            self.assertIsNone(ws.create_workspace_client("u1", "t1", "   "))

    def test_success_trims_and_returns_id(self):
        cur = FakeCursor(fetchone={"id": 11})
        with patch_cursor(cur):
            wid = ws.create_workspace_client(
                "u1", "t1", "  ACME Co  ", tax_id="  123  ", erp_endpoint_id=" ep1 "
            )
        self.assertEqual(wid, 11)
        self.assertIn("INSERT INTO workspace_clients", cur.last_sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)
        p = cur.last_params
        self.assertEqual(p[0], "u1")
        self.assertEqual(p[1], "t1")
        self.assertEqual(p[2], "ACME Co")  # trimmed
        self.assertEqual(p[3], "123")  # tax_id trimmed
        self.assertEqual(p[4], "ep1")  # endpoint trimmed

    def test_blank_tax_becomes_none(self):
        cur = FakeCursor(fetchone={"id": 1})
        with patch_cursor(cur):
            ws.create_workspace_client("u1", None, "X", tax_id="   ")
        self.assertIsNone(cur.last_params[3])  # blank tax → None

    def test_exception_returns_none(self):
        with patch_cursor_raises():
            self.assertIsNone(ws.create_workspace_client("u1", "t1", "X"))


class SubjectTypeTests(unittest.TestCase):
    """用户引导闭环:subject_type company|personal + personal 幂等 + 归一。"""

    def test_norm_subject_type(self):
        self.assertEqual(ws._norm_subject_type("personal"), "personal")
        self.assertEqual(ws._norm_subject_type("PERSONAL"), "personal")
        self.assertEqual(ws._norm_subject_type("company"), "company")
        self.assertEqual(ws._norm_subject_type("garbage"), "company")
        self.assertEqual(ws._norm_subject_type(None), "company")

    def test_company_create_passes_subject_type_param(self):
        cur = FakeCursor(fetchone={"id": 7})
        with patch_cursor(cur):
            wid = ws.create_workspace_client("u1", "t1", "ACME", subject_type="company")
        self.assertEqual(wid, 7)
        self.assertIn("INSERT INTO workspace_clients", cur.last_sql)
        self.assertIn("subject_type", cur.last_sql)
        # INSERT 列尾序:subject_type, fiscal_year_start_month, doc_prefix → subject_type 在 -3
        self.assertEqual(cur.last_params[-3], "company")

    def test_unknown_subject_type_falls_back_company(self):
        cur = FakeCursor(fetchone={"id": 8})
        with patch_cursor(cur):
            ws.create_workspace_client("u1", "t1", "ACME", subject_type="weird")
        self.assertEqual(cur.last_params[-3], "company")

    def test_personal_create_returns_existing_without_insert(self):
        # _find_active_personal 命中 → 幂等返回既有 id · 绝不再 INSERT。
        cur = FakeCursor(fetchone={"id": 99})
        with patch_cursor(cur):
            wid = ws.create_workspace_client("u1", "t1", "ME", subject_type="personal")
        self.assertEqual(wid, 99)
        self.assertNotIn("INSERT INTO workspace_clients", cur.all_sql())
        self.assertIn("subject_type = 'personal'", cur.all_sql())

    def test_update_passes_subject_type(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ok = ws.update_workspace_client(5, "u1", tenant_id="t1", subject_type="company")
        self.assertTrue(ok)
        self.assertIn("subject_type = %s", cur.last_sql)
        self.assertIn("company", cur.last_params)


class AccountingSettingsTests(unittest.TestCase):
    """账务设置(引导步③):财年起始月 + 单据前缀 per-主体 持久化 + 归一。"""

    def test_norm_fy_month(self):
        self.assertEqual(ws._norm_fy_month(6), 6)
        self.assertEqual(ws._norm_fy_month(1), 1)
        self.assertEqual(ws._norm_fy_month(12), 12)
        self.assertEqual(ws._norm_fy_month(0), 1)  # 越界归 1
        self.assertEqual(ws._norm_fy_month(13), 1)
        self.assertEqual(ws._norm_fy_month(None), 1)
        self.assertEqual(ws._norm_fy_month("x"), 1)

    def test_norm_doc_prefix(self):
        self.assertEqual(ws._norm_doc_prefix("inv"), "INV")  # 大写
        self.assertEqual(ws._norm_doc_prefix("  ab "), "AB")  # 去空白
        self.assertEqual(ws._norm_doc_prefix("a" * 30), "A" * 20)  # 截 20
        self.assertIsNone(ws._norm_doc_prefix(""))  # 空 → None(回落租户级)
        self.assertIsNone(ws._norm_doc_prefix(None))

    def test_create_persists_fiscal_and_prefix(self):
        cur = FakeCursor(fetchone={"id": 5})
        with patch_cursor(cur):
            ws.create_workspace_client(
                "u1", "t1", "ACME", fiscal_year_start_month=4, doc_prefix="ab"
            )
        self.assertIn("fiscal_year_start_month", cur.last_sql)
        self.assertIn("doc_prefix", cur.last_sql)
        self.assertEqual(cur.last_params[-2], 4)  # fy 归一后
        self.assertEqual(cur.last_params[-1], "AB")  # 前缀大写

    def test_update_persists_fiscal_and_prefix(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ws.update_workspace_client(
                5, "u1", tenant_id="t1", fiscal_year_start_month=3, doc_prefix="x"
            )
        self.assertIn("fiscal_year_start_month = %s", cur.last_sql)
        self.assertIn("doc_prefix = %s", cur.last_sql)
        self.assertIn(3, cur.last_params)
        self.assertIn("X", cur.last_params)


class TaxIdDuplicateTests(unittest.TestCase):
    """税号重复检测(向导步1 边界 · workspace-entry §五)。"""

    def test_empty_tax_never_duplicate_no_db(self):
        with patch_cursor_raises():  # 空税号直接返 False,绝不查库
            self.assertFalse(ws.tax_id_in_use("u1", "t1", "   "))
            self.assertFalse(ws.tax_id_in_use("u1", "t1", None))

    def test_found_returns_true_tenant_scope(self):
        cur = FakeCursor(fetchone={"?column?": 1})
        with patch_cursor(cur):
            self.assertTrue(ws.tax_id_in_use("u1", "t1", "  0105551234567 "))
        self.assertIn("tax_id = %s", cur.last_sql)
        self.assertIn("tenant_id = %s", cur.last_sql)
        self.assertIn("0105551234567", cur.last_params)  # trim 后比对

    def test_not_found_returns_false(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertFalse(ws.tax_id_in_use("u1", "t1", "0105551234567"))

    def test_exclude_id_for_self_on_update(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            ws.tax_id_in_use("u1", "t1", "0105551234567", exclude_id=5)
        self.assertIn("id <> %s", cur.last_sql)
        self.assertIn(5, cur.last_params)

    def test_check_failure_fails_open(self):
        with patch_cursor_raises():  # 检查失败不阻塞建主体
            self.assertFalse(ws.tax_id_in_use("u1", "t1", "0105551234567"))


class GetTests(unittest.TestCase):
    def test_tenant_path(self):
        cur = FakeCursor(fetchone={"id": 5, "name": "W"})
        with patch_cursor(cur):
            out = ws.get_workspace_client(5, "u1", tenant_id="t1")
        self.assertEqual(out["id"], 5)
        self.assertIn("tenant_id = %s", cur.last_sql)
        self.assertEqual(cur.last_params, (5, "t1"))

    def test_user_path_when_no_tenant(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(ws.get_workspace_client(5, "u1", tenant_id=None))
        self.assertIn("user_id = %s", cur.last_sql)
        self.assertIn("tenant_id IS NULL", cur.last_sql)

    def test_exception_returns_none(self):
        with patch_cursor_raises():
            self.assertIsNone(ws.get_workspace_client(5, "u1", "t1"))


class ListTests(unittest.TestCase):
    def test_restrict_ids_empty_returns_empty_without_db(self):
        with patch_cursor_raises():
            self.assertEqual(ws.list_workspace_clients("u1", "t1", restrict_ids=[]), [])

    def test_tenant_active_only_default(self):
        cur = FakeCursor(fetchall=[{"id": 1}])
        with patch_cursor(cur):
            out = ws.list_workspace_clients("u1", tenant_id="t1")
        self.assertEqual(len(out), 1)
        self.assertIn("tenant_id = %s", cur.last_sql)
        self.assertIn("is_active = TRUE", cur.last_sql)

    def test_user_path_and_inactive_included(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            ws.list_workspace_clients("u1", tenant_id=None, active_only=False)
        self.assertIn("user_id = %s", cur.last_sql)
        self.assertNotIn("is_active = TRUE", cur.last_sql)

    def test_restrict_ids_nonempty_adds_any(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            ws.list_workspace_clients("u1", "t1", restrict_ids=[3, 4])
        self.assertIn("id = ANY(%s)", cur.last_sql)
        self.assertIn([3, 4], cur.last_params)

    def test_exception_returns_empty(self):
        with patch_cursor_raises():
            self.assertEqual(ws.list_workspace_clients("u1", "t1"), [])


class UpdateTests(unittest.TestCase):
    def test_no_fields_returns_false_without_db(self):
        with patch_cursor_raises():
            self.assertFalse(ws.update_workspace_client(1, "u1", "t1"))

    def test_name_empty_string_not_updated_so_only_tax(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ok = ws.update_workspace_client(1, "u1", "t1", name="   ", tax_id="999")
        self.assertTrue(ok)
        self.assertIn("tax_id = %s", cur.last_sql)
        self.assertNotIn("name = %s", cur.last_sql)  # 空名不改

    def test_name_and_tax_update_tenant_path(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ws.update_workspace_client(1, "u1", "t1", name="New", tax_id="123")
        self.assertIn("name = %s", cur.last_sql)
        self.assertIn("updated_at = NOW()", cur.last_sql)
        self.assertIn("tenant_id = %s", cur.last_sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_rowcount_zero_false(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(ws.update_workspace_client(1, "u1", None, name="N"))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(ws.update_workspace_client(1, "u1", "t1", name="N"))


class ArchiveTests(unittest.TestCase):
    def test_archive_tenant_path(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(ws.archive_workspace_client(1, "u1", "t1", active=False))
        self.assertIn("is_active = %s", cur.last_sql)
        self.assertEqual(cur.last_params[0], False)
        self.assertIn("tenant_id = %s", cur.last_sql)

    def test_restore_user_path(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ws.archive_workspace_client(1, "u1", None, active=True)
        self.assertEqual(cur.last_params[0], True)
        self.assertIn("user_id = %s", cur.last_sql)

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(ws.archive_workspace_client(1, "u1", "t1"))


class EnrichedTests(unittest.TestCase):
    def test_enriched_join_and_rows(self):
        cur = FakeCursor(fetchall=[{"id": 1, "invoice_count": 3, "total_amount": 10}])
        with patch_cursor(cur):
            out = ws.list_workspace_clients_enriched("u1", tenant_id="t1")
        self.assertEqual(out[0]["invoice_count"], 3)
        self.assertIn("LEFT JOIN", cur.last_sql)
        self.assertIn("wc.tenant_id = %s", cur.last_sql)

    def test_enriched_exception_falls_back_to_basic_list(self):
        # get_cursor 全程 raise → enriched 兜底调 list_workspace_clients(也 raise)→ []
        with patch_cursor_raises():
            self.assertEqual(ws.list_workspace_clients_enriched("u1", "t1"), [])


class BindTests(unittest.TestCase):
    def test_bind_tenant_path(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(ws.bind_workspace_endpoint(1, "  ep9  ", "u1", "t1"))
        self.assertIn("erp_endpoint_id = %s", cur.last_sql)
        self.assertEqual(cur.last_params[0], "ep9")  # trimmed
        self.assertIn("tenant_id = %s", cur.last_sql)

    def test_unbind_none(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ws.bind_workspace_endpoint(1, None, "u1", tenant_id=None)
        self.assertIsNone(cur.last_params[0])
        self.assertIn("user_id = %s", cur.last_sql)

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(ws.bind_workspace_endpoint(1, "ep", "u1", "t1"))


class GetEndpointIdTests(unittest.TestCase):
    def test_delegates_and_returns_endpoint(self):
        cur = FakeCursor(fetchone={"id": 1, "erp_endpoint_id": "epX"})
        with patch_cursor(cur):
            self.assertEqual(ws.get_workspace_endpoint_id(1, "u1", "t1"), "epX")

    def test_no_workspace_returns_none(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(ws.get_workspace_endpoint_id(1, "u1", "t1"))

    def test_workspace_without_endpoint_returns_none(self):
        cur = FakeCursor(fetchone={"id": 1, "erp_endpoint_id": None})
        with patch_cursor(cur):
            self.assertIsNone(ws.get_workspace_endpoint_id(1, "u1", "t1"))


if __name__ == "__main__":
    unittest.main()
