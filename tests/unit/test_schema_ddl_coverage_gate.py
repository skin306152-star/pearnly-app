# -*- coding: utf-8 -*-
"""scripts/check_schema_ddl_coverage.py 的正证 + 反证。

正证 = 当前仓库真的过闸;反证 = 喂有毒输入必须报红。没有反证的清单式闸会
在"名单写死了没人核对"时静默失效(见 [[css-property-set-is-not-effect-working]]:
闸报绿 ≠ 闸看过)。
"""

import shutil
import sys
import tempfile
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

    def test_debt_list_is_empty(self):
        # 2026-08-01 起闸是硬门。名单一旦长回去,等于又开始记债——要么是真表没 DDL,
        # 要么是有人拿名单糊闸,两种都得在 review 里被看见。
        self.assertEqual(gate.KNOWN_UNCOVERED, {})


class ScanScopeTests(unittest.TestCase):
    """扫描范围是这个闸的立身之本:tests/ 里的手抄桩、docs/ 里的快照都不算覆盖
    (误收任一个,全表恒绿)。26 张欠账还清之后,拿真仓库断言"users 没被覆盖"
    已经证明不了任何事,所以毒饵改放进只有毒饵的合成目录树。"""

    def _root(self, files):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        for rel, text in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return d

    def test_tests_dir_ddl_does_not_count(self):
        root = self._root({"tests/integration/test_x.py": "CREATE TABLE IF NOT EXISTS bait_a ()"})
        self.assertEqual(gate.product_ddl_tables(root), set())

    def test_docs_snapshot_does_not_count(self):
        root = self._root({"docs/db/prod-schema.sql": "CREATE TABLE IF NOT EXISTS bait_b ()"})
        self.assertEqual(gate.product_ddl_tables(root), set())

    def test_alembic_sql_payload_counts(self):
        # 2026-08-01 新增的扫描面:baseline 的 DDL 载荷是 .sql 不是 .py。
        # 这一条漏了,26 张刚补好的表当场又算"无 DDL",闸整片报红。
        root = self._root({"alembic/sql/legacy.sql": "CREATE TABLE IF NOT EXISTS bait_c ()"})
        self.assertEqual(gate.product_ddl_tables(root), {"bait_c"})


class PoisonedInputTests(unittest.TestCase):
    def test_new_table_without_ddl_is_flagged(self):
        problems = gate.evaluate({"users", "brand_new_table"}, {"users"}, set())
        self.assertTrue(any("brand_new_table" in p for p in problems), problems)

    def test_stale_entry_flagged_when_ddl_added(self):
        problems = gate.evaluate({"users"}, {"users"}, {"users"})
        self.assertTrue(any("名单过期" in p and "users" in p for p in problems), problems)

    def test_stale_entry_flagged_when_table_dropped(self):
        problems = gate.evaluate({"users"}, {"users"}, {"users", "gone_table"})
        self.assertTrue(any("gone_table" in p for p in problems), problems)

    def test_losing_the_baseline_reds_every_legacy_table(self):
        # 反证 baseline 本身:假设 001a_legacy_tables 的 DDL 没了(文件被删 / 被改坏 /
        # 扫描面又漏了 alembic/sql),闸必须把每一张表逐个点名,而不是安静地绿。
        prod = gate.snapshot_tables(gate.SNAPSHOT.read_text(encoding="utf-8"))
        problems = gate.evaluate(prod, set(), set())
        self.assertEqual(len(problems), len(prod) - 1)  # alembic_version 不算
        self.assertTrue(any("表 users " in p for p in problems), problems[:3])


if __name__ == "__main__":
    unittest.main()
