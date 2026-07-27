#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_money_single_exit.py

Pearnly AI SPA 金额排版的单出口机械闸。

฿ 与数字之间垫窄空格是排版口径,不是某个函数的私事:115 个 JS 里任何一处自己拼 "฿" + n,
那一处就在同一屏上跟 AI.format.money 的产物长得不一样,而这种不一致没人 review 得出来。
两条机械规则把它焊死:

  1. 货币前缀只在 ai-format.js 声明一次(AI.format.BAHT)· 别处一律借,不自己写;
  2. ฿ 后面永远不紧跟数字/占位符 —— 词典里手写的「฿10」与格式化产物一样会糊。

射程只到 static/ai/**(AI SPA 自己的排版口径)。src/home/** 的老站 SPA 是另一套格式化
函数,不在本闸管辖内。
"""

from __future__ import annotations

import json
import re
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, BAHT, _run_node

_PREFIX_OWNER = "ai-format.js"

# 「只装货币前缀」的字符串字面量:'฿' / '฿\u2009' —— 后面接内容的文案串不算。
_PREFIX_LITERAL = re.compile(r"(['\"])฿(?:\\u[0-9a-fA-F]{4}|\s)*\1")

# ฿ 紧贴数字 / {占位符} / ${模板表达式} = 糊成一团的那个形态。
_GLUED_TO_NUMBER = re.compile(r"฿(?=[0-9{$])")


def _hits(pattern: re.Pattern[str], source: str) -> list[int]:
    """命中行号(1 起)· 违规信息要能直接定位,不能只报「有问题」。"""
    return [i for i, line in enumerate(source.splitlines(), 1) if pattern.search(line)]


def _ai_sources() -> list[tuple[str, str]]:
    return [(p.name, p.read_text(encoding="utf-8")) for p in sorted(AI_DIR.glob("*.js"))]


def _require(name: str) -> str:
    """node -e 里的 require 字面量(Windows 反斜杠路径必须转义)。"""
    return f"require({json.dumps(str(AI_DIR / name))})"


class MoneyPrefixSingleExitTests(unittest.TestCase):
    def setUp(self):
        self.sources = _ai_sources()
        # 判据自检:扫不到文件时下面每条断言都会「通过」,绿得毫无意义。
        self.assertGreater(len(self.sources), 100)
        self.assertIn(_PREFIX_OWNER, [name for name, _ in self.sources])

    def test_only_ai_format_declares_the_currency_prefix(self):
        offenders = {
            name: _hits(_PREFIX_LITERAL, src)
            for name, src in self.sources
            if name != _PREFIX_OWNER and _PREFIX_LITERAL.search(src)
        }
        self.assertFalse(
            offenders,
            f"货币前缀只能在 {_PREFIX_OWNER} 声明,别处借 AI.format.BAHT:{offenders}",
        )

    def test_the_owner_declares_it_exactly_once(self):
        src = dict(self.sources)[_PREFIX_OWNER]
        self.assertEqual(len(_PREFIX_LITERAL.findall(src)), 1)

    def test_currency_glyph_is_never_glued_to_a_number(self):
        offenders = {
            name: _hits(_GLUED_TO_NUMBER, src)
            for name, src in self.sources
            if _GLUED_TO_NUMBER.search(src)
        }
        self.assertFalse(offenders, f"฿ 紧跟数字会糊成一团,中间垫 \\u2009:{offenders}")

    def test_the_gate_catches_what_it_claims_to(self):
        """反证:三条全绿也可能是正则从来没认出过东西。拿真违规样本各喂一遍。"""
        self.assertTrue(_PREFIX_LITERAL.search("return '฿' + n;"))
        self.assertTrue(_PREFIX_LITERAL.search('var b = "฿\\u2009";'))
        self.assertTrue(_GLUED_TO_NUMBER.search("bill_max: 'Maximum ฿500,000',"))
        self.assertTrue(_GLUED_TO_NUMBER.search("stw_spent: '已用 ฿{spent}',"))
        self.assertTrue(_GLUED_TO_NUMBER.search("tip: `฿${n}`"))
        # 反过来也别乱咬:฿ 后面是空白/汉字的注释与文案合法。
        self.assertIsNone(_GLUED_TO_NUMBER.search("// ฿ 的墨迹比字宽宽半像素"))
        self.assertIsNone(_PREFIX_LITERAL.search("label: '฿ 余额'"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class MoneyPrefixBehaviourTests(unittest.TestCase):
    """静态扫描管「没人手拼」,这一层管「两个出口真吐同一个前缀」。"""

    def test_prefix_is_baht_plus_a_narrow_space(self):
        self.assertEqual(BAHT, "฿\u2009")

    def test_both_exits_emit_the_shared_prefix(self):
        out = _run_node(f"""
            const f = {_require("ai-format.js")};
            const b = {_require("ai-billing-render.js")};
            process.stdout.write(JSON.stringify([f.BAHT, f.money(1), b.fmtBahtInt(1000)]));
            """)
        prefix, from_money, from_int = out
        self.assertEqual(prefix, BAHT)
        self.assertEqual(from_money, f"{BAHT}1.00")
        self.assertEqual(from_int, f"{BAHT}1,000")


if __name__ == "__main__":
    unittest.main()
