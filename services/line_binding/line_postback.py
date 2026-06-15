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
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode

ACTION_CONFIRM = "exp_confirm"
ACTION_UNDO = "exp_undo"
ACTION_DISCARD = "exp_discard"
ACTION_INBOX_POST = "exp_in_post"
ACTION_INBOX_DROP = "exp_in_drop"
_ACTIONS = (ACTION_CONFIRM, ACTION_UNDO, ACTION_DISCARD, ACTION_INBOX_POST, ACTION_INBOX_DROP)


def _data(action: str, ref_id: str) -> str:
    return urlencode({"a": action, "doc": ref_id})


def confirm_data(doc_id: str) -> str:
    """草稿单 → 入账。"""
    return _data(ACTION_CONFIRM, doc_id)


def undo_data(doc_id: str) -> str:
    """已入账正式单 → 撤销(冲销)。"""
    return _data(ACTION_UNDO, doc_id)


def discard_data(doc_id: str) -> str:
    """草稿单 → 丢弃(仅草稿可删)。"""
    return _data(ACTION_DISCARD, doc_id)


def inbox_post_data(item_id: str) -> str:
    """待归类项 → 仍要入账。"""
    return _data(ACTION_INBOX_POST, item_id)


def inbox_drop_data(item_id: str) -> str:
    """待归类项 → 丢弃。"""
    return _data(ACTION_INBOX_DROP, item_id)


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
