# -*- coding: utf-8 -*-
"""LINE 卡片动作 postback 编解码(docs/smart-intake/15 §4 · 全套动作)。

承载数据卡上的动作,让用户「想干嘛干嘛」、永不卡死:
  exp_confirm  草稿 → 入账(post_doc)
  exp_undo     已入账 → 撤销(void_doc 冲销)
  exp_discard  草稿 → 丢弃(delete_doc,仅草稿)
  exp_in_post  待归类项 → 仍要入账(resolve_inbox+post)
  exp_in_drop  待归类项 → 丢弃(resolve_inbox dismiss)
不做「去采购还是费用」的路由问询。data 用 querystring,纯函数可单测。
doc 字段统一装 id(草稿为 doc_id,待归类为 intake_item id)。
可选 n 字段=一次性防重放令牌(PO-12);带 n 时服务端据令牌反查目标记录,旧卡无 n 走兼容链路。
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode

ACTION_CONFIRM = "exp_confirm"
ACTION_UNDO = "exp_undo"
ACTION_DISCARD = "exp_discard"
ACTION_INBOX_POST = "exp_in_post"
ACTION_INBOX_DROP = "exp_in_drop"
_ACTIONS = (ACTION_CONFIRM, ACTION_UNDO, ACTION_DISCARD, ACTION_INBOX_POST, ACTION_INBOX_DROP)


def _data(action: str, ref_id: str, token: str = "") -> str:
    kv = {"a": action, "doc": ref_id}
    if token:
        kv["n"] = token
    return urlencode(kv)


def confirm_data(doc_id: str, token: str = "") -> str:
    """草稿单 → 入账。"""
    return _data(ACTION_CONFIRM, doc_id, token)


def undo_data(doc_id: str, token: str = "") -> str:
    """已入账正式单 → 撤销(冲销)。"""
    return _data(ACTION_UNDO, doc_id, token)


def discard_data(doc_id: str, token: str = "") -> str:
    """草稿单 → 丢弃(仅草稿可删)。"""
    return _data(ACTION_DISCARD, doc_id, token)


def inbox_post_data(item_id: str, token: str = "") -> str:
    """待归类项 → 仍要入账。"""
    return _data(ACTION_INBOX_POST, item_id, token)


def inbox_drop_data(item_id: str, token: str = "") -> str:
    """待归类项 → 丢弃。"""
    return _data(ACTION_INBOX_DROP, item_id, token)


def parse(data: str) -> dict:
    """postback.data → {action, doc_id, token};非法 → 全空。"""
    try:
        kv = dict(parse_qsl(data or "", keep_blank_values=False))
    except (ValueError, TypeError):
        return {"action": "", "doc_id": "", "token": ""}
    action = kv.get("a", "")
    if action not in _ACTIONS:
        return {"action": "", "doc_id": "", "token": ""}
    return {"action": action, "doc_id": kv.get("doc", ""), "token": kv.get("n", "")}
