# -*- coding: utf-8 -*-
"""金额抽取 + 非金额数字剥离(L1 确定性 · 从 line_quick_entry 抽出 · 单一职责)。

只认"有金钱语境"的数字当总额:币种标记数优先;否则剥掉 负号 / 时间 / 百分比 / 单位后缀
(分钟/小时/人/角度…)/ 标签前缀(车牌/房号/年龄/电话/年份/楼层/税表名)/ 日期 / 长编号 /
卖家店号 / 笑声 555,再取剩余最大裸数。治"残留名词 + 任意数字"被 L1 当总额误记。
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

_NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
_CURRENCY = "บาท ฿ thb 元 块".split()
# 数字紧跟这些单位 = 不是钱(时长/计数/重量/包装量词)→ 是数量不是金额(单笔/多笔共用)。
_UNIT_AFTER = (
    "นาที โมง ชั่วโมง วินาที คน เดือน กิโล กก โล ครั้ง รอบ องศา "
    "โหล แพ็ค แพค ขวด ลิตร งวด กล่อง ถุง ห่อ ใบ"
).split()
# 这些标签后跟数字 = 不是钱(车牌/房号/年龄/电话/单据号/楼层/年份/型号/税表名)。
_LABEL_BEFORE = "ทะเบียน ห้อง อายุ เบอร์ โทร เลขที่ ชั้น ปี รุ่น ภพ ภงด บ้านเลขที่".split()


def _dec(s: str) -> Optional[Decimal]:
    try:
        return Decimal(s.replace(",", ""))
    except (InvalidOperation, AttributeError):
        return None


def strip_nonmoney(text: str) -> str:
    """剥掉"明显不是钱"的数字:负号数 / 时间 HH:MM / 百分比 / 单位后缀 / 标签前缀。"""
    s = " " + (text or "") + " "
    s = re.sub(r"(?<!\d)-\s*\d+(?:[.,]\d+)*", " ", s)  # 负数不是支出额
    s = re.sub(r"\d{1,2}:\d{2}", " ", s)  # 时间 14:30(别把分钟当钱)
    s = re.sub(rf"({_NUM})\s*%", " ", s)  # 百分比
    after = "|".join(re.escape(w) for w in _UNIT_AFTER)
    s = re.sub(rf"({_NUM})\s*(?:{after})", " ", s, flags=re.IGNORECASE)
    before = "|".join(re.escape(w) for w in _LABEL_BEFORE)
    # 标签前不被泰文字粘连(保护「ค่าโทร/ค่าห้อง/ค่าต่อทะเบียน」等 ค่า+X 费用·只剥独立标签);
    # 标签后可夹 1-2 个泰文辅音再到数字(车牌「ทะเบียน กข 1234」),不误伤「เลขที่บิล 500」。
    s = re.sub(
        rf"(?<![ก-๎])(?:{before})\s*(?:[ก-ฮ]{{1,2}}\s*)?\.?\s*({_NUM})",
        " ",
        s,
        flags=re.IGNORECASE,
    )
    return s


def money_numbers(text: str) -> list:
    """原文里"有金钱语境"的数字(剥掉非金额数后)→ Decimal 列表。供金额接地核验(LLM 不编金额)。"""
    nums = [_dec(x) for x in re.findall(_NUM, strip_nonmoney(text))]
    return [n for n in nums if n is not None]


def extract_amount(text, qty, unit_price):
    """总额:币种标记数优先;否则剥噪声后取最大裸数(多数字时丢纯 5{3,} 笑声)。"""
    from services.expense.line_quick_entry import _strip_vendor_brands

    text = strip_nonmoney(text)
    low = text.lower()
    marks = "|".join(re.escape(m) for m in _CURRENCY)
    m = re.search(rf"(?:฿)\s*({_NUM})|({_NUM})\s*(?:{marks})", low)
    if m:
        return _dec(m.group(1) or m.group(2))
    if qty is not None and unit_price is not None:
        return qty * unit_price
    cleaned = re.sub(r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}", " ", text)  # 日期
    cleaned = re.sub(r"[A-Za-z]*\d[\d/\-]{6,}", " ", cleaned)  # 长编号/税号/超长数字
    cleaned = _strip_vendor_brands(cleaned)  # 卖家店号(7-11/711 不是价)
    toks = re.findall(_NUM, cleaned)
    if len(toks) >= 2:  # 「กาแฟ 50 555」笑声 555 不顶替真额(仅有别的数字时丢)
        toks = [t for t in toks if not re.fullmatch(r"5{3,}", t.replace(",", ""))]
    nums = [_dec(x) for x in toks]
    nums = [n for n in nums if n is not None and n not in (qty, unit_price)]
    return max(nums) if nums else None
