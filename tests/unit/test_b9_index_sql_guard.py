#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_b9_index_sql_guard.py · REFACTOR-WA-B9

守护 scripts/sql/b9_perf_indexes.sql 的安全不变量(防后续编辑引入锁表/破坏性 DDL):
  1. 每条建索引都用 CONCURRENTLY(大表在线建不锁写)。
  2. 每条都 IF NOT EXISTS(幂等可重复执行)。
  3. 不含破坏性语句(DROP / DELETE / TRUNCATE / ALTER)。
  4. 覆盖审计认定的 3 个缺口索引。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_PATH = PROJECT_ROOT / "scripts" / "sql" / "b9_perf_indexes.sql"

EXPECTED_INDEXES = {
    "idx_ocr_history_user_created",
    "idx_erp_push_logs_dedup",
    "idx_erp_push_logs_user_created",
}


class B9IndexSqlGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sql = SQL_PATH.read_text(encoding="utf-8")
        # 按 ; 切语句 · 去掉整行注释行后保留含 CREATE INDEX 的语句
        self.creates = []
        for stmt in self.sql.split(";"):
            lines = [ln for ln in stmt.splitlines() if not ln.strip().startswith("--")]
            body = " ".join(lines).strip()
            if "CREATE INDEX" in body.upper():
                self.creates.append(body)

    def test_file_exists_and_has_creates(self) -> None:
        self.assertTrue(SQL_PATH.exists())
        self.assertEqual(len(self.creates), 3)

    def test_all_concurrent_and_if_not_exists(self) -> None:
        for stmt in self.creates:
            flat = " ".join(stmt.split())
            self.assertIn("CONCURRENTLY", flat.upper(), f"非并发建索引会锁表: {flat}")
            self.assertIn("IF NOT EXISTS", flat.upper(), f"非幂等: {flat}")

    def test_no_destructive_ddl(self) -> None:
        for bad in ("DROP ", "DELETE ", "TRUNCATE", "ALTER "):
            self.assertNotIn(bad, self.sql.upper(), f"不应含破坏性语句: {bad}")

    def test_covers_audited_gaps(self) -> None:
        for name in EXPECTED_INDEXES:
            self.assertIn(name, self.sql, f"缺审计认定的索引: {name}")


if __name__ == "__main__":
    unittest.main()
