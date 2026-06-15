# -*- coding: utf-8 -*-
"""LINE 卡片动作 postback 编解码(最小 · 仅撤销/确认 · docs/smart-intake/15 §4)。

只承载数据卡上的两个动作:↩️撤销(已入账→反过账)、✅确认(草稿→入账)。
不做「去采购还是费用」的路由问询(那套已废)。data 用 querystring 形态,纯函数可单测。
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode

ACTION_UNDO = "exp_undo"
ACTION_CONFIRM = "exp_confirm"
_ACTIONS = (ACTION_UNDO, ACTION_CONFIRM)


def undo_data(doc_id: str) -> str:
    """撤销按钮 postback.data(已入账的正式单 → void)。"""
    return urlencode({"a": ACTION_UNDO, "doc": doc_id})


def confirm_data(doc_id: str) -> str:
    """确认按钮 postback.data(草稿单 → post)。"""
    return urlencode({"a": ACTION_CONFIRM, "doc": doc_id})


def parse(data: str) -> dict:
    """postback.data → {action, doc_id};非法 → {action:'', doc_id:''}。"""
    try:
        kv = dict(parse_qsl(data or "", keep_blank_values=False))
    except (ValueError, TypeError):
        return {"action": "", "doc_id": ""}
    action = kv.get("a", "")
    if action not in _ACTIONS:
        return {"action": "", "doc_id": ""}
    return {"action": action, "doc_id": kv.get("doc", "")}
