# -*- coding: utf-8 -*-
"""/ai 词典引用闸(scripts/check_ai_i18n_refs.py)的反证与判定核测试。

反证是这份测试存在的理由:清单式闸不喂坏样本,「PASS」分不清是代码干净还是闸根本没看
——2026-07-30 的 intake_failed_batch_n 就是这么在 check_i18n --strict 全绿下印上界面的
(那道闸只看 static/i18n-data.js)。所以每种能落空的引用形状都配一条「造一个不存在的键,
闸必须红」,再配一条「合法写法不许误报」。
"""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

_MOD_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "check_ai_i18n_refs.py"
_spec = importlib.util.spec_from_file_location("check_ai_i18n_refs", _MOD_PATH)
refs_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(refs_gate)

AI_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "ai"

DICT = """window.__AI_I18N_ZH__ = {
    known_a: '甲',
    known_b: '乙',
};
"""

# 本地 t() 包装:只有转发给 at() 的那种才算取词入口(见闸顶注)。
T_WRAPPER = """(function (root) {
    function t(k, vars) {
        return typeof root.at === 'function' ? root.at(k, vars) : k;
    }
    root.render = function () {
        return t('%s');
    };
})(this);
"""


class GateFixture(unittest.TestCase):
    """每个用例一份最小 /ai 目录:一份词典 + 若干源文件。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "ai-i18n-zh.js").write_text(DICT, encoding="utf-8")
        self.addCleanup(self._tmp.cleanup)

    def write(self, name, text):
        (self.dir / name).write_text(text, encoding="utf-8")

    def run_gate(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = refs_gate.main(["--dir", str(self.dir)])
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

    def test_plain_at_call_with_unknown_key_fails(self):
        self.write("ai-x.js", "var s = at('ghost_key');\n")
        out = self.assertRed("ghost_key")
        self.assertIn("ai-x.js:1", out)

    def test_at_call_with_vars_and_unknown_key_fails(self):
        # 出事的那一条就长这样:at('intake_failed_batch_n', { n: n })
        self.write("ai-x.js", "\nvar s = at('ghost_key', { n: 2 });\n")
        self.assertIn("ai-x.js:2", self.assertRed("ghost_key"))

    def test_multiline_ternary_branch_with_unknown_key_fails(self):
        self.write(
            "ai-x.js",
            "var s = at(\n    row.kind === 'zip'\n        ? 'known_a'\n        : 'ghost_key'\n);\n",
        )
        self.assertIn("ai-x.js:4", self.assertRed("ghost_key"))

    def test_fallback_after_or_with_unknown_key_fails(self):
        self.write("ai-x.js", "var s = at(ctx.errKey || 'ghost_key');\n")
        self.assertRed("ghost_key")

    def test_local_t_wrapper_with_unknown_key_fails(self):
        self.write("ai-x.js", T_WRAPPER % "ghost_key")
        self.assertRed("ghost_key")

    def test_html_data_at_with_unknown_key_fails(self):
        self.write("ai.html", '<h1 data-at="ghost_key"></h1>\n')
        self.assertRed("ghost_key")

    def test_html_data_at_ph_with_unknown_key_fails(self):
        self.write("ai.html", '<input data-at-ph="ghost_key">\n')
        self.assertRed("ghost_key")

    def test_key_defined_only_in_another_shard_still_counts(self):
        # 定义散在多份分片里,查得到就行 —— 闸不管这条键在哪一片、有没有四语。
        (self.dir / "ai-i18n-fail.js").write_text(
            "Object.assign(window.__AI_I18N_ZH__, {\n    known_c: '丙',\n});\n", encoding="utf-8"
        )
        self.write("ai-x.js", "var s = at('known_c');\n")
        self.assertGreen()


class NoFalseAlarmTests(GateFixture):
    """合法写法不许误报 —— 噪声会让人把这道闸静音,等于没有。"""

    def test_known_key_passes(self):
        self.write("ai-x.js", "var s = at('known_a', { n: 1 });\n")
        self.assertGreen()

    def test_concatenated_key_is_not_a_key(self):
        # 'bill_st_' 是半截前缀,当键查必然落空;真键由调用方自己的测试兜。
        self.write("ai-x.js", "var s = at('ghost_prefix_' + row.status);\n")
        self.assertGreen()

    def test_comparison_literal_is_not_a_key(self):
        self.write("ai-x.js", "var s = at(msg.role === 'ghost_role' ? 'known_a' : 'known_b');\n")
        self.assertGreen()

    def test_nested_call_argument_is_not_a_key(self):
        self.write("ai-x.js", "var s = at(el.getAttribute('ghost_attr'));\n")
        self.assertGreen()

    def test_interpolation_values_are_not_keys(self):
        self.write("ai-x.js", "var s = at('known_a', { name: 'ghost_name' });\n")
        self.assertGreen()

    def test_array_at_method_is_not_a_getter(self):
        self.write("ai-x.js", "var last = rows.at('ghost_idx');\n")
        self.assertGreen()

    def test_bare_t_without_at_wrapper_is_not_a_getter(self):
        # 没有转发到 at() 的 t( 只是同名函数(ai-desk.js 的 var t = e.target 之流)。
        self.write("ai-x.js", "function t(x) {\n    return x;\n}\nvar s = t('ghost_local');\n")
        self.assertGreen()

    def test_key_inside_comment_is_ignored(self):
        self.write("ai-x.js", "// 历史上这里写过 at('ghost_old')\nvar s = at('known_a');\n")
        self.assertGreen()

    def test_dictionary_shard_itself_is_not_scanned_as_source(self):
        # 词典分片里的示例注释不该被当成引用(它就是定义的地方)。
        (self.dir / "ai-i18n-zh-2.js").write_text(
            "/* at('ghost_doc') 是这条的用法 */\nObject.assign(window.__AI_I18N_ZH__, {\n"
            "    known_d: '丁',\n});\n",
            encoding="utf-8",
        )
        self.assertGreen()


class RealTreeTests(unittest.TestCase):
    def test_repo_ai_tree_has_no_dangling_key(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = refs_gate.main(["--dir", str(AI_DIR)])
        self.assertEqual(code, 0, buf.getvalue())

    def test_gate_actually_reads_the_real_tree(self):
        # 闸报绿也可能是「一处都没扫到」。真树上必须扫出成百上千处引用,
        # 数量骤降(比如取词函数改名了没同步闸)在这里就露馅。
        found = refs_gate.key_references(AI_DIR)
        self.assertGreater(len(found), 800)
        self.assertIn(
            "intake_failed_batch_n",
            {key for _, _, key in found},
        )


if __name__ == "__main__":
    unittest.main()
