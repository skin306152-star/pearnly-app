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
from services.expense.line_classify import classify_expense_type

# 分类不在此硬编码 —— 改由 webhook 拿本套账真实科目树(expense_categories)+ intake._match_category
# 匹配(图/文共用同一套树,不分叉)。本文件只做与树无关的确定性字段抽取。
# 费用类型/付款方式 关键词归类抽到 line_classify(保本文件 <500)。

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
    # 主流商超/便利/药妆(泰英中别名·精确不误伤)。供应商单列 + 从品名剥除(_strip_vendor_brands)。
    # 拉丁词用 (?<![a-z])X(?![a-z]) 边界(非 \b):\b 在 CJK 紧邻时失效(「在tops买」中 在|t 皆 \w
    # 无边界);此守卫只把 ASCII 字母算边界,故 CJK 紧邻也命中、laptops 不误伤。
    (r"(?<![a-z])tops(?![a-z])|ท็อปส์|ท็อป มาร์เก็ต", "Tops"),
    (r"villa\s?market|วิลล่า\s?มาร์เก็ต|วิลลามาร์เก็ต|维拉超市", "Villa Market"),
    (r"foodland|ฟู้ดแลนด์|ฟู้ดแลน", "Foodland"),
    (r"maxvalu|แม็กซ์แวลู|แมกซ์แวลู", "MaxValu"),
    (r"gourmet\s?market|กูร์เมต์\s?มาร์เก็ต|กูร์เมต์", "Gourmet Market"),
    (r"robinson|โรบินสัน|รอบินสัน", "Robinson"),
    (r"watsons?|วัตสัน", "Watsons"),
    (r"(?<![a-z])boots(?![a-z])|บู๊ทส์|บูทส์", "Boots"),
    (r"cp\s?fresh\s?mart|ซีพี\s?เฟรช\s?มาร์ท", "CP Fresh Mart"),
)
# 中文「在X买/吃/喝/付…」→ X 为卖家(泰文 ที่ 歧义大·不走介词只靠品牌字典)。
_ZH_AT_VENDOR = re.compile(r"在([^\d,，。、\s]{1,12}?)(?:买|買|吃|喝|付|消费|花|刷|订|點|点)")

# 逗号分组分支须真带逗号(+ 不是 *):否则 findall 对裸「1500」会贪婪切成「150」+「0」→ max=150
# (空调 1500 被记成 150 的真因)。非逗号数走第二分支整体匹配。
_NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"


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
    # 年首/ISO(2026-06-18 · 2026/6/18 · 佛历 2569/6/18−543)先试,再回退 DD/MM/YY[YY]。
    my = re.search(r"(?<!\d)(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})(?!\d)", text)
    if my:
        yy, mo, d = int(my.group(1)), int(my.group(2)), int(my.group(3))
        if yy >= 2400:
            yy -= 543
        try:
            return date(yy, mo, d).isoformat()
        except ValueError:
            pass
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


# 动词/连接/介词噪声(抽干净物品名时剔除)· 泰中英 · 单笔「详情」结构化用。顺序敏感(长词先剥·
# 「买了」须在「买」前),故按空格列举的次序即剥除次序。
_NAME_NOISE = (
    "ซื้อมา ซื้อ ดื่ม กิน รับประทาน จ่าย ที่ ใน และ กับ แล้ว 买了 买 買 吃 喝 点了 点 订 消费 "
    "花了 花 付了 付 共 在 和 跟 价格 价 ราคา bought paid spent buy"
).split()


def _strip_vendor_brands(text: str) -> str:
    """抹掉已识别卖家品牌(连数字一起去·7-11/711)·物品名与金额共用:店号绝不当名/当价(否则记成 711 THB)。"""
    s = text or ""
    for pat, _name in _VENDOR_BRANDS:
        s = re.sub(pat, " ", s, flags=re.IGNORECASE)
    return s


def _extract_item_name(text: str) -> str:
    """一句话清出干净物品名(去 日期/金额/数量/币种/卖家/动词/连接词)· 单笔「详情」结构化(#10b)。

    启发式(零 LLM·非完美·用户可改):清不出 → 空,调用方回落原文。
    """
    s = " " + (text or "").strip() + " "
    for w in _TODAY_WORDS + _YESTERDAY_WORDS + _DAYBEFORE_WORDS:
        s = s.replace(w, " ")
    s = re.sub(r"\d+\s*(?:天前|วันก่อน|days?\s+ago)", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}", " ", s)
    s = _strip_vendor_brands(s)  # 卖家品牌(已单列字段·不进物品名)
    units = "|".join(re.escape(u) for u in _QTY_UNITS)
    s = re.sub(rf"\d+(?:\.\d+)?\s*(?:{units})", " ", s)  # 数量+单位
    s = re.sub(r"[xX×]\s*\d+", " ", s)
    s = re.sub(r"(?:@|ต่อหน่วย|单价)\s*\d+(?:\.\d+)?", " ", s)
    marks = "|".join(re.escape(m) for m in _CURRENCY_MARK)
    s = re.sub(rf"(?:{marks})", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"\d+(?:[,.]\d+)*", " ", s)  # 剩余裸数字(金额·日期/编号已先除)
    for w in _NAME_NOISE:
        s = s.replace(w, " ")
    s = re.sub(r"[\s,，。、:：/·\-]+", " ", s).strip()
    return s


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
    """商品(goods)还是服务(service)· 委托 line_classify(图/文共用同一服务词表)。"""
    return classify_expense_type(text)


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


def text_numbers(text: str) -> list[Decimal]:
    """原文里出现的所有数字(去逗号 · 确定性)→ Decimal 列表。供测试 harness 端状态核验。"""
    return [n for n in (_to_decimal(x) for x in re.findall(_NUM, text or "")) if n is not None]


def looks_like_expense(text: str) -> bool:
    """有金额线索(币种标记 or 裸数字)即视为记账意图(doc 10 §2 L1)。"""
    return parse_expense(text).has_amount()


def has_item_context(text) -> bool:
    """有物品名或卖家即 True;纯裸数字(无物品/无卖家·如「1」「65」)→ False。

    裸数字无「买了啥/在哪买」上下文,不该当可信费用直接入账(否则往账上灌 1/2/3 THB 垃圾条目)。
    """
    return bool(_extract_item_name(text)) or bool(_extract_vendor(text))


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


def qty_label(name: str, qty=None) -> str:
    """卡片明细名:数量>1 缀「×N」,否则原名(图/文单/多笔共用 · #10b)。"""
    q = _to_decimal(str(qty)) if qty not in (None, "", 0) else None
    if q is not None and q > 1:
        return f"{name} ×{format(q.normalize(), 'f')}"
    return name


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
# 问句/非陈述句标记(多语):L1 见到即不快路记账,交大脑判 speech_act(无 key 落澄清),
# 防「จ่าย 50 ใช่ไหม」「ถ้าซื้อ 100」被 L1 直记。ไหม 用 contains(误伤「ผ้าไหม」仅改走大脑·仍会记)。
_Q_WORDS = "ไหม มั้ย เหรอ หรอ ป่าว รึเปล่า หรือเปล่า ทำไม เท่าไหร่ เท่าไร เมื่อไหร่ ยังไง ที่ไหน กี่บาท กี่โมง 吗 呢 嘛".split()
_HYPO_NEG = "ถ้า สมมติ หาก ไม่ต้อง ไม่เอา ไม่ใช่ 如果 假设 假如 别记 不要记 不用记".split()


def l1_intent(text: str) -> Optional[str]:
    """记账之外的 L1 意图:support 求助 / query 查账。都不是 → None(交 L1 记账或 L2)。"""
    low = (text or "").lower()
    if any(k in low for k in _SUPPORT_KW):
        return "support"
    if any(k in low for k in _QUERY_KW):
        return "query"
    return None


def is_question(text: str) -> bool:
    """问句线索(?/吗呢嘛 + 泰语疑问词 ไหม/มั้ย/เหรอ/เท่าไหร่…)→ 含数字也不当记账。"""
    t = (text or "").strip()
    return t.endswith(("?", "?")) or any(w in t for w in _Q_WORDS)


def is_nonassertive(text: str) -> bool:
    """假设/否定记账标记(确定性·mirror 大脑 speech_act)→ L1 不快路记账
    (防「ถ้าซื้อ100」「ไม่ต้องบันทึก100」被直记成支出)。"""
    low = (text or "").lower()
    return any(m in low for m in _HYPO_NEG)


# 改错信号(P2):「上一笔改成X / 卖家改成7-11」走改错流,不被 L1 当新记一笔(「上一笔改成550」≠ 新花 550)。
_EDIT_KW = (
    "改成",
    "改为",
    "改回",
    "改到",
    "更正",
    "修改",
    "แก้ไข",
    "แก้เป็น",
    "แก้ยอด",
    "เปลี่ยนเป็น",
    # 调整金额类(组合词·不撞商品名):「ปรับยอด」≠ค่าปรับ/ปรับอากาศ;「调整/调成」≠空调/调味料/ค่าปรับ。
    "ปรับยอด",
    "เปลี่ยนยอด",
    "ลดยอด",
    "调整",
    "调成",
    "调到",
    "调为",
    "change to",
    "edit it",
    "correct it",
)
_CN_NUM = {c: i for i, c in enumerate("一二三四五六七八九十", 1)}
_ORDINAL_RE = re.compile(r"(?:第|รายการที่|item|no\.?|#)\s*([0-9０-９一二三四五六七八九十])")


# 调整金额结构(稳态·非枚举·防打地鼠):金额名词 + 「改成/เป็น/=」后接数字 → 改错。误伤守卫:
# ค่าปรับ/空调/调味料/ค่าปรับจราจร 无「金额名词 + 改成数字」结构 → 不命中。
_AMOUNT_NOUN_RE = re.compile(r"ยอดรวม|ยอดเงิน|ยอด|จำนวนรวม|จำนวนเงิน|金额|总金额|总额|金額")
_ADJUST_RE = re.compile(r"(?:เป็น|改成|改为|调成|调到|调为|=)\s*฿?\s*\d")


def is_edit_request(text: str) -> bool:
    """强改错词,或「金额名词 + 改成/เป็น/= 数字」结构 → 改错(L1 记账前分流守卫·不当新支出)。"""
    low = (text or "").lower()
    if any(k.lower() in low for k in _EDIT_KW):
        return True
    return bool(_AMOUNT_NOUN_RE.search(low) and _ADJUST_RE.search(low))


def parse_ordinal(text: str) -> Optional[int]:
    """抽序号:「第1张/第一笔/รายการที่ 2/item 3」→ N(≥1);无 → None。"""
    m = _ORDINAL_RE.search(text or "")
    if not m:
        return None
    ch = m.group(1)
    if ch in _CN_NUM:
        return _CN_NUM[ch]
    digit = ch.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    try:
        n = int(digit)
    except ValueError:
        return None
    return n if n >= 1 else None


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
    from services.expense import amount_extract

    text = (text or "").strip()
    qty = _extract_qty(text)
    unit_price = _extract_unit_price(text)
    amount = amount_extract.extract_amount(text, qty, unit_price)
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
        # note = 清出的干净物品名(供「详情」结构化 + 入账行描述);清不出回落原文。
        note=_extract_item_name(text) or text,
        raw_text=text,
        source="line_text",
        confidence=Decimal("0.90") if amount is not None else Decimal("0"),
    )


# 多项一句话:「电费50 买菜40 电费10 吃饭50」→ 多笔(名+额)·每项独立归类/合计(对标 Paypers)。
# 数字两侧 lookaround:紧贴 数字-连字号(店名/编号「7-11」、区间「02-99」)的数字段不是金额 → 不匹配
# (P1E-3:店名「ที่ 7-11」的 7 此前被当金额累加致总额 +7)。仅排连字号数字串,不误伤「100-เก่า」。
_MULTI_RE = re.compile(r"([^\d฿]+?)\s*(?<!\d-)([\d,]+(?:\.\d+)?)(?!-\d)")
_UNIT_TAIL = re.compile(r"(?i)\s*(元|块|บาท|泰铢|thb|baht|฿|kip)+\s*$")
_NAME_LEAD = re.compile(r"(?i)^[\s、,，/和跟加与及还有然后＋+]+|^(元|块|บาท|thb|baht|฿)\s*")
# 日期(数字 + 泰文月缩写)不是商品也不是金额 → 多笔拆分前剥掉(否则 15 ม.ค. 68 被当两项)。
_TH_MONTH = "ม\\.?ค|ก\\.?พ|มี\\.?ค|เม\\.?ย|พ\\.?ค|มิ\\.?ย|ก\\.?ค|ส\\.?ค|ก\\.?ย|ต\\.?ค|พ\\.?ย|ธ\\.?ค"
_MULTI_DATE_RE = re.compile(
    rf"\d{{1,2}}[/\-.]\d{{1,2}}[/\-.]\d{{2,4}}|\d{{1,2}}\s*(?:{_TH_MONTH})\.?\s*\d{{0,4}}"
)


# 句中字段声明词(「ผู้ขาย 711 / ร้านค้า 7-11」)是卖家/字段标注,不是商品项(P1E-3·多项句内联卖家)。
# 长词在前(extract_inline_vendor 按序匹配·ร้านค้า 先于 ร้าน,免「ร้านค้า X」被 ร้าน 截成「ค้า」)。
_VENDOR_DECL_WORDS = ("ผู้ขาย", "ชื่อร้าน", "ร้านค้า", "ร้าน", "卖家", "商家", "供应商", "店名")
# 价标签段(「ราคา 50000 / ส่วนลด 50」)是金额标注·不是独立商品 → 不当一项(否则被加进总额)。
_PRICE_LABELS = "ราคา ส่วนลด หัก ยอด รวม เป็นเงิน ภาษี 价 折扣 小计 合计".split()
_FIELD_WORD_NAMES = frozenset(
    {*_VENDOR_DECL_WORDS, *_PRICE_LABELS, "วันที่", "หมวดหมู่", "หมวด", "日期", "分类", "科目"}
)


def extract_inline_vendor(text: str) -> str:
    """多项句里内联卖家声明「ผู้ขาย 711 / ร้านค้า 7-11 / 卖家 X」→ 卖家名;无 → ''(P1E-3)。"""
    for kw in _VENDOR_DECL_WORDS:
        m = re.search(re.escape(kw) + r"\s*[:：]?\s*([^\s,，]+)", text or "")
        if m:
            v = m.group(1).strip(" -·:、,，/")
            if v and v not in _FIELD_WORD_NAMES:
                return v
    return ""


def parse_multi(text: str) -> Optional[list]:
    """一句话拆多项 → [{name, amount(Decimal)}];<2 项返 None(走单笔老路)。

    名去首尾货币词/连接词(和/跟/加…)。确定性正则(不靠 LLM 拆·避免误拆)。字段声明词
    (「ผู้ขาย 711」)是卖家标注非商品 → 不计入金额(P1E-3·总额不被内联卖家撑大);连字号数字串
    (店名「7-11」)由 _MULTI_RE 的 lookaround 直接排除,不进 items。拆分前先剥非金额数字(单位/
    日期/税率/型号邻接 · 与单笔路共用 strip_nonmoney)→ 型号/数量/日期不再被当独立项加进总额。
    """
    from services.expense import amount_extract

    clean = _MULTI_DATE_RE.sub(" ", amount_extract.strip_nonmoney(text or ""))
    items = []
    for m in _MULTI_RE.finditer(clean.strip()):
        name = _UNIT_TAIL.sub("", _NAME_LEAD.sub("", m.group(1).strip())).strip(" -·:、,，/")
        try:
            amt = Decimal(m.group(2).replace(",", ""))
        except (InvalidOperation, ValueError):
            continue
        if name and name not in _FIELD_WORD_NAMES and amt > 0:
            items.append({"name": name, "amount": amt})
    return items if len(items) >= 2 else None
