# -*- coding: utf-8 -*-
"""泰文金额大写(จำนวนเงินตัวอักษร · docs/16 §262 泰国收据/发票标配)。

纯逻辑叶子,不连库。原实现在 billing/topup_receipt(充值凭证),G2 全式税票也要印,
单一定义处挪到发票域;billing 侧改为从这里引。规则:整数部分逐段读(สิบ/ร้อย/พัน/
หมื่น/แสน,超六位递归 ล้าน),个位 1 读 เอ็ด、十位 2 读 ยี่สิบ、十位 1 读 สิบ;
无 สตางค์ 收 บาทถ้วน,有则读两位 สตางค์。
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

_THAI_NUM = ["ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
_THAI_POS = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน"]


def _read_group(s: str) -> str:
    """读一段 ≤6 位数字(无 ล้าน)。"""
    s = s.lstrip("0")
    if not s:
        return ""
    text = ""
    length = len(s)
    for i, ch in enumerate(s):
        d = int(ch)
        pos = length - 1 - i
        if d == 0:
            continue
        if pos == 0 and d == 1 and length > 1:
            text += "เอ็ด"
        elif pos == 1 and d == 2:
            text += "ยี่สิบ"
        elif pos == 1 and d == 1:
            text += "สิบ"
        else:
            text += _THAI_NUM[d] + _THAI_POS[pos]
    return text


def _read_int(n: int) -> str:
    if n == 0:
        return "ศูนย์"
    s = str(n)
    if len(s) > 6:  # ล้าน 递归(支持 ล้านล้าน)
        return _read_int(int(s[:-6])) + "ล้าน" + _read_group(s[-6:])
    return _read_group(s)


def baht_text(amount) -> str:
    """泰文金额大写:整数部分 + บาท + (ถ้วน | สตางค์)。"""
    q = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    baht = int(q)
    satang = int((q - baht) * 100)
    out = _read_int(baht) + "บาท"
    out += "ถ้วน" if satang == 0 else _read_group(str(satang)) + "สตางค์"
    return out
