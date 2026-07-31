#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_copy_flash.py

复制反馈两份实现的行为闸(真 node 跑源文件,注入假 window + 假按钮)。

两份:static/shared/copy-flash.js(/ai + /dms 共用 · 浏览器全局 root.CopyFlash)与
src/home/copy-flash.ts(/home 的 Vite ESM 版)。分两份不是漏抽 —— 两棵树由不同构建器
打包、没有共享 import 图,详见各自文件头。行为契约在这里一起钉,漂了就红。

这个模块是为了一个具体缺陷存在的:两处复制按钮都在【点击时】才抓 textContent 当"原文",
1.5 秒内连点第二次抓到的是「已复制」,计时器到点还原成「已复制」——按钮再也变不回来
(2026-07-30 真浏览器走查实测)。因此本文件第一条测的就是"连点两次仍能还原成原文",
其余测的是失败路径不许静默、原文只记一次。

另有静态闸:调用方不许再各自留一份 flash();共享模块必须真进 ai.js 与 dms.js 两个
bundle(不进 bundle = 上线即 CopyFlash undefined,点一次复制整块 JS 抛错);
/home 那份不许把「剪贴板不可用就静默 return」写回来。
"""

from __future__ import annotations

import json
import re
import shutil
import unittest
from pathlib import Path

from tests.unit._node_harness import AI_DIR, PROJECT_ROOT, _run_node

_SHARED_DIR = PROJECT_ROOT / "static" / "shared"
_MODULE = _SHARED_DIR / "copy-flash.js"
_HOME_MODULE = PROJECT_ROOT / "src" / "home" / "copy-flash.ts"
# /ai 与 /dms 里所有走共享出口的点击处 —— 少列一个,那个文件就能偷偷长回私版 flash()。
_CALLERS = (
    AI_DIR / "ai-steward-actions.js",
    AI_DIR / "ai-billing.js",
    AI_DIR / "ai-review-inbox.js",
    PROJECT_ROOT / "static" / "dms" / "dms-billing-topup.js",
)


def _code_only(path: Path) -> str:
    """去掉注释再匹配 —— 这些闸禁的是「代码里又写回来了」,不是「文档里提了一嘴」。

    不剥的话,copy-flash.ts 文件头引用旧坏写法当反面教材,自己就把自己的闸弄红了。
    """
    src = path.read_text(encoding="utf-8")
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(?m)//.*$", "", src)


def _require(path: Path) -> str:
    """node -e 里的 require 字面量(Windows 反斜杠路径必须转义)。"""
    return f"require({json.dumps(str(path))})"


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
            const cf = {_require(_MODULE)};
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
            const cf = {_require(_MODULE)};
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
            const cf = {_require(_MODULE)};
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
            const cf = {_require(_MODULE)};
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
            const cf = {_require(_MODULE)};
            const win = makeWin({{ writeText: () => Promise.reject(new Error('denied')) }});
            const btn = makeBtn('复制');
            cf.copy(btn, 'ERR_X', '已复制', {{ win }});
            setTimeout(() => process.stdout.write(JSON.stringify({{ flashed: btn.textContent }})), 0);
            """)
        self.assertEqual(out["flashed"], "已复制")

    def test_missing_clipboard_api_does_not_throw(self):
        out = _run_node(f"""
            {_FAKE_ENV}
            const cf = {_require(_MODULE)};
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
            const cf = {_require(_MODULE)};
            const win = makeWin({{ writeText: () => Promise.resolve() }});
            let threw = false;
            try {{ cf.copy(null, 'x', '已复制', {{ win }}); }} catch (e) {{ threw = true; }}
            setTimeout(() => process.stdout.write(JSON.stringify({{ threw }})), 0);
            """)
        self.assertFalse(out["threw"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class HomeCopyFlashBehaviourTests(unittest.TestCase):
    """/home 那份 TS 实现跑同样的行为断言 —— 静态闸只看得出「代码长得对」,看不出它真的对。

    esbuild 现场把 TS 转成 CJS 再执行,window/navigator 由外层注入(模块里是裸全局引用)。
    """

    @staticmethod
    def _boot(clipboard_js: str, prelude: str = "") -> str:
        """加载 src/home/copy-flash.ts,注入假 window/navigator,返回 node 前导代码。"""
        return f"""
            {prelude}
            const esbuild = require({json.dumps(str(PROJECT_ROOT / "node_modules" / "esbuild"))});
            const fs = require('fs');
            const src = fs.readFileSync({json.dumps(str(_HOME_MODULE))}, 'utf8');
            const js = esbuild.transformSync(src, {{ loader: 'ts', format: 'cjs' }}).code;
            const timers = new Map();
            let seq = 0;
            const win = {{
                setTimeout(fn, ms) {{ timers.set(++seq, {{ fn, ms }}); return seq; }},
                clearTimeout(id) {{ timers.delete(id); }},
                runAll() {{ [...timers.values()].forEach((t) => t.fn()); timers.clear(); }},
                timers,
            }};
            const nav = {clipboard_js};
            const mod = {{ exports: {{}} }};
            new Function('module', 'exports', 'window', 'navigator', js)(
                mod, mod.exports, win, nav);
            const cf = mod.exports;
            const makeBtn = (text) => ({{ textContent: text }});
        """

    def test_double_click_still_restores_the_original_label(self):
        """与共享 JS 版同一条判据:1.5s 内连点两次,还原回的必须是原文。"""
        out = _run_node(f"""
            {self._boot("{ clipboard: null }")}
            const btn = makeBtn('复制账号');
            cf.flash(btn, '已复制');
            cf.flash(btn, '已复制');
            const pending = win.timers.size;
            win.runAll();
            process.stdout.write(JSON.stringify({{ pending, restored: btn.textContent }}));
            """)
        self.assertEqual(out["pending"], 1)
        self.assertEqual(out["restored"], "复制账号")

    def test_missing_clipboard_api_still_flashes(self):
        """本轮修的正题:非安全上下文下 navigator.clipboard 不存在,点了必须有反应。"""
        out = _run_node(f"""
            {self._boot("{}")}
            const btn = makeBtn('复制账号');
            let threw = false;
            try {{ cf.copy(btn, '2300913684', '已复制'); }} catch (e) {{ threw = true; }}
            process.stdout.write(JSON.stringify({{ threw, flashed: btn.textContent }}));
            """)
        self.assertFalse(out["threw"])
        self.assertEqual(out["flashed"], "已复制", "剪贴板不可用时按钮毫无反应 = 用户以为坏了")

    def test_copy_writes_the_undashed_digits_and_restores(self):
        clipboard = (
            "{ clipboard: { writeText: (t) => { wrote.push(t); return Promise.resolve(); } } }"
        )
        out = _run_node(f"""
            {self._boot(clipboard, prelude="const wrote = [];")}
            const btn = makeBtn('复制账号');
            cf.copy(btn, '2300913684', '已复制');
            setTimeout(() => {{
                const flashed = btn.textContent;
                win.runAll();
                process.stdout.write(JSON.stringify({{
                    wrote, flashed, restored: btn.textContent,
                }}));
            }}, 0);
            """)
        self.assertEqual(out["wrote"], ["2300913684"])
        self.assertEqual(out["flashed"], "已复制")
        self.assertEqual(out["restored"], "复制账号")


class CopyFlashWiringTests(unittest.TestCase):
    """静态闸:调用方不许再留私版,共享模块必须真进两个 bundle。"""

    def test_callers_no_longer_keep_their_own_flash(self):
        # 判据自检:每个调用方文件必须真的存在且真的调了共享出口,否则下面的"没有私版"
        # 会因为文件被改名/删空而白绿。
        for path in _CALLERS:
            src = path.read_text(encoding="utf-8")
            self.assertIn("CopyFlash.copy(", src, f"{path.name} 没走共享出口")
            self.assertIsNone(
                re.search(r"function flash\s*\(", src),
                f"{path.name} 又留了一份私版 flash() —— 连点还原成「已复制」的坑会再长回来",
            )

    def test_shared_module_is_in_both_shell_bundles(self):
        """/ai 与 /dms 各自打包,少列一张清单那个壳上线就是 CopyFlash undefined。"""
        text = (PROJECT_ROOT / "scripts" / "build-home-js.mjs").read_text(encoding="utf-8")
        self.assertEqual(text.count("'shared/copy-flash.js'"), 2)

    def test_home_copy_button_never_silently_does_nothing(self):
        """/home 那份原先 `if (!navigator.clipboard) return;` —— 非安全上下文点了毫无反应。

        这条钉的是"不许写回来":剪贴板不可用时也得闪一下,闪的是「点到了」而不是「写成功了」。
        """
        src = _code_only(_HOME_MODULE)
        self.assertIsNone(
            re.search(r"if\s*\(\s*!\s*navigator\.clipboard\s*\)\s*return", src),
            "剪贴板不可用就静默 return 又长回来了 —— 用户只会以为按钮坏了再点一次",
        )
        self.assertIn("catch", src, "剪贴板 API 缺失时属性访问会抛,必须兜住")
        billing = _code_only(PROJECT_ROOT / "src" / "home" / "billing.ts")
        self.assertIn("copyFlash(", billing, "/home 充值弹窗没走本模块")
        self.assertIsNone(
            re.search(r"navigator\.clipboard", billing),
            "billing.ts 又自己碰剪贴板了 —— 复制反馈只许有一个出口",
        )

    def test_the_hold_window_is_declared_once(self):
        for module in (_MODULE, _HOME_MODULE):
            src = module.read_text(encoding="utf-8")
            self.assertEqual(
                len(re.findall(r"\b1500\b", src)), 1, f"{module.name} 里 1500 不止一处"
            )
        for path in _CALLERS:
            self.assertNotIn("1500", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
