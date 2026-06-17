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


def classify_expense_type(text: str) -> str:
    """商品(goods)还是服务(service)· 命中服务关键词→service,否则默认 goods(图/文共用·防重复词表)。"""
    low = (text or "").lower()
    return "service" if any(w.lower() in low for w in _SERVICE_WORDS) else "goods"


def detect_payment_method(text: str) -> str:
    """一句话里真识别到的付款方式(规范码 promptpay/transfer/card/cash)。无信号 → ''(不猜)。"""
    low = (text or "").lower()
    for code, words in _PAY_PATTERNS:
        if any(w.lower() in low for w in words):
            return code
    return ""


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


def intro_intent(text: str) -> str:
    """引导类意图(零成本):capability 能力说明 / upload 如何上传 / start 如何开始。无 → ''。

    用在记账解析前的分流,避免「怎么开始」被当成记一笔(这些短语极少出现在正常记一笔里)。
    """
    low = (text or "").strip().lower()
    if not low:
        return ""
    for kind, words in _INTRO_PATTERNS:
        if any(w.lower() in low for w in words):
            return kind
    return ""
