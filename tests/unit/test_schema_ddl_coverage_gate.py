# -*- coding: utf-8 -*-
"""scripts/check_schema_ddl_coverage.py 的正证 + 反证。

正证 = 当前仓库真的过闸;反证 = 喂有毒输入必须报红。没有反证的清单式闸会
在"名单写死了没人核对"时静默失效(见 [[css-property-set-is-not-effect-working]]:
闸报绿 ≠ 闸看过)。
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_schema_ddl_coverage as gate  # noqa: E402


class SnapshotIsTheFactSourceTests(unittest.TestCase):
    def test_snapshot_exists_and_parses(self):
        self.assertTrue(gate.SNAPSHOT.is_file(), "生产 schema 快照缺失")
        tables = gate.snapshot_tables(gate.SNAPSHOT.read_text(encoding="utf-8"))
        self.assertGreater(len(tables), 100, "快照解析不出表名,正则或格式漂了")
        self.assertIn("users", tables)

    def test_repo_passes_today(self):
        prod = gate.snapshot_tables(gate.SNAPSHOT.read_text(encoding="utf-8"))
        covered = gate.product_ddl_tables()
        self.assertEqual(gate.evaluate(prod, covered, set(gate.KNOWN_UNCOVERED)), [])

    def test_known_uncovered_really_is_uncovered(self):
        # 名单不是摆设:里面每张表在产品代码里确实没有 CREATE。有一张被补上了
        # 却忘了删名单,evaluate 会报"名单过期"——这里先直接断死,定位更快。
        covered = gate.product_ddl_tables()
        self.assertEqual(sorted(set(gate.KNOWN_UNCOVERED) & covered), [])

    def test_tests_dir_ddl_does_not_count_as_coverage(self):
        # 闸的立身之本:测试桩里的手抄 DDL 不算数。users 只在 tests/integration
        # 有 CREATE,若扫描范围误收 tests/,它会凭空"被覆盖"。
        self.assertNotIn("users", gate.product_ddl_tables())

    def test_snapshot_file_itself_does_not_count(self):
        # 快照在 docs/ 下,自带 176 条 CREATE TABLE。扫描范围若误收 docs/,
        # 全部表恒绿 —— 闸变成永远通过的摆设。
        self.assertNotIn("api_keys", gate.product_ddl_tables())


class PoisonedInputTests(unittest.TestCase):
    def test_new_table_without_ddl_is_flagged(self):
        problems = gate.evaluate({"users", "brand_new_table"}, {"users"}, {"users"})
        self.assertTrue(any("brand_new_table" in p for p in problems), problems)

    def test_stale_entry_flagged_when_ddl_added(self):
        problems = gate.evaluate({"users"}, {"users"}, {"users"})
        self.assertTrue(any("名单过期" in p and "users" in p for p in problems), problems)

    def test_stale_entry_flagged_when_table_dropped(self):
        problems = gate.evaluate({"users"}, {"users"}, {"users", "gone_table"})
        self.assertTrue(any("gone_table" in p for p in problems), problems)

    def test_real_debt_would_be_caught_with_empty_baseline(self):
        # 名单清空 = 装闸当下的"未修代码"状态:26 张真欠账必须被逐张点名,
        # 证明闸命中的是真问题,不是靠名单把自己糊过去。
        prod = gate.snapshot_tables(gate.SNAPSHOT.read_text(encoding="utf-8"))
        problems = gate.evaluate(prod, gate.product_ddl_tables(), set())
        self.assertEqual(len(problems), len(gate.KNOWN_UNCOVERED))
        self.assertTrue(any("表 users " in p for p in problems), problems[:3])


if __name__ == "__main__":
    unittest.main()
