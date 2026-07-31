#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_check_scan_optin.py · 条码枪 opt-in 声明闸(scripts/check_scan_optin.py)的反证

一道只会报绿的闸比没有闸更坏 —— 它让人以为有人在看。所以这里的重点不是「闸能跑」,是:
  · 拿【真产品文件的真声明行】做变异:把 ="gun" 抹掉,闸必须当场红。红不了 = 闸没盯到那一行。
  · 合法档位从引擎常量读,不是写死在闸里:引擎里没有 MODE_* 时闸要自己红,不许默认放行。
  · 一处声明都没扫到时报红(路径漂了 = 假绿,这正是本仓吃过亏的那种绿)。
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = PROJECT_ROOT / "scripts" / "check_scan_optin.py"

# 产品里真正声明接枪的框。变异测试拿它们当靶子,而清单会漂 —— 加一个框忘了往这里加,
# 那个新框就一辈子没被反证过(单价框正是这么漏了一轮)。所以下面配了覆盖率断言。
REAL_DECLARATION_SITES = [
    (Path("src/home/inventory-modals.ts"), 'data-k="qty"'),
    (Path("src/home/inventory-modals.ts"), 'data-k="unit_cost"'),
    (Path("src/home/inventory-modals.ts"), 'data-k="batch_no"'),
    (Path("src/home/inventory-modals.ts"), 'data-k="expiry_date"'),
    (Path("src/home/sales-products-scan.ts"), 'id="${INPUT_ID}"'),
]


def _load_gate():
    spec = importlib.util.spec_from_file_location("check_scan_optin", GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


GATE = _load_gate()
MODES = GATE.allowed_modes()


class ModesComeFromTheEngineTests(unittest.TestCase):
    def test_gun_is_a_legal_mode_and_it_came_from_the_engine_source(self):
        self.assertIn("gun", MODES)
        # 写死在闸里就会跟引擎漂:引擎源里必须真有这个常量,闸才认得出它。
        self.assertIn("MODE_GUN = 'gun'", GATE.WEDGE.read_text(encoding="utf-8"))

    def test_engine_without_mode_constants_makes_the_gate_fail_not_pass(self):
        original = GATE.WEDGE
        blank = PROJECT_ROOT / "tests" / "unit" / "_scan_optin_no_modes.tmp.js"
        blank.write_text("var ATTR = 'data-enable-barcode';\n", encoding="utf-8")
        try:
            GATE.WEDGE = blank
            with self.assertRaises(SystemExit):
                GATE.allowed_modes()
        finally:
            GATE.WEDGE = original
            blank.unlink()


class DeclarationShapeTests(unittest.TestCase):
    def _bad(self, text: str) -> list[str]:
        bad, _ = GATE.check_text(text, MODES)
        return [why for _, _, why in bad]

    def test_explicit_gun_declaration_passes(self):
        self.assertEqual(self._bad('<input data-enable-barcode="gun">'), [])

    def test_bare_declaration_is_caught(self):
        self.assertEqual(len(self._bad("<input data-enable-barcode>")), 1)

    def test_bare_declaration_before_another_attribute_is_caught(self):
        self.assertEqual(len(self._bad('<input data-enable-barcode class="x">')), 1)

    def test_unknown_tier_value_is_caught(self):
        # 「always」正是被删掉的那一档(裸声明当年的含义)· 有人把它写回来必须红
        why = self._bad('<input data-enable-barcode="always">')
        self.assertEqual(len(why), 1)
        self.assertIn("always", why[0])

    def test_empty_value_is_caught(self):
        self.assertEqual(len(self._bad('<input data-enable-barcode="">')), 1)

    def test_dynamic_value_is_caught_because_it_cannot_be_audited(self):
        why = self._bad('<input data-enable-barcode="${mode}">')
        self.assertEqual(len(why), 1)
        self.assertIn("字面量", why[0])

    def test_runtime_dataset_write_is_caught(self):
        why = self._bad("el.dataset.enableBarcode = '';")
        self.assertEqual(len(why), 1)
        self.assertIn("dataset", why[0])

    def test_attribute_name_as_a_string_constant_is_not_a_declaration(self):
        # 引擎自己那行 var ATTR = 'data-enable-barcode' 不是声明,闸不能拿它当违规
        bad, total = GATE.check_text("var ATTR = 'data-enable-barcode';", MODES)
        self.assertEqual(bad, [])
        self.assertEqual(total, 0)


class RealProductFilesTests(unittest.TestCase):
    def test_product_source_passes_today(self):
        for rel, _ in REAL_DECLARATION_SITES:
            bad, total = GATE.check_text((PROJECT_ROOT / rel).read_text(encoding="utf-8"), MODES)
            self.assertEqual(bad, [], f"{rel} 现状就违规")
            self.assertGreater(total, 0, f"{rel} 里一处声明都没扫到 · 闸没盯着这个文件")

    def test_every_declaration_in_the_repo_is_on_the_mutation_list(self):
        """清单式反证必须配覆盖率:漏登记一个框 = 那个框永远不会被变异测到。

        单价框就是这么漏的 —— 它加进产品时没人往上面那张表里补一行,而全套测试照旧全绿。
        """
        # 闸自己数的 total 把注释里提到这个属性的行也算进去(它拦裸声明,不管写在哪儿)。
        # 这里要的是「真长在元素上的那几处」,所以先把注释行去掉再数。
        found = []
        for path in GATE.scan_files():
            for num, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                bare = line.lstrip()
                if bare.startswith(("//", "*", "/*")):
                    continue
                if GATE.check_text(line, MODES)[1]:
                    found.append(f"{path.relative_to(PROJECT_ROOT).as_posix()}:{num}")
        self.assertEqual(
            len(found),
            len(REAL_DECLARATION_SITES),
            f"真长在元素上的声明有 {len(found)} 处 {found},变异清单只登记了 "
            f"{len(REAL_DECLARATION_SITES)} 处",
        )

    def test_stripping_the_tier_off_a_real_line_turns_the_gate_red(self):
        """变异反证:每个真声明点各自退回裸声明,闸必须逐个抓到。

        这是本闸唯一有意义的证据 —— 「今天绿」证明不了「明天有人漏写时会红」。
        """
        for rel, anchor in REAL_DECLARATION_SITES:
            with self.subTest(file=str(rel), anchor=anchor):
                text = (PROJECT_ROOT / rel).read_text(encoding="utf-8")
                lines = text.splitlines()
                hits = [i for i, l in enumerate(lines) if anchor in l and GATE.ATTR in l]
                self.assertEqual(len(hits), 1, f"{rel} 里找不到 {anchor} 那一行的声明")
                lines[hits[0]] = lines[hits[0]].replace(f'{GATE.ATTR}="gun"', GATE.ATTR)
                bad, _ = GATE.check_text("\n".join(lines), MODES)
                self.assertEqual(len(bad), 1, f"{rel} 的 {anchor} 退回裸声明,闸没红")
                self.assertIn("裸声明", bad[0][2])

    def test_gate_reports_red_when_it_sees_nothing(self):
        # 路径漂了 = 一处都扫不到。这种情况必须红 —— 本仓吃过「闸报绿但根本没看过」的亏。
        original_globs, original_argv = GATE.SCAN_GLOBS, sys.argv
        try:
            GATE.SCAN_GLOBS = ("no/such/dir/**/*.ts",)
            sys.argv = ["check_scan_optin.py", "--quiet"]
            self.assertEqual(GATE.scan_files(), [])
            self.assertEqual(GATE.main(), 1, "什么都没扫到还报绿")
        finally:
            GATE.SCAN_GLOBS, sys.argv = original_globs, original_argv

    def test_gate_returns_zero_on_the_repo_as_it_stands(self):
        original_argv = sys.argv
        try:
            sys.argv = ["check_scan_optin.py", "--quiet"]
            self.assertEqual(GATE.main(), 0)
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
