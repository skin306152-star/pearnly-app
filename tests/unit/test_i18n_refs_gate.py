#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词典引用闸(scripts/check_i18n_refs.py)的反证与判定核测试。

这道闸补的是 check_i18n.py 的一个真洞:`sx-p-bc-dup-unit` / `sx-p-bc-self-unit`
**四语一起缺**,用户扫重复条码时屏上就是裸键名,而 check_i18n --strict 同时报 0 missing
—— 它比的是「某语言比别的语言少哪些键」,四语一起缺就没有参照物。

所以第一条反证喂的不是「th 缺了一条」这种理想输入(那种 check_i18n 早就抓得到,拿它验
本闸等于什么都没验),而是「四语一起缺」这种会出事的输入 —— 并且当场把 check_i18n 拉过来
跑同一份词典,证明它确实照样报绿。两道闸不是重复,是两条轴。

另一半是误伤:闸一旦开始误报就会被人 skip 掉,还不如不装。所以每种「长得像键但不是键」
的写法都配一条不许红 —— 现拼的键、比较值、插值参数、注释里的旧键、文案里带冒号的引号,
以及词典一行挤好几条这种写法(第一版判据正是栽在这里:9 处误报)。
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    # 先登记再 exec:闸里的 @dataclass 在 `from __future__ import annotations` 下要回查
    # sys.modules[__module__] 才解得开注解字符串,不登记就 AttributeError 在 import 期。
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load("check_i18n_refs")
check_i18n = _load("check_i18n")

# 真词典的形状:window.I18N = { zh: {…}, en: {…}, th: {…}, ja: {…} },键缩进 8。
# check_i18n.parse_i18n_blocks 认的也是这个形状,两道闸才能喂同一份样本对着比。
_DICT_TMPL = """window.I18N = {
    zh: {
%s
    },
    en: {
%s
    },
    th: {
%s
    },
    ja: {
%s
    },
};
"""


def dict_js(*per_lang: str) -> str:
    return _DICT_TMPL % per_lang


def entries(*pairs: tuple[str, str]) -> str:
    return "\n".join(f"        '{k}': '{v}'," for k, v in pairs)


# 四语齐全的底料 · 每条用例在它之上加/减一个键
_BASE = [("kept-a", "甲"), ("kept-b", "乙")]


class GateFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.write_dict(*(entries(*_BASE),) * 4)

    def write_dict(self, *per_lang: str):
        (self.dir / "dict.js").write_text(dict_js(*per_lang), encoding="utf-8")

    def write_src(self, name: str, text: str):
        (self.dir / name).write_text(text, encoding="utf-8")

    def surface(self, **kw):
        return gate.Surface(
            name="fixture",
            dict_file=self.dir / "dict.js",
            heads=(gate._T_HEAD,),
            sources=tuple(sorted(p for p in self.dir.glob("*") if p.name != "dict.js")),
            min_keys=kw.pop("min_keys", 2),
            **kw,
        )

    def fails(self, **kw) -> list[str]:
        _, fails, _ = gate.check(self.surface(**kw))
        return fails

    def assertCaught(self, key: str, **kw):
        hits = self.fails(**kw)
        self.assertTrue(
            any(f"`{key}`" in f for f in hits), f"闸没抓到落空的键 {key} · 实际: {hits}"
        )

    def assertClean(self, why: str, **kw):
        self.assertEqual(self.fails(**kw), [], f"误伤:{why}")


class MissingInAllFourLanguages(GateFixture):
    """本闸存在的理由 —— 会出事的那种输入。"""

    def test_key_absent_from_every_language_is_caught(self):
        self.write_src("page.ts", "el.textContent = t('sx-p-bc-dup-unit');\n")
        self.assertCaught("sx-p-bc-dup-unit")

    def test_the_old_gate_calls_the_same_dictionary_clean(self):
        """同一份词典喂给 check_i18n:它报 0 missing —— 这正是那两个键当年怎么上屏的。"""
        text = (self.dir / "dict.js").read_text(encoding="utf-8")
        diffs = check_i18n.diff_keysets(check_i18n.parse_i18n_blocks(text))
        self.assertEqual(
            {lang: d for lang, d in diffs.items() if d["missing"] or d["extra"]},
            {},
            "样本没构造对:check_i18n 若在这里就报红,本闸补的洞不成立",
        )

    def test_missing_in_one_language_is_the_old_gate_job(self):
        """对照组:只有 th 缺 —— check_i18n 抓得到,本闸不该也跟着报(键仍有定义)。"""
        self.write_dict(
            entries(*_BASE, ("only-zh", "丙")),
            entries(*_BASE, ("only-zh", "C")),
            entries(*_BASE),
            entries(*_BASE, ("only-zh", "丙")),
        )
        self.write_src("page.ts", "t('only-zh');\n")
        self.assertClean("键在某一种语言里有定义,漏译是 check_i18n 的活")
        text = (self.dir / "dict.js").read_text(encoding="utf-8")
        diffs = check_i18n.diff_keysets(check_i18n.parse_i18n_blocks(text))
        self.assertEqual(diffs["th"]["missing"], ["only-zh"], "对照组该由 check_i18n 抓住")


class AttributeKeys(GateFixture):
    """一半的取词写在标记里(815 处 data-i18n)· 只扫 JS 会漏掉同一种翻车。"""

    def test_data_i18n_attribute_is_scanned(self):
        self.write_src("tpl.ts", 'const H = `<div data-i18n="ghost-label">占位</div>`;\n')
        self.assertCaught("ghost-label")

    def test_placeholder_attribute_is_scanned(self):
        self.write_src("tpl.ts", '<input data-i18n-placeholder="ghost-ph">\n')
        self.assertCaught("ghost-ph")

    def test_vars_attribute_is_not_a_key(self):
        self.write_src("tpl.ts", '<div data-i18n="kept-a" data-i18n-vars=\'{"n":3}\'></div>\n')
        self.assertClean("data-i18n-vars 装的是插值参数,不是键")

    def test_attribute_built_at_runtime_is_skipped(self):
        self.write_src("tpl.ts", "const H = '<div data-i18n=\"' + from + '\">';\n")
        self.assertClean("现拼的属性值静态查不了,认成键必然落空")


class MultipleKeysPerLine(GateFixture):
    """词典一行挤好几条 —— 第一版判据只认行首那条,当场造出 9 处误报。"""

    PACKED = "        'help-modal-title': '帮助', 'help-modal-tip': '提示',"
    # 值里带引号带冒号:整条是文案,不是「两个东西」
    QUOTED = """        'quote-line': '他说 "hi": 好', 'kept-a': '甲',"""

    def test_second_key_on_a_line_counts_as_defined(self):
        self.write_dict(*[self.PACKED] * 4)
        self.write_src("page.ts", "t('help-modal-tip');\n")
        self.assertClean("同一行的第二条词条也是定义")

    def test_a_key_absent_from_such_a_line_is_still_caught(self):
        self.write_dict(*[self.PACKED] * 4)
        self.write_src("page.ts", "t('help-modal-foot');\n")
        self.assertCaught("help-modal-foot")

    def test_quoted_text_inside_a_value_is_not_a_definition(self):
        """值里的 `"hi":` 是文案的一部分 —— 当成定义就等于给闸开了个后门。"""
        self.write_dict(*[self.QUOTED] * 4)
        self.write_src("page.ts", "t('kept-a');\nt('hi');\n")
        self.assertCaught("hi")


class NotAKey(GateFixture):
    """长得像键但不是键的写法,一条都不许红。"""

    CLEAN = {
        "现拼的键": "t('bill_st_' + status);",
        "变量键": "t(key); t(BLOCKED[reason]);",
        "内层调用的参数": "t(el.getAttribute('data-i18n'));",
        "比较值不是键": "t(role === 'user' ? 'kept-a' : 'kept-b');",
        "插值参数的值": "t('kept-a', { name: 'ghost-name' });",
        "同名不同物的调用": "const x = parseInt('12', 10); el.at('ghost-at');",
        "注释里的旧键": "// 老版本这里是 t('renamed-away')\nt('kept-a');",
        "块注释里的旧键": "/* t('renamed-away-too') */\nt('kept-b');",
        "带 ${} 的模板串": "t(`prefix-${kind}`);",
        "中文/带空格的字面量": "t('未命中 · 请重扫');",
    }

    def test_none_of_these_shapes_fire(self):
        for why, src in self.CLEAN.items():
            with self.subTest(why=why):
                self.write_src("page.ts", src + "\n")
                self.assertClean(why)

    def test_but_the_same_file_shape_still_catches_a_real_miss(self):
        """反面的反面:上面那堆干净写法里混一条真落空,闸不许被它们带着一起放过。"""
        self.write_src("page.ts", "\n".join(self.CLEAN.values()) + "\nt('ghost-real');\n")
        self.assertCaught("ghost-real")


class GateSelfCheck(GateFixture):
    def test_unparseable_dictionary_is_a_red_not_a_pass(self):
        """词典结构变了(解析不出键)→ 每条查询都落空或全过 · 绿得毫无意义,当红报。"""
        (self.dir / "dict.js").write_text("window.I18N = {};\n", encoding="utf-8")
        self.write_src("page.ts", "t('kept-a');\n")
        hits = self.fails(min_keys=50)
        self.assertTrue(any("闸在空转" in f for f in hits), hits)

    def test_missing_dictionary_file_is_a_red(self):
        (self.dir / "dict.js").unlink()
        self.assertTrue(any("词典文件不存在" in f for f in self.fails()))


class RealTreeTests(unittest.TestCase):
    """闸报绿也可能是「一处都没扫到」· 真树上的量级与已知键在这里兜。"""

    def test_home_surface_is_really_being_read(self):
        surface = gate.home_surface()
        self.assertGreater(len(gate.defined_keys(surface.dict_file, surface.langs)), 4000)
        keys = {k for _, _, k in gate.key_references(surface)}
        self.assertGreater(len(keys), 1500)
        # 取词入口改名了没同步闸 → 这两条先红,而不是闸悄悄空转
        self.assertIn("inv-scan-hint", keys, "t() 调用没被扫到")
        self.assertIn("set-page-title", keys, "data-i18n 属性没被扫到")

    def test_pos_surface_is_really_being_read(self):
        surface = gate.pos_surface()
        self.assertGreater(len(gate.defined_keys(surface.dict_file, surface.langs)), 200)
        keys = {k for _, _, k in gate.key_references(surface)}
        self.assertIn("posui.bscan.aim", keys, "POS.t() 调用没被扫到")

    def test_repo_has_no_dangling_key(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = gate.main([])
        self.assertEqual(code, 0, buf.getvalue())


if __name__ == "__main__":
    unittest.main()
