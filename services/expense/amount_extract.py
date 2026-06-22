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
# 这些标签后跟数字 = 不是钱(车牌/房号/年龄/电话/单据号/楼层/型号/税表名)。年份单独处理(见 strip)。
_LABEL_BEFORE = "ทะเบียน ห้อง อายุ เบอร์ โทร เลขที่ ชั้น รุ่น ภพ ภงด บ้านเลขที่".split()


def _dec(s: str) -> Optional[Decimal]:
    try:
        return Decimal(s.replace(",", ""))
    except (InvalidOperation, AttributeError):
        return None


# 数字量级词(均为互不包含的独立词·限「数字+量级」形式·拼写数字 ห้าร้อย 是分词难题归大脑)。
_MULT = (("ล้าน", 1000000), ("แสน", 100000), ("หมื่น", 10000), ("พัน", 1000), ("ร้อย", 100))
# 泰数字 + 全角数字 → 阿拉伯(会计/正式文档常用·数字符号非词子串·安全)。
_NORM_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙０１２３４５６７８９", "01234567890123456789")


def _scaled(num: str, mul: int) -> str:
    d = _dec(num)
    return format(d * mul, "f") if d is not None else num


def normalize_words(text: str) -> str:
    """数字简写归一(确定性):泰/全角数字→阿拉伯 · 1k→1000 · 2หมื่น→20000 · 欧式 1.250,50→1250.50。"""
    s = (text or "").translate(_NORM_DIGITS)
    s = re.sub(  # 欧式千分位(点分千·逗号分小数)
        r"\d{1,3}(?:\.\d{3})+,\d+", lambda m: m.group(0).replace(".", "").replace(",", "."), s
    )
    s = re.sub(r"(\d+(?:\.\d+)?)\s*[kK](?![a-zA-Z])", lambda m: _scaled(m.group(1), 1000), s)
    for word, mul in _MULT:
        s = re.sub(rf"(\d+(?:\.\d+)?)\s*{word}", lambda m, mul=mul: _scaled(m.group(1), mul), s)
    return s


def strip_nonmoney(text: str) -> str:
    """剥掉"明显不是钱"的数字:负号数 / 时间 HH:MM / 百分比 / 单位后缀 / 标签前缀。"""
    s = " " + (text or "") + " "
    s = re.sub(r"(?<!\d)-\s*\d+(?:[.,]\d+)*", " ", s)  # 负数不是支出额
    s = re.sub(r"\d{1,2}:\d{2}", " ", s)  # 时间 14:30(别把分钟当钱)
    s = re.sub(rf"({_NUM})\s*%", " ", s)  # 百分比
    # 笑声 555/5555(独立·非更大数一部分·后不接币种)→ 非金额(治「รอ 15 นาที 555」「20 555」)。
    s = re.sub(r"(?<!\d)5{3,}(?!\d)(?!\s*(?:บาท|฿|thb|baht))", " ", s, flags=re.IGNORECASE)
    # 年份引用(ปีนี้/ปีหน้า/ปี 2567)→ 年不是钱;不误伤「รายปี 5000」(5000 非 25xx/20xx)。
    s = re.sub(r"(?:ปีนี้|ปีหน้า|ปีที่แล้ว|ปีก่อน|ปี)\s*((?:25|24|19|20)\d{2})", " ", s)
    after = "|".join(re.escape(w) for w in _UNIT_AFTER)
    s = re.sub(rf"({_NUM})\s*(?:{after})", " ", s, flags=re.IGNORECASE)
    before = "|".join(re.escape(w) for w in _LABEL_BEFORE)
    # 仅在 ค่า/ต่อ 费用前缀时保护金额(「ค่าโทร/ค่าห้อง/ค่าต่อทะเบียน」是费用·不剥);其余粘连前缀
    # (「ป้ายทะเบียน」车牌)照剥。标签后夹 1-2 泰文辅音(车牌)+ 斜杠续段(房号「99/12」整剥)。
    s = re.sub(
        rf"(?<!ค่า)(?<!ต่อ)(?:{before})\s*(?:[ก-ฮ]{{1,2}}\s*)?\.?\s*({_NUM}(?:/\d+)*)",
        " ",
        s,
        flags=re.IGNORECASE,
    )
    return s


def money_numbers(text: str) -> list:
    """原文里"有金钱语境"的数字(剥掉非金额数后)→ Decimal 列表。供金额接地核验(LLM 不编金额)。"""
    nums = [_dec(x) for x in re.findall(_NUM, strip_nonmoney(normalize_words(text)))]
    return [n for n in nums if n is not None]


def extract_amount(text, qty, unit_price):
    """总额:数字简写归一 → 币种标记数优先;否则剥噪声后取最大裸数(多数字时丢纯 5{3,} 笑声)。"""
    from services.expense.line_quick_entry import _strip_vendor_brands

    text = strip_nonmoney(normalize_words(text))
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
    nums = [_dec(x) for x in re.findall(_NUM, cleaned)]
    nums = [n for n in nums if n is not None and n not in (qty, unit_price)]
    return max(nums) if nums else None
