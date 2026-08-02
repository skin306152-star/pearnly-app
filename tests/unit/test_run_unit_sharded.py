# -*- coding: utf-8 -*-
"""分片 runner 的覆盖面契约:切段前后模块集合必须逐一相同、字母序不许打乱。

分片并行只许改「怎么跑」,不许改「跑什么/什么顺序」—— 少一个模块是静默漏测,
打乱顺序会踩存量测试的顺序耦合(2026-08-02 乱序分桶实测炸出 auth_password 两红)。
"""

import unittest
from pathlib import Path

from scripts.run_unit_sharded import UNIT_DIR, collect_modules, make_shards


class CollectMatchesDiscover(unittest.TestCase):
    def test_collect_covers_every_test_file(self):
        files = {p.stem for p in Path(UNIT_DIR).glob("test_*.py")}
        collected = {m.rsplit(".", 1)[1] for m, _ in collect_modules()}
        self.assertEqual(collected, files)
        self.assertIn("test_run_unit_sharded", collected)  # 本文件自身也在射程内


class ShardsPartitionExactly(unittest.TestCase):
    def test_no_loss_no_dup_and_order_preserved(self):
        mods = collect_modules()
        ordered = [m for m, _ in mods]
        for n in (1, 4, 6, 50):
            for times in ({}, {ordered[0]: 30.0, ordered[-1]: 0.01}):
                shards = make_shards(mods, n, times)
                flat = [m for s in shards for m in s]
                self.assertEqual(flat, ordered, f"workers={n} times={bool(times)}")
                self.assertTrue(all(s for s in shards), f"workers={n} 出了空桶")

    def test_more_workers_than_modules_still_partitions(self):
        mods = [("tests.unit.test_a", 10), ("tests.unit.test_b", 20)]
        shards = make_shards(mods, 8, {})
        self.assertEqual([m for s in shards for m in s], ["tests.unit.test_a", "tests.unit.test_b"])


class HookRunsFullSuite(unittest.TestCase):
    """钩子对 runner 不许带 --exclude:全量就是全量,裁剪清单是会被蚕食的风险面。

    2026-08-03 曾因 scan_camera 单模块 323s 裁剪过一天;虚拟时钟治本(→5s)后撤掉。
    再要裁剪,先治慢模块本身。"""

    def test_hook_invokes_runner_without_exclude(self):
        hook = (Path(UNIT_DIR).parents[1] / "scripts" / "git-hooks" / "pre-push").read_text(
            encoding="utf-8"
        )
        self.assertIn("python scripts/run_unit_sharded.py --quiet", hook)
        self.assertNotIn("--exclude", hook)
