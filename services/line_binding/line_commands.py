# -*- coding: utf-8 -*-
"""LINE 文字命令解析(取链接 · 纯 · 阶段三)。

用户发「ขอ link drive」/「ขอ google sheet」等 → 返回当年归档 Drive 夹 / 主体×年 Sheet 链接
(接阶段二外流)。多语/多写法归一:命中关键词组合即认。纯函数,真取链接在 webhook 层。
"""

from __future__ import annotations

LINK_DRIVE = "drive_link"
LINK_SHEET = "sheet_link"

# 关键词(泰/中/英 · 小写匹配)。命中"取/要 + drive|sheet"即认对应命令。
_ASK = ("ขอ", "link", "ลิงก์", "取", "要", "给我", "get", "请给")
_DRIVE = ("drive", "ไดรฟ", "ไดร์ฟ", "云盘", "网盘")
_SHEET = ("sheet", "ชีต", "ชีท", "spreadsheet", "表格", "报表")


def parse_link_command(text: str):
    """文字 → LINK_DRIVE / LINK_SHEET / None。需同时含"取链接"意图词 + drive|sheet 词。"""
    s = (text or "").strip().lower()
    if not s:
        return None
    has_ask = any(k in s for k in _ASK)
    if not has_ask:
        return None
    if any(k in s for k in _SHEET):
        return LINK_SHEET
    if any(k in s for k in _DRIVE):
        return LINK_DRIVE
    return None
