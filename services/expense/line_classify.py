# -*- coding: utf-8 -*-
"""LINE 一句话记账的轻量文本分类(费用类型 + 付款方式)· 确定性关键词,无 IO,图/文共用。

从 line_quick_entry 抽出(保其 <500)。只做与科目树无关的关键词归类:
  classify_expense_type  服务关键词命中 → service,否则 goods
  detect_payment_method  真识别到的付款方式码(无信号 → '',不猜)
"""

from __future__ import annotations

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

# 付款方式关键词(真识别到才填·对齐卡片付款方式规范码)· promptpay 比 transfer 具体先判。
_PAY_PATTERNS = (
    ("promptpay", ("พร้อมเพย์", "promptpay", "prompt pay")),
    ("transfer", ("โอนเงิน", "โอน", "transfer", "转账", "轉賬", "汇款", "匯款")),
    ("card", ("บัตรเครดิต", "รูดบัตร", "บัตร", "credit card", "debit card", "刷卡", "信用卡")),
    ("cash", ("เงินสด", "จ่ายสด", "cash", "现金", "付现", "现付")),
)


def _first_match(text: str, patterns) -> str:
    """规范化文本 → 命中的 (key, 关键词组) 里第一个 key;无命中 → ''(付款方式/引导意图共用)。"""
    low = (text or "").strip().lower()
    if not low:
        return ""
    for key, words in patterns:
        if any(w.lower() in low for w in words):
            return key
    return ""


def classify_expense_type(text: str) -> str:
    """商品(goods)还是服务(service)· 命中服务关键词→service,否则默认 goods(图/文共用·防重复词表)。"""
    low = (text or "").lower()
    return "service" if any(w.lower() in low for w in _SERVICE_WORDS) else "goods"


def detect_payment_method(text: str) -> str:
    """一句话里真识别到的付款方式(规范码 promptpay/transfer/card/cash)。无信号 → ''(不猜)。"""
    return _first_match(text, _PAY_PATTERNS)


# OCR 票面付款方式归一(只作用于 OCR 抽出的 payment_method 字段·比文本检测更宽:含 qr/card 裸词)。
# 单独成表,避免把裸 qr/card 塞进 detect_payment_method 误判正常记账文本。
_PAY_NORMALIZE = (
    (
        "promptpay",
        ("พร้อมเพย์", "promptpay", "prompt pay", "qrpayment", "qr payment", "qr code", "qr"),
    ),
    ("transfer", ("โอนเงิน", "โอน", "transfer", "汇款", "转账")),
    ("card", ("บัตรเครดิต", "บัตร", "credit", "debit", "card", "刷卡", "信用卡")),
    ("cash", ("เงินสด", "cash", "现金", "付现")),
)


def normalize_payment_method(raw: str) -> str:
    """OCR 票面付款文本(如 "QRPayment(API)" / "เงินสด" / "card")→ 卡片规范码;认不出 → ''。"""
    return _first_match(raw, _PAY_NORMALIZE)


# 引导类意图关键词(零成本·泰语优先):能力说明 / 如何上传 / 如何开始。
_INTRO_PATTERNS = (
    (
        "capability",
        (
            "ทำอะไรได้",
            "ทำอะไรให้",
            "สามารถทำอะไร",
            "ช่วยอะไร",
            "ช่วยบันทึก",
            "ฟังก์ชัน",
            "เมนู",
            "ใช้งานยังไง",
            "你能做什么",
            "能做什么",
            "能做啥",
            "能帮我做什么",
            "有什么功能",
            "帮我记",
            "帮助",
            "菜单",
            "怎么用",
            "what can you",
            "can you do",
            "help me record",
            "help",
            "menu",
            "何ができ",
            "ヘルプ",
            "メニュー",
            "使い方",
        ),
    ),
    (
        "upload",
        (
            "อัปโหลด",
            "ส่งรูปยังไง",
            "ส่งใบเสร็จยังไง",
            "แนบไฟล์",
            "上传",
            "怎么拍",
            "怎么发票据",
            "拍照",
            "upload",
            "attach file",
            "send photo",
            "アップロード",
            "送り方",
        ),
    ),
    (
        "start",
        (
            "เริ่มยังไง",
            "เริ่มต้น",
            "เริ่มใช้",
            "怎么开始",
            "如何开始",
            "从哪开始",
            "how to start",
            "get started",
            "始め方",
            "はじめ方",
        ),
    ),
)


# 问日期(在范围内:日期与记账相关 → 答今天日期再引导,不当离题)。
_DATE_PATTERNS = (
    (
        "date",
        (
            "วันนี้วันที่เท่าไหร่",
            "วันที่เท่าไหร่",
            "วันนี้วันที่อะไร",
            "วันนี้วันอะไร",
            "วันที่เท่าไร",
            "今天几号",
            "今天是几号",
            "今天日期",
            "现在几号",
            "今天星期几",
            "what date",
            "today's date",
            "todays date",
            "what's the date",
            "date today",
            "今日は何日",
            "今日の日付",
            "何日ですか",
        ),
    ),
)


def is_date_query(text: str) -> bool:
    """问「今天几号/วันนี้วันที่เท่าไหร่」→ True。日期与记账相关,答日期再引导,不当离题。"""
    return _first_match(text, _DATE_PATTERNS) == "date"


# 「这条记录识别错了/不对」反馈(引用某条记录时用)→ 进澄清改哪里,不当 OCR 失败让重拍。
# 词面宽(错了/ผิด/wrong),由调用方限「引用了记录」才触发,故不会误伤泛泛聊天。
_FEEDBACK_PATTERNS = (
    (
        "wrong",
        (
            "识别错",
            "认错",
            "读错",
            "记错",
            "搞错",
            "弄错",
            "不对",
            "错了",
            "有误",
            "อ่านผิด",
            "อ่านไม่ถูก",
            "ไม่ถูก",
            "ไม่ตรง",
            "ผิด",
            "recognized wrong",
            "recognised wrong",
            "read it wrong",
            "incorrect",
            "wrong",
        ),
    ),
)


def is_correction_feedback(text: str) -> bool:
    """「这张你识别错了/不对/อ่านผิด/wrong」→ True(指出记录有误·未必给出具体改成什么)。"""
    return _first_match(text, _FEEDBACK_PATTERNS) == "wrong"


# 改错指向的字段(P1E-2):用户在改错澄清里点名要改哪项 → 据此问新值 / 引导详情页。
# items / payment 顺位靠前(其专有词「明细/รายการย่อย/付款方式/วิธีชำระ」更具体,先于泛词命中)。
_FIELD_PATTERNS = (
    (
        "items",
        (
            "明细",
            "逐项",
            "项目",
            "条目",
            "รายการย่อย",
            "รายการสินค้า",
            "line item",
            "line items",
            "items",
            "明細",
        ),
    ),
    (
        "payment",
        (
            "付款方式",
            "支付方式",
            "付款",
            "支付",
            "วิธีชำระ",
            "การชำระ",
            "ชำระเงิน",
            "payment",
            "支払",
        ),
    ),
    (
        "amount",
        (
            "金额",
            "钱",
            "价钱",
            "价格",
            "总额",
            "ยอดเงิน",
            "ยอด",
            "จำนวนเงิน",
            "amount",
            "total",
            "金額",
            "値段",
        ),
    ),
    ("date", ("日期", "时间", "วันที่", "date", "日付")),
    (
        "seller",
        (
            "卖家",
            "商家",
            "店名",
            "店家",
            "供应商",
            "ร้านค้า",
            "ร้าน",
            "ผู้ขาย",
            "seller",
            "vendor",
            "shop",
            "販売",
            "店",
        ),
    ),
    (
        "category",
        ("分类", "科目", "类别", "类型", "หมวดหมู่", "หมวด", "ประเภท", "category", "分類"),
    ),
)


def detect_correction_field(text: str) -> str:
    """改错澄清里点名的字段 → amount/date/seller/category/payment/items;没点名 → ''。"""
    return _first_match(text, _FIELD_PATTERNS)


def detect_text_lang(text: str) -> str:
    """按字符脚本判输入语言(zh/th/en/ja)→ 回复跟随用户输入,不被账号主语言带偏。无字母 → ''。"""
    s = text or ""
    for ch in s:
        o = ord(ch)
        if 0x0E00 <= o <= 0x0E7F:
            return "th"
        if 0x3040 <= o <= 0x30FF:  # 平/片假名 → 日语(先于 CJK 汉字判)
            return "ja"
    for ch in s:
        if 0x4E00 <= ord(ch) <= 0x9FFF:
            return "zh"
    for ch in s:
        if ch.isascii() and ch.isalpha():
            return "en"
    return ""


def intro_intent(text: str) -> str:
    """引导类意图(零成本):capability 能力说明 / upload 如何上传 / start 如何开始。无 → ''。

    用在记账解析前的分流,避免「怎么开始」被当成记一笔(这些短语极少出现在正常记一笔里)。
    """
    return _first_match(text, _INTRO_PATTERNS)
