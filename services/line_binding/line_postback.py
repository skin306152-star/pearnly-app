# -*- coding: utf-8 -*-
"""LINE Flex 卡按钮回调(postback)数据编解码(纯 · 阶段三)。

卡上 [确认入采购]/[改方向] 按钮带 postback.data;webhook 收到 postback 事件 → parse →
接 intake 分流(confirm=按猜测方向入采购 / redirect=切到指定方向)。querystring 形态,
不含敏感数据(只 doc_id + 动作),签名校验在 webhook 层。
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode

ACTION_CONFIRM = "confirm"
ACTION_REDIRECT = "redirect"
_VALID_DIRECTIONS = ("purchase", "expense", "sales", "inbox")


def confirm_data(doc_id: str) -> str:
    """[确认入采购] → 按当前猜测方向落单。"""
    return urlencode({"action": ACTION_CONFIRM, "doc": str(doc_id)})


def redirect_data(doc_id: str, direction: str) -> str:
    """[改方向] → 切到指定方向(进项/费用/销项/待归类)。"""
    return urlencode({"action": ACTION_REDIRECT, "doc": str(doc_id), "dir": direction})


def parse(data: str) -> dict:
    """postback.data → {action, doc_id, direction?}。非法 → {action:''}。"""
    try:
        kv = dict(parse_qsl(data or "", keep_blank_values=False))
    except (ValueError, TypeError):
        return {"action": ""}
    action = kv.get("action", "")
    if action not in (ACTION_CONFIRM, ACTION_REDIRECT):
        return {"action": ""}
    out = {"action": action, "doc_id": kv.get("doc", "")}
    if action == ACTION_REDIRECT:
        d = kv.get("dir", "")
        out["direction"] = d if d in _VALID_DIRECTIONS else ""
    return out
