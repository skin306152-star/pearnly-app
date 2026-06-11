# -*- coding: utf-8 -*-
"""对账中心「销项税报告核查」(VEX)渲染防递归静态契约闸。

真因:_doRenderVexRows 收尾调 _applyVexSearch,而 _applyVexSearch 调 _renderVexTaskList
→ _renderVexTaskList 又调 _doRenderVexRows → render↔search 死递归,只靠爆栈终止
(RangeError 被 _loadVexTaskList 的 try/catch 静默吞),每次进 tab 阻塞主线程 ~1s
→ 快速切 tab 卡顿。修法:render 收尾只过滤不重渲(_applyVexFilter)。

无 jsdom · 用静态文本契约锁死递归不复发(对照 test_brv2_anchor_audit_static.py)。
"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src", "home", "excel-recon-tasklist.ts")


def _extract_fn_body(src: str, name: str) -> str:
    """取 `function <name>(` 起到配对右花括号止的函数体(含签名)。"""
    m = re.search(r"function\s+" + re.escape(name) + r"\s*\(", src)
    assert m, f"未找到函数 {name}"
    i = src.index("{", m.start())
    depth = 0
    for j in range(i, len(src)):
        c = src[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[m.start() : j + 1]
    raise AssertionError(f"{name} 花括号不配对")


class VexRenderNoRecursionStatic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SRC, "r", encoding="utf-8") as f:
            cls.src = f.read()

    def test_render_rows_does_not_call_search(self):
        body = _extract_fn_body(self.src, "_doRenderVexRows")
        self.assertNotIn(
            "_applyVexSearch(",
            body,
            "_doRenderVexRows 不得调用 _applyVexSearch(会重渲→死递归)· 用 _applyVexFilter",
        )
        self.assertIn(
            "_applyVexFilter(",
            body,
            "_doRenderVexRows 收尾应调 _applyVexFilter(只过滤不重渲)",
        )

    def test_filter_does_not_rerender(self):
        body = _extract_fn_body(self.src, "_applyVexFilter")
        self.assertNotIn(
            "_renderVexTaskList(",
            body,
            "_applyVexFilter 只做 DOM 显隐 · 不得重渲(否则递归回来)",
        )
        self.assertNotIn("_doRenderVexRows(", body)

    def test_functions_exist(self):
        for fn in ("_applyVexFilter", "_applyVexSearch", "_renderVexTaskList", "_doRenderVexRows"):
            self.assertRegex(self.src, r"function\s+" + fn + r"\s*\(", f"缺函数 {fn}")


if __name__ == "__main__":
    unittest.main()
