# -*- coding: utf-8 -*-
"""管家商品收发存查询 stock_card_lookup 的文案(zh + th · 纯函数,零 I/O)。

从 copy.py 分出来的原因只有一个:体积闸(单文件 <500 行),不是语义分家 —— copy 仍是唯一
入口,tool_title / reply / error 按工具委派到这里。

泰文用词与事务所端收发存报表页面(static/i18n-data.js 的 stc-* 键)逐字一致,不另起一套
翻译 —— 会计在对话里读到的词跟她点开报表页看到的词必须是同一个词,两处各翻一遍迟早漂:
  期初 ยอดยกมา · 入库 รับเข้า · 出库 จ่ายออก · 结存 คงเหลือ · 负库存 ติดลบ · 未归并 ยังไม่จับคู่
"""

from __future__ import annotations

from services.steward import registry
from services.steward.copy_lang import t as _t

# 负库存的成因提示,与报表页 stc-rule-negative / stc-list-hint 同一句(出库大于入库多半是
# 采购票没送齐,不是真的库存变负),不是本模块另编的新说法。
_NEGATIVE_CAUSE = {
    "zh": "出库大于入库,采购票可能没送齐",
    "th": "จ่ายออกมากกว่ารับเข้า บิลซื้ออาจไม่ครบ",
}

# 完整逐笔流水这里给不了(对话里念不完整期明细也没意义),统一指去事务所端报表页 —— 路径
# 原样抄导航文案(nav-group-firm-goods · nav-stock-card),不是本模块编的路名。
_POINTER = {
    "zh": "完整流水看事务所端『商品 → 收发存报表』。",
    "th": "ดูรายการเคลื่อนไหวทั้งหมดได้ที่「สินค้า → รายงานสต็อคการ์ด」ฝั่งสำนักงานบัญชี",
}

_SUMMARY = {
    "zh": "{client} · {period}:商品 {product_count} 个 · 负库存 {negative_count} 个 · "
    "未归并 {unmatched_count} 个 · 结存总额 ฿{bal_value_total}。{negative}{pointer}",
    "th": "{client} · งวด {period}: สินค้า {product_count} รายการ · ติดลบ {negative_count} "
    "รายการ · ยังไม่จับคู่ {unmatched_count} รายการ · มูลค่าคงเหลือรวม ฿{bal_value_total} "
    "{negative}{pointer}",
}
_SUMMARY_EMPTY = {
    "zh": "{client} · {period}:这期没有能生成收发存的商品单据(试试放宽期间,或先完成识别录入)。",
    "th": "{client} · งวด {period}: ไม่มีเอกสารสินค้าที่ลงสต็อคการ์ดได้ในงวดนี้ "
    "(ลองขยายช่วงเวลา หรือทำการรับรู้เอกสารก่อน)",
}
_SUMMARY_NEGATIVE = {
    "zh": "负库存:{items}({cause})。",
    "th": "สินค้าติดลบ: {items} ({cause}) ",
}

_PRODUCT = {
    "zh": "{client} · {period} · {name}:期初 {opening_qty}{unit} · 入 {in_qty}{unit}"
    "(฿{in_amount}) · 出 {out_qty}{unit}(฿{out_amount}) · 结存 {bal_qty}{unit}"
    "(单价 ฿{bal_unit_cost} · 金额 ฿{bal_value}){negative}。{pointer}",
    "th": "{client} · งวด {period} · {name}: ยอดยกมา {opening_qty}{unit} · รับเข้า "
    "{in_qty}{unit} (฿{in_amount}) · จ่ายออก {out_qty}{unit} (฿{out_amount}) · คงเหลือ "
    "{bal_qty}{unit} (ราคาต่อหน่วย ฿{bal_unit_cost} · มูลค่า ฿{bal_value}){negative} "
    "{pointer}",
}
_PRODUCT_NEGATIVE = {"zh": " · 负库存({cause})", "th": " · ติดลบ ({cause})"}

ERR_NOT_FOUND = "steward.stockcard_product_not_found"
ERR_AMBIGUOUS = "steward.stockcard_product_ambiguous"

_ERROR_NOT_FOUND = {
    "zh": "{client} · {period}:商品名录里没有「{keyword}」这一项。换个说法,"
    "或问「这个月库存怎么样」看全表。",
    "th": '{client} · งวด {period}: ไม่พบสินค้า "{keyword}" ในรายการ พิมพ์ชื่ออื่น '
    'หรือถามว่า "สต็อกเดือนนี้เป็นยังไง" เพื่อดูทั้งตาราง',
}
_ERROR_AMBIGUOUS = {
    "zh": "「{keyword}」对上了 {total} 个商品:{names}。说清楚是哪一个,商品编码最准。",
    "th": 'คำว่า "{keyword}" ตรงกับสินค้า {total} รายการ: {names} '
    "ระบุให้ชัดว่าอันไหน รหัสสินค้าจะตรงที่สุด",
}
ERRORS = {ERR_NOT_FOUND: _ERROR_NOT_FOUND, ERR_AMBIGUOUS: _ERROR_AMBIGUOUS}

TITLES = {registry.STOCK_CARD_LOOKUP: {"zh": "查商品收发存", "th": "ดูสต็อคการ์ดสินค้า"}}


def _unit_suffix(unit) -> str:
    unit = (unit or "").strip()
    return f" {unit}" if unit else ""


def _is_negative(qty) -> bool:
    return str(qty or "0").strip().startswith("-")


def _row_label(row: dict) -> str:
    return f"{row.get('name', '')} {row.get('bal_qty', '0')}"


def reply(data: dict, lang: str) -> str:
    if "product" in data:
        return _product_reply(data, lang)
    return _summary_reply(data, lang)


def _summary_reply(data: dict, lang: str) -> str:
    client, period = data.get("client_name", ""), data.get("period", "")
    if not data.get("product_count"):
        return _t(_SUMMARY_EMPTY, lang).format(client=client, period=period)
    negative_count = data.get("negative_count", 0)
    negative = ""
    if negative_count:
        items = ", ".join(_row_label(r) for r in data.get("negative_rows") or [])
        negative = _t(_SUMMARY_NEGATIVE, lang).format(items=items, cause=_t(_NEGATIVE_CAUSE, lang))
    return _t(_SUMMARY, lang).format(
        client=client,
        period=period,
        product_count=data.get("product_count", 0),
        negative_count=negative_count,
        unmatched_count=data.get("unmatched_count", 0),
        bal_value_total=data.get("bal_value_total", "0.00"),
        negative=negative,
        pointer=_t(_POINTER, lang),
    )


def _product_reply(data: dict, lang: str) -> str:
    product = data.get("product") or {}
    totals = data.get("totals") or {}
    unit = _unit_suffix(product.get("unit"))
    bal_qty = totals.get("bal_qty", "0")
    negative = (
        _t(_PRODUCT_NEGATIVE, lang).format(cause=_t(_NEGATIVE_CAUSE, lang))
        if _is_negative(bal_qty)
        else ""
    )
    return _t(_PRODUCT, lang).format(
        client=data.get("client_name", ""),
        period=data.get("period", ""),
        name=product.get("name") or data.get("keyword", ""),
        unit=unit,
        opening_qty=data.get("opening_qty", "0"),
        in_qty=totals.get("in_qty", "0"),
        in_amount=totals.get("in_amount", "0.00"),
        out_qty=totals.get("out_qty", "0"),
        out_amount=totals.get("out_amount", "0.00"),
        bal_qty=bal_qty,
        bal_unit_cost=totals.get("bal_unit_cost") or "-",
        bal_value=totals.get("bal_value", "0.00"),
        negative=negative,
        pointer=_t(_POINTER, lang),
    )


def error(code: str, data: dict, lang: str) -> str:
    if code == ERR_NOT_FOUND:
        return _t(_ERROR_NOT_FOUND, lang).format(
            client=data.get("client_name", ""),
            period=data.get("period", ""),
            keyword=data.get("keyword", ""),
        )
    names = ", ".join(_row_label(r) for r in data.get("candidates") or [])
    return _t(_ERROR_AMBIGUOUS, lang).format(
        keyword=data.get("keyword", ""), total=data.get("total", 0), names=names
    )


REPLIES = {registry.STOCK_CARD_LOOKUP: reply}
