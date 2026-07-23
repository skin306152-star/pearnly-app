# -*- coding: utf-8 -*-
"""DMS LINE 会话内全局命令的词形判定(单一事实源)。

判据此前散在 flow(เริ่มใหม่)与 menu_flow(เมนู/问候语)两处,分发顺序又把 editing 态
排在菜单词之前,用户改姓名时打 เมนู 会被当成新姓名写进 id_card。词表收到这里,调用方
一律引用 classify,不许再就地写前缀比较——两处各写一份就是漂移的温床。

纯函数:只看词形,不读会话、不做 IO。不含解绑词(webhook 层就地处理,不进对话流),
也不含 ยกเลิก(它是 editing 态的取消,不是全局词)。
"""

from __future__ import annotations

from typing import Optional

CMD_RESET = "reset"
CMD_MENU = "menu"
CMD_GREETING = "greeting"

RESET_WORD = "เริ่มใหม่"

_MENU_PREFIX = "เมน"
_MENU_MAX_LEN = 6  # เมนู 的常见打错(เมน/เมนB · 2026-07-19 真机实拍)都落在此长度内
_GREETING_PREFIX = "สวัสดี"


def classify(text: str) -> Optional[str]:
    """文本 → 全局命令,无命中返回 None。"""
    stripped = (text or "").strip()
    if stripped == RESET_WORD:
        return CMD_RESET
    if len(stripped) <= _MENU_MAX_LEN and stripped.startswith(_MENU_PREFIX):
        return CMD_MENU
    if stripped.startswith(_GREETING_PREFIX):
        return CMD_GREETING
    return None
