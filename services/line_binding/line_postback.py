# -*- coding: utf-8 -*-
"""LINE 卡片动作 postback 编解码(docs/smart-intake/15 §4 · 全套动作)。

承载数据卡上的动作,让用户「想干嘛干嘛」、永不卡死:
  exp_confirm  草稿 → 入账(post_doc)
  exp_undo     已入账 → 撤销(void_doc 冲销)
  exp_discard  草稿 → 丢弃(delete_doc,仅草稿)
data 用 querystring,纯函数可单测。doc 字段装草稿/已入账的 purchase_doc id。
可选 n 字段=一次性防重放令牌(PO-12);带 n 时服务端据令牌反查目标记录,旧卡无 n 走兼容链路。
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode

ACTION_CONFIRM = "exp_confirm"
ACTION_UNDO = "exp_undo"
ACTION_DISCARD = "exp_discard"
# 批量撤销(确认/取消):目标 id 列表存于一次性令牌的 action_ref,data 只带 token(不带 doc)。
ACTION_BULK_UNDO = "exp_bulk_undo"
ACTION_BULK_CANCEL = "exp_bulk_cancel"
_ACTIONS = (ACTION_CONFIRM, ACTION_UNDO, ACTION_DISCARD, ACTION_BULK_UNDO, ACTION_BULK_CANCEL)


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


def bulk_undo_data(token: str) -> str:
    """批量撤销确认(目标 id 列表在令牌 action_ref·data 只带 token)。"""
    return urlencode({"a": ACTION_BULK_UNDO, "n": token})


def bulk_cancel_data(token: str) -> str:
    """批量撤销取消(作废令牌·不撤任何单)。"""
    return urlencode({"a": ACTION_BULK_CANCEL, "n": token})


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
