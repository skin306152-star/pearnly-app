# -*- coding: utf-8 -*-
"""scripts/check_file_size.py 的反证 —— 重点是 2026-08-01 那笔「static/ai 进监控 + 存量基线」。

出身:`static/ai/**` 从建站起就不在 MONITORED_GLOBS 里(/ai 是独立 SPA,不走 src/home 的
vite 打包),于是那 119 个 .js 谁也没量过。收进闸当天 7 个文件越线,最长的 ai-review.js 770 行 ——
闸没查过的地方,标准就等于不存在。

本文件钉四件事,缺一件基线机制就是个摆设:
  ① 造一个新的越线文件必须红(基线不是给新债用的);
  ② 基线里的文件涨一行必须红(只许降不许升);
  ③ 降了要提示可以收紧,而且 --quiet 下也得打 —— pre-push 只用 --quiet,不打就等于没有;
  ④ 干净样本不许误报,词典豁免面必须真的是纯词典(别让「名字里有 i18n」变成免罪符)。

真仓那几条(RealTreeCoverage)对着真文件跑,不喂桩:被验的标识符必须来自真实产物,
否则又是一次「验收脚本用桩造出产品里不存在的对象来验自己」。
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

REPO = Path(__file__).resolve().parents[2]

_SPEC = importlib.util.spec_from_file_location(
    "check_file_size_under_test", REPO / "scripts" / "check_file_size.py"
)
gate = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = gate
_SPEC.loader.exec_module(gate)

# 建基线当天记下的 7 个越线文件 —— 只许从这个集合里减。想往基线里加新条目,
# 得先改这条断言,免不成默默的(同 check_home_i18n_refs 的 0 容忍断言先例)。
#
# 里面两批,来路不同:
#   · static/ai 七个 —— 2026-08-01 把 static/ai/**/*.js 收进监控当天记的存量。
#   · static/pos 四个 —— 上游 2026-07-31 把 static/pos/** 收进监控时的存量,原本记在
#     check_file_size.py 的 EXEMPT_CURRENT_BIG_FILES;合并那笔(`6dc3536a`)按原值平移进
#     baseline.json,不是新债,是换了个记账的地方。deadline 在 baseline 的 _notes 里:
#     三个 .js 2026-09-30、pos.html 2026-12-31,到期直接删条目让它红。
# 这条断言在合并当天真拦住过一次:POS 四条进来时它当场红,逼这一笔显式认账。
BASELINE_ALLOWED = {
    "static/ai/ai-review.js",
    "static/ai/ai-intake.js",
    "static/ai/ai.js",
    "static/ai/ai-desk.js",
    "static/ai/ai-intake-render.js",
    "static/ai/ai-steward.js",
    "static/pos/pos-cashier.js",
    "static/pos/pos-data.js",
    "static/pos/pos.js",
    "static/pos/pos.html",
}


def _run(root: Path, *argv: str) -> tuple[int, str]:
    """把闸指到临时树上跑,返回 (退出码, 输出)。"""
    buf = io.StringIO()
    saved_root, gate.PROJECT_ROOT = gate.PROJECT_ROOT, root
    saved_base, gate.BASELINE_PATH = (
        gate.BASELINE_PATH,
        root / "scripts" / "file_size_baseline.json",
    )
    saved_argv, sys.argv = sys.argv, ["check_file_size.py", *argv]
    try:
        with contextlib.redirect_stdout(buf):
            return gate.main(), buf.getvalue()
    finally:
        gate.PROJECT_ROOT, gate.BASELINE_PATH, sys.argv = saved_root, saved_base, saved_argv


class _TempTree(unittest.TestCase):
    """每个用例一棵临时树:造文件 + 造基线,再把闸指过去。"""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="file_size_gate_"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def write(self, rel: str, lines: int) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(f"// line {i}\n" for i in range(lines)), encoding="utf-8")

    def baseline(self, entries: dict[str, int]) -> None:
        path = self.root / "scripts" / "file_size_baseline.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, object] = {"_notes": "反证用", **entries}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class NewOverLimitFileIsRed(_TempTree):
    """反证① —— 基线是给存量的,新债一行都不许欠。"""

    def test_new_static_ai_file_over_ceiling_is_red(self) -> None:
        self.write("static/ai/ai-brand-new.js", 501)
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 1, out)
        self.assertIn("ai-brand-new.js", out)
        self.assertIn("新越线", out)

    def test_exactly_at_ceiling_is_green(self) -> None:
        """500 行是"≤ 上限"的合规边界 —— 真有文件正卡在这(static/ai/ai-client.js)。"""
        self.write("static/ai/ai-edge.js", 500)
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 0, out)

    def test_nested_static_ai_dir_is_also_monitored(self) -> None:
        """glob 是 `static/ai/**/*.js` —— 往子目录里藏一个巨石同样红。"""
        self.write("static/ai/panels/ai-huge.js", 900)
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 1, out)
        self.assertIn("panels/ai-huge.js", out)


class BaselineRatchet(_TempTree):
    """反证②③ —— 只许降不许升,降了要说得出「可以收紧了」。"""

    def test_growing_past_baseline_is_red(self) -> None:
        self.baseline({"static/ai/ai-big.js": 510})
        self.write("static/ai/ai-big.js", 511)
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 1, out)
        self.assertIn("又长了 1 行", out)

    def test_holding_at_baseline_is_green(self) -> None:
        self.baseline({"static/ai/ai-big.js": 510})
        self.write("static/ai/ai-big.js", 510)
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 0, out)

    def test_shrinking_hints_that_baseline_can_tighten(self) -> None:
        self.baseline({"static/ai/ai-big.js": 510})
        self.write("static/ai/ai-big.js", 505)
        code, out = _run(self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("已降到 505 行", out)
        self.assertIn("--update-baseline", out)

    def test_tighten_hint_also_prints_in_quiet_mode(self) -> None:
        """pre-push 只用 --quiet · 提示在那里不打,就等于这条提示不存在。"""
        self.baseline({"static/ai/ai-big.js": 510})
        self.write("static/ai/ai-big.js", 505)
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 0, out)
        self.assertIn("--update-baseline", out)

    def test_back_under_ceiling_hints_entry_removal(self) -> None:
        self.baseline({"static/ai/ai-big.js": 510})
        self.write("static/ai/ai-big.js", 480)
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 0, out)
        self.assertIn("删掉这条", out)

    def test_stale_entry_for_deleted_file_hints_cleanup(self) -> None:
        """文件改名/删掉之后基线条目会留成僵尸 —— 不判红,但必须说出来。"""
        self.baseline({"static/ai/ai-gone.js": 600})
        self.write("static/ai/ai-alive.js", 100)
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 0, out)
        self.assertIn("ai-gone.js", out)
        self.assertIn("清掉这条", out)

    def test_update_baseline_rewrites_and_keeps_notes(self) -> None:
        self.baseline({"static/ai/ai-big.js": 510})
        self.write("static/ai/ai-big.js", 505)
        code, out = _run(self.root, "--update-baseline")
        self.assertEqual(code, 0, out)
        written = json.loads((self.root / "scripts" / "file_size_baseline.json").read_text("utf-8"))
        self.assertEqual(written["static/ai/ai-big.js"], 505)
        self.assertEqual(written["_notes"], "反证用")


class CleanSampleStaysGreen(_TempTree):
    """反证④ —— 干净样本一个字都不该输出(--quiet 的契约)。"""

    def test_no_false_positive_on_clean_tree(self) -> None:
        self.write("static/ai/ai-small.js", 120)
        self.write("services/demo/thing.py", 300)
        self.write("src/home/widget.ts", 499)
        self.write("tests/e2e/_huge_spec.js", 3000)  # tests/ 豁免
        self.write("scripts/tool.py", 2000)  # scripts/ 豁免
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "")


class DictShardExemption(_TempTree):
    """词典分片豁免的边界:判据卡在中划线上,别让「名字里有 i18n」变成免罪符。"""

    def test_dict_shard_over_ceiling_is_exempt(self) -> None:
        self.write("static/ai/ai-i18n-zh.js", 900)
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 0, out)

    def test_i18n_assembly_layer_is_still_monitored(self) -> None:
        """ai-i18n.js 带 detectLang/at()/atSetLang,是代码不是词典 —— 越线照红。"""
        self.write("static/ai/ai-i18n.js", 600)
        code, out = _run(self.root, "--quiet")
        self.assertEqual(code, 1, out)
        self.assertIn("ai-i18n.js", out)


class RealTreeCoverage(unittest.TestCase):
    """对着真文件跑 —— 桩能证明逻辑对,证明不了这道闸真的盯着 /ai 那 119 个文件。"""

    def setUp(self) -> None:
        self.baseline = gate.load_baseline()

    def test_static_ai_js_is_in_monitored_globs(self) -> None:
        self.assertIn("static/ai/**/*.js", gate.MONITORED_GLOBS)

    def test_gate_actually_collects_static_ai_files(self) -> None:
        collected = {p.relative_to(REPO).as_posix() for p in gate.collect_files()}
        ai_js = {p for p in collected if p.startswith("static/ai/")}
        self.assertGreater(len(ai_js), 90, "static/ai 只收到这么几个,glob 大概是写错了")
        self.assertIn("static/ai/ai-steward.js", ai_js)

    def test_baseline_entries_are_real_files_still_over_ceiling(self) -> None:
        """基线里不许摆不存在的路径或早就合规的文件 —— 那是假账,会把新债掩护进来。"""
        for rel, recorded in self.baseline.items():
            path = REPO / rel
            self.assertTrue(path.exists(), f"基线里的 {rel} 在树上不存在")
            lines = gate.count_lines(path)
            self.assertGreater(lines, gate.DEFAULT_CEILING, f"{rel} 已合规,该从基线里删掉")
            self.assertLessEqual(lines, recorded, f"{rel} 涨过基线({lines} > {recorded})")

    def test_baseline_only_shrinks(self) -> None:
        extra = set(self.baseline) - BASELINE_ALLOWED
        self.assertEqual(extra, set(), f"基线新增了条目:{sorted(extra)} —— 新债该拆不该记账")

    def test_no_over_limit_static_ai_file_escapes_the_baseline(self) -> None:
        """真树上每个越线的 /ai 文件都得在基线里,否则闸就是在假绿地放行。"""
        over = {
            p.relative_to(REPO).as_posix()
            for p in gate.collect_files()
            if p.relative_to(REPO).as_posix().startswith("static/ai/")
            and gate.count_lines(p) > gate.DEFAULT_CEILING
        }
        self.assertEqual(over - set(self.baseline), set())

    def test_exempted_shards_are_really_pure_dictionaries(self) -> None:
        """豁免面按文件名收,所以它的正当性得由内容来兜:分片里出现逻辑就是走私。"""
        shards = sorted((REPO / "static" / "ai").glob("ai-i18n-*.js"))
        self.assertGreaterEqual(len(shards), 10, "词典分片一个都没扫到,glob 写错了")
        for shard in shards:
            text = shard.read_text(encoding="utf-8")
            rel = shard.relative_to(REPO).as_posix()
            self.assertTrue(gate.is_exempt_path(rel), f"{rel} 没被豁免面收进去")
            self.assertNotIn("function", text, f"{rel} 里有 function —— 那就不是纯词典,别豁免它")
            self.assertNotIn("=>", text, f"{rel} 里有箭头函数 —— 那就不是纯词典,别豁免它")


if __name__ == "__main__":
    unittest.main()
