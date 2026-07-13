# -*- coding: utf-8 -*-
"""控制台输出兜底(CLI 共用):目标控制台编码不一时不让成功路径因打印崩溃。"""

from __future__ import annotations

import sys


def make_stdout_encoding_safe() -> None:
    """摘要含泰文/中文而目标控制台编码不一(cp874/cp936/utf-8):保留控制台原生编码
    (cp874 下泰文照常显示),编不了的字符退化为 '?'(fileconv cp874 打印崩的血泪)。"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
