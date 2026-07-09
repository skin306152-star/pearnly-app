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
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AI_DIR = PROJECT_ROOT / "static" / "ai"


def _run_node(js_source: str) -> dict:
    proc = subprocess.run(
        ["node", "-e", js_source],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        timeout=15,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"node failed: {proc.stderr.decode('utf-8', 'replace')}")
    return json.loads(proc.stdout.decode("utf-8"))
