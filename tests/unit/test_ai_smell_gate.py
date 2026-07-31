# -*- coding: utf-8 -*-
"""scripts/check_ai_smell.py 的反证 —— 每种形状喂一份毒样本,断言闸真会红。

这道闸装了两个月其实基本没扫到东西(只收 .js/.mjs,而 src/ 下是 231 个 .ts;只认行首注释,
行尾注释一概看不见)。所以这里除了常规的「毒样本必红 / 合法写法不许误报」,还多两类:
  · 射程测试:.ts 必须在射程里、dist/vendor/*.min.js 必须不在 —— 直接钉住那两个洞。
  · 真树测试:闸在本仓上真的扫到了东西(防空扫)、基线每一条今天仍然成立(防基线腐烂)。
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = PROJECT_ROOT / "scripts" / "check_ai_smell.py"

_spec = importlib.util.spec_from_file_location("check_ai_smell_under_test", GATE_PATH)
gate = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = gate
_spec.loader.exec_module(gate)


class _TempTree:
    """临时前端源树:写文件、跑闸、拿退出码 —— 不碰仓库,也不碰真基线。"""

    def __init__(self, case: unittest.TestCase) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="ai_smell_gate_"))
        case.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, relpath: str, body: str) -> Path:
        path = self.dir / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def baseline(self, payload: dict) -> Path:
        path = self.dir / "baseline.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def run(self, *extra: str, baseline: Path | None = None) -> int:
        argv = ["--root", str(self.dir), *extra]
        if baseline is not None:
            argv += ["--baseline", str(baseline)]
        else:
            argv += ["--baseline", str(self.dir / "missing.json")]
        # 闸的报告是给人看的,跑在全量单测里只会淹掉真失败 —— 吞掉。
        with contextlib.redirect_stdout(io.StringIO()):
            return gate.main(argv)


class PoisonedSamplesGoRed(unittest.TestCase):
    """毒样本:每一种都必须让闸红。"""

    def setUp(self) -> None:
        self.tree = _TempTree(self)

    def test_emoji_in_ts_comment(self) -> None:
        # 这条就是「.ts 从没被扫过」那个洞:同样的内容放 .js 早就红了。
        self.tree.write("src/home/x.ts", "// ✅ 搞定了\nexport const a = 1;\n")
        self.assertEqual(self.tree.run("--all"), 1)

    def test_console_log_in_ts(self) -> None:
        self.tree.write("src/home/x.ts", "export function f() {\n  console.log('debug');\n}\n")
        self.assertEqual(self.tree.run("--all"), 1)

    def test_trailing_comment_emoji(self) -> None:
        # 行尾注释:旧闸的 ^\s*(//|\*) 看不见,src/main.js 里 4 处因此从没被报过。
        self.tree.write("src/main.js", "import './a.js'; // \U0001f534 高敏\n")
        self.assertEqual(self.tree.run("--all"), 1)

    def test_block_comment_continuation_emoji(self) -> None:
        self.tree.write("src/home/x.ts", "/**\n * ⚠️ 注意\n */\nexport const a = 1;\n")
        self.assertEqual(self.tree.run("--all"), 1)

    def test_static_spa_source_is_in_range(self) -> None:
        # /ai 与 /dms 两个 SPA 的真源也在 static/ 下,一样得查。
        self.tree.write("static/ai/ai-desk.js", "// ⭐ 重点\nconst a = 1;\n")
        self.assertEqual(self.tree.run("--all"), 1)

    def test_emoji_presentation_selector_alone(self) -> None:
        """基码不在图形区、只靠 FE0F 变体选择符成 emoji 的(ℹ️ ▶️)也得认出来。"""
        self.tree.write("src/home/x.ts", "// ℹ️ 提示\nconst a = 1;\n")
        self.assertEqual(self.tree.run("--all"), 1)

    def test_new_file_gets_no_grace_from_baseline(self) -> None:
        base = self.tree.baseline({"src/home/old.ts": {"emoji": 3}})
        self.tree.write("src/home/old.ts", "// ✅\n// ✅\n// ✅\n")
        self.tree.write("src/home/new.ts", "// ✅\n")
        self.assertEqual(self.tree.run("--all", baseline=base), 1)

    def test_one_more_than_baseline_is_red(self) -> None:
        base = self.tree.baseline({"src/home/x.ts": {"emoji": 1}})
        self.tree.write("src/home/x.ts", "// ✅\n// \U0001f534\n")
        self.assertEqual(self.tree.run("--all", baseline=base), 1)

    def test_changed_file_mode_also_reds(self) -> None:
        """pre-push 传的是文件清单(不是 --all)· 这条路也得能红。"""
        path = self.tree.write("src/home/x.ts", "// ✅\n")
        self.assertEqual(self.tree.run(str(path)), 1)


class LegitCodeStaysGreen(unittest.TestCase):
    """合法写法不许误报 —— 闸一开始误报就会被人静音,等于没装。"""

    def setUp(self) -> None:
        self.tree = _TempTree(self)

    def test_emoji_in_string_literal(self) -> None:
        # 产品 UI 文字里的 emoji 是 verbatim 内容,不是 AI 味。
        self.tree.write("src/home/x.ts", "export const label = '✅ 完成';\n")
        self.assertEqual(self.tree.run("--all"), 0)

    def test_emoji_inside_multiline_template(self) -> None:
        body = 'export const html = `\n  <div>✅ done</div>\n  <a href="https://x">⭐</a>\n`;\n'
        self.tree.write("src/home/x.ts", body)
        self.assertEqual(self.tree.run("--all"), 0)

    def test_console_warn_error_info(self) -> None:
        body = "try { f(); } catch (e) {\n  console.warn(e);\n  console.error(e);\n  console.info(e);\n}\n"
        self.tree.write("src/home/x.ts", body)
        self.assertEqual(self.tree.run("--all"), 0)

    def test_arrows_and_shapes_are_not_ai_smell(self) -> None:
        # → ← ▼ ● 是技术排版符,故意不在 emoji 区里。
        self.tree.write("src/home/x.ts", "// a → b ← c ▼ ●\nconst a = 1;\n")
        self.assertEqual(self.tree.run("--all"), 0)

    def test_at_baseline_count_passes(self) -> None:
        base = self.tree.baseline({"src/home/x.ts": {"emoji": 2}})
        self.tree.write("src/home/x.ts", "// ✅\n// \U0001f534\n")
        self.assertEqual(self.tree.run("--all", baseline=base), 0)

    def test_dropping_below_baseline_passes(self) -> None:
        base = self.tree.baseline({"src/home/x.ts": {"emoji": 2}})
        self.tree.write("src/home/x.ts", "// ✅\n")
        self.assertEqual(self.tree.run("--all", baseline=base), 0)


class ScopeRules(unittest.TestCase):
    """射程:哪些文件该查、哪些不该。"""

    def test_ts_is_in_scope(self) -> None:
        self.assertTrue(gate.in_scope("src/home/core.ts"))

    def test_static_spa_in_scope(self) -> None:
        self.assertTrue(gate.in_scope("static/ai/ai-desk-render.js"))

    def test_build_output_out_of_scope(self) -> None:
        self.assertFalse(gate.in_scope("static/dist/main.js"))

    def test_vendor_and_minified_out_of_scope(self) -> None:
        self.assertFalse(gate.in_scope("static/landing/vendor/three.min.js"))
        self.assertFalse(gate.in_scope("static/whatever.min.js"))

    def test_non_frontend_paths_out_of_scope(self) -> None:
        self.assertFalse(gate.in_scope("tests/e2e/_x.spec.js"))
        self.assertFalse(gate.in_scope("scripts/build-home-js.mjs"))

    def test_css_html_json_ignored(self) -> None:
        # pre-push 把 .css/.html/.json 一起塞进 $FE_CHANGED,闸得自己筛掉。
        self.assertFalse(gate.in_scope("static/home.css"))
        self.assertFalse(gate.in_scope("src/home/x.json"))


class RealTree(unittest.TestCase):
    """本仓真树:闸真扫到了东西 + 基线没有腐烂。"""

    def setUp(self) -> None:
        self.files = gate.all_scoped_files(gate.ROOT)
        self.detail, self.live = gate.survey(gate.ROOT, self.files)
        self.base = gate.load_baseline(gate.BASELINE)

    def test_gate_is_green_today(self) -> None:
        self.assertEqual(gate.over_baseline(self.live, self.base), {})

    def test_gate_actually_reaches_the_ts_tree(self) -> None:
        """防空扫:射程里必须真有几百个文件,且 .ts 占大头。"""
        ts_files = [f for f in self.files if f.endswith(".ts")]
        self.assertGreater(len(self.files), 300, "纳管文件太少 · 闸大概率又扫空了")
        self.assertGreater(len(ts_files), 200, ".ts 没进射程 —— 这正是 2026-07-31 修的那个洞")

    def test_baseline_is_not_looser_than_reality(self) -> None:
        """基线只许降不许升:记着的债今天还在,才算记账;还完了就得收紧。"""
        slack = gate.loosened(self.live, self.base, set(self.files))
        self.assertEqual(
            slack,
            {},
            "基线比现实松了(债已还完却还记着)· 跑 "
            "python scripts/check_ai_smell.py --all --update-baseline 收紧",
        )

    def test_removing_the_baseline_turns_the_real_tree_red(self) -> None:
        """反证:今天的绿是基线免的,不是闸瞎了。"""
        self.assertNotEqual(gate.over_baseline(self.live, {}), {})


if __name__ == "__main__":
    unittest.main()
