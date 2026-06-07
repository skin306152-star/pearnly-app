# -*- coding: utf-8 -*-
"""销项 PDF 标签字典 + 文档语言解析(从 pdf.py 拆出 · SRP · 控单文件 <500)。

标签存 (泰, 英, 中) 三元组;_label_fn(lang) 按 doc_language 出:
th=仅泰 / th_en=泰+英(默认) / th_zh=泰+中。泰文恒在(泰国合规硬要求),仅切次语。
pdf.py 与 pdf_thermal.py 共用(thermal 经 pdf_mod.* 取这些 re-export 名)。
"""

from __future__ import annotations


def _label_fn(lang: str, sep: str = " / "):
    def L(th: str, en: str = "", zh: str = "") -> str:
        if lang == "th":
            return th
        sec = zh if lang == "th_zh" else en
        return f"{th}{sep}{sec}" if sec else th

    return L


def _doc_label(doc_type: str, L) -> str:
    return L(*_DOC_LABEL.get(doc_type, (doc_type or "", "", "")))


_DOC_LABEL = {
    "tax_invoice": ("ใบกำกับภาษี", "Tax Invoice", "税务发票"),
    "tax_invoice_simple": ("ใบกำกับภาษีอย่างย่อ", "Simplified Tax Invoice", "简易税务发票"),
    "tax_invoice_receipt": ("ใบกำกับภาษี/ใบเสร็จรับเงิน", "Tax Invoice / Receipt", "税务发票/收据"),
    "receipt": ("ใบเสร็จรับเงิน", "Receipt", "收据"),
    "credit_note": ("ใบลดหนี้", "Credit Note", "贷项通知单"),
    "debit_note": ("ใบเพิ่มหนี้", "Debit Note", "借项通知单"),
    "quotation": ("ใบเสนอราคา", "Quotation", "报价单"),
}

# 买方税号标签随买方类型变(docs/15 §4):公司=税号 / 个人=身份证 / 外国=护照。
_BUYER_TIN_LABEL = {
    "company": ("เลขประจำตัวผู้เสียภาษี", "Tax ID", "税号"),
    "individual": ("เลขบัตรประชาชน", "National ID", "身份证号"),
    "foreigner": ("เลขหนังสือเดินทาง", "Passport No.", "护照号"),
}

_PAYMENT_METHOD_LABEL = {
    "cash": ("เงินสด", "Cash", "现金"),
    "transfer": ("โอนเงิน", "Transfer", "转账"),
    "cheque": ("เช็ค", "Cheque", "支票"),
    "card": ("บัตร", "Card", "刷卡"),
    "promptpay": ("พร้อมเพย์", "PromptPay", "PromptPay"),
}

# 正本给买方 / 副本自留(泰国 VAT 注册方至少出 2 联 · docs/16 §E2)。
_COPY_LABEL = {
    "original": ("ต้นฉบับ", "Original", "正本"),
    "copy": ("สำเนา", "Copy", "副本"),
}
