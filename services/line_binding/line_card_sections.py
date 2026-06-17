# -*- coding: utf-8 -*-
"""LINE 数据卡的 Flex 原语与分区构建块(从 line_card 抽出 · 保 line_card <500)。

纯函数、无 IO、可单测。颜色令牌 + 文本原语 + 字段行/税额拆解/卖家行/明细行/分隔白卡。
line_card 负责编排(状态头/金额区/动作区/终态卡),本模块只产可复用的小块。
"""

from __future__ import annotations

# 颜色令牌(与定稿原型一致)。
BRAND = "#2563EB"
AMOUNT = "#111827"
AMOUNT_MISS = "#98A2B3"
LABEL = "#98A2B3"
DESC = "#475467"
VALUE = "#344054"
VALUE_STRONG = "#202939"
LOW = "#B45309"
META_STRONG = "#475467"
SEP = "#EEF0F3"
LINK = "#4D607C"
LINK_DANGER = "#8F4A4A"

REVIEW_BELOW = 0.85


def txt(text, *, size, color, **kw) -> dict:
    return {"type": "text", "text": str(text), "size": size, "color": color, **kw}


def field_row(label: str, value: str, t: dict, *, low: bool, strong: bool) -> dict:
    """两列字段行(左标签灰 · 右值)。低置信值缀「请核对」并转琥珀。"""
    val = (value or "").strip() or t["na"]
    if low and val != t["na"]:
        val = f"{val} {t['review']}"
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            txt(label, size="sm", color=LABEL, flex=4, wrap=True),
            txt(
                val,
                size="sm",
                color=LOW if low else (VALUE if not strong else "#202939"),
                flex=6,
                wrap=True,
                weight="bold" if strong else "regular",
            ),
        ],
    }


def breakdown_rows(fields: dict, t: dict) -> list:
    """税额拆解条:税前 ฿ · VAT ฿ · WHT ฿ · 舍入 ฿(各项有值才显·无 → 空不占位)。"""
    sub = str(fields.get("subtotal") or "").strip()
    vat = str(fields.get("vat") or "").strip()
    wht = str(fields.get("wht") or "").strip()
    rounding = str(fields.get("rounding") or "").strip()
    parts = []
    if sub:
        parts.append(f"{t['subtotal']} ฿{sub}")
    if vat:
        parts.append(f"VAT ฿{vat}")
    if wht and wht.replace(".", "").strip("0"):
        parts.append(f"WHT ฿{wht}")
    if rounding and rounding.replace(".", "").replace("-", "").strip("0"):
        parts.append(f"{t['rounding']} ฿{rounding}")
    if not parts:
        return []
    return [txt(" · ".join(parts), size="xxs", color=LABEL, margin="sm", wrap=True)]


def seller_rows(fields: dict, t: dict) -> list:
    """卖家税号/地址条件行(有值才显·空则不堆空行)。"""
    rows = []
    tax = str(fields.get("seller_tax") or "").strip()
    addr = str(fields.get("seller_addr") or "").strip()
    if tax:
        rows.append(field_row(t["tax_id"], tax, t, low=False, strong=False))
    if addr:
        rows.append(field_row(t["address"], addr, t, low=False, strong=False))
    return rows


def seclabel(text: str) -> dict:
    """分区小标题(灰·小号)。"""
    return txt(text, size="xs", color=LABEL, weight="bold")


def strip(text: str, bg: str, color: str) -> dict:
    """贴顶满宽细色条(融入卡·非浮动圆角块):总额不符 / 可能重复。"""
    return {
        "type": "box",
        "layout": "vertical",
        "paddingTop": "10px",
        "paddingBottom": "10px",
        "paddingStart": "18px",
        "paddingEnd": "18px",
        "backgroundColor": bg,
        "contents": [txt(text, size="xxs", color=color, wrap=True)],
    }


def items_section(items: list, t: dict, *, cap: int = 5) -> list:
    """明细分区:小标题 + 逐条(编号 + 名称 + 右对齐价)。超 cap 行 → 截断 + 「还有N行,去详情页」。"""
    items = items or []
    rows = [seclabel(t["detail"])]
    for i, it in enumerate(items[:cap], 1):
        name = (str(it.get("name") or "").strip()) or t["na"]
        amt = str(it.get("amount") or "").strip()
        rows.append(
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    txt(f"{i}. {name}", size="sm", color=VALUE, flex=5, wrap=True),
                    txt(
                        f"฿{amt}" if amt else "",
                        size="sm",
                        color=VALUE_STRONG,
                        weight="bold",
                        flex=2,
                        align="end",
                        wrap=True,
                    ),
                ],
            }
        )
    extra = len(items) - cap
    if extra > 0:
        rows.append(txt(t["items_more"].format(n=extra), size="xxs", color=LABEL, wrap=True))
    return rows


def sheet(sections: list) -> list:
    """把各非空分区拼成一张连续白卡:区与区之间一条细横线(融入·按类分隔)。"""
    out = []
    for contents in sections:
        if not contents:
            continue
        if out:
            out.append({"type": "separator", "color": SEP})
        out.append(
            {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "spacing": "sm",
                "contents": contents,
            }
        )
    return out
