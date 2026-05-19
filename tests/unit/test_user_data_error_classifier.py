#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_user_data_error_classifier.py

守门测试 · 批 1 改动 3 (Zihao 2026-05-19 拍板 · v118.34.33).

`db.is_user_data_error()` 是 retry 决策的源头 · 如果它返 False · 用户
数据错(ERR_NO_CLIENT / 重复发票 / 客户码缺映射)会被丢进 retry 队列
反复推 MR.ERP · 制造无效负载。所以这条逻辑必须有强守门。

覆盖:
  1. ERR_* 前缀全集 (USER_DATA_ERROR_CODES) · 一个都不能漏
  2. 泰文 raw 模式 (USER_DATA_ERROR_THAI_PATTERNS) · 直接出现在 error_msg
  3. 非用户数据错的常见情况返 False (网络/timeout/session/未知)
  4. 边界:None / "" / 不含任何关键词的随机串
  5. 包含 ERR_NO_CLIENT 的复合字符串("...ERR_NO_CLIENT, retry skipped")
"""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Test 环境可能没装 psycopg2 · 但 is_user_data_error 是纯字符串逻辑 ·
# 跟 PG 一点关系没有. stub 出 psycopg2 让 db.py import 通过即可.
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
        def __init__(self, *a, **k): pass
        def getconn(self): raise RuntimeError("stub")
        def putconn(self, *a, **k): pass
        def closeall(self): pass
    fake_pg.pool.ThreadedConnectionPool = _StubPool
    fake_pg.pool.SimpleConnectionPool = _StubPool
    fake_pg.sql = types.ModuleType("psycopg2.sql")
    fake_pg.sql.SQL = lambda s: s
    fake_pg.sql.Identifier = lambda s: s
    sys.modules["psycopg2"] = fake_pg
    sys.modules["psycopg2.extras"] = fake_pg.extras
    sys.modules["psycopg2.pool"] = fake_pg.pool
    sys.modules["psycopg2.sql"] = fake_pg.sql


import db as DB  # noqa: E402


class UserDataErrorCodeCoverageTests(unittest.TestCase):
    """USER_DATA_ERROR_CODES 必须覆盖产品规则里的所有用户数据错 code."""

    REQUIRED_CODES = (
        "ERR_NO_CLIENT",
        "ERR_NO_CUSTOMER_MAPPING",
        "ERR_NO_INVOICE_NO",
        "ERR_DUPLICATE_INVOICE",
        "ERR_DATE_FUTURE",
        "ERR_INVOICE_NO_TOO_LONG",
        "ERR_CUSTOMER_CODE_TOO_LONG",
        "ERR_NEGATIVE_AMOUNT",
    )

    def test_required_codes_all_in_set(self):
        missing = [c for c in self.REQUIRED_CODES if c not in DB.USER_DATA_ERROR_CODES]
        self.assertFalse(
            missing,
            f"USER_DATA_ERROR_CODES 漏了关键 code: {missing}. "
            f"这些 code 是不可重试的用户数据错 · 漏掉会导致 retry worker "
            f"反复推 MR.ERP 制造无效负载.",
        )


class IsUserDataErrorPositiveTests(unittest.TestCase):
    """正向: 应该判 True 的情况."""

    def test_bare_err_code(self):
        self.assertTrue(DB.is_user_data_error("ERR_NO_CLIENT"))

    def test_err_code_in_compound_message(self):
        self.assertTrue(
            DB.is_user_data_error(
                "ERR_NO_CLIENT: history.client_id is None, "
                "wizard 让用户先指定 Pearnly 客户"
            )
        )

    def test_duplicate_invoice_err_code(self):
        self.assertTrue(
            DB.is_user_data_error("ERR_DUPLICATE_INVOICE: invoice_no 已存在")
        )

    def test_thai_raw_duplicate_pattern_1(self):
        # MR.ERP 报错的 raw 泰文 · 直接命中 USER_DATA_ERROR_THAI_PATTERNS
        self.assertTrue(
            DB.is_user_data_error("เลขที่ดังกล่าวมีอยู่ในระบบแล้ว")
        )

    def test_thai_raw_duplicate_pattern_2(self):
        self.assertTrue(DB.is_user_data_error("เลขที่เอกสารซ้ำ"))

    def test_thai_raw_customer_missing(self):
        self.assertTrue(
            DB.is_user_data_error("ไม่พบข้อมูลรหัสลูกค้า")
        )

    def test_all_required_codes_individually(self):
        for code in UserDataErrorCodeCoverageTests.REQUIRED_CODES:
            with self.subTest(code=code):
                self.assertTrue(
                    DB.is_user_data_error(code),
                    f"{code} 在 USER_DATA_ERROR_CODES 里但 is_user_data_error 没命中",
                )


class IsUserDataErrorNegativeTests(unittest.TestCase):
    """反向: 不应该判 True 的情况(否则 retry worker 会错误丢弃可重试错)."""

    def test_none(self):
        self.assertFalse(DB.is_user_data_error(None))

    def test_empty_string(self):
        self.assertFalse(DB.is_user_data_error(""))

    def test_network_timeout(self):
        # ETIMEDOUT / Connection reset 都是技术错 · 应 retry
        self.assertFalse(DB.is_user_data_error("ETIMEDOUT after 30s"))
        self.assertFalse(DB.is_user_data_error("Connection reset by peer"))

    def test_playwright_session_expired(self):
        # session 丢失是技术错 · re-login 后能恢复
        self.assertFalse(
            DB.is_user_data_error(
                "Page navigated to login.php · session expired"
            )
        )

    def test_listing_fetch_timeout(self):
        # listing 30s × 3 retries 失败 · 不是用户数据错 · MR.ERP 慢的事
        self.assertFalse(
            DB.is_user_data_error("listing fetch failed: wait_for_selector timeout")
        )

    def test_random_text(self):
        self.assertFalse(DB.is_user_data_error("totally unrelated text"))
        self.assertFalse(DB.is_user_data_error("500 Internal Server Error"))


if __name__ == "__main__":
    unittest.main()
