# -*- coding: utf-8 -*-
"""/home 词典引用闸(scripts/check_home_i18n_refs.py)的反证与判定核测试。

反证是这份测试存在的理由:清单式闸不喂坏样本,「PASS」分不清是代码干净还是闸根本没看。
本仓已经栽过两次,建这道闸的当天又栽了第三次 —— 定义侧最初按缩进认键(`^ {8}'key':`),
而 i18n-data.js:1073 那种一行挤两条词条的地方后一条就漏了,于是闸把 8 个明明有定义的键
报成落空。所以这里两头都锁:每种能落空的引用形状配一条「造个不存在的键,闸必须红」,
定义侧配一条 node eval 交叉验证(正则认出来的键集合 == 浏览器真拿到的)。
"""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

from tests.unit._node_harness import PROJECT_ROOT, _run_node

_MOD_PATH = PROJECT_ROOT / "scripts" / "check_home_i18n_refs.py"
_spec = importlib.util.spec_from_file_location("check_home_i18n_refs", _MOD_PATH)
refs_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(refs_gate)

DICT = """window.I18N = {
    zh: {
        'known-a': '甲',
        'known-b': '乙', 'known-c': '丙',
    },
    th: {
        'known-a': 'ก',
        'known-b': 'ข', 'known-c': 'ค',
    },
};
"""

# 各模块自己的轻桥。⚠️ `window.t(k) || fb` 这个形状救不了落空的键:window.t 取不到时返回
# key 本身(真值),fb 永远轮不上 —— 所以带兜底的包装跟裸调 t() 是同一种翻车。
WRAPPER = """function %s(k, fb) {
    return (typeof window.t === 'function' ? window.t(k) : fb) || fb || k;
}
export function render() {
    return %s('%s');
}
"""

SHARED_GETTER = """export function kbT(key, fallback) {
    if (typeof window.t === 'function') {
        const s = window.t(key);
        if (s && s !== key) return s;
    }
    return fallback;
}
"""


class GateFixture(unittest.TestCase):
    """每个用例一份最小 /home 树:一份 window.I18N + 若干源文件。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "static").mkdir()
        (self.root / "src" / "home").mkdir(parents=True)
        (self.root / "static" / "i18n-data.js").write_text(DICT, encoding="utf-8")
        self.baseline = self.root / "baseline.txt"
        self.addCleanup(self._tmp.cleanup)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def src(self, name, text):
        self.write(f"src/home/{name}", text)

    def run_gate(self, *extra):
        buf = io.StringIO()
        argv = ["--root", str(self.root), "--baseline", str(self.baseline), *extra]
        with contextlib.redirect_stdout(buf):
            code = refs_gate.main(argv)
        return code, buf.getvalue()

    def assertGreen(self):
        code, out = self.run_gate()
        self.assertEqual(code, 0, out)
        return out

    def assertRed(self, key):
        code, out = self.run_gate()
        self.assertEqual(code, 1, out)
        self.assertIn(key, out)
        return out


class CounterEvidenceTests(GateFixture):
    """喂不存在的键 —— 每一种引用形状都必须红。"""

    def test_bare_global_t_with_unknown_key_fails(self):
        self.src("x.ts", "const s = t('ghost-key');\n")
        self.assertIn("src/home/x.ts:1", self.assertRed("ghost-key"))

    def test_t_call_with_interpolation_vars_fails(self):
        self.src("x.ts", "\nconst s = t('ghost-key', { n: 2 });\n")
        self.assertIn("src/home/x.ts:2", self.assertRed("ghost-key"))

    def test_multiline_ternary_branch_with_unknown_key_fails(self):
        self.src(
            "x.ts",
            "const s = t(\n    row.kind === 'zip'\n        ? 'known-a'\n        : 'ghost-key'\n);\n",
        )
        self.assertIn("src/home/x.ts:4", self.assertRed("ghost-key"))

    def test_fallback_after_or_with_unknown_key_fails(self):
        # erp-log-card.ts 的 t(_DUP_FIELD_I18N[f.field] || 'erp-dup-field-other') 就是这形状,
        # 2026-07-31 这道闸刚上线就在别的窗口的在飞改动里抓到它漏补词典。
        self.src("x.ts", "const s = t(TABLE[f.field] || 'ghost-key');\n")
        self.assertRed("ghost-key")

    def test_local_underscore_wrapper_with_unknown_key_fails(self):
        self.src("x.ts", WRAPPER % ("_t", "_t", "ghost-key"))
        self.assertRed("ghost-key")

    def test_local_bt_wrapper_with_unknown_key_fails(self):
        self.src("x.ts", WRAPPER % ("_bt", "_bt", "ghost-key"))
        self.assertRed("ghost-key")

    def test_uppercase_t_wrapper_with_unknown_key_fails(self):
        self.src(
            "x.ts",
            "function T(k) {\n    const w = window;\n    return typeof w.t === 'function'"
            " ? w.t(k) : k;\n}\nconst s = T('ghost-key');\n",
        )
        self.assertRed("ghost-key")

    def test_imported_shared_getter_with_unknown_key_fails(self):
        self.src("knowledge-api.ts", SHARED_GETTER)
        self.src(
            "knowledge-ask.ts",
            "import { kbT } from './knowledge-api.js';\nconst s = kbT('ghost-key', '兜底');\n",
        )
        self.assertIn("knowledge-ask.ts:2", self.assertRed("ghost-key"))

    def test_data_i18n_attribute_with_unknown_key_fails(self):
        self.src("x.ts", 'const html = `<div data-i18n="ghost-key">连接</div>`;\n')
        self.assertRed("ghost-key")

    def test_data_i18n_placeholder_with_unknown_key_fails(self):
        self.src("x.ts", 'const html = `<input data-i18n-placeholder="ghost-key">`;\n')
        self.assertRed("ghost-key")

    def test_index_html_attribute_with_unknown_key_fails(self):
        self.write("home.html", '<span data-i18n="ghost-key">切换中...</span>\n')
        self.assertIn("home.html:1", self.assertRed("ghost-key"))

    def test_direct_i18n_index_with_unknown_key_fails(self):
        # core-boot.ts 的 I18N[lang]['lang-name'] 那种直接下标。
        self.src("x.ts", "el.textContent = I18N[lang]['ghost-key'];\n")
        self.assertRed("ghost-key")

    def test_key_defined_in_only_one_language_block_still_counts(self):
        # 本闸只管"引用得到定义",四语齐不齐是 check_i18n --strict 的活,别把现状轰红。
        self.write(
            "static/i18n-data.js",
            "window.I18N = {\n    zh: {\n        'known-a': '甲',\n    },\n"
            "    th: {\n        'only-th': 'ก',\n    },\n};\n",
        )
        self.src("x.ts", "const s = t('only-th');\n")
        self.assertGreen()


class BaselineRatchetTests(GateFixture):
    """存量基线只许降不许升。"""

    def test_baselined_entry_is_forgiven(self):
        self.src("x.ts", "const s = t('ghost-key');\n")
        self.baseline.write_text("src/home/x.ts\tghost-key\n", encoding="utf-8")
        self.assertGreen()

    def test_new_entry_beside_baselined_one_still_fails(self):
        self.src("x.ts", "const s = t('ghost-key');\nconst u = t('ghost-two');\n")
        self.baseline.write_text("src/home/x.ts\tghost-key\n", encoding="utf-8")
        out = self.assertRed("ghost-two")
        self.assertNotIn("ghost-key", out)

    def test_baseline_is_pinned_to_the_file_not_just_the_key(self):
        # 同一个键搬到别的文件 = 新债,不许蹭旧账免罪。
        self.src("x.ts", "const s = t('ghost-key');\n")
        self.baseline.write_text("src/home/other.ts\tghost-key\n", encoding="utf-8")
        self.assertRed("ghost-key")

    def test_update_baseline_rewrites_and_then_passes(self):
        self.src("x.ts", "const s = t('ghost-key');\n")
        code, _ = self.run_gate("--update-baseline")
        self.assertEqual(code, 0)
        self.assertIn("ghost-key", self.baseline.read_text(encoding="utf-8"))
        self.assertGreen()

    def test_fixed_baseline_entry_is_reported_for_tightening(self):
        self.src("x.ts", "const s = t('known-a');\n")
        self.baseline.write_text("src/home/x.ts\tghost-key\n", encoding="utf-8")
        self.assertIn("--update-baseline", self.assertGreen())


class NoFalseAlarmTests(GateFixture):
    """合法写法不许误报 —— 噪声会让人把这道闸静音,等于没有。"""

    def test_known_key_passes(self):
        self.src("x.ts", "const s = t('known-a', { n: 1 });\n")
        self.assertGreen()

    def test_second_key_on_a_shared_line_counts_as_defined(self):
        # 建闸当天的假红根因:定义侧按缩进认键,一行两条只认到第一条。
        self.src("x.ts", "const s = t('known-c');\n")
        self.assertGreen()

    def test_concatenated_key_is_not_a_key(self):
        self.src("x.ts", "const s = t('ghost-prefix-' + row.status);\n")
        self.assertGreen()

    def test_comparison_literal_is_not_a_key(self):
        self.src("x.ts", "const s = t(msg.role === 'ghost-role' ? 'known-a' : 'known-b');\n")
        self.assertGreen()

    def test_nested_call_argument_is_not_a_key(self):
        self.src("x.ts", "const s = t(el.getAttribute('ghost-attr'));\n")
        self.assertGreen()

    def test_interpolation_values_are_not_keys(self):
        self.src("x.ts", "const s = t('known-a', { name: 'ghost-name' });\n")
        self.assertGreen()

    def test_key_inside_comment_is_ignored(self):
        self.src("x.ts", "// 历史上这里写过 t('ghost-old')\nconst s = t('known-a');\n")
        self.assertGreen()

    def test_shadowing_local_t_is_not_a_getter(self):
        self.src("x.ts", "function t(x) {\n    return x;\n}\nconst s = t('ghost-local');\n")
        self.assertGreen()

    def test_uppercase_t_without_wrapper_is_not_a_getter(self):
        # T 在 TS 里是泛型参数的常用名;没有转发 window.t 的 T( 不算取词。
        self.src("x.ts", "const s = T('ghost-generic');\n")
        self.assertGreen()

    def test_interpolated_attribute_selector_is_not_a_key(self):
        # module-nav.ts 的 '[data-i18n="' + from + '"]' —— 拼出来的属性值不是键。
        self.src("x.ts", "document.querySelectorAll('[data-i18n=\"' + from + '\"]');\n")
        self.assertGreen()

    def test_literal_attribute_selector_still_counts(self):
        # 反过来:选择器里写死的键得算引用,否则改名后没人拦。
        self.src("x.ts", "el.querySelector('[data-i18n=\"ghost-sel\"]');\n")
        self.assertRed("ghost-sel")

    def test_data_i18n_vars_attribute_is_not_a_key(self):
        self.src("x.ts", 'const h = `<span data-i18n="known-a" data-i18n-vars=\'{"n":0}\'>`;\n')
        self.assertGreen()

    def test_lookalike_constant_table_is_not_the_dictionary(self):
        # erp-log-card.ts 的 _EXPRESS_REASON_I18N[code] 名字里也带 I18N,不是词典本尊。
        self.src("x.ts", "const s = _EXPRESS_REASON_I18N[code]['ghost-sub'];\n")
        self.assertGreen()


class ConstantKeyTableTests(GateFixture):
    """常量键表 —— `const M = { code: '键' }` 再 t(M[code]) 取出来的那一路。

    2026-07-31 之前这块完全在射程外(实测 16 张表 117 个键)。判据不靠命名靠对拍词典,
    所以这里既要证「表里的坏键会红」,也要证「非 i18n 的常量表不会被误当键表」。
    """

    def test_unknown_key_inside_a_key_table_fails(self):
        self.src("x.ts", "const M = { a: 'known-a', b: 'ghost-in-table' };\n")
        self.assertRed("ghost-in-table")

    def test_typed_record_declaration_also_counted(self):
        # 真树上的写法带类型标注:const _DUP_FIELD_I18N: Record<string, string> = {...}
        self.src(
            "x.ts",
            "const _T: Record<string, string> = { a: 'known-a', b: 'ghost-in-typed' };\n",
        )
        self.assertRed("ghost-in-typed")

    def test_braces_inside_string_values_do_not_break_matching(self):
        self.src(
            "x.ts",
            "const M = { a: 'known-a', b: '{n} 件', c: 'ghost-after-brace' };\nconst z = 1;\n",
        )
        self.assertRed("ghost-after-brace")

    def test_non_i18n_constant_table_is_not_treated_as_keys(self):
        """一个词典键都对不上的表 = 不是键表。误报会让人把闸静音,等于没装。"""
        self.src("x.ts", "const STORAGE_KEYS = { token: 'mrpilot_token', lang: 'mrpilot_lang' };\n")
        self.assertGreen()

    def test_non_key_shaped_values_in_a_mixed_table_are_ignored(self):
        """archive-settings.ts 的 FIELD_META 真长这样:键和日期格式混着放。"""
        self.src(
            "x.ts",
            "const FIELD_META = { a: 'known-a', b: 'known-b', fmt: 'YYYY-MM-DD', sep: '_' };\n",
        )
        self.assertGreen()

    def test_single_key_table_is_out_of_range_on_purpose(self):
        """只有一个像键的值时判不出这是不是键表 —— 宁漏不误报,写在这儿别当它查过了。"""
        self.src("x.ts", "const M = { only: 'ghost-single' };\n")
        self.assertGreen()

    def test_table_inside_a_comment_is_ignored(self):
        self.src("x.ts", "// const M = { a: 'known-a', b: 'ghost-commented' };\nconst z = 1;\n")
        self.assertGreen()


class RealTreeTests(unittest.TestCase):
    def test_repo_home_tree_has_no_new_dangling_key(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = refs_gate.main([])
        self.assertEqual(code, 0, buf.getvalue())

    def test_gate_actually_reads_the_real_tree(self):
        # 闸报绿也可能是「一处都没扫到」。真树上必须扫出三千多处引用,数量骤降
        # (比如取词函数改名了没同步闸)在这里就露馅。
        found = refs_gate.key_references(PROJECT_ROOT)
        self.assertGreater(len(found), 3000)
        keys = {key for _, _, key in found}
        self.assertIn("set-page-title", keys)  # data-i18n 属性这一路
        self.assertIn("col-conf-tip", keys)  # 裸调 t() 这一路
        self.assertIn("erp-dup-field-date", keys)  # 常量键表这一路(_DUP_FIELD_I18N)

    def test_constant_key_tables_are_really_reached(self):
        """常量键表那一路单独防空扫:全树 16 张表 117 个键,数量骤降说明判据被改瞎了。"""
        known = refs_gate.defined_keys(PROJECT_ROOT)
        total = 0
        tables = 0
        for _rel, text in refs_gate.documents(PROJECT_ROOT):
            found = refs_gate.table_keys(text, known)
            if found:
                tables += 1
                total += len(found)
        self.assertGreaterEqual(tables, 10, "键表数量骤降 · 判据是不是被改窄了")
        self.assertGreaterEqual(total, 100, f"只扫到 {total} 个表内键 · 建闸日是 117 个")

    def test_defined_keys_match_a_real_eval(self):
        """定义侧交叉验证:正则认出来的键 == node 真 eval window.I18N 拿到的键。

        闸的定义侧一旦多认/漏认,红绿都是假的:漏认 → 好键被报成落空(建闸当天就这么假红
        8 处);多认 → 真落空的键被当成有定义放过去。所以不拿正则自证,拿浏览器同款
        求值对拍。
        """
        js = (
            "global.window = {};"
            "require('./static/i18n-data.js');"
            "const out = {};"
            "for (const l of Object.keys(window.I18N)) out[l] = Object.keys(window.I18N[l]);"
            "console.log(JSON.stringify(out));"
        )
        blocks = _run_node(js)
        self.assertEqual(sorted(blocks), ["en", "ja", "th", "zh"])
        truth = set()
        for keys in blocks.values():
            truth |= set(keys)
        parsed = refs_gate.defined_keys(PROJECT_ROOT)
        self.assertEqual(sorted(parsed - truth), [], "正则多认了这些键(真词典里没有)")
        self.assertEqual(sorted(truth - parsed), [], "正则漏认了这些键(真词典里有)")

    def test_gate_is_zero_tolerance_no_baseline_left(self):
        """存量已清零 → 基线文件不该还在。

        建闸时唯一那处存量(auto-erp-subtab-connect-only)已补上四语文案,基线随之删掉,
        闸切成 0 容忍。留一个空基线文件的坏处是它随时能被人添一行当免罪符,而空文件
        本身不会让任何测试红。这里两头都钉:文件不许回来,树上不许有落空。
        """
        self.assertFalse(
            refs_gate.BASELINE.exists(),
            "基线文件回来了 —— 新债要么当场修,要么明写理由再改这条测试,别默默免罪",
        )
        live = sorted((rel, key) for rel, _, key in refs_gate.dangling(PROJECT_ROOT))
        self.assertEqual(live, [], "有引用落空了,补词典条目;真要免罪得先改掉这条测试")


if __name__ == "__main__":
    unittest.main()
