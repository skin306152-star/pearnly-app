#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/_node_harness.py

Pearnly AI 前端纯函数测试共享 harness:PROJECT_ROOT/AI_DIR 路径 + _run_node()
(真 node 子进程 require 源文件、断言 stdout JSON)。此前 test_ai_board_pure.py 与
test_ai_pure_modules.py 逐字节重复同一份定义,收到这里两处 import。下划线开头文件名 ·
unittest discovery 不收本文件当测试模块。
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AI_DIR = PROJECT_ROOT / "static" / "ai"

_BAHT_DECL = re.compile(r"var BAHT = '([^']*)';")
_JS_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def _baht_prefix() -> str:
    """ai-format.js 里金额前缀的真值(฿ + 分隔空白)。

    金额断言此前逐字写死 "฿6.00",前缀一改就集体假红,而红的是排版口径不是金额算错。
    前缀从真源读、小数位/千分位/负号照旧写死:排版归 test_ai_money_single_exit 那道闸管,
    这里只管数字对不对。
    """
    src = (AI_DIR / "ai-format.js").read_text(encoding="utf-8")
    m = _BAHT_DECL.search(src)
    if not m:
        raise AssertionError("ai-format.js 里找不到 BAHT 声明 —— 判据失效比断言失败更危险")
    return _JS_ESCAPE.sub(lambda e: chr(int(e.group(1), 16)), m.group(1))


BAHT = _baht_prefix()


def _run_node(js_source: str, timeout: float = 15) -> dict:
    """timeout 可调:按真实节拍跑的剧本(见 _scan_camera_harness.py)一条就要好几秒,
    15 秒的默认值会把「剧本还没演完」变成一条看不懂的 TimeoutExpired。"""
    proc = subprocess.run(
        ["node", "-e", js_source],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"node failed: {proc.stderr.decode('utf-8', 'replace')}")
    return json.loads(proc.stdout.decode("utf-8"))
