#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_home_money_single_exit.py

/home SPA(会计主壳 · src/home/** + static/i18n-data.js)金额排版的单出口机械闸。

同 tests/unit/test_ai_money_single_exit.py,射程换成老站这一片 —— 两片各有一个出口
(AI.format.BAHT / src/home/money.ts 的 BAHT),但垫的是同一个窄空格,不是两套口径。

为什么要焊:2026-07-30 四语双端走查在 /home 首页同一屏上实测到三种写法并存(「฿ 0.」
「฿1.5」「฿0.7」),另有三处「数字在前 ฿ 在后」;而 src/home/dashboard.ts 的注释当时
明写着「฿ 与数字间垫窄空格」,下一行写的却是普通空格 —— 靠注释和 review 拦不住。

两条规则:
  1. 货币前缀只在 src/home/money.ts 声明一次 · 别处一律 import,不自己写;
  2. ฿ 后面永远不紧跟数字/占位符 —— 词典里手写的「฿10」与格式化产物一样会糊。
     例外只有一种:฿ 紧跟在数字/占位符【后面】(「{total}฿」)是后缀写法,那是 LINE
     Agent 的对话文案,不是 /home 的金额排版,本闸不管它 —— 但第三条规则钉死这种写法
     只许出现在 agent.* 词条上,免得有人拿它当免死金牌把 /home 的金额也写成后缀。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests.unit._node_harness import BAHT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOME_DIR = PROJECT_ROOT / "src" / "home"
I18N = PROJECT_ROOT / "static" / "i18n-data.js"

_PREFIX_OWNER = "src/home/money.ts"

# 「只装货币前缀」的字符串字面量:'฿' / '฿ ' —— 后面接内容的文案串不算。
_PREFIX_LITERAL = re.compile(r"(['\"])฿(?:\\u[0-9a-fA-F]{4}|\s)*\1")

# ฿ 紧贴数字 / {占位符} / ${模板表达式} = 糊成一团的那个形态(前面是数字/占位符收尾的
# 后缀写法除外,见模块头第 2 条)。
_GLUED_TO_NUMBER = re.compile(r"(?<![0-9}])฿(?=[0-9{$])")

# 后缀写法本身(数字/占位符 + ฿)。
_SUFFIX_FORM = re.compile(r"[0-9}]฿")
_AGENT_KEY_LINE = re.compile(r"^\s*'agent\.")


_DECL = re.compile(r"BAHT = '([^']*)'")
_JS_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def _declared_prefix(src: str) -> str:
    r"""money.ts 里声明的前缀真值(\uXXXX 转义解开)。"""
    m = _DECL.search(src)
    assert m, "money.ts 里找不到 BAHT 声明 —— 判据失效比断言失败更危险"
    return _JS_ESCAPE.sub(lambda e: chr(int(e.group(1), 16)), m.group(1))


def _hits(pattern: re.Pattern[str], source: str) -> list[int]:
    """命中行号(1 起)· 违规信息要能直接定位,不能只报「有问题」。"""
    return [i for i, line in enumerate(source.splitlines(), 1) if pattern.search(line)]


def _home_sources() -> list[tuple[str, str]]:
    """src/home/**(.ts + .js)+ 词典,统一用仓库相对路径当名字。"""
    files = sorted(HOME_DIR.glob("*.ts")) + sorted(HOME_DIR.glob("*.js")) + [I18N]
    return [(p.relative_to(PROJECT_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in files]


class HomeMoneyPrefixSingleExitTests(unittest.TestCase):
    def setUp(self):
        self.sources = _home_sources()
        # 判据自检:扫不到文件时下面每条断言都会「通过」,绿得毫无意义。
        self.assertGreater(len(self.sources), 200)
        self.assertIn(_PREFIX_OWNER, [name for name, _ in self.sources])
        self.assertTrue(any("฿" in src for _, src in self.sources))

    def test_only_money_ts_declares_the_currency_prefix(self):
        offenders = {
            name: _hits(_PREFIX_LITERAL, src)
            for name, src in self.sources
            if name != _PREFIX_OWNER and _PREFIX_LITERAL.search(src)
        }
        self.assertFalse(
            offenders,
            f"货币前缀只能在 {_PREFIX_OWNER} 声明,别处 import BAHT:{offenders}",
        )

    def test_the_owner_declares_it_exactly_once_and_matches_the_ai_shell(self):
        src = dict(self.sources)[_PREFIX_OWNER]
        self.assertEqual(len(_PREFIX_LITERAL.findall(src)), 1)
        # 与 /ai 那一侧同一个前缀:两片各有出口,但不是两套口径。两边都从真源解出值再比,
        # 不比字面 —— 字面里那个窄空格可以写成转义,也可以是个看不见的真字符。
        self.assertEqual(_declared_prefix(src), BAHT)
        self.assertEqual([hex(ord(c)) for c in BAHT], ["0xe3f", "0x2009"])

    def test_currency_glyph_is_never_glued_to_a_number(self):
        offenders = {
            name: _hits(_GLUED_TO_NUMBER, src)
            for name, src in self.sources
            if _GLUED_TO_NUMBER.search(src)
        }
        self.assertFalse(offenders, f"฿ 紧跟数字会糊成一团,借 BAHT 或垫 \\u2009:{offenders}")

    def test_the_suffix_spelling_is_confined_to_conversation_copy(self):
        """「{total}฿」这种数字在前的写法只许出现在对话词条上,不许漏进界面文案。"""
        offenders = []
        for name, src in self.sources:
            for i, line in enumerate(src.splitlines(), 1):
                if _SUFFIX_FORM.search(line) and not _AGENT_KEY_LINE.match(line):
                    offenders.append(f"{name}:{i}")
        self.assertFalse(offenders, f"界面文案不写「数字+฿」后缀形态,统一前缀:{offenders}")

    def test_the_gate_catches_what_it_claims_to(self):
        """反证:三条全绿也可能是正则从来没认出过东西。拿真违规样本各喂一遍。"""
        self.assertTrue(_PREFIX_LITERAL.search("return '฿' + n;"))
        self.assertTrue(_PREFIX_LITERAL.search('const b = "฿\\u2009";'))
        self.assertTrue(_GLUED_TO_NUMBER.search("'topup-amount-invalid': '最低 ฿10',"))
        self.assertTrue(_GLUED_TO_NUMBER.search("'pur-pay-after-partial': '剩余 ฿{remain}',"))
        self.assertTrue(_GLUED_TO_NUMBER.search("`<span>฿${fmtMoney(v)}</span>`"))
        self.assertTrue(_SUFFIX_FORM.search('<span class="v">{n}฿</span>'))
        # 反过来也别乱咬:฿ 后面是空白/汉字/右括号的注释与文案合法,后缀形态也不该被
        # 「紧贴数字」那条重复报一次。
        self.assertIsNone(_GLUED_TO_NUMBER.search("// ฿ 的墨迹比字宽宽半像素"))
        self.assertIsNone(_GLUED_TO_NUMBER.search("fAmountLimit: '金额上限(฿)',"))
        self.assertIsNone(_GLUED_TO_NUMBER.search("'合计 {total}฿{by_category}',"))
        self.assertIsNone(_PREFIX_LITERAL.search("label: '฿ 余额'"))
        self.assertIsNone(_AGENT_KEY_LINE.match("    'history-amt-vat': '税额 {v}฿',"))


class HomeMoneyWiringTests(unittest.TestCase):
    """出口不进 vite 图 = 上线即 undefined;这里只验引用侧真的 import 了它。"""

    def test_every_file_that_uses_baht_imports_it(self):
        offenders = []
        for path in sorted(HOME_DIR.glob("*.ts")) + sorted(HOME_DIR.glob("*.js")):
            if path.name == "money.ts":
                continue
            src = path.read_text(encoding="utf-8")
            if re.search(r"\bBAHT\b", src) and "from './money.js'" not in src:
                offenders.append(path.name)
        self.assertFalse(offenders, f"用了 BAHT 却没 import:{offenders}")

    def test_the_exit_is_actually_used(self):
        users = [
            p.name
            for p in HOME_DIR.glob("*.ts")
            if p.name != "money.ts" and "from './money.js'" in p.read_text(encoding="utf-8")
        ]
        # 只有一两个用户说明收口没做完 —— 走查当时数出 28 个文件手写 ฿。
        self.assertGreaterEqual(len(users), 20, f"用上单出口的文件太少:{users}")


if __name__ == "__main__":
    unittest.main()
