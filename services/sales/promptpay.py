# -*- coding: utf-8 -*-
"""PromptPay 付款二维码(L1 · docs/16 §L1)。

按 EMVCo / 泰国 BOT「PromptPay anyID」格式拼付款 payload(代理 = 手机号 / 身份证或税号 /
e-Wallet),含金额时出动态 QR(收款人即卖方账套的 promptpay_id)。便利功能,非税务合规件:
仅未收款的票或显式付款请求时出。纯函数叶子,不连库;QR 图按需用 qrcode 渲染。
"""

from __future__ import annotations

import io
from decimal import Decimal

# BOT PromptPay 的 EMVCo Application ID。
_AID = "A000000677010111"
_CURRENCY_THB = "764"
_COUNTRY_TH = "TH"


def _emv(tag: str, value: str) -> str:
    """EMVCo TLV 字段:标签(2) + 长度(2 位十进制) + 值。"""
    return f"{tag}{len(value):02d}{value}"


def _crc16(data: str) -> str:
    """CRC-16/CCITT-FALSE(poly 0x1021 · init 0xFFFF),EMVCo ID 63 校验,大写 4 位十六进制。"""
    crc = 0xFFFF
    for byte in data.encode("ascii"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def _proxy(promptpay_id: str) -> tuple[str, str]:
    """归一化代理 → (子标签, 值)。手机号(tag 01·0066+9 位补零至 13)/ 身份证或税号
    (13 位·tag 02)/ e-Wallet(15 位·tag 03)。"""
    digits = "".join(c for c in str(promptpay_id or "") if c.isdigit())
    if len(digits) >= 15:
        return "03", digits[:15]
    if len(digits) == 13:
        return "02", digits
    # 手机号:去前导 0 换 66,左补零到 13 位(0066xxxxxxxxx)。
    mobile = "66" + digits[1:] if digits.startswith("0") else digits
    return "01", ("0000000000000" + mobile)[-13:]


def build_payload(promptpay_id: str, amount=None) -> str:
    """拼 PromptPay EMV payload 字符串(可直接编码成 QR)。amount 为空 = 静态码(扫后自填)。"""
    sub_tag, target = _proxy(promptpay_id)
    merchant = _emv("00", _AID) + _emv(sub_tag, target)
    parts = [
        _emv("00", "01"),
        _emv("01", "12" if amount is not None else "11"),
        _emv("29", merchant),
        _emv("58", _COUNTRY_TH),
        _emv("53", _CURRENCY_THB),
    ]
    if amount is not None:
        parts.append(_emv("54", f"{Decimal(str(amount)):.2f}"))
    body = "".join(parts) + "6304"
    return body + _crc16(body)


def build_qr_png(promptpay_id: str, amount=None) -> bytes:
    """渲染 PromptPay 付款二维码 PNG 字节(qrcode + Pillow)。"""
    import qrcode

    img = qrcode.make(build_payload(promptpay_id, amount))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
