# -*- coding: utf-8 -*-
"""Express 推送单据防呆体检(确定性纯函数 · 不连库 · 不调 LLM)。

preflight 在方向判定后、映射前调用。挡掉"不该当普通票直接入账"的单据,命中即返
规范 reason → preflight 落 manual 转人工(doc28 §8 deferred 的"转人工即可"):

  currency_not_thb  外币票(无币种核对会把 USD 当泰铢记 · 金额性质错 · 最严重)
  credit_note       贷项/退货单(应走负向冲销,不当正向采购/销项)
  deposit_receipt   押金/定金收据(尚未发生费用 · 转人工)
  date_future       未来日期(反造假 · 标可疑复核)
  date_reissued     补开/倒签(ออกใบแทน 等 · 标可疑复核)
  tax_id_invalid    对手方税号位数非法(非 13 位)

判定全确定性(币种归一 / 关键词 / 位数 / 日期比较),只读票面字段,绝不写库。空信号
一律放行 —— 仅在票面"明确"出现外币/贷项/押金/未来日期/坏税号时拦,避免误伤正常票。
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, List, Optional

from services.purchase.field_clean import clean_tax_id

# 票面 currency 字段归一小写后,视为"泰铢/未标注"的取值(放行)。其余一律视外币。
_THB_CURRENCY = {"", "thb", "บาท", "baht", "฿", "thai baht"}

# 贷项/退货单印记(document_type 兜底 · 票面措辞)。
_CREDIT_KW = ("ใบลดหนี้", "credit note", "creditnote")
# 押金/定金/保证金印记。
_DEPOSIT_KW = ("เงินมัดจำ", "มัดจำ", "เงินประกัน", "เงินวางประกัน", "deposit")
# 补开/倒签印记(同一原始单据事后另开一张)。
_REISSUE_KW = ("ออกใบแทน", "ใบแทน", "ออกแทน", "reissue", "re-issue")


def _text_blob(fields: Dict[str, Any]) -> str:
    """票面自由文本(备注 + 摘要 + 行项目名)归一小写,供关键词匹配。"""
    parts: List[str] = [str(fields.get("notes") or ""), str(fields.get("category") or "")]
    items = fields.get("items")
    if isinstance(items, list):
        for it in items:
            if isinstance(it, dict):
                parts.append(str(it.get("name") or ""))
    return " ".join(parts).lower()


def _parse_iso_date(raw: Any) -> Optional[date]:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(raw or "").strip())
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def check_document(
    fields: Dict[str, Any],
    history: Dict[str, Any],
    direction: str,
    *,
    today: Optional[date] = None,
) -> Optional[str]:
    """跑单据防呆,返回规范 manual reason(命中)或 None(放行)。按严重度从高到低。"""
    # 1 · 币种(最严重):非泰铢票不能当泰铢直接入账。
    currency = str(fields.get("currency") or "").strip().lower()
    if currency and currency not in _THB_CURRENCY:
        return f"currency_not_thb:{currency[:12]}"

    # 票面自由文本(关键词匹配用)· 币种已早返不需,到此再建。
    blob = _text_blob(fields)

    # 2 · 贷项/退货单:应走负向冲销。document_type 优先,措辞兜底。
    doc_type = str(fields.get("document_type") or "").strip().lower()
    if doc_type == "credit_note" or any(k in blob for k in _CREDIT_KW):
        return "credit_note"

    # 3 · 押金/定金:尚未发生费用,转人工。
    if any(k in blob for k in _DEPOSIT_KW):
        return "deposit_receipt"

    # 4 · 日期合理性:未来日期 / 补开倒签 → 标可疑复核。
    invoice_date = _parse_iso_date(history.get("invoice_date") or fields.get("date"))
    if invoice_date is not None and invoice_date > (today or date.today()):
        return "date_future"
    if any(k in blob for k in _REISSUE_KW):
        return "date_reissued"

    # 5 · 对手方税号位数:采购看卖方、销项看买方;有值但非 13 位 → 标无效(轻)。
    # clean_tax_id 是全包"恰好 13 位数字否则空"的权威口径(direction/mapper 同用),不重复实现。
    raw_tax = fields.get("seller_tax") if direction != "sales" else fields.get("buyer_tax")
    party_tax = str(raw_tax or "")
    if any(ch.isdigit() for ch in party_tax) and not clean_tax_id(party_tax):
        return "tax_id_invalid"

    return None
