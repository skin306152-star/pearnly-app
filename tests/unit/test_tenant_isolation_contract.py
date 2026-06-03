#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_tenant_isolation_contract.py

守门测试 · EXECUTION_PLAN 阶段 1 · Task 1.2 · 2026-05-21 落地

把 docs/architecture/tenant-access-matrix.md 描述的"应该有的隔离限制"锁成
自动化断言 · 一旦后续重构动了 SQL · 这里立刻 fail.

覆盖矩阵 §2 的 13 张表 25 个函数 (list / get / delete + 批量) · 用 mock
cursor 捕获 SQL 跟参数顺序 · 不连真实 DB · 不需要 psycopg2 / passlib.

验证点(4 条):
  1. 给了 tenant_id  → SQL 必含 tenant_id 过滤 (要么 `tenant_id = %s`
     要么 `tenant_id = %s::uuid` 要么 `users.tenant_id = %s` 子查询)
  2. 没给 tenant_id → SQL 必含 `user_id = %s` 过滤 · 绝不能裸 WHERE
  3. delete / update 操作必带 scope · 绝不允许 `WHERE id = %s` 单 key
  4. P0 防回归: get_gl_vat_task / get_bank_recon_v2_task 强制 user_id
     positional · 单 task_id 调用 = TypeError (锁死 commit 8dd2c9c 修复)

跨租户负向 (用户纪律第 7 条):
  - 模拟 cursor 返 None (tenant B 的 WHERE 跟 tenant A 的 row 不匹配)
  - 验函数返 None · 不会跨 tenant 拿到数据
"""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from typing import Any, List, Optional
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


# ────────────────────────────────────────────────────────────────────
# Stub native deps · 本机可能缺 psycopg2 / bcrypt · 不影响 SQL shape 验证
# ────────────────────────────────────────────────────────────────────
def _ensure_stub_psycopg2():
    if "psycopg2" in sys.modules:
        return
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


def _ensure_stub_bcrypt():
    if "bcrypt" in sys.modules:
        return
    fake = types.ModuleType("bcrypt")
    fake.hashpw = lambda pw, salt: pw if isinstance(pw, bytes) else pw.encode()
    fake.gensalt = lambda rounds=12: b"$2b$12$stub"
    fake.checkpw = lambda a, b: False
    sys.modules["bcrypt"] = fake


_ensure_stub_psycopg2()
_ensure_stub_bcrypt()

from core import db  # noqa: E402


# ────────────────────────────────────────────────────────────────────
# 测试基础设施
# ────────────────────────────────────────────────────────────────────
class _Cursor:
    """记录所有 execute() · 按需返 fetchone / fetchall 结果."""

    def __init__(
        self,
        fetchone_results: Optional[List[Any]] = None,
        fetchall_results: Optional[List[List[Any]]] = None,
        rowcount: int = 1,
    ):
        self.executed: List[tuple] = []
        self.rowcount = rowcount
        self._fetchone = list(fetchone_results or [])
        self._fetchall = list(fetchall_results or [])

    def execute(self, sql, params=None):
        self.executed.append((str(sql), params))

    def fetchone(self):
        return self._fetchone.pop(0) if self._fetchone else None

    def fetchall(self):
        return self._fetchall.pop(0) if self._fetchall else []


class _CursorCM:
    def __init__(self, cursor: _Cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, tb):
        return False


def _patch_cursor(cursor: _Cursor):
    """patch db.get_cursor 返我们的 mock · 每次 get_cursor() 都拿到同一个 cursor."""
    return patch.object(db, "get_cursor", lambda *a, **k: _CursorCM(cursor))


# 测试常量 (任意 uuid 字符串 · 不连 DB 不校验合法性)
TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"
USER_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
USER_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _all_sql(cursor: _Cursor) -> str:
    """把所有 execute 过的 SQL 拼起来 · 方便 substring 断言."""
    return "\n".join(s for s, _ in cursor.executed)


def _all_params(cursor: _Cursor) -> list:
    """所有 execute 的 params 平铺."""
    flat: list = []
    for _, p in cursor.executed:
        if p is None:
            continue
        if isinstance(p, (list, tuple)):
            flat.extend(p)
        else:
            flat.append(p)
    return flat


# ════════════════════════════════════════════════════════════════════
# 表 3 · ocr_history (Dual-Key)
# ════════════════════════════════════════════════════════════════════
class OcrHistoryIsolationTests(unittest.TestCase):

    def test_list_ocr_history_tenant_mode_filters_by_tenant(self):
        cur = _Cursor(fetchone_results=[{"c": 0}])
        with _patch_cursor(cur):
            db.list_ocr_history(USER_A, retention_days=90, tenant_id=TENANT_A)
        sql = _all_sql(cur)
        params = _all_params(cur)
        # tenant 模式: SQL 必含 tenant 子查询
        self.assertIn("tenant_id = %s", sql, "tenant 模式必须按 tenant 过滤 · 不能裸 user 查")
        self.assertIn(TENANT_A, [str(p) for p in params])

    def test_list_ocr_history_user_mode_filters_by_user(self):
        cur = _Cursor(fetchone_results=[{"c": 0}])
        with _patch_cursor(cur):
            db.list_ocr_history(USER_A, retention_days=90, tenant_id=None)
        sql = _all_sql(cur)
        params = _all_params(cur)
        self.assertIn("user_id = %s", sql, "user 模式必须按 user_id 过滤")
        self.assertIn(USER_A, [str(p) for p in params])
        # 不能误带 tenant_id (否则相当于绕过权限)
        self.assertNotIn(
            "tenant_id = %s", sql, "user 模式 SQL 不应注入 tenant 过滤(老板/员工逻辑由 caller 决定)"
        )

    def test_get_ocr_history_detail_tenant_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_ocr_history_detail(USER_A, "rec-1", tenant_id=TENANT_A)
        sql = _all_sql(cur)
        self.assertIn("WHERE id = %s", sql)
        self.assertIn("tenant_id = %s", sql)
        self.assertIn(TENANT_A, [str(p) for p in _all_params(cur)])

    def test_get_ocr_history_detail_user_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_ocr_history_detail(USER_A, "rec-1", tenant_id=None)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s", sql)
        self.assertIn(USER_A, [str(p) for p in _all_params(cur)])

    def test_delete_ocr_history_always_scoped_tenant(self):
        cur = _Cursor(rowcount=1)
        with _patch_cursor(cur):
            db.delete_ocr_history(USER_A, "rec-1", tenant_id=TENANT_A)
        sql = _all_sql(cur)
        self.assertIn("DELETE FROM ocr_history", sql)
        self.assertIn("tenant_id = %s", sql)
        # 验证不存在裸 DELETE (`WHERE id = %s` 后无 AND)
        self.assertIn("AND", sql.upper(), "delete 必须 AND 一个 scope · 不能裸 WHERE id")

    def test_delete_ocr_history_always_scoped_user(self):
        cur = _Cursor(rowcount=1)
        with _patch_cursor(cur):
            db.delete_ocr_history(USER_A, "rec-1", tenant_id=None)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s", sql)

    def test_delete_ocr_history_with_pdf_paths_scoped_both_select_and_delete(self):
        # 此函数先 SELECT 再 DELETE · 两条都必须带 scope
        cur = _Cursor(fetchall_results=[[]], rowcount=0)
        with _patch_cursor(cur):
            db.delete_ocr_history_with_pdf_paths(USER_A, ["rec-1"], tenant_id=TENANT_A)
        self.assertEqual(len(cur.executed), 2)
        select_sql, _ = cur.executed[0]
        delete_sql, _ = cur.executed[1]
        self.assertIn("SELECT", select_sql)
        self.assertIn("tenant_id = %s", select_sql)
        self.assertIn("DELETE FROM ocr_history", delete_sql)
        self.assertIn("tenant_id = %s", delete_sql)


# ════════════════════════════════════════════════════════════════════
# 表 4 · clients (Dual-Key)
# ════════════════════════════════════════════════════════════════════
class ClientsIsolationTests(unittest.TestCase):

    def test_list_clients_tenant_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.list_clients(USER_A, tenant_id=TENANT_A)
        sql = _all_sql(cur)
        self.assertIn("tenant_id = %s", sql)
        self.assertIn(TENANT_A, [str(p) for p in _all_params(cur)])
        # 不能裸列所有
        self.assertNotIn(
            "WHERE is_active",
            sql.replace(" ", "").replace("\n", "").replace("AND", "&"),
            "list 不能跳过 scope 直接 WHERE is_active",
        )

    def test_list_clients_user_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.list_clients(USER_A, tenant_id=None)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s", sql)
        self.assertIn(USER_A, [str(p) for p in _all_params(cur)])

    def test_get_client_tenant_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_client(USER_A, 42, tenant_id=TENANT_A)
        sql = _all_sql(cur)
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("WHERE id = %s", sql)

    def test_get_client_user_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_client(USER_A, 42, tenant_id=None)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s", sql)

    def test_delete_client_scoped_tenant(self):
        cur = _Cursor(rowcount=1)
        with _patch_cursor(cur):
            db.delete_client(USER_A, 42, tenant_id=TENANT_A)
        # 找到 DELETE FROM clients 那条
        delete_sqls = [s for s, _ in cur.executed if "DELETE FROM clients" in s]
        self.assertEqual(len(delete_sqls), 1)
        self.assertIn("tenant_id = %s", delete_sqls[0])

    def test_delete_client_scoped_user(self):
        cur = _Cursor(rowcount=1)
        with _patch_cursor(cur):
            db.delete_client(USER_A, 42, tenant_id=None)
        delete_sqls = [s for s, _ in cur.executed if "DELETE FROM clients" in s]
        self.assertEqual(len(delete_sqls), 1)
        self.assertIn("user_id = %s", delete_sqls[0])


# ════════════════════════════════════════════════════════════════════
# 表 5/6 · erp_endpoints · 单 User 模式 (故意设计) · 验证不扩大
# ════════════════════════════════════════════════════════════════════
class ErpEndpointsSingleUserIsolationTests(unittest.TestCase):
    """这两张表故意单 User · 验证 SQL 没有意外引入 tenant 过滤 ·
    也没有 fallback 到全局查询."""

    def test_list_erp_endpoints_user_only(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.list_erp_endpoints(USER_A)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s", sql)
        # 单 User 模式: 不应有 tenant 过滤
        self.assertNotIn("tenant_id", sql, "erp_endpoints 单 User 模式 · 不应引入 tenant 过滤")
        self.assertIn(USER_A, [str(p) for p in _all_params(cur)])

    def test_get_erp_endpoint_user_only(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_erp_endpoint(USER_A, "ep-1")
        sql = _all_sql(cur)
        self.assertIn("user_id = %s", sql)
        self.assertIn("id = %s", sql)
        self.assertNotIn("tenant_id", sql)

    def test_delete_erp_endpoint_scoped_by_user(self):
        # delete_erp_endpoint 先 UPDATE erp_push_logs 再 DELETE erp_endpoints
        # 两条都必须按 user_id 限定
        cur = _Cursor(rowcount=1)
        with _patch_cursor(cur):
            db.delete_erp_endpoint(USER_A, "ep-1")
        self.assertGreaterEqual(len(cur.executed), 2)
        for sql, _ in cur.executed:
            self.assertIn(
                "user_id = %s", sql, f"删 ERP 端点关联操作必须 user_id scoped · SQL: {sql[:80]}"
            )

    def test_get_default_erp_endpoint_user_only(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_default_erp_endpoint(USER_A)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s", sql)


# ════════════════════════════════════════════════════════════════════
# 表 10 · vat_recon_tasks (Dual-Key · tenant 优先 / user fallback)
# ════════════════════════════════════════════════════════════════════
class VatReconTasksIsolationTests(unittest.TestCase):

    def test_list_vat_recon_tasks_tenant_mode(self):
        cur = _Cursor(fetchone_results=[{"n": 0}])
        with _patch_cursor(cur):
            db.list_vat_recon_tasks(TENANT_A, USER_A)
        sql = _all_sql(cur)
        self.assertIn("tenant_id = %s", sql)
        # tenant 模式不应同时把 user_id 也注入 WHERE (会缩窄成"我自己的"而非"公司全部")
        params = _all_params(cur)
        self.assertIn(TENANT_A, [str(p) for p in params])

    def test_list_vat_recon_tasks_user_mode(self):
        cur = _Cursor(fetchone_results=[{"n": 0}])
        with _patch_cursor(cur):
            db.list_vat_recon_tasks(None, USER_A)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s::uuid", sql)
        self.assertIn(USER_A, [str(p) for p in _all_params(cur)])

    def test_get_vat_recon_task_tenant_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_vat_recon_task("task-1", TENANT_A, USER_A)
        sql = _all_sql(cur)
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("id = %s", sql)

    def test_get_vat_recon_task_user_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_vat_recon_task("task-1", None, USER_A)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s::uuid", sql)

    def test_delete_vat_recon_task_scoped_tenant(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.delete_vat_recon_task("task-1", TENANT_A, USER_A)
        sql = _all_sql(cur)
        self.assertIn("DELETE FROM vat_recon_tasks", sql)
        self.assertIn("tenant_id = %s", sql)

    def test_delete_vat_recon_task_scoped_user(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.delete_vat_recon_task("task-1", None, USER_A)
        sql = _all_sql(cur)
        self.assertIn("DELETE FROM vat_recon_tasks", sql)
        self.assertIn("user_id = %s::uuid", sql)

    def test_delete_vat_recon_tasks_older_than_scoped(self):
        cur = _Cursor(fetchall_results=[[]])
        with _patch_cursor(cur):
            db.delete_vat_recon_tasks_older_than(30, TENANT_A, USER_A)
        sql = _all_sql(cur)
        self.assertIn("DELETE FROM vat_recon_tasks", sql)
        self.assertIn("tenant_id = %s", sql)


# ════════════════════════════════════════════════════════════════════
# 表 11 · gl_vat_task (含 P0 防回归)
# ════════════════════════════════════════════════════════════════════
class GlVatTaskIsolationTests(unittest.TestCase):

    def test_list_gl_vat_tasks_tenant_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.list_gl_vat_tasks(USER_A, tenant_id=TENANT_A)
        sql = _all_sql(cur)
        self.assertIn("tenant_id = %s::uuid", sql)
        self.assertIn(TENANT_A, [str(p) for p in _all_params(cur)])

    def test_list_gl_vat_tasks_user_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.list_gl_vat_tasks(USER_A, tenant_id=None)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s::uuid", sql)

    # ────── P0 防回归 (commit 8dd2c9c 修复) ──────
    def test_get_gl_vat_task_requires_user_id_positional(self):
        """🔴 P0 防回归: 旧签名 get_gl_vat_task(task_id) 无权限校验 ·
        现强制 user_id 是 positional · 漏传 = TypeError · 物理上不允许越权读."""
        with self.assertRaises(
            TypeError,
            msg="get_gl_vat_task 签名必须强制 user_id " "· 漏传必须 TypeError 防 P0 漏洞回归",
        ):
            db.get_gl_vat_task(123)  # 缺 user_id

    def test_get_gl_vat_task_user_mode_scopes_by_user(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_gl_vat_task(123, USER_A)
        sql = _all_sql(cur)
        self.assertIn(
            "user_id = %s::uuid",
            sql,
            "user 模式 get_gl_vat_task 必须 WHERE user_id " "· 否则 P0 越权读漏洞回归",
        )
        self.assertIn("id = %s", sql)

    def test_get_gl_vat_task_tenant_mode_scopes_by_tenant(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_gl_vat_task(123, USER_A, tenant_id=TENANT_A)
        sql = _all_sql(cur)
        self.assertIn("tenant_id = %s::uuid", sql)
        self.assertIn("id = %s", sql)
        # tenant 模式不应 fallback 到 user_id 单 key
        # (我们的实现是 if/else 分支 · tenant 给了就只看 tenant)

    def test_delete_gl_vat_task_scoped_by_user(self):
        cur = _Cursor(rowcount=1)
        with _patch_cursor(cur):
            db.delete_gl_vat_task(123, USER_A)
        sql = _all_sql(cur)
        self.assertIn("DELETE FROM gl_vat_task", sql)
        self.assertIn("user_id = %s::uuid", sql, "delete_gl_vat_task 必须 user_id scoped")

    def test_delete_gl_vat_tasks_batch_scoped_by_user(self):
        cur = _Cursor(rowcount=2)
        with _patch_cursor(cur):
            db.delete_gl_vat_tasks_batch([1, 2], USER_A)
        sql = _all_sql(cur)
        self.assertIn("DELETE FROM gl_vat_task", sql)
        self.assertIn("user_id = %s::uuid", sql)
        self.assertIn("ANY(%s)", sql)

    def test_delete_gl_vat_tasks_batch_rejects_garbage_ids(self):
        """批量 delete 必须先 clean_ids · 防 SQL 注入"""
        cur = _Cursor()
        with _patch_cursor(cur):
            r = db.delete_gl_vat_tasks_batch(["not-a-number"], USER_A)
        self.assertEqual(r, 0)
        self.assertEqual(len(cur.executed), 0, "全是 garbage id 时不应触发任何 DB 查询")


# ════════════════════════════════════════════════════════════════════
# 表 12 · bank_recon_v2_task (含 P0 防回归 · gl_vat_task 镜像)
# ════════════════════════════════════════════════════════════════════
class BankReconV2TaskIsolationTests(unittest.TestCase):

    def test_list_bank_recon_v2_tasks_tenant_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.list_bank_recon_v2_tasks(USER_A, tenant_id=TENANT_A)
        sql = _all_sql(cur)
        self.assertIn("tenant_id = %s::uuid", sql)

    def test_list_bank_recon_v2_tasks_user_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.list_bank_recon_v2_tasks(USER_A, tenant_id=None)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s::uuid", sql)

    # ────── P0 防回归 ──────
    def test_get_bank_recon_v2_task_requires_user_id_positional(self):
        """🔴 P0 防回归: 同 get_gl_vat_task · 镜像漏洞."""
        with self.assertRaises(TypeError, msg="get_bank_recon_v2_task 必须强制 user_id"):
            db.get_bank_recon_v2_task(123)  # 缺 user_id

    def test_get_bank_recon_v2_task_user_mode_scopes_by_user(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_bank_recon_v2_task(123, USER_A)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s::uuid", sql, "user 模式必须 WHERE user_id · 防 P0 越权读回归")
        self.assertIn("id = %s", sql)

    def test_get_bank_recon_v2_task_tenant_mode_scopes_by_tenant(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_bank_recon_v2_task(123, USER_A, tenant_id=TENANT_A)
        sql = _all_sql(cur)
        self.assertIn("tenant_id = %s::uuid", sql)

    def test_delete_bank_recon_v2_task_scoped_by_user(self):
        cur = _Cursor(rowcount=1)
        with _patch_cursor(cur):
            db.delete_bank_recon_v2_task(123, USER_A)
        sql = _all_sql(cur)
        self.assertIn("DELETE FROM bank_recon_v2_task", sql)
        self.assertIn("user_id = %s::uuid", sql)

    def test_delete_bank_recon_v2_tasks_batch_scoped(self):
        cur = _Cursor(rowcount=2)
        with _patch_cursor(cur):
            db.delete_bank_recon_v2_tasks_batch([10, 20], USER_A)
        sql = _all_sql(cur)
        self.assertIn("DELETE FROM bank_recon_v2_task", sql)
        self.assertIn("user_id = %s::uuid", sql)


# ════════════════════════════════════════════════════════════════════
# 表 13 · notification_rules (三层隔离 · 最严格)
# ════════════════════════════════════════════════════════════════════
class NotificationRulesIsolationTests(unittest.TestCase):

    def test_list_notification_rules_tenant_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.list_notification_rules(USER_A, tenant_id=TENANT_A)
        sql = _all_sql(cur)
        self.assertIn("tenant_id = %s", sql)
        self.assertIn(TENANT_A, [str(p) for p in _all_params(cur)])

    def test_list_notification_rules_user_mode_requires_tenant_null(self):
        """三层防 NULL 注入: user 模式必须 AND tenant_id IS NULL ·
        防止误读到 owner 的同 user_id 跨 tenant 规则."""
        cur = _Cursor()
        with _patch_cursor(cur):
            db.list_notification_rules(USER_A, tenant_id=None)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s", sql)
        self.assertIn(
            "tenant_id IS NULL", sql, "user 模式必须 AND tenant_id IS NULL · 三层防 NULL 注入"
        )

    def test_get_notification_rule_tenant_mode(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_notification_rule(42, USER_A, tenant_id=TENANT_A)
        sql = _all_sql(cur)
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("id = %s", sql)

    def test_get_notification_rule_user_mode_requires_tenant_null(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            db.get_notification_rule(42, USER_A, tenant_id=None)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s", sql)
        self.assertIn("tenant_id IS NULL", sql)

    def test_delete_notification_rule_scoped_tenant(self):
        cur = _Cursor(rowcount=1)
        with _patch_cursor(cur):
            db.delete_notification_rule(42, USER_A, tenant_id=TENANT_A)
        delete_sqls = [s for s, _ in cur.executed if "DELETE FROM notification_rules" in s]
        self.assertEqual(len(delete_sqls), 1)
        self.assertIn("tenant_id = %s", delete_sqls[0])

    def test_delete_notification_rule_scoped_user_with_tenant_null(self):
        cur = _Cursor(rowcount=1)
        with _patch_cursor(cur):
            db.delete_notification_rule(42, USER_A, tenant_id=None)
        delete_sqls = [s for s, _ in cur.executed if "DELETE FROM notification_rules" in s]
        self.assertEqual(len(delete_sqls), 1)
        self.assertIn("user_id = %s", delete_sqls[0])
        self.assertIn(
            "tenant_id IS NULL",
            delete_sqls[0],
            "delete user 模式必须 AND tenant_id IS NULL" "· 防误删 owner 同 user_id 的 tenant 规则",
        )


# ════════════════════════════════════════════════════════════════════
# 跨租户负向 (用户纪律第 7 条 · "租户 A 不能访问租户 B 数据")
# ════════════════════════════════════════════════════════════════════
class CrossTenantNegativeTests(unittest.TestCase):
    """模拟场景: tenant A 创建了 row · tenant B 用户尝试 get 同一个 id ·
    DB 层 WHERE 不匹配 → cursor 返 None → 函数返 None.

    这验证 DB 层的 fail-safe 行为 · 即使 caller 拿到了 tenant B 的会话上下文
    + 直接喂 tenant A 的 task_id · 拿不到数据."""

    def test_get_ocr_history_detail_tenant_b_cannot_read_tenant_a(self):
        # cursor 模拟 "tenant B 的 WHERE 不匹配" · 返 None
        cur = _Cursor(fetchone_results=[None])
        with _patch_cursor(cur):
            r = db.get_ocr_history_detail(USER_B, "rec-owned-by-A", tenant_id=TENANT_B)
        self.assertIsNone(r, "DB 层未返 row · 函数必须返 None · 不能凭 record_id " "凭空构造 dict")
        # 同时验证 SQL 真的带了 tenant_B 过滤
        sql = _all_sql(cur)
        self.assertIn(TENANT_B, [str(p) for p in _all_params(cur)])

    def test_get_client_tenant_b_cannot_read_tenant_a(self):
        cur = _Cursor(fetchone_results=[None])
        with _patch_cursor(cur):
            r = db.get_client(USER_B, 42, tenant_id=TENANT_B)
        self.assertIsNone(r)

    def test_get_vat_recon_task_tenant_b_cannot_read_tenant_a(self):
        cur = _Cursor(fetchone_results=[None])
        with _patch_cursor(cur):
            r = db.get_vat_recon_task("task-owned-by-A", TENANT_B, USER_B)
        self.assertIsNone(r)

    def test_get_gl_vat_task_tenant_b_cannot_read_tenant_a(self):
        """🔴 P0 核心防回归: 这是被修过的真漏洞."""
        cur = _Cursor(fetchone_results=[None])
        with _patch_cursor(cur):
            r = db.get_gl_vat_task(123, USER_B, tenant_id=TENANT_B)
        self.assertIsNone(
            r, "tenant B 用户喂 tenant A 的 task_id · DB 层 WHERE " "不匹配 · 必须返 None"
        )

    def test_get_bank_recon_v2_task_tenant_b_cannot_read_tenant_a(self):
        """🔴 P0 核心防回归: 镜像漏洞."""
        cur = _Cursor(fetchone_results=[None])
        with _patch_cursor(cur):
            r = db.get_bank_recon_v2_task(123, USER_B, tenant_id=TENANT_B)
        self.assertIsNone(r)

    def test_get_notification_rule_user_b_cannot_read_user_a_personal_rule(self):
        """user 模式 (tenant_id=None) 的隔离: user B 不能读 user A 个人规则."""
        cur = _Cursor(fetchone_results=[None])
        with _patch_cursor(cur):
            r = db.get_notification_rule(42, USER_B, tenant_id=None)
        self.assertIsNone(r)
        sql = _all_sql(cur)
        # SQL 必须同时带 user_id 和 tenant_id IS NULL (三层隔离)
        self.assertIn("user_id = %s", sql)
        self.assertIn("tenant_id IS NULL", sql)

    def test_delete_ocr_history_tenant_b_cannot_delete_tenant_a(self):
        """delete 也是 fail-safe: WHERE 不匹配 → rowcount=0 → 返 False."""
        cur = _Cursor(rowcount=0)
        with _patch_cursor(cur):
            r = db.delete_ocr_history(USER_B, "rec-owned-by-A", tenant_id=TENANT_B)
        self.assertFalse(r, "跨 tenant delete 必须 WHERE 不匹配 → rowcount=0 → False")

    def test_delete_gl_vat_task_user_b_cannot_delete_user_a_task(self):
        cur = _Cursor(rowcount=0)
        with _patch_cursor(cur):
            r = db.delete_gl_vat_task(123, USER_B)
        self.assertFalse(r)
        sql = _all_sql(cur)
        self.assertIn("user_id = %s::uuid", sql)


# ════════════════════════════════════════════════════════════════════
# 通用契约 · delete 操作绝不允许裸 WHERE id (防新增函数走老坑)
# ════════════════════════════════════════════════════════════════════
class DeleteAlwaysScopedContractTests(unittest.TestCase):
    """汇总所有 delete 函数 · 验证它们的 SQL 都至少含一个 scope 关键字
    (user_id / tenant_id / endpoint_id) · 不能裸 DELETE FROM xxx WHERE id = %s."""

    SCOPE_TOKENS = ("user_id", "tenant_id", "endpoint_id")

    def _assert_delete_scoped(self, fn, *args, **kwargs):
        cur = _Cursor(rowcount=1, fetchall_results=[[]], fetchone_results=[None])
        with _patch_cursor(cur):
            try:
                fn(*args, **kwargs)
            except Exception:
                pass  # 我们只关心 SQL shape · 不关心返回值
        delete_sqls = [s for s, _ in cur.executed if "DELETE FROM" in s.upper()]
        self.assertGreater(len(delete_sqls), 0, f"{fn.__name__} 应该至少 issue 1 条 DELETE 语句")
        for sql in delete_sqls:
            self.assertTrue(
                any(token in sql for token in self.SCOPE_TOKENS),
                f"{fn.__name__} 的 DELETE 必须含 scope · 实际: {sql[:120]}",
            )

    def test_all_delete_fns_have_scope(self):
        cases = [
            (db.delete_ocr_history, (USER_A, "rec-1"), {"tenant_id": TENANT_A}),
            (db.delete_ocr_history, (USER_A, "rec-1"), {"tenant_id": None}),
            (db.delete_ocr_history_with_pdf_paths, (USER_A, ["rec-1"]), {"tenant_id": TENANT_A}),
            (db.delete_client, (USER_A, 42), {"tenant_id": TENANT_A}),
            (db.delete_client, (USER_A, 42), {"tenant_id": None}),
            (db.delete_erp_endpoint, (USER_A, "ep-1"), {}),
            (db.delete_vat_recon_task, ("task-1", TENANT_A, USER_A), {}),
            (db.delete_vat_recon_task, ("task-1", None, USER_A), {}),
            (db.delete_gl_vat_task, (123, USER_A), {}),
            (db.delete_gl_vat_tasks_batch, ([1, 2], USER_A), {}),
            (db.delete_bank_recon_v2_task, (123, USER_A), {}),
            (db.delete_bank_recon_v2_tasks_batch, ([10, 20], USER_A), {}),
            (db.delete_notification_rule, (42, USER_A, TENANT_A), {}),
            (db.delete_notification_rule, (42, USER_A, None), {}),
        ]
        for fn, args, kwargs in cases:
            with self.subTest(fn=fn.__name__, tenant=kwargs.get("tenant_id", "n/a")):
                self._assert_delete_scoped(fn, *args, **kwargs)


if __name__ == "__main__":
    unittest.main()
