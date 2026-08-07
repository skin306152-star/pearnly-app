# -*- coding: utf-8 -*-
"""分片 runner 的覆盖面契约:切段前后模块集合必须逐一相同、字母序不许打乱。

分片并行只许改「怎么跑」,不许改「跑什么/什么顺序」—— 少一个模块是静默漏测,
打乱顺序会踩存量测试的顺序耦合(2026-08-02 乱序分桶实测炸出 auth_password 两红)。
"""

import unittest
from pathlib import Path

from scripts.run_unit_sharded import (
    UNIT_DIR,
    _collect_times,
    _is_load_failure,
    collect_modules,
    make_shards,
)


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


class HookUsesImpactPlanner(unittest.TestCase):
    """钩子通过 impact.py 分流,生产 Python 仍由 planner 保留 full fallback。"""

    def test_hook_invokes_impact_and_planner_keeps_full_runner(self):
        hook = (Path(UNIT_DIR).parents[1] / "scripts" / "git-hooks" / "pre-push").read_text(
            encoding="utf-8"
        )
        impact = (Path(UNIT_DIR).parents[1] / "scripts" / "impact.py").read_text(encoding="utf-8")
        self.assertIn("python scripts/impact.py --base", hook)
        self.assertIn("scripts/run_unit_sharded.py", impact)
        self.assertNotIn("--exclude", impact)


class LoadFailureClassificationTests(unittest.TestCase):
    """抗负载自愈分类核(2026-08-06):只该把「初始化/负载型」红判成可复跑,
    任何 FAIL:(断言失败)必须直接红——复跑是在掩盖确定性失败。"""

    _SETUPCLASS = (
        "ERROR: setUpClass (tests.unit.test_some_module)\n"
        "----------------------------------------------------------------------\n"
        "Traceback (most recent call last):\n"
        "  File ...\n"
    )

    def test_all_setupclass_errors_are_healable(self):
        self.assertTrue(_is_load_failure(1, self._SETUPCLASS))

    def test_crashed_worker_rc_is_healable(self):
        # 0xC0000142 = 3221225794:Windows 子进程初始化失败(并行抢资源典型)
        self.assertTrue(_is_load_failure(3221225794, ""))

    def test_any_fail_line_is_never_healable(self):
        out = self._SETUPCLASS + "FAIL: test_assert (tests.unit.test_x)\n"
        self.assertFalse(_is_load_failure(1, out))
        # 即使 returncode 是 0xC0000142,有 FAIL 也直接红(断言失败优先级最高)
        self.assertFalse(_is_load_failure(3221225794, out))

    def test_plain_test_error_is_not_healable(self):
        out = "ERROR: test_foo (tests.unit.test_x)\n" + self._SETUPCLASS
        self.assertFalse(_is_load_failure(1, out))

    def test_nonzero_exit_without_failure_lines_is_not_healable(self):
        # 无 FAIL 无 ERROR 却非零退出:未知红,不浪费一次全片重跑
        self.assertFalse(_is_load_failure(2, "Ran 0 tests\n"))

    def test_zero_exit_with_error_text_is_not_healable(self):
        # exit 0 根本走不到复跑,但分类函数本身不把 0 当红
        self.assertFalse(_is_load_failure(0, self._SETUPCLASS))


class TimesCollectTests(unittest.TestCase):
    def test_collect_times_merges_shard_mark_lines(self):
        all_times = {}
        _collect_times('SHARD_TIMES_JSON:{"tests.unit.test_a": 1.5}\n', all_times)
        _collect_times('noise\nSHARD_TIMES_JSON:{"tests.unit.test_b": 2.5}\n', all_times)
        self.assertEqual(all_times, {"tests.unit.test_a": 1.5, "tests.unit.test_b": 2.5})

    def test_collect_times_ignores_bad_json(self):
        all_times = {"keep": 1.0}
        _collect_times("SHARD_TIMES_JSON:{not json}\n", all_times)
        self.assertEqual(all_times, {"keep": 1.0})
