# -*- coding: utf-8 -*-
"""LINE 一句话记账 · L1 确定性解析引擎(doc 10 §2/§3 · 代码优先)。

只做确定性规则(正则 + 泰语字典):金额/数量/单价/日期/税号/发票号/分类/卖家。
够清楚就直接出确认卡(0 成本/毫秒)。真自然语言兜底(L2 LLM)= P1,本文件不含。
模型只"听懂"不"开口":本引擎纯产出 ExpenseDraft 数据,用户可见文案全在 line_i18n 模板。
泰语优先。产出对齐 services/ocr ThaiInvoice 字段,图/文两路下游共用。
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.expense.expense_draft import ExpenseDraft

# 分类不在此硬编码 —— 改由 webhook 拿本套账真实科目树(expense_categories)+ intake._match_category
# 匹配(图/文共用同一套树,不分叉)。本文件只做与树无关的确定性字段抽取。

# 服务类关键词(命中→service,否则默认 goods)· 泰语优先。
# 含公用事业(水/电/网/话费):它们是服务,不是商品(修「水费=商品」误判)。
_SERVICE_WORDS = (
    "บริการ",
    "ค่าจ้าง",
    "ซ่อม",
    "ค่าเช่า",
    "ที่ปรึกษา",
    "อบรม",
    "โฆษณา",
    "ขนส่ง",
    "ทำความสะอาด",
    "ค่าน้ำ",
    "ค่าไฟ",
    "ค่าไฟฟ้า",
    "น้ำประปา",
    "ค่าโทรศัพท์",
    "ค่าอินเทอร์เน็ต",
    "ค่าเน็ต",
    "service",
    "rent",
    "repair",
    "consult",
    "utility",
    "water",
    "electric",
    "internet",
    "服务",
    "维修",
    "咨询",
    "租",
    "培训",
    "广告",
    "运",
    "水费",
    "电费",
    "水电",
    "网费",
    "话费",
    "电话费",
    "燃气",
    "煤气",
    "宽带",
)

# 量词(数量信号)· 泰语优先。
_QTY_UNITS = ("ชิ้น", "จาน", "อัน", "ลัง", "กล่อง", "แก้ว", "个", "杯", "份", "件", "pcs", "pc")
_CURRENCY_MARK = ("บาท", "฿", "thb", "元", "块")
_TODAY_WORDS = ("วันนี้", "today", "今天")
_YESTERDAY_WORDS = ("เมื่อวาน", "yesterday", "昨天")
_DAYBEFORE_WORDS = ("เมื่อวานซืน", "วานซืน", "前天")

# 卖家品牌字典(#9·高频泰国商户·高精度)→ 规范名。L1 单笔路确定性抽卖家(对齐多笔 LLM 路)。
_VENDOR_BRANDS = (
    (r"สตาร์บัคส์|starbucks|星巴克", "Starbucks"),
    (r"เซเว่น|7[\s-]?eleven|7[\s-]?11|seven\s?eleven", "7-Eleven"),
    (r"แฟมิลี่มาร์ท|family\s?mart|全家", "FamilyMart"),
    (r"โลตัส|lotus'?s?|莲花超市", "Lotus's"),
    (r"บิ๊กซี|big\s?c", "Big C"),
    (r"แม็คโคร|makro", "Makro"),
    (r"เทสโก้|tesco", "Tesco"),
    (r"แกร็บ|\bgrab\b|grabfood", "Grab"),
    (r"ไลน์แมน|line\s?man", "LINE MAN"),
    (r"โบลท์|\bbolt\b", "Bolt"),
    (r"ปตท|\bptt\b", "PTT"),
    (r"บางจาก|bangchak", "Bangchak"),
    (r"เชลล์|\bshell\b", "Shell"),
    (r"แมคโดนัลด์|mcdonald'?s?|麦当劳|麦记", "McDonald's"),
    (r"เคเอฟซี|\bkfc\b|肯德基", "KFC"),
)
# 中文「在X买/吃/喝/付…」→ X 为卖家(泰文 ที่ 歧义大·不走介词只靠品牌字典)。
_ZH_AT_VENDOR = re.compile(r"在([^\d,，。、\s]{1,12}?)(?:买|買|吃|喝|付|消费|花|刷|订|點|点)")

_NUM = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?"


def _to_decimal(s: str) -> Optional[Decimal]:
    try:
        return Decimal(s.replace(",", ""))
    except (InvalidOperation, AttributeError):
        return None


def _today() -> date:
    return date.today()


def _parse_date(text: str) -> Optional[str]:
    """相对词 + DD/MM/YY[YY](佛历 25xx−543) → YYYY-MM-DD。认不出 → None(调用方默认今天)。"""
    low = text.lower()
    if any(w in low for w in _DAYBEFORE_WORDS):  # 前天/วานซืน(放 today/yesterday 前·含「昨」)
        return (_today() - timedelta(days=2)).isoformat()
    if any(w in low for w in _TODAY_WORDS):
        return _today().isoformat()
    if any(w in low for w in _YESTERDAY_WORDS):
        return (_today() - timedelta(days=1)).isoformat()
    mrel = re.search(r"(\d+)\s*(?:天前|วันก่อน|days?\s+ago)", low)  # N 天前
    if mrel:
        n = int(mrel.group(1))
        if 0 < n <= 366:
            return (_today() - timedelta(days=n)).isoformat()
    m = re.search(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b", text)
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y < 100:  # 2 位年:先试佛历 25YY-543,落在合理范围用它,否则公历 20YY
        be = 2500 + y - 543
        y = be if 2000 <= be <= _today().year + 1 else 2000 + y
    elif y >= 2400:  # 4 位佛历
        y -= 543
    try:
        return date(y, mo, d).isoformat()
    except ValueError:
        return None


def _extract_vendor(text: str) -> str:
    """确定性抽卖家(#9·单笔路对齐多笔 LLM):品牌字典命中优先 → 中文「在X买」→ 否则空。"""
    low = (text or "").lower()
    for pat, name in _VENDOR_BRANDS:
        if re.search(pat, low):
            return name
    m = _ZH_AT_VENDOR.search(text or "")
    if m:
        v = m.group(1).strip()
        if v and v not in ("这里", "那里", "这", "那", "网上", "外面"):
            return v
    return ""


def _extract_expense_type(text: str) -> str:
    """商品(goods)还是服务(service)· 命中服务关键词→service,否则默认 goods。"""
    low = text.lower()
    return "service" if any(w.lower() in low for w in _SERVICE_WORDS) else "goods"


def _extract_qty(text: str) -> Optional[Decimal]:
    m = re.search(r"[x×X]\s*(\d+(?:\.\d+)?)", text)
    if m:
        return _to_decimal(m.group(1))
    units = "|".join(re.escape(u) for u in _QTY_UNITS)
    m = re.search(rf"({_NUM})\s*(?:{units})", text)
    return _to_decimal(m.group(1)) if m else None


def _extract_unit_price(text: str) -> Optional[Decimal]:
    m = re.search(rf"(?:@|ต่อหน่วย|单价)\s*({_NUM})", text)
    return _to_decimal(m.group(1)) if m else None


def _extract_tax_and_invoice(text: str) -> tuple[str, str]:
    """13 位纯数字 → 卖家税号;字母前缀+数字码(如 IV69/00179)或其它长数字串 → 发票号(原样留前缀)。"""
    m = re.search(r"\b\d{13}\b", text)
    tax_id = m.group(0) if m else ""
    invoice_number = ""
    mm = re.search(r"\b[A-Za-z]{1,6}\d[\w/\-]*\b", text)  # 字母前缀编号
    if mm:
        invoice_number = mm.group(0)
    else:
        for run in re.finditer(r"\b\d{6,}\b", text):  # 兜底:长数字串(非税号)
            if run.group(0) != tax_id:
                invoice_number = run.group(0)
                break
    return tax_id, invoice_number


def _extract_amount(
    text: str, qty: Optional[Decimal], unit_price: Optional[Decimal]
) -> Optional[Decimal]:
    """金额(总额)。带币种标记的数优先;否则取剩余裸数字里最大的(排除已识别的数量)。"""
    low = text.lower()
    marks = "|".join(re.escape(m) for m in _CURRENCY_MARK)
    m = re.search(rf"(?:฿)\s*({_NUM})|({_NUM})\s*(?:{marks})", low)
    if m:
        return _to_decimal(m.group(1) or m.group(2))
    if qty is not None and unit_price is not None:
        return qty * unit_price
    # 裸数字兜底:先抹掉日期(13/06/69)和长编号/税号,再排除量词/单价,取剩下最大的当总额。
    cleaned = re.sub(r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}", " ", text)
    cleaned = re.sub(r"[A-Za-z]*\d[\d/\-]{6,}", " ", cleaned)
    nums = [_to_decimal(x) for x in re.findall(_NUM, cleaned)]
    nums = [n for n in nums if n is not None and n not in (qty, unit_price)]
    return max(nums) if nums else None


def looks_like_expense(text: str) -> bool:
    """有金额线索(币种标记 or 裸数字)即视为记账意图(doc 10 §2 L1)。"""
    return parse_expense(text).has_amount()


def split_qty_price(amount, qty=None, unit_price=None) -> tuple[str, str]:
    """(总额, 数量, 单价?) → 采购行的 (qty, unit_price) 字符串(图/文共用 · #8)。

    「买2杯咖啡共120」→ qty=2、单价=60。单价缺省由 总额÷数量 算(全精度·下游 totals 的
    gross=q(qty×price) 量化吸收·总额不漂);数量≤1 → qty=1、单价=总额(保持原行为)。
    """
    amt = _to_decimal(str(amount)) if amount not in (None, "") else None
    if amt is None:
        amt = Decimal("0")
    q = _to_decimal(str(qty)) if qty not in (None, "", 0) else None
    up = _to_decimal(str(unit_price)) if unit_price not in (None, "", 0) else None
    if q is not None and q > 1:
        if up is None or up <= 0:
            up = amt / q
        return (format(q.normalize(), "f"), format(up, "f"))
    return ("1", format(amt, "f"))


# L1 零成本意图(记账之外)——即便无 L2 也能正确分流,且即便句中有数字也不误记。
_SUPPORT_KW = (
    "人工",
    "客服",
    "转人工",
    "投诉",
    "真人",
    "human",
    "support agent",
    "ติดต่อเจ้าหน้าที่",
    "แอดมิน",
    "คุยกับคน",
)
_QUERY_KW = (
    "花了多少",
    "花多少",
    "本月花",
    "这个月花",
    "本月支出",
    "支出多少",
    "花销",
    "用了多少",
    "spent this month",
    "how much",
    "เดือนนี้จ่าย",
    "เดือนนี้ใช้",
    "ใช้ไปเท่าไหร่",
)
_QUESTION_MARK = ("吗", "呢", "嘛")


def l1_intent(text: str) -> Optional[str]:
    """记账之外的 L1 意图:support 求助 / query 查账。都不是 → None(交 L1 记账或 L2)。"""
    low = (text or "").lower()
    if any(k in low for k in _SUPPORT_KW):
        return "support"
    if any(k in low for k in _QUERY_KW):
        return "query"
    return None


def is_question(text: str) -> bool:
    """问句线索(吗/呢/嘛/?/?)→ 即便含数字也不当记账(防「我刚不是花了50吗」被误记)。"""
    t = (text or "").strip()
    return t.endswith(("?", "?")) or any(m in t for m in _QUESTION_MARK)


# 收入信号(#7):「收到货款500 / ขายได้ / 卖了」是收入,别当支出记。LINE 暂无收入流 →
# 只识别 + 不误记 + 引导。保守:须有明确收入词【且】无购买动词才判收入,宁漏勿误挡正常买东西。
_INCOME_KW = (
    # 泰语
    "ขายได้",
    "ขาย",
    "รับเงิน",
    "ได้รับเงิน",
    "เงินเข้า",
    "รายได้",
    "ยอดขาย",
    "ลูกค้าโอน",
    # 中文
    "收到货款",
    "货款",
    "收入",
    "卖",
    "销售",
    "营业额",
    "进账",
    "收款",
    "回款",
    # 英文
    "received payment",
    "got paid",
    "income",
    "revenue",
    "sold",
    "sales",
)
# 购买/付款动词:出现即视为支出,收入判定让位(防把「买/付/ซื้อ/จ่าย」误挡)。
_PURCHASE_VERB = ("ซื้อ", "จ่าย", "买", "付", "花", "bought", "paid", "spent", "buy")


def detect_income(text: str) -> bool:
    """疑似收入?仅当含明确收入词【且】无购买动词才 True(保守·宁漏勿误挡支出 · #7)。"""
    low = (text or "").lower()
    if not any(k.lower() in low for k in _INCOME_KW):
        return False
    return not any(v.lower() in low for v in _PURCHASE_VERB)


def parse_expense(text: str) -> ExpenseDraft:
    """自由文本 → ExpenseDraft(确定性映射 · doc 10 §3)。无金额 → amount=None(调用方澄清)。"""
    text = (text or "").strip()
    qty = _extract_qty(text)
    unit_price = _extract_unit_price(text)
    amount = _extract_amount(text, qty, unit_price)
    tax_id, invoice_number = _extract_tax_and_invoice(text)
    doc_date = _parse_date(text) or _today().isoformat()
    # category/subcategory 由 webhook 拿真实科目树解析(图/文共用 · 不在此分叉)。
    return ExpenseDraft(
        amount=amount,
        qty=qty,
        unit_price=unit_price,
        expense_type=_extract_expense_type(text),
        vendor_name=_extract_vendor(text),
        vendor_tax_id=tax_id,
        invoice_number=invoice_number,
        doc_date=doc_date,
        note=text,
        raw_text=text,
        source="line_text",
        confidence=Decimal("0.90") if amount is not None else Decimal("0"),
    )


# 多项一句话:「电费50 买菜40 电费10 吃饭50」→ 多笔(名+额)·每项独立归类/合计(对标 Paypers)。
_MULTI_RE = re.compile(r"([^\d฿]+?)\s*([\d,]+(?:\.\d+)?)")
_UNIT_TAIL = re.compile(r"(?i)\s*(元|块|บาท|泰铢|thb|baht|฿|kip)+\s*$")
_NAME_LEAD = re.compile(r"(?i)^[\s、,，/和跟加与及还有然后＋+]+|^(元|块|บาท|thb|baht|฿)\s*")


def parse_multi(text: str) -> Optional[list]:
    """一句话拆多项 → [{name, amount(Decimal)}];<2 项返 None(走单笔老路)。

    名去首尾货币词/连接词(和/跟/加…)。确定性正则(不靠 LLM 拆·避免误拆)。
    """
    items = []
    for m in _MULTI_RE.finditer((text or "").strip()):
        name = _UNIT_TAIL.sub("", _NAME_LEAD.sub("", m.group(1).strip())).strip(" -·:、,，/")
        try:
            amt = Decimal(m.group(2).replace(",", ""))
        except (InvalidOperation, ValueError):
            continue
        if name and amt > 0:
            items.append({"name": name, "amount": amt})
    return items if len(items) >= 2 else None
