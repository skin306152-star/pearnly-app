# -*- coding: utf-8 -*-
"""OCR document_type 原始码 → 4 语人话(数据卡/详情避免显 simplified_tax_invoice 等英文代号)。

枚举对标 docs/smart-intake/16 §2(Paypers 逆向 · ~26 类单据 + 银行/电商「证据」)。术语对齐网页
pur-dt-*。空 → 空;未知码 → 原值兜底(不编造)。OCR 现仅主动产出收付类 5 种 + 两类截图证据
(payment_evidence/order_evidence · 见 layer2_prompts);其余码供 UI 下拉 / 手改 / 后续分流显示。
"""

from __future__ import annotations

# (code, zh, th, en, ja) · th 取自 docs/16 §2 原文。
_DOC_TYPES = [
    ("tax_invoice", "税务发票", "ใบกำกับภาษี", "Tax invoice", "税額票"),
    (
        "simplified_tax_invoice",
        "简式税票",
        "ใบกำกับภาษีอย่างย่อ",
        "Simplified tax invoice",
        "簡易税額票",
    ),
    ("receipt", "收据", "ใบเสร็จรับเงิน", "Receipt", "領収書"),
    ("cash_bill", "现金账单", "บิลเงินสด", "Cash bill", "現金請求書"),
    ("invoice", "发票 / 账单", "ใบแจ้งหนี้", "Invoice", "請求書"),
    ("paid_invoice", "已付账单", "ใบแจ้งหนี้ที่ชำระแล้ว", "Paid invoice", "支払済請求書"),
    ("billing_note", "请款单", "ใบวางบิล", "Billing note", "ビリングノート"),
    ("receipt_voucher", "收款凭证", "ใบสำคัญรับ", "Receipt voucher", "入金伝票"),
    ("payment_voucher", "付款凭证", "ใบสำคัญจ่าย", "Payment voucher", "出金伝票"),
    (
        "substitute_receipt",
        "替代收据",
        "ใบรับรองแทนใบเสร็จ",
        "Substitute receipt",
        "領収書代替証明",
    ),
    ("credit_note", "贷项通知单", "ใบลดหนี้", "Credit note", "クレジットノート"),
    ("debit_note", "借项通知单", "ใบเพิ่มหนี้", "Debit note", "デビットノート"),
    ("quotation", "报价单", "ใบเสนอราคา", "Quotation", "見積書"),
    ("purchase_request", "请购单", "ใบขอซื้อ", "Purchase request", "購買依頼書"),
    ("purchase_order", "采购订单", "ใบสั่งซื้อ", "Purchase order", "発注書"),
    ("order_confirmation", "订单确认", "ใบยืนยันคำสั่งซื้อ", "Order confirmation", "注文確認書"),
    ("work_order", "工单", "ใบสั่งงาน", "Work order", "作業指示書"),
    ("delivery_note", "送货单", "ใบส่งของ", "Delivery note", "納品書"),
    ("goods_receipt", "收货单", "ใบรับสินค้า", "Goods receipt", "入荷伝票"),
    ("transfer_note", "调拨单", "ใบโอนสินค้า", "Transfer note", "移動伝票"),
    ("bank_statement", "银行对账单", "รายการเดินบัญชีธนาคาร", "Bank statement", "銀行取引明細"),
    (
        "credit_card_statement",
        "信用卡对账单",
        "ใบแจ้งยอดบัตรเครดิต",
        "Credit card statement",
        "クレジットカード明細",
    ),
    ("payslip", "工资单", "สลิปเงินเดือน", "Payslip", "給与明細"),
    ("payment_evidence", "付款证据", "หลักฐานการชำระเงิน", "Payment evidence", "支払証憑"),
    ("order_evidence", "订单证据", "หลักฐานคำสั่งซื้อ", "Order evidence", "注文証憑"),
    ("other", "其他", "อื่น ๆ", "Other", "その他"),
]

_DOC_TYPE_LABELS = {c: {"zh": zh, "th": th, "en": en, "ja": ja} for c, zh, th, en, ja in _DOC_TYPES}


def doc_type_label(code: str, lang: str) -> str:
    """document_type 原始码 → 当前语言人话。空 → 空;未知码 → 原值兜底。"""
    code = (code or "").strip()
    if not code:
        return ""
    m = _DOC_TYPE_LABELS.get(code)
    if not m:
        return code
    return m.get((lang or "zh").lower()) or m["en"]
