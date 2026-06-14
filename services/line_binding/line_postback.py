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
# 文本路一句话记账确认卡(doc 10 §5):草稿先落,用户点按钮才确认/丢弃 —— 绝不静默入账。
ACTION_EXP_CONFIRM = "exp_confirm"
ACTION_EXP_DISCARD = "exp_discard"
_VALID_DIRECTIONS = ("purchase", "expense", "sales", "inbox")
_VALID_ACTIONS = (ACTION_CONFIRM, ACTION_REDIRECT, ACTION_EXP_CONFIRM, ACTION_EXP_DISCARD)


def confirm_data(doc_id: str) -> str:
    """[确认入采购] → 按当前猜测方向落单。"""
    return urlencode({"action": ACTION_CONFIRM, "doc": str(doc_id)})


def expense_confirm_data(draft_id: str) -> str:
    """[确认入账] → 确认费用草稿。"""
    return urlencode({"action": ACTION_EXP_CONFIRM, "draft": str(draft_id)})


def expense_discard_data(draft_id: str) -> str:
    """[取消] → 丢弃费用草稿(留痕 discarded · 不静默删)。"""
    return urlencode({"action": ACTION_EXP_DISCARD, "draft": str(draft_id)})


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
    if action not in _VALID_ACTIONS:
        return {"action": ""}
    out = {"action": action, "doc_id": kv.get("doc", "")}
    if action in (ACTION_EXP_CONFIRM, ACTION_EXP_DISCARD):
        out["draft_id"] = kv.get("draft", "")
    if action == ACTION_REDIRECT:
        d = kv.get("dir", "")
        out["direction"] = d if d in _VALID_DIRECTIONS else ""
    return out
