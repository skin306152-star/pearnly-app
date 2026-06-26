#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_billing_contract.py

守门测试 · EXECUTION_PLAN 阶段 2 · Task 2.1 · 2026-05-21 落地

把 Credits 计费系统的关键路径锁成契约测试 · 阻止下次重构悄悄改价 / 漏扣 /
错误地放行/拒绝用户。Credits 直接影响收入 · bug 直接亏钱。

覆盖 (按用户纪律第 4 条 · 加 5 大类场景):
  A. 价格规则 (纯数学 · 不连 DB):
     - PDF 分级: 当月 ≤ 200 张 ฿1.50 · > 200 张 ฿0.75 · 跨界自动拆段
     - Excel 字符: 50 字符 = 1 satang (฿0.01) · 向上取整
     - 边界: 199/200/201/250 used · 49/50/51 chars
  B. 余额检查 get_billing_status_combined:
     - 白名单 exempt → 允许 (跳 DB)
     - 无 tenant → 拒绝 + no_tenant
     - balance > 0 → 允许
     - balance <= 0 → 拒绝 + insufficient_balance
  C. 扣费 charge_ocr (失败不扣):
     - 未知 kind → ok=False · 无 DB 写
     - 无 tenant → ok=False · 无 DB 写
     - 豁免账号 → ok=True charged=0 · 无 DB 写
     - cost == 0 → ok=True · 无 DB 写
  D. 扣费 charge_ocr (成功路径 · 必写流水):
     - PDF: 必 UPDATE tenant_credits + INSERT credit_transactions
            + UPSERT monthly_page_usage (3 个写)
     - Excel: 必 UPDATE tenant_credits + INSERT credit_transactions
              (无 monthly_page_usage 写)
     - SELECT FOR UPDATE 必须存在 (防并发双扣)
  E. 重复请求语义 (用户纪律第 4 条):
     - charge_ocr 本身不幂等 (每次扣 · 锁定当前契约)
     - 重复防护在 app.py 层 file_hash 缓存 (find_ocr_by_hash) · 命中不扣
     - 测试两次调 charge_ocr → 写 2 笔流水 (符合"调用方负责 dedup"契约)

价格 v0.21 当前规则 (Korn 2026-05-21 拍板):
  PDF_TIER1_LIMIT_V21 = 200
  PDF_TIER1_PRICE_V21 = ฿1.50
  PDF_TIER2_PRICE_V21 = ฿0.75
  EXCEL_CHARS_PER_SATANG_V21 = 50
  EXCEL_SATANG_PRICE_V21 = ฿0.01
"""

from __future__ import annotations

import sys
import types
import unittest
from decimal import Decimal
from pathlib import Path
from typing import Any, List, Optional
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


# ────────────────────────────────────────────────────────────────────
# Stub native deps · 跟 test_tenant_isolation_contract.py 完全一致
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
    # 同一 fake cursor 同时挂到两路:get_billing_status_combined 先经 get_cursor 查 exempt,
    # 再经 get_cursor_rls 查 balance(charge_ocr/deduct_thb 亦走 RLS 游标)· executed 累计不丢。
    from contextlib import contextmanager

    cm = lambda *a, **k: _CursorCM(cursor)  # noqa: E731

    @contextmanager
    def _both():
        with patch.object(db, "get_cursor", cm), patch.object(db, "get_cursor_rls", cm):
            yield

    return _both()


# 常量
TENANT_A = "11111111-1111-1111-1111-111111111111"
USER_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _clear_exempt_cache():
    """每个测试前清空白名单 cache · 防测试间污染."""
    db._EXEMPT_CACHE_V21.clear()


def _all_sql(cursor: _Cursor) -> str:
    return "\n".join(s for s, _ in cursor.executed)


# ════════════════════════════════════════════════════════════════════
# A. 价格规则 · estimate_pdf_cost_thb (纯数学 · 不连 DB)
# ════════════════════════════════════════════════════════════════════
class PdfCostEstimationTests(unittest.TestCase):
    """锁定 v0.21 PDF 定价规则 · Korn 2026-05-21 拍板 ·
    任何价格改动必须先改本测试 · 防"悄悄改价"."""

    def test_zero_pages_zero_cost(self):
        self.assertEqual(db.estimate_pdf_cost_thb(0, 0), Decimal("0.00"))
        self.assertEqual(db.estimate_pdf_cost_thb(100, 0), Decimal("0.00"))

    def test_tier1_only_fresh_user(self):
        """0 used + 100 pages → 100 × ฿1.50 = ฿150.00"""
        self.assertEqual(db.estimate_pdf_cost_thb(0, 100), Decimal("150.00"))

    def test_tier1_full_at_200(self):
        """0 used + 200 pages → 200 × ฿1.50 = ฿300.00 (恰好 tier1 满)"""
        self.assertEqual(db.estimate_pdf_cost_thb(0, 200), Decimal("300.00"))

    def test_boundary_199_used_plus_1_page_still_tier1(self):
        """199 used + 1 page = 第 200 张 · 仍 tier1 → ฿1.50"""
        self.assertEqual(db.estimate_pdf_cost_thb(199, 1), Decimal("1.50"))

    def test_boundary_199_used_plus_2_pages_crosses_tier(self):
        """199 used + 2 pages → 1 张 tier1 (第 200) + 1 张 tier2 (第 201)
        = 1.50 + 0.75 = ฿2.25"""
        self.assertEqual(db.estimate_pdf_cost_thb(199, 2), Decimal("2.25"))

    def test_boundary_200_used_plus_1_page_is_tier2(self):
        """200 used + 1 page = 第 201 张 · 入 tier2 → ฿0.75"""
        self.assertEqual(db.estimate_pdf_cost_thb(200, 1), Decimal("0.75"))

    def test_tier2_fully(self):
        """250 used + 10 pages · 全部 tier2 → 10 × ฿0.75 = ฿7.50"""
        self.assertEqual(db.estimate_pdf_cost_thb(250, 10), Decimal("7.50"))

    def test_mixed_tier_crossing(self):
        """100 used + 150 pages → 100 张 tier1 (101-200) + 50 张 tier2 (201-250)
        = 100 × 1.50 + 50 × 0.75 = ฿150 + ฿37.50 = ฿187.50"""
        self.assertEqual(db.estimate_pdf_cost_thb(100, 150), Decimal("187.50"))

    def test_negative_inputs_treated_as_zero(self):
        """防御性: 负数当 0 · 不抛"""
        self.assertEqual(db.estimate_pdf_cost_thb(-10, 5), Decimal("7.50"))  # used=0 + 5 in tier1
        self.assertEqual(db.estimate_pdf_cost_thb(0, -5), Decimal("0.00"))

    def test_pricing_constants_locked(self):
        """价格常量必须等于 Korn 2026-05-21 拍板的值 · 改了请同步改本测试 + commit message 说明."""
        self.assertEqual(
            db.PDF_TIER1_LIMIT_V21, 200, "PDF tier1 阈值改了 = 业务模型变 · 请 Zihao 拍板"
        )
        self.assertEqual(db.PDF_TIER1_PRICE_V21, Decimal("1.50"))
        self.assertEqual(db.PDF_TIER2_PRICE_V21, Decimal("0.75"))


# ════════════════════════════════════════════════════════════════════
# A. 价格规则 · estimate_excel_cost_thb
# ════════════════════════════════════════════════════════════════════
class ExcelCostEstimationTests(unittest.TestCase):
    """锁定 Excel/Word/CSV 字符计费规则."""

    def test_zero_chars(self):
        self.assertEqual(db.estimate_excel_cost_thb(0), Decimal("0.00"))

    def test_boundary_49_chars_rounds_up_to_1_satang(self):
        """49 字符 · ceil(49/50) = 1 satang = ฿0.01"""
        self.assertEqual(db.estimate_excel_cost_thb(49), Decimal("0.01"))

    def test_boundary_50_chars_exactly_1_satang(self):
        """50 字符整 = 1 satang = ฿0.01"""
        self.assertEqual(db.estimate_excel_cost_thb(50), Decimal("0.01"))

    def test_boundary_51_chars_rounds_up_to_2_satang(self):
        """51 字符 · ceil(51/50) = 2 satang = ฿0.02 (向上取整)"""
        self.assertEqual(db.estimate_excel_cost_thb(51), Decimal("0.02"))

    def test_100_chars_exactly_2_satang(self):
        self.assertEqual(db.estimate_excel_cost_thb(100), Decimal("0.02"))

    def test_5000_chars_100_satang(self):
        """5000 字符 / 50 = 100 satang = ฿1.00"""
        self.assertEqual(db.estimate_excel_cost_thb(5000), Decimal("1.00"))

    def test_negative_treated_as_zero(self):
        self.assertEqual(db.estimate_excel_cost_thb(-100), Decimal("0.00"))

    def test_pricing_constants_locked(self):
        self.assertEqual(db.EXCEL_CHARS_PER_SATANG_V21, 50)
        self.assertEqual(db.EXCEL_SATANG_PRICE_V21, Decimal("0.01"))


# ════════════════════════════════════════════════════════════════════
# B. 余额检查 · get_billing_status_combined
# ════════════════════════════════════════════════════════════════════
class BillingStatusCombinedTests(unittest.TestCase):
    """前置余额检查 · 决定是否抛 402"""

    def setUp(self):
        _clear_exempt_cache()

    def test_exempt_user_always_allowed_no_db_lookup_for_balance(self):
        """🟢 白名单: is_billing_exempt=True · 允许 · 不查 balance"""
        # 第 1 次 cursor 是 is_user_billing_exempt 的 SELECT · 返 TRUE
        cur = _Cursor(fetchone_results=[{"x": True}])
        with _patch_cursor(cur):
            r = db.get_billing_status_combined(USER_A, TENANT_A)
        self.assertTrue(r["allowed"])
        self.assertTrue(r["is_exempt"])
        # 只该有 1 次 DB 查询 (exempt SELECT) · 不查 balance
        self.assertEqual(len(cur.executed), 1, "exempt user 不应查 balance · v0.21 性能要求")

    def test_no_tenant_rejected_with_no_tenant_code(self):
        """无 tenant: 拒绝 + error_code=no_tenant"""
        cur = _Cursor(fetchone_results=[{"x": False}])
        with _patch_cursor(cur):
            r = db.get_billing_status_combined(USER_A, None)
        self.assertFalse(r["allowed"])
        self.assertFalse(r["is_exempt"])
        self.assertEqual(r["error_code"], "no_tenant")

    def test_positive_balance_allowed(self):
        """余额 > 0 → allowed=True · error_code=None"""
        cur = _Cursor(
            fetchone_results=[
                {"x": False},  # exempt = False
                {"balance_thb": 100.0, "pages_used": 50},
            ]
        )
        with _patch_cursor(cur):
            r = db.get_billing_status_combined(USER_A, TENANT_A)
        self.assertTrue(r["allowed"])
        self.assertEqual(r["balance_thb"], 100.0)
        self.assertEqual(r["pages_used_this_month"], 50)
        self.assertIsNone(r["error_code"])

    def test_zero_balance_rejected_with_insufficient_code(self):
        """余额 = 0 → 拒绝 + insufficient_balance (P0 漏洞防回归 · 之前 0 余额能用 OCR)"""
        cur = _Cursor(
            fetchone_results=[
                {"x": False},
                {"balance_thb": 0.0, "pages_used": 0},
            ]
        )
        with _patch_cursor(cur):
            r = db.get_billing_status_combined(USER_A, TENANT_A)
        self.assertFalse(r["allowed"], "🔴 P0 防回归: 余额 0 不能放行 OCR (历史 v0.20 真出过)")
        self.assertEqual(r["error_code"], "insufficient_balance")

    def test_negative_balance_rejected(self):
        """余额负 (透支后) → 拒绝"""
        cur = _Cursor(
            fetchone_results=[
                {"x": False},
                {"balance_thb": -10.0, "pages_used": 200},
            ]
        )
        with _patch_cursor(cur):
            r = db.get_billing_status_combined(USER_A, TENANT_A)
        self.assertFalse(r["allowed"])
        self.assertEqual(r["error_code"], "insufficient_balance")

    def test_balance_lookup_uses_single_combined_query(self):
        """v0.21 性能要求: balance + pages_used 一次 SELECT 拿到 · 不能拆 3 次查"""
        cur = _Cursor(
            fetchone_results=[
                {"x": False},
                {"balance_thb": 50.0, "pages_used": 100},
            ]
        )
        with _patch_cursor(cur):
            db.get_billing_status_combined(USER_A, TENANT_A)
        # 应该 = 2 次 (1 次 exempt + 1 次 combined) · 不能 > 2
        self.assertEqual(
            len(cur.executed),
            2,
            "v0.21 性能要求: 非 exempt 用户最多 2 次 DB 查询 "
            "(exempt + combined). 否则会触发连接池打满 (v0.20 真出过)",
        )
        # 第 2 次必须是合并查询: tenant_credits LEFT JOIN monthly_page_usage
        second_sql = cur.executed[1][0]
        self.assertIn("tenant_credits", second_sql)
        self.assertIn("monthly_page_usage", second_sql)
        self.assertIn(
            "LEFT JOIN", second_sql, "必须 LEFT JOIN · 即使表无 row 也能返 0 而不是 KeyError"
        )


# ════════════════════════════════════════════════════════════════════
# B. is_user_billing_exempt · 白名单查询 + cache
# ════════════════════════════════════════════════════════════════════
class IsBillingExemptTests(unittest.TestCase):

    def setUp(self):
        _clear_exempt_cache()

    def test_returns_true_when_user_flagged(self):
        cur = _Cursor(fetchone_results=[{"x": True}])
        with _patch_cursor(cur):
            self.assertTrue(db.is_user_billing_exempt(USER_A))

    def test_returns_false_when_not_flagged(self):
        cur = _Cursor(fetchone_results=[{"x": False}])
        with _patch_cursor(cur):
            self.assertFalse(db.is_user_billing_exempt(USER_A))

    def test_returns_false_when_user_missing(self):
        cur = _Cursor(fetchone_results=[None])
        with _patch_cursor(cur):
            self.assertFalse(db.is_user_billing_exempt(USER_A))

    def test_empty_user_id_short_circuits_no_db(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            self.assertFalse(db.is_user_billing_exempt(""))
            self.assertFalse(db.is_user_billing_exempt(None))
        # 空 user_id 不该触发 DB 查 · 防 cache key 污染
        self.assertEqual(len(cur.executed), 0)

    def test_db_error_fails_safe_to_false(self):
        """🔴 安全: DB 挂了 → 返 False (=不豁免 = 走付费逻辑) ·
        而非 fail-open 返 True (会让所有人免费用)."""

        class _RaisingCursor(_Cursor):
            def execute(self, sql, params=None):
                raise RuntimeError("DB exploded")

        cur = _RaisingCursor()
        with _patch_cursor(cur):
            self.assertFalse(
                db.is_user_billing_exempt(USER_A),
                "DB 失败必须 fail-closed 到 not-exempt · 不能给所有人放行",
            )

    def test_cache_hit_skips_db_lookup(self):
        """v0.21 性能: 5 分钟 cache · 同 user 第 2 次不查 DB"""
        cur = _Cursor(fetchone_results=[{"x": True}])
        with _patch_cursor(cur):
            r1 = db.is_user_billing_exempt(USER_A)
            r2 = db.is_user_billing_exempt(USER_A)
        self.assertTrue(r1)
        self.assertTrue(r2)
        self.assertEqual(len(cur.executed), 1, "cache 命中应跳过 DB · v0.21 性能优化")


# ════════════════════════════════════════════════════════════════════
# C. charge_ocr · 失败不扣
# ════════════════════════════════════════════════════════════════════
class ChargeOcrFailsCleanlyTests(unittest.TestCase):
    """失败路径绝不能写 DB · 否则会"扣了但没记账"或"扣 0 但写流水"."""

    def setUp(self):
        _clear_exempt_cache()

    def test_no_tenant_returns_error_no_db_write(self):
        cur = _Cursor()
        with _patch_cursor(cur):
            r = db.charge_ocr(USER_A, None, "pdf", 100)
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "no_tenant")
        self.assertEqual(len(cur.executed), 0, "no_tenant 失败不允许任何 DB 写")

    def test_unknown_kind_returns_error_no_db_write(self):
        # 必须先让 exempt 返 False · 否则会走 exempt 早期 return
        cur = _Cursor(fetchone_results=[{"x": False}])
        with _patch_cursor(cur):
            r = db.charge_ocr(USER_A, TENANT_A, "doc-format-99", 100)
        self.assertFalse(r["ok"])
        self.assertIn("unknown_kind", r["error"])
        # 只允许 exempt 查询 · 不能写 tenant_credits / credit_transactions
        for sql, _ in cur.executed:
            self.assertNotIn("UPDATE tenant_credits", sql)
            self.assertNotIn("INSERT INTO credit_transactions", sql)

    def test_exempt_user_returns_ok_zero_no_db_write(self):
        """豁免账号: 直接返 ok=True charged=0 · 不写流水."""
        cur = _Cursor(fetchone_results=[{"x": True}])
        with _patch_cursor(cur):
            r = db.charge_ocr(USER_A, TENANT_A, "pdf", 100)
        self.assertTrue(r["ok"])
        self.assertEqual(r["charged_thb"], 0.0)
        self.assertTrue(r["exempt"])
        self.assertIsNone(r["transaction_id"])
        # 只允许 exempt 查询 · 没有 UPDATE/INSERT
        for sql, _ in cur.executed:
            self.assertNotIn("UPDATE tenant_credits", sql)
            self.assertNotIn("INSERT INTO credit_transactions", sql)

    def test_zero_cost_returns_ok_no_db_write(self):
        """0 字符 Excel · cost=0 · 不应写流水 (避免 ฿0 流水污染)."""
        cur = _Cursor(fetchone_results=[{"x": False}])
        with _patch_cursor(cur):
            r = db.charge_ocr(USER_A, TENANT_A, "excel", 0)
        self.assertTrue(r["ok"])
        self.assertEqual(r["charged_thb"], 0.0)
        # 不应有 UPDATE tenant_credits 写入
        for sql, _ in cur.executed:
            self.assertNotIn("UPDATE tenant_credits", sql)
            self.assertNotIn("INSERT INTO credit_transactions", sql)


# ════════════════════════════════════════════════════════════════════
# D. charge_ocr · 成功路径 · 必写流水
# ════════════════════════════════════════════════════════════════════
class ChargeOcrSuccessPathTests(unittest.TestCase):
    """成功扣费必须写 3 个表 (PDF) 或 2 个表 (Excel) · 不能漏."""

    def setUp(self):
        _clear_exempt_cache()

    def test_pdf_charge_writes_all_three_tables(self):
        """PDF 100 页 (0 used) = ฿150 · 必写 tenant_credits + credit_transactions + monthly_page_usage"""
        cur = _Cursor(
            fetchone_results=[
                {"x": False},  # is_user_billing_exempt
                {"u": 0},  # monthly pages_used lookup
                {"balance_thb": Decimal("500")},  # SELECT FOR UPDATE
                {"id": "txn-1"},  # INSERT credit_transactions RETURNING id
            ]
        )
        with _patch_cursor(cur):
            r = db.charge_ocr(USER_A, TENANT_A, "pdf", 100, history_id="h-1")

        self.assertTrue(r["ok"])
        self.assertEqual(r["charged_thb"], 150.0)
        self.assertEqual(r["balance_after"], 350.0)  # 500 - 150
        self.assertEqual(r["transaction_id"], "txn-1")

        sql_all = _all_sql(cur)
        # 必须写到 3 个目标表
        self.assertIn("SELECT balance_thb FROM tenant_credits", sql_all)
        self.assertIn("FOR UPDATE", sql_all, "必须 SELECT FOR UPDATE 锁行 · 防并发双扣")
        self.assertIn("UPDATE tenant_credits", sql_all)
        self.assertIn("INSERT INTO credit_transactions", sql_all)
        self.assertIn(
            "monthly_page_usage", sql_all, "PDF 必须更新月度页数统计 · 否则 tier1/tier2 算错"
        )
        self.assertIn("ON CONFLICT", sql_all, "monthly_page_usage 必须 UPSERT · 防当月第一次扣报错")

    def test_excel_charge_writes_only_credits_no_page_usage(self):
        """Excel 100 字符 = ฿0.02 · 写 tenant_credits + credit_transactions · 不写 monthly_page_usage"""
        cur = _Cursor(
            fetchone_results=[
                {"x": False},
                {"balance_thb": Decimal("100")},
                {"id": "txn-2"},
            ]
        )
        with _patch_cursor(cur):
            r = db.charge_ocr(USER_A, TENANT_A, "excel", 100)

        self.assertTrue(r["ok"])
        self.assertEqual(r["charged_thb"], 0.02)

        sql_all = _all_sql(cur)
        self.assertIn("UPDATE tenant_credits", sql_all)
        self.assertIn("INSERT INTO credit_transactions", sql_all)
        # Excel 不该写月度页数表 (那是 PDF 专用)
        self.assertNotIn(
            "INSERT INTO monthly_page_usage", sql_all, "Excel 扣费不应该写 PDF 月度页数表"
        )

    def test_charge_writes_negative_amount_to_transaction(self):
        """credit_transactions.amount_thb 必须是负数 (扣费 · 不是充值)"""
        cur = _Cursor(
            fetchone_results=[
                {"x": False},
                {"balance_thb": Decimal("100")},
                {"id": "txn-3"},
            ]
        )
        with _patch_cursor(cur):
            db.charge_ocr(USER_A, TENANT_A, "excel", 5000)  # = ฿1.00

        # 找到 INSERT credit_transactions
        for sql, params in cur.executed:
            if "INSERT INTO credit_transactions" in sql:
                # params 里第 3 个是 amount_thb (按 INSERT 列顺序: tenant_id, user_id, type, amount_thb, ...)
                # 应是 "-1.00" 字符串
                amt_str = str(params[2])
                self.assertTrue(
                    amt_str.startswith("-"), f"扣费 amount_thb 必须负数 · 实际: {amt_str}"
                )
                return
        self.fail("没找到 INSERT INTO credit_transactions")

    def test_charge_handles_missing_tenant_credits_row_with_upsert(self):
        """tenant_credits 没行 → 自动 INSERT 0 → 再继续扣"""
        cur = _Cursor(
            fetchone_results=[
                {"x": False},  # exempt
                {"u": 0},  # monthly_page_usage = 0
                None,  # SELECT FOR UPDATE 没行
                {"balance_thb": Decimal("0")},  # INSERT 返 0
                {"id": "txn-4"},  # INSERT credit_transactions
            ]
        )
        with _patch_cursor(cur):
            r = db.charge_ocr(USER_A, TENANT_A, "pdf", 10)

        self.assertTrue(r["ok"])
        sql_all = _all_sql(cur)
        # 必须有"建零行"逻辑
        self.assertIn("INSERT INTO tenant_credits", sql_all)
        # 然后还得继续扣费
        self.assertIn("UPDATE tenant_credits", sql_all)
        self.assertIn("INSERT INTO credit_transactions", sql_all)


# ════════════════════════════════════════════════════════════════════
# E. 重复请求语义 (用户纪律第 4 条 · "重复请求不重复扣")
# ════════════════════════════════════════════════════════════════════
class DuplicateRequestSemanticsTests(unittest.TestCase):
    """重复防护**不**在 charge_ocr 层 · 在 app.py 的 file_hash 缓存层
    (find_ocr_by_hash) · 命中直接返旧结果 · charge_ocr 都不调.

    本测试锁定**当前真实契约**:
      - charge_ocr 本身非幂等 · 调 2 次 = 扣 2 次 = 写 2 笔流水
      - 这是设计 (合理) · 因为去重在上游 file_hash 缓存
      - 若未来想给 charge_ocr 加 history_id 幂等性 · 必须先改本测试 + 加 unique index"""

    def setUp(self):
        _clear_exempt_cache()

    def test_charge_ocr_twice_writes_two_transactions(self):
        """🔵 当前契约: charge_ocr(history_id='h-1') 调 2 次 → 2 笔流水 (锁定)

        注意: is_user_billing_exempt 有 5 分钟 cache · 第 2 次不查 DB ·
        所以 fixture 池不放 call 2 的 {x: False}."""
        results_pool = [
            {"x": False},  # call 1: exempt (DB 查 · 结果被缓存)
            {"u": 0},  # call 1: monthly used
            {"balance_thb": Decimal("100")},  # call 1: SELECT FOR UPDATE
            {"id": "txn-A"},  # call 1: INSERT credit_transactions
            # call 2: exempt 走 cache · 不消耗 fixture
            {"u": 10},  # call 2: monthly used (累加后)
            {"balance_thb": Decimal("85")},  # call 2: balance
            {"id": "txn-B"},  # call 2: INSERT credit_transactions
        ]
        cur = _Cursor(fetchone_results=results_pool)
        with _patch_cursor(cur):
            r1 = db.charge_ocr(USER_A, TENANT_A, "pdf", 10, history_id="h-1")
            r2 = db.charge_ocr(USER_A, TENANT_A, "pdf", 10, history_id="h-1")

        self.assertTrue(r1["ok"])
        self.assertTrue(r2["ok"])
        # 关键: 2 笔不同的 transaction_id (没幂等)
        self.assertNotEqual(r1["transaction_id"], r2["transaction_id"])

        # 流水表应该有 2 个 INSERT
        insert_count = sum(1 for sql, _ in cur.executed if "INSERT INTO credit_transactions" in sql)
        self.assertEqual(
            insert_count,
            2,
            "当前契约: charge_ocr 不幂等 · 重复调 = 2 笔流水. "
            "去重在 app.py file_hash 缓存层 (find_ocr_by_hash). "
            "若未来想改幂等 · 请先改本测试 + 给 credit_transactions 加 unique index.",
        )

    def test_file_hash_cache_dedup_path_exists(self):
        """🔵 验证去重路径在: find_ocr_by_hash 函数存在 + 可被 app.py 调用
        (实际命中后 OCR 不跑 · charge_ocr 不调 · 由 OCR 路由集成测试覆盖)"""
        self.assertTrue(
            hasattr(db, "find_ocr_by_hash"),
            "去重路径函数必须存在: db.find_ocr_by_hash · "
            "app.py 上游靠它跳过重复 OCR + 跳过重复扣费",
        )


# ════════════════════════════════════════════════════════════════════
# F. 并发防护 · SELECT FOR UPDATE 锁定 + 月度页数 UPSERT
# ════════════════════════════════════════════════════════════════════
class ConcurrencySafetyContractTests(unittest.TestCase):
    """并发场景下 · 同 tenant 2 个 OCR 同时完成 · 必须串行扣费."""

    def setUp(self):
        _clear_exempt_cache()

    def test_charge_uses_for_update_lock(self):
        """SELECT FOR UPDATE 是单原子事务核心 · 必须存在"""
        cur = _Cursor(
            fetchone_results=[
                {"x": False},
                {"u": 0},
                {"balance_thb": Decimal("100")},
                {"id": "txn-1"},
            ]
        )
        with _patch_cursor(cur):
            db.charge_ocr(USER_A, TENANT_A, "pdf", 10)
        # 找出 balance SELECT 那条
        select_sqls = [s for s, _ in cur.executed if "SELECT balance_thb FROM tenant_credits" in s]
        self.assertEqual(len(select_sqls), 1)
        self.assertIn(
            "FOR UPDATE",
            select_sqls[0],
            "🔴 必须 SELECT FOR UPDATE · 否则并发 OCR 完成时 "
            "可能双扣 (读到同一 balance · 各扣一次).",
        )

    def test_pdf_monthly_usage_uses_upsert(self):
        """monthly_page_usage UPSERT (ON CONFLICT) · 不能用 INSERT OR UPDATE 两次"""
        cur = _Cursor(
            fetchone_results=[
                {"x": False},
                {"u": 0},
                {"balance_thb": Decimal("100")},
                {"id": "txn-1"},
            ]
        )
        with _patch_cursor(cur):
            db.charge_ocr(USER_A, TENANT_A, "pdf", 5)
        sql_all = _all_sql(cur)
        self.assertIn(
            "ON CONFLICT",
            sql_all,
            "monthly_page_usage 必须用 ON CONFLICT 单语句 · "
            "防 SELECT-then-INSERT 的 TOCTOU race condition.",
        )


# ════════════════════════════════════════════════════════════════════
# G. 跨租户·扣费不能扣到 wrong tenant
# ════════════════════════════════════════════════════════════════════
class CrossTenantBillingIsolationTests(unittest.TestCase):
    """charge_ocr 调用时 tenant_id 必须出现在所有 DB 写入中 ·
    不能误扣到别的 tenant."""

    def setUp(self):
        _clear_exempt_cache()

    def test_charge_uses_passed_tenant_id_for_all_writes(self):
        cur = _Cursor(
            fetchone_results=[
                {"x": False},
                {"u": 0},
                {"balance_thb": Decimal("500")},
                {"id": "txn-1"},
            ]
        )
        with _patch_cursor(cur):
            db.charge_ocr(USER_A, TENANT_A, "pdf", 50)

        # 所有写入操作的 params 里必须含 TENANT_A
        write_sqls = [
            (s, p)
            for s, p in cur.executed
            if any(
                verb in s
                for verb in (
                    "UPDATE tenant_credits",
                    "INSERT INTO credit_transactions",
                    "INSERT INTO monthly_page_usage",
                    "SELECT balance_thb",
                )
            )
        ]
        for sql, params in write_sqls:
            params_str = [str(p) for p in (params or ())]
            self.assertIn(
                TENANT_A,
                params_str,
                f"扣费 SQL 必须按调用方 tenant_id 写入 · "
                f"SQL: {sql[:60]}... · params: {params_str}",
            )


if __name__ == "__main__":
    unittest.main()
