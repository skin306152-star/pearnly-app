# -*- coding: utf-8 -*-
"""字段卫生质量层(P2B · 确定性纯函数 · 卡片/详情统一口径)。

OCR/结构化不确定时不裸露脏数据:在 field_clean(清洗)之上做「质量判定」——
  seller   全问号/乱码/纯数字/被 field_clean 剔空 → unclear(卡片显「ผู้ขายไม่ชัดเจน」不写正式卖家)
  date     非法/年份 < 2015/未来(佛历已在 schemas_invoice 先转公历)→ suspect(标待检查·不静默入账)
  tax_id   非 13 位合法 → invalid(留空·不显假税号)
  invoice  乱码/被剔空 → dirty
  address  乱码/碎片 → dirty(卡片不显·详情页可补)
判定结果用于:脏字段喂 field_confidence(卡片+详情自动标黄·口径一致)+ dirty_fields 日志 + 卡片状态分级。
只产判定,不改 OCR、不改金额/VAT/复式账。raw 仍留库供调试。
"""

from __future__ import annotations

import re
from datetime import date as _date

from services.purchase import field_clean

# 采购进项票合理日期下限(早于此 = OCR/年份解析错·不静默入账)。上限 = 今天(不接受未来日期)。
MIN_DATE = _date(2015, 1, 1)

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_DIGIT_ONLY_RE = re.compile(r"^[\d\s,.\-/]+$")


def seller_status(raw) -> str:
    """ok|unclear|absent。被 field_clean 剔空 / 乱码 / 纯数字符号 → unclear;原本就空 → absent。"""
    s = str(raw or "").strip()
    if not s:
        return "absent"
    if not field_clean.clean_seller(s) or field_clean.is_garbled(s) or _DIGIT_ONLY_RE.match(s):
        return "unclear"
    return "ok"


def date_status(date_str, today=None) -> str:
    """ok|suspect。非法格式 / 年份越界([2015, 今天]) / 未来 → suspect(佛历已上游转公历)。空 → absent。"""
    s = str(date_str or "").strip()
    if not s:
        return "absent"
    m = _DATE_RE.match(s)
    if not m:
        return "suspect"
    try:
        d = _date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return "suspect"
    if d < MIN_DATE or d > (today or _date.today()):
        return "suspect"
    return "ok"


def tax_status(raw) -> str:
    """ok|invalid|absent。13 位合法 → ok;有值但非法 → invalid;空 → absent。"""
    s = str(raw or "").strip()
    if not s:
        return "absent"
    return "ok" if field_clean.clean_tax_id(s) else "invalid"


def invoice_status(raw) -> str:
    """ok|dirty|absent。乱码/被剔空 → dirty;空 → absent。"""
    s = str(raw or "").strip()
    if not s:
        return "absent"
    return "ok" if (field_clean.clean_invoice_no(s) and not field_clean.is_garbled(s)) else "dirty"


def assess(fields: dict, *, today=None) -> dict:
    """统一质量判定 → {"quality": {seller/date/tax_id/invoice/address}, "dirty": [脏字段名]}。

    脏 = 有值但不可信(unclear/suspect/invalid/dirty);absent(本就没有)不进 dirty(不误报)。
    """
    quality = {
        "seller": seller_status(fields.get("seller_name")),
        "date": date_status(fields.get("date"), today),
        "tax_id": tax_status(fields.get("seller_tax")),
        "invoice": invoice_status(fields.get("invoice_number")),
        "address": "dirty" if field_clean.is_garbled(fields.get("seller_addr")) else "ok",
    }
    bad = {"unclear", "suspect", "invalid", "dirty"}
    dirty = [f for f, st in quality.items() if st in bad]
    return {"quality": quality, "dirty": dirty}


def card_signals(fields: dict, fc: dict, amount_dec, *, today=None):
    """质量判定 → 卡片/详情显示信号(P2B 单一接线点)。返回 (fc, signals)。

    脏 seller/date 喂 field_confidence(卡片 low() + 详情 mapConf 自动标黄·口径一致);
    amount_unreliable = 总额≤0 或 total_amount 像素置信 <0.85(卡片撤确认按钮·只去详情)。
    signals = {quality, dirty_fields, seller_unclear, date_suspect, amount_unreliable}。
    """
    res = assess(fields, today=today)
    quality, dirty = res["quality"], res["dirty"]
    fc = dict(fc or {})
    if quality["seller"] == "unclear":
        fc["seller_name"] = 0.5  # 详情页 supplier 标「请确认」(卡片走 seller_unclear 兜底文案)
    if quality["date"] == "suspect":
        fc["date"] = 0.5  # 卡片 date 缀「请核对」+ 详情 doc_date 标黄
    total_conf = fc.get("total_amount")
    amount_unreliable = amount_dec <= 0 or (total_conf is not None and float(total_conf) < 0.85)
    return fc, {
        "quality": quality,
        "dirty_fields": dirty,
        "seller_unclear": quality["seller"] == "unclear",
        "date_suspect": quality["date"] == "suspect",
        "amount_unreliable": amount_unreliable,
    }
