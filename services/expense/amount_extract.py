# -*- coding: utf-8 -*-
"""金额抽取 + 非金额数字剥离(L1 确定性 · 从 line_quick_entry 抽出 · 单一职责)。

只认"有金钱语境"的数字当总额:币种标记数优先;否则剥掉 负号 / 时间 / 百分比 / 单位后缀
(分钟/小时/人/角度…)/ 标签前缀(车牌/房号/年龄/电话/年份/楼层/税表名)/ 日期 / 长编号 /
卖家店号 / 笑声 555,再取剩余最大裸数。治"残留名词 + 任意数字"被 L1 当总额误记。
正则均模块级预编译(strip/normalize 在每条消息热路径上跑 2-3 次)。
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

_NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
_CURRENCY = "บาท ฿ thb 元 块".split()
# 数字紧跟这些单位 = 不是钱(时长/计数/重量/包装量词/容器规格)→ 是数量不是金额(单笔/多笔共用)。
_UNIT_AFTER = (
    "นาที โมง ชั่วโมง วินาที คน เดือน กิโล กก โล ครั้ง รอบ องศา "
    "โหล แพ็ค แพค ขวด ลิตร งวด กล่อง ถุง ห่อ ใบ "
    "แก้ว จาน ชาม ถ้วย ชิ้น กระป๋อง ซอง "  # 餐饮量词(3แก้ว/2จาน)=份数不是钱·
    # 刻意不收 ที่(=「在/at」误伤「500 ที่บัญชี」)/ ลูก(撞前缀「ลูกค้า 客户」)
    "มล ml มิลลิลิตร ซีซี cc กรัม ขีด"  # 容器规格(125ml/300กรัม)=尺寸不是钱
).split()
# 这些标签后跟数字 = 不是钱(车牌/房号/年龄/电话/单据号/楼层/型号/税表名)。年份单独处理(见 _RE_YEAR)。
_LABEL_BEFORE = "ทะเบียน ห้อง อายุ เบอร์ โทร เลขที่ ชั้น รุ่น ภพ ภงด บ้านเลขที่".split()
# 品牌/型号里整体含数字(数字是名不是价)→ 整词剥(精确匹配·不碰 ห้าง 歧义·治真大脑也把 M150→记150)。
# 收录标准(严):数字必须是品牌名【固有】一部分(M-150 的 150 / 100Plus 的 100)。无数字品牌
# (สปอนเซอร์/คาราบาว/ลีโอ)不收——剥它们无意义且可能误删。容器规格(125ml)走单位词不在此。
# 剥后金额取真价;money_numbers 同剥 → 大脑编型号数字也被接地拒。扩词典在此加一行,守住"固有数字"标准。
_PRODUCT_BRANDS = (
    r"m\s?-?\s?150",  # M-150 ชูกำลัง(energy drink)
    r"เอ็ม\s?-?\s?150",
    r"100\s?\+?\s?(?:plus|พลัส)",  # 100Plus / 100 พลัส(sports drink)
    r"7\s?-?\s?up",  # 7Up น้ำอัดลม(soda)
    r"เซเว่นอัพ",
    r"(?:3|สาม)\s?แม่ครัว",  # 3 แม่ครัว / สามแม่ครัว ปลากระป๋อง(canned fish)
)
# 数字量级词(均为互不包含的独立词·限「数字+量级」形式·拼写数字 ห้าร้อย 是分词难题归大脑)。
_MULT = (("ล้าน", 1000000), ("แสน", 100000), ("หมื่น", 10000), ("พัน", 1000), ("ร้อย", 100))
# 泰数字 + 全角数字 → 阿拉伯(会计/正式文档常用·数字符号非词子串·安全)。
_NORM_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙０１２３４５６７８９", "01234567890123456789")
_RE_THAI_REPEAT_MARK = re.compile(r"([ะาิีึืุูเแโใไ])\1+")

# ── 预编译(下面的模式都是常量·strip/normalize 每条消息跑多次,不能每次重建)。 ──────────────
_RE_PRODUCT = tuple(re.compile(p, re.IGNORECASE) for p in _PRODUCT_BRANDS)
_RE_EU = re.compile(r"\d{1,3}(?:\.\d{3})+,\d+")  # 欧式千分位(点分千·逗号分小数)
_RE_K = re.compile(r"(\d+(?:\.\d+)?)\s*[kK](?![a-zA-Z])")  # 1k→1000
_RE_MULT = tuple((re.compile(rf"(\d+(?:\.\d+)?)\s*{w}"), m) for w, m in _MULT)
_RE_NEG = re.compile(r"(?<!\d)-\s*\d+(?:[.,]\d+)*")  # 负数不是支出额
_RE_TIME = re.compile(r"\d{1,2}:\d{2}")  # 时间 14:30 别把分钟当钱
_RE_PCT = re.compile(rf"({_NUM})\s*%")
# 笑声 555/5555(独立·非更大数一部分·后不接币种)→ 非金额(治「รอ 15 นาที 555」「20 555」)。
_RE_LAUGH = re.compile(r"(?<!\d)5{3,}(?!\d)(?!\s*(?:บาท|฿|thb|baht))", re.IGNORECASE)
# 年份引用(ปีนี้/ปีหน้า/ปี 2567)→ 年不是钱;不误伤「รายปี 5000」(5000 非 25xx/20xx)。
_RE_YEAR = re.compile(r"(?:ปีนี้|ปีหน้า|ปีที่แล้ว|ปีก่อน|ปี)\s*((?:25|24|19|20)\d{2})")
_RE_UNIT_AFTER = re.compile(
    rf"({_NUM})\s*(?:{'|'.join(re.escape(w) for w in _UNIT_AFTER)})", re.IGNORECASE
)
# 仅 ค่า/ต่อ 费用前缀时保护金额(「ค่าโทร/ค่าห้อง/ค่าต่อทะเบียน」是费用·不剥);其余粘连前缀
# (「ป้ายทะเบียน」车牌)照剥。标签后夹 1-2 泰文辅音(车牌)+ 斜杠续段(房号「99/12」整剥)。
_RE_LABEL_BEFORE = re.compile(
    rf"(?<!ค่า)(?<!ต่อ)(?:{'|'.join(re.escape(w) for w in _LABEL_BEFORE)})"
    rf"\s*(?:[ก-ฮ]{{1,2}}\s*)?\.?\s*({_NUM}(?:/\d+)*)",
    re.IGNORECASE,
)
_RE_NUM_DATE = re.compile(r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}")  # 数字日期 13/06/69
_RE_LONG_ID = re.compile(r"[A-Za-z]*\d[\d/\-]{6,}")  # 长编号/税号/发票号(单笔+多笔共用)
_RE_CURRENCY = re.compile(
    rf"(?:฿)\s*({_NUM})|({_NUM})\s*(?:{'|'.join(re.escape(m) for m in _CURRENCY)})"
)
_RE_FINDNUM = re.compile(_NUM)


def _dec(s: str) -> Optional[Decimal]:
    try:
        return Decimal(s.replace(",", ""))
    except (InvalidOperation, AttributeError):
        return None


def _scaled(num: str, mul: int) -> str:
    d = _dec(num)
    return format(d * mul, "f") if d is not None else num


def normalize_words(text: str) -> str:
    """数字简写归一(确定性):泰/全角数字→阿拉伯 · 1k→1000 · 2หมื่น→20000 · 欧式 1.250,50→1250.50。"""
    s = _RE_THAI_REPEAT_MARK.sub(r"\1", text or "").translate(_NORM_DIGITS)
    s = _RE_EU.sub(lambda m: m.group(0).replace(".", "").replace(",", "."), s)
    s = _RE_K.sub(lambda m: _scaled(m.group(1), 1000), s)
    for rx, mul in _RE_MULT:
        s = rx.sub(lambda m, mul=mul: _scaled(m.group(1), mul), s)
    return s


def strip_nonmoney(text: str) -> str:
    """剥掉"明显不是钱"的数字:型号品牌 / 负号 / 时间 / 百分比 / 笑声 / 年份 / 单位后缀 / 标签前缀。"""
    s = " " + (text or "") + " "
    for rx in _RE_PRODUCT:  # 型号/品牌里的数字是名不是价(M150/100พลัส)→ 整词先剥
        s = rx.sub(" ", s)
    s = _RE_NEG.sub(" ", s)
    s = _RE_TIME.sub(" ", s)
    s = _RE_PCT.sub(" ", s)
    s = _RE_LAUGH.sub(" ", s)
    s = _RE_YEAR.sub(" ", s)
    s = _RE_UNIT_AFTER.sub(" ", s)
    s = _RE_LABEL_BEFORE.sub(" ", s)
    return s


def money_numbers(text: str) -> list:
    """原文里"有金钱语境"的数字(剥掉非金额数后)→ Decimal 列表。供金额接地核验(LLM 不编金额)。"""
    nums = [_dec(x) for x in _RE_FINDNUM.findall(strip_nonmoney(normalize_words(text)))]
    return [n for n in nums if n is not None]


def extract_amount(text, qty, unit_price):
    """总额:数字简写归一 → 币种标记数优先;否则剥噪声(日期/长编号/卖家店号)后取最大裸数。"""
    from services.expense.line_quick_entry import _strip_vendor_brands

    text = strip_nonmoney(normalize_words(text))
    m = _RE_CURRENCY.search(text.lower())
    if m:
        return _dec(m.group(1) or m.group(2))
    if qty is not None and unit_price is not None:
        return qty * unit_price
    cleaned = _RE_LONG_ID.sub(" ", _RE_NUM_DATE.sub(" ", text))
    cleaned = _strip_vendor_brands(cleaned)  # 卖家店号(7-11/711 不是价)
    nums = [_dec(x) for x in _RE_FINDNUM.findall(cleaned)]
    nums = [n for n in nums if n is not None and n not in (qty, unit_price)]
    return max(nums) if nums else None
