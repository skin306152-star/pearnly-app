#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_copy_flash.py

static/ai/ai-copy-flash.js 的行为闸(真 node 跑源文件,注入假 window + 假按钮)。

这个模块是为了一个具体缺陷存在的:两处复制按钮都在【点击时】才抓 textContent 当"原文",
1.5 秒内连点第二次抓到的是「已复制」,计时器到点还原成「已复制」——按钮再也变不回来
(2026-07-30 真浏览器走查实测)。因此本文件第一条测的就是"连点两次仍能还原成原文",
其余测的是失败路径不许静默、原文只记一次。

另有两条静态闸:两个调用方不许再各自留一份 flash(),新模块必须真进 ai.js bundle
(不进 bundle = 上线即 AI.copyFlash undefined,点一次复制整块 JS 抛错)。
"""

from __future__ import annotations

import json
import re
import shutil
import unittest
from pathlib import Path

from tests.unit._node_harness import AI_DIR, PROJECT_ROOT, _run_node

_MODULE = AI_DIR / "ai-copy-flash.js"
_CALLERS = ("ai-steward-actions.js", "ai-billing.js")


def _require(name: str) -> str:
    """node -e 里的 require 字面量(Windows 反斜杠路径必须转义)。"""
    return f"require({json.dumps(str(AI_DIR / name))})"


# 假 window:setTimeout 只把回调排队,由 run(n) 显式触发,时间由测试说了算。
_FAKE_ENV = """
    function makeWin(clipboard) {
        const timers = new Map();
        let seq = 0;
        return {
            timers,
            fired: [],
            navigator: { clipboard },
            setTimeout(fn, ms) { timers.set(++seq, { fn, ms }); return seq; },
            clearTimeout(id) { timers.delete(id); },
            runAll() { [...timers.values()].forEach((t) => t.fn()); timers.clear(); },
        };
    }
    function makeBtn(text) { return { textContent: text }; }
"""


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CopyFlashBehaviourTests(unittest.TestCase):
    def test_double_click_still_restores_the_original_label(self):
        """本模块存在的理由:1.5s 内连点两次,还原回的必须是原文而不是「已复制」。"""
        out = _run_node(f"""
            {_FAKE_ENV}
            const cf = {_require("ai-copy-flash.js")};
            const win = makeWin(null);
            const btn = makeBtn('复制错误码');
            cf.flash(btn, '已复制', {{ win }});
            const afterFirst = btn.textContent;
            cf.flash(btn, '已复制', {{ win }});   // 计时器还没到点就再点一次
            const afterSecond = btn.textContent;
            const pending = win.timers.size;      // 旧计时器被清掉,只剩一个
            win.runAll();
            process.stdout.write(JSON.stringify({{
                afterFirst, afterSecond, pending, restored: btn.textContent,
            }}));
            """)
        self.assertEqual(out["afterFirst"], "已复制")
        self.assertEqual(out["afterSecond"], "已复制")
        self.assertEqual(out["pending"], 1)
        self.assertEqual(out["restored"], "复制错误码")

    def test_three_clicks_in_a_row_are_still_honest(self):
        out = _run_node(f"""
            {_FAKE_ENV}
            const cf = {_require("ai-copy-flash.js")};
            const win = makeWin(null);
            const btn = makeBtn('คัดลอกรหัส');
            cf.flash(btn, 'คัดลอกแล้ว', {{ win }});
            cf.flash(btn, 'คัดลอกแล้ว', {{ win }});
            cf.flash(btn, 'คัดลอกแล้ว', {{ win }});
            win.runAll();
            process.stdout.write(JSON.stringify({{ restored: btn.textContent }}));
            """)
        self.assertEqual(out["restored"], "คัดลอกรหัส")

    def test_a_later_click_after_restore_records_the_current_label(self):
        """还原之后再点:原文要重新记一次(按钮文案可能已被重渲染换过)。"""
        out = _run_node(f"""
            {_FAKE_ENV}
            const cf = {_require("ai-copy-flash.js")};
            const win = makeWin(null);
            const btn = makeBtn('复制');
            cf.flash(btn, '已复制', {{ win }});
            win.runAll();
            btn.textContent = '复制账号';   // 期间整块重渲染换了文案
            cf.flash(btn, '已复制', {{ win }});
            win.runAll();
            process.stdout.write(JSON.stringify({{ restored: btn.textContent }}));
            """)
        self.assertEqual(out["restored"], "复制账号")

    def test_copy_writes_the_text_and_flashes_on_success(self):
        out = _run_node(f"""
            {_FAKE_ENV}
            const cf = {_require("ai-copy-flash.js")};
            const wrote = [];
            const win = makeWin({{ writeText: (t) => {{ wrote.push(t); return Promise.resolve(); }} }});
            const btn = makeBtn('复制');
            cf.copy(btn, 'ERR_X', '已复制', {{ win }});
            setTimeout(() => {{
                const flashed = btn.textContent;
                win.runAll();
                process.stdout.write(JSON.stringify({{ wrote, flashed, restored: btn.textContent }}));
            }}, 0);
            """)
        self.assertEqual(out["wrote"], ["ERR_X"])
        self.assertEqual(out["flashed"], "已复制")
        self.assertEqual(out["restored"], "复制")

    def test_clipboard_rejection_still_gives_feedback(self):
        """写剪贴板被拒(非安全上下文/无权限)时按钮不动 = 用户只会再点一次。"""
        out = _run_node(f"""
            {_FAKE_ENV}
            const cf = {_require("ai-copy-flash.js")};
            const win = makeWin({{ writeText: () => Promise.reject(new Error('denied')) }});
            const btn = makeBtn('复制');
            cf.copy(btn, 'ERR_X', '已复制', {{ win }});
            setTimeout(() => process.stdout.write(JSON.stringify({{ flashed: btn.textContent }})), 0);
            """)
        self.assertEqual(out["flashed"], "已复制")

    def test_missing_clipboard_api_does_not_throw(self):
        out = _run_node(f"""
            {_FAKE_ENV}
            const cf = {_require("ai-copy-flash.js")};
            const win = makeWin(undefined);
            const btn = makeBtn('复制');
            let threw = false;
            try {{ cf.copy(btn, 'ERR_X', '已复制', {{ win }}); }} catch (e) {{ threw = true; }}
            process.stdout.write(JSON.stringify({{ threw, flashed: btn.textContent }}));
            """)
        self.assertFalse(out["threw"])
        self.assertEqual(out["flashed"], "已复制")

    def test_null_button_is_a_no_op(self):
        """ai-billing.js 的 closest() 可能回 null —— 这条路必须不抛。"""
        out = _run_node(f"""
            {_FAKE_ENV}
            const cf = {_require("ai-copy-flash.js")};
            const win = makeWin({{ writeText: () => Promise.resolve() }});
            let threw = false;
            try {{ cf.copy(null, 'x', '已复制', {{ win }}); }} catch (e) {{ threw = true; }}
            setTimeout(() => process.stdout.write(JSON.stringify({{ threw }})), 0);
            """)
        self.assertFalse(out["threw"])


class CopyFlashWiringTests(unittest.TestCase):
    """静态闸:调用方不许再留私版,新模块必须真进 bundle。"""

    def test_callers_no_longer_keep_their_own_flash(self):
        # 判据自检:两个调用方文件必须真的存在且真的调了共享出口,否则下面的"没有私版"
        # 会因为文件被改名/删空而白绿。
        for name in _CALLERS:
            src = (AI_DIR / name).read_text(encoding="utf-8")
            self.assertIn("AI.copyFlash.copy(", src, f"{name} 没走共享出口")
            self.assertIsNone(
                re.search(r"function flash\s*\(", src),
                f"{name} 又留了一份私版 flash() —— 连点还原成「已复制」的坑会再长回来",
            )

    def test_module_is_in_the_ai_bundle(self):
        text = (PROJECT_ROOT / "scripts" / "build-home-js.mjs").read_text(encoding="utf-8")
        self.assertIn("'ai/ai-copy-flash.js'", text)

    def test_the_hold_window_is_declared_once(self):
        src = _MODULE.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"\b1500\b", src)), 1)
        for name in _CALLERS:
            self.assertNotIn("1500", (AI_DIR / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
