#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_check_file_size_gate.py

防屎山闸 #1(scripts/check_file_size.py)的覆盖率反证。

为什么要有这一份:2026-07-31 实测,`static/pos/**` 与 `static/scan/**` 一个都不在 MONITORED_GLOBS
的射程里 —— 收银 SPA 从上线起就没被 500 行硬线管过,期间 pos-cashier.js 长到 1252、本批新写的
pos-scan.js 长到 530,而闸一路报 PASS。**闸报绿不等于闸看过**,而"看没看过"这件事本身也得有东西
守着,否则下一次把哪个目录漏掉,还是只有人眼能发现。

所以这里断的不是"闸的代码写对了",是两侧各一条真会红的证据:
  正向  在真的 static/pos/ 下放一个 501 行文件 → 闸必须当场抓到(闸真的看得见这个目录)
  反向  把某条基线豁免摘掉 → 那个真存在的巨石必须当场变红(豁免真的在挡红,不是摆设)
两条都用真仓库里的真文件跑,不喂假路径 —— 拿桩验桩的话,glob 写错一个字符照样全绿。

2026-08-01 改口径:存量豁免从 check_file_size.py 里那本 basename 字典
(EXEMPT_CURRENT_BIG_FILES)换成了 scripts/file_size_baseline.json —— 键改成仓库相对路径,
且只此一套(两套豁免机制并存必漂,理由写在闸的文件头)。本文件的每条断言原样保留,
只把"豁免"这个词指向新的那本账。

与 tests/unit/test_file_size_gate.py 的分工:那边验**机制**(新越线要红 / 基线涨要红 /
降了要提示 / 词典豁免面必须真是纯词典);这边验**射程与账本**(/pos 与 /scan 真在射程里、
每条记账都真在挡红、不留余量、不跨目录串味)。改闸时两份都要跑。
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MOD_PATH = PROJECT_ROOT / "scripts" / "check_file_size.py"
_spec = importlib.util.spec_from_file_location("check_file_size", _MOD_PATH)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

# 这两个目录是本次补进射程的;各挑一个真源文件当哨兵。
POS_SENTINEL = "static/pos/pos-scan.js"
SCAN_SENTINEL = "static/scan/scan-wedge.js"


def _statuses(
    ceiling: int = gate.DEFAULT_CEILING, baseline: dict[str, int] | None = None
) -> dict[str, tuple[str, int, int]]:
    """跑一遍真实收集 + 判定,按仓库相对路径索引。

    baseline 省略时读真账本(scripts/file_size_baseline.json);要验"摘掉某条记账会不会红"
    就把改过的那本传进来 —— 不再像旧字典那样去改模块全局,免得用例之间互相串。
    """
    base = gate.load_baseline() if baseline is None else baseline
    out = {}
    for path in gate.collect_files():
        row = gate.check_one(path, ceiling, base)
        out[row.rel] = (row.status, row.lines, row.limit)
    return out


class GateActuallySeesPosAndScan(unittest.TestCase):
    """闸自检:射程里没有这两个目录的话,下面每条断言都会"通过"得毫无意义。"""

    def setUp(self):
        self.seen = _statuses()

    def test_pos_spa_sources_are_in_range(self):
        self.assertIn(POS_SENTINEL, self.seen, "收银 SPA 不在射程里 —— 闸报 PASS 只是没看见")

    def test_scan_base_sources_are_in_range(self):
        self.assertIn(SCAN_SENTINEL, self.seen, "扫码地基不在射程里")

    def test_the_whole_repo_is_currently_clean(self):
        fails = {rel: v for rel, v in self.seen.items() if v[0] == "FAIL"}
        self.assertEqual(fails, {}, "本闸当前就是红的 —— 先修这些,反证才有意义")


class NewOversizeFileIsCaught(unittest.TestCase):
    """正向反证:往真目录里放一个超线文件,闸必须抓到。

    文件真的落在 static/pos/ 下(不是喂给函数一个假路径):glob 写错、目录写错、扩展名漏了,
    这一条都会红 —— 那正是本次要守住的东西。
    """

    def setUp(self):
        self.probe = PROJECT_ROOT / "static" / "pos" / "_size_gate_probe.js"
        self.addCleanup(lambda: self.probe.exists() and self.probe.unlink())

    def _write(self, n: int):
        # 纯行注释:即便这一刻别的窗口在跑 prettier / eslint,这份内容也是干净的。
        self.probe.write_text("// size gate probe\n" * n, encoding="utf-8")

    def test_501_lines_fails(self):
        self._write(501)
        got = _statuses().get("static/pos/_size_gate_probe.js")
        self.assertIsNotNone(got, "新文件压根没进射程")
        self.assertEqual(got[0], "FAIL")
        self.assertEqual(got[1], 501)

    def test_500_lines_is_the_boundary_and_passes(self):
        # 判据量的是"超过 500",不是"接近 500":边界写反的话上面那条照样红,分不出是哪种错。
        self._write(500)
        got = _statuses().get("static/pos/_size_gate_probe.js")
        self.assertIsNotNone(got)
        self.assertEqual(got[0], "OK")


class ExemptionsAreLoadBearing(unittest.TestCase):
    """反向反证:摘掉豁免,对应的真文件必须当场变红。

    豁免是本次唯一放行存量巨石的口子。它要是根本没在挡红(路径写错、键写错、文件已改名),
    上面"全仓当前是干净的"那条照样绿 —— 那时闸就是在替一个不存在的东西开门。
    """

    def setUp(self):
        self.baseline = gate.load_baseline()
        # 判据自检:账本读空的话下面每条都会"通过"得毫无意义(_notes 那类下划线键不算数)。
        self.assertGreater(len(self.baseline), 0, "基线读不出条目 —— 判据失效比断言失败更危险")

    def test_every_exemption_points_at_a_real_monitored_file(self):
        seen = _statuses()
        missing = [k for k in self.baseline if k not in seen]
        self.assertEqual(missing, [], "基线指到了射程外/不存在的文件 —— 这条记账谁都没用上")

    def test_dropping_each_exemption_turns_that_file_red(self):
        for key in self.baseline:
            with self.subTest(exempt=key):
                without = {k: v for k, v in self.baseline.items() if k != key}
                got = _statuses(baseline=without).get(key)
                self.assertIsNotNone(got, f"{key} 不在射程里")
                self.assertEqual(got[0], "FAIL", f"摘掉 {key} 的记账它却不红 —— 这条记账是摆设")

    def test_no_exemption_carries_headroom(self):
        """记账值必须钉死在当前行数:留余量 = 悄悄发一张"还能再涨 N 行"的通行证。

        文件真拆小了,跑 `--update-baseline` 把这个数收到新行数即可(棘轮只准往下走)。
        """
        padded = []
        for key, recorded in self.baseline.items():
            actual = gate.count_lines(PROJECT_ROOT / key)
            if recorded > actual:
                padded.append(f"{key}: 基线 {recorded} > 实际 {actual}")
        self.assertEqual(padded, [], "基线留了余量 · 跑 --update-baseline 收紧")


class DictionaryDataIsExemptByPath(unittest.TestCase):
    """POS 词典按数据豁免 —— 对齐 static/i18n-data.js 的既有处理。"""

    def test_pos_dictionary_is_not_collected(self):
        self.assertTrue(gate.is_exempt_path("static/pos/pos-i18n.js"))
        self.assertNotIn("static/pos/pos-i18n.js", _statuses())

    def test_pos_logic_files_are_not_swept_up_by_that_pattern(self):
        # 豁免写成 "static/pos/" 前缀的话整个 SPA 会跟着一起豁免掉,而这一条会红。
        self.assertFalse(gate.is_exempt_path(POS_SENTINEL))


class ExemptionDoesNotBleedAcrossDirectories(unittest.TestCase):
    """`static/pos/pos.js` 的 538 行口子,不许被别处任何一个 pos.js 白捡。

    旧字典按 basename 认键(那时全是根目录巨石,不会串);2026-08-01 起基线一律写仓库相对
    路径 —— 这一条守的正是"换了目录还认不认"。
    """

    def test_same_basename_elsewhere_gets_the_plain_ceiling(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (root / "src" / "home").mkdir(parents=True)
        other = root / "src" / "home" / "pos.js"
        other.write_text("// x\n" * 600, encoding="utf-8")
        original_root = gate.PROJECT_ROOT
        gate.PROJECT_ROOT = root
        self.addCleanup(lambda: setattr(gate, "PROJECT_ROOT", original_root))
        row = gate.check_one(other, gate.DEFAULT_CEILING, gate.load_baseline())
        self.assertEqual(row.rel, "src/home/pos.js")
        self.assertEqual(row.status, "FAIL")
        self.assertEqual(row.limit, 500, "它拿到了 static/pos/pos.js 的基线值 —— 串味了")


if __name__ == "__main__":
    unittest.main()
