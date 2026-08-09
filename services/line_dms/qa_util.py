# -*- coding: utf-8 -*-
"""DMS LINE 订车逐问(DL-7 · batch 1/3)的纯函数工具(文本归一 / 金额解析 / 主档行)。

booking_qa 状态机拆出的无状态叶子:搜索归一、泰文金额解析、主档行取标签、支付渠道
收尾。零 IO、零会话、不反向依赖状态机本体(booking_qa 单向 import 本文件),把它
压回 500 行以内。金额一律 Decimal,不用 float。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

MAX_AMOUNT = Decimal("99999999")
THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")

# 支付渠道补充信息的形态(单一事实源:booking_qa 步进 / qa_cards 文案共用):
# src_dst=转账问来源+到账两步;ref=单条补充文本;detail=自由描述;None=金额即完结。
CHANNEL_EXTRA_SHAPE = {
    "cash": None,
    "transfer": "src_dst",
    "cheque": "ref",
    "cashier_cheque": "ref",
    "card": "ref",
    "other": "detail",
}


def parse_amount(text: Optional[str]) -> Optional[Decimal]:
    """泰文数字→阿拉伯、去逗号/空白后 Decimal;非法/超界/超 2 位小数 → None。"""
    s = (text or "").translate(THAI_DIGITS).replace(",", "")
    s = "".join(s.split())
    if not s:
        return None
    try:
        value = Decimal(s)
    except InvalidOperation:
        return None
    if not value.is_finite() or value <= 0 or value > MAX_AMOUNT:
        return None
    if value != value.quantize(Decimal("0.01")):
        return None
    return value


def complete_channel(qa: Dict[str, Any]) -> None:
    """支付渠道收尾:追加进 payments、清 pending、回 pay_more。"""
    qa.setdefault("payments", []).append(qa["pending_channel"])
    qa["pending_channel"] = {}
    qa["step"] = "pay_more"


def norm(text: Optional[str]) -> str:
    """搜索归一:casefold + 只留字母数字。去连字符让 D-Max 能被 dmax 命中。"""
    return "".join(ch for ch in (text or "").casefold() if ch.isalnum())


def norm_row(row) -> str:
    """主档行可比串:名称 + 代码(同一归一)。"""
    name = str(row[2]) if len(row) > 2 else ""
    code = str(row[1]) if len(row) > 1 else ""
    return norm(f"{name} {code}")


def row_name(row) -> str:
    """主档行 [id, code, name, ...] 的名称;缺名回退代码/ID。"""
    if len(row) > 2 and row[2]:
        return str(row[2])
    return str(row[1]) if len(row) > 1 else str(row[0])


def car_label(row) -> str:
    """车型行标签:代码 + 名称(与 qa_cards._car_label 同形)。"""
    code = str(row[1]) if len(row) > 1 else ""
    name = str(row[2]) if len(row) > 2 else ""
    return (code + " " + name).strip()


def car_label_of(qa: Dict[str, Any]) -> str:
    return str((qa.get("answers") or {}).get("car", {}).get("label") or "")


def find_row(rows: Optional[List[list]], rid: Optional[str]) -> Optional[list]:
    for r in rows or []:
        if r and str(r[0]) == str(rid):
            return r
    return None
