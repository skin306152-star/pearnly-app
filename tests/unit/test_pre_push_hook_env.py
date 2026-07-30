#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pre-push 钩子的环境守门 —— 按钩子导出的环境真跑一遍,不是读一眼那行 export。

出身(2026-07-31 实测):钩子当时只 `export PYTHONIOENCODING=utf-8`,本机跑全量就有两个
模块假红,而两个方向的原因还相反 ——

    只设 PYTHONIOENCODING → test_file_crypto 红
        它 subprocess.run(..., text=True) 读子进程管道,解码用的是 locale 编码(本机
        cp874)。子进程照 UTF-8 写、父进程照 cp874 读 → 读线程 UnicodeDecodeError →
        proc.stderr 变成 None → assertIn(str, None) TypeError。
    什么都不设   → test_agent_capability_audit 红
        它的子进程 print 中文进 cp874 管道 → UnicodeEncodeError → 退 1 → 当成闸真红。

也就是说:按当时的钩子在本机推送,会被两条假红轮流拦住;想绕就只能 --no-verify,那等于
把整排闸一起关掉。PYTHONUTF8=1 是 UTF-8 模式,连 locale 编码一起改,两个方向才对齐。

断言的方式是【真跑】:拿钩子里 export 出来的那份环境去跑那两个模块。把 export 那行当字符串
断言的话,下次有人改成 PYTHONIOENCODING=utf8(少个横杠)照样绿 —— 而本机会当场假红。
"""

from __future__ import annotations

import locale
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / "scripts" / "git-hooks" / "pre-push"

# 两个金丝雀:一个证明「父进程读子进程管道」这条路通,一个证明「子进程打印中文」这条路通。
# 它们是本机唯一两个对环境编码敏感的模块 —— 换句话说,钩子设错了先在这两条上炸。
CANARIES = ("tests.unit.test_file_crypto", "tests.unit.test_agent_capability_audit")

_EXPORT = re.compile(r"^export\s+([A-Z_][A-Z0-9_]*)=(\S*)\s*$", re.M)
_ENCODING_VARS = ("PYTHONUTF8", "PYTHONIOENCODING")


def hook_text() -> str:
    return HOOK.read_text(encoding="utf-8")


def hook_exports() -> dict[str, str]:
    """钩子在跑闸之前 export 出去的环境。"""
    return {m.group(1): m.group(2) for m in _EXPORT.finditer(hook_text())}


def run_canaries(overrides: dict[str, str]) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in _ENCODING_VARS}
    env.update(overrides)
    return subprocess.run(
        [sys.executable, "-m", "unittest", *CANARIES],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        # 本进程读它的输出别再踩同一个坑:显式 utf-8,不吃 locale
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )


def native_encoding() -> str:
    """这台机器【没设任何 Python 编码变量时】的 locale 编码。

    不能直接问 locale:本测试自己很可能就跑在 UTF-8 模式下,问出来的是 utf-8。
    """
    env = {k: v for k, v in os.environ.items() if k not in _ENCODING_VARS}
    proc = subprocess.run(
        [sys.executable, "-c", "import locale;print(locale.getpreferredencoding(False))"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return (proc.stdout or "").strip().lower()


_NATIVE_IS_UTF8 = locale.normalize(native_encoding() or "utf-8").split(".")[-1] in (
    "utf-8",
    "utf8",
    "utf_8",
)


class HookEnvContract(unittest.TestCase):
    def test_hook_turns_on_utf8_mode(self):
        self.assertEqual(
            hook_exports().get("PYTHONUTF8"),
            "1",
            "钩子没开 UTF-8 模式 —— 本机跑全量会被假红拦住,只能 --no-verify 绕过整排闸",
        )

    def test_the_export_happens_before_any_gate_runs(self):
        """设在跑闸之后等于没设。"""
        text = hook_text()
        self.assertLess(
            text.index("export PYTHONUTF8=1"),
            text.index("python -m unittest"),
            "PYTHONUTF8 设在跑测试之后了",
        )


class CanaryModules(unittest.TestCase):
    """判据落在真跑上:换成任何别的写法,这里立刻红。"""

    def test_canaries_are_green_under_the_hook_env(self):
        proc = run_canaries(hook_exports())
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    @unittest.skipIf(_NATIVE_IS_UTF8, "这台机器 locale 本来就是 UTF-8 · 两种设法都不会炸")
    def test_the_old_hook_setting_really_did_fail_here(self):
        """反证:换回钩子改之前那一行,金丝雀必须真的红 —— 否则上面那条绿得没有意义。"""
        proc = run_canaries({"PYTHONIOENCODING": "utf-8"})
        self.assertNotEqual(proc.returncode, 0, "旧设法在这台机器上没炸,反证不成立")
        self.assertIn("test_file_crypto", proc.stdout + proc.stderr)

    @unittest.skipIf(_NATIVE_IS_UTF8, "这台机器 locale 本来就是 UTF-8 · 两种设法都不会炸")
    def test_setting_nothing_also_fails_here(self):
        """另一头:什么都不设时炸的是另一个模块 —— 两头都堵住才轮得到 PYTHONUTF8。"""
        proc = run_canaries({})
        self.assertNotEqual(proc.returncode, 0, "不设任何编码变量竟然全绿,反证不成立")
        self.assertIn("agent_capability_audit", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
