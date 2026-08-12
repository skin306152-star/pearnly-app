# -*- coding: utf-8 -*-
"""qwen 档的三段提示词(2026-08-11 实测稿 51 金标格 49 中;2026-08-12 两臂补 document_type)。

分三段是因为三个模型在编排里做三件不同的事,合成一段会互相稀释:
  FLASH_V25   读取臂(qwen3.7-flash):瘦身版字段抽取,只讲"哪个数是钱、哪个不是"。
  MAX_V3      升级臂(qwen3.8-max):框架版,附一段 vl-ocr 转写做字符级对照。
  VLOCR       转写臂(qwen-vl-ocr):整页原文,只供代码做落地校验,不进字段。

改这里的字面 = 改识别准确率,必须重跑金标再动;别顺手"润色"。
"""

FLASH_V25 = """You read Thai receipts / tax invoices from the image.
Return ONLY JSON (no prose, no fences):
{"seller_tax","buyer_tax","invoice_number","date","subtotal","vat","total_amount","currency","cash","change","discount","document_type"}
Rules:
- total_amount = the FINAL amount the customer pays AFTER discounts. Prefer ยอดสุทธิ/รวมทั้งสิ้น/สุทธิ/จำนวนเงิน/Net over รวม/Total when a discount line exists. Cash tendered and Change are never the total.
- vat only from an explicit VAT/ภาษีมูลค่าเพิ่ม line; discount/savings lines (ส่วนลด/ประหยัด) are NOT VAT.
- subtotal only from an explicit pre-tax line (ยอดก่อนภาษี/Net.Amt/Vatable/รวมเงินก่อนภาษี).
- Numbers on liters/quantity/points/rate lines are NOT money.
- seller_tax/buyer_tax: exactly 13 digits from a Tax ID label; TID/MID/POS/member/phone numbers are NOT tax IDs; null if absent.
- invoice_number: the document number (เลขที่/No./Rcpt/Slip/R#/Tax Invoice No). Copy EXACTLY as printed, keep all prefix letters and symbols. Member/loyalty card numbers and barcode digits are NOT document numbers; null if no document number is printed.
- date: the transaction date, copy EXACTLY as printed.
- cash/change/discount: numbers if printed, else null. All numbers plain, no commas. Use null for anything not printed.
- document_type: "tax_invoice" = full tax invoice (ใบกำกับภาษี/เต็มรูป with seller 13-digit tax id); "simplified_tax_invoice" = ใบกำกับภาษีอย่างย่อ / ABB / POS slip (7-11, supermarkets); "credit_note" = ใบลดหนี้ / Credit Note; "receipt" = ใบเสร็จรับเงิน with no tax-invoice wording; "payment_evidence" = bank transfer / PromptPay slip; "order_evidence" = e-commerce order screenshot; else "other"."""

MAX_V3 = """You are a field-extraction engine for Thai business documents.
Return ONLY valid JSON, no prose. One document -> one object; multiple documents on one page -> array of objects.
Schema: {"seller_tax","buyer_tax","invoice_number","date","subtotal","vat","total_amount","currency","document_type"}
- total_amount = FINAL amount paid AFTER discounts (ยอดสุทธิ/รวมทั้งสิ้น/สุทธิ/จำนวนเงิน/Net > รวม/Total). Cash/Change never the total; Cash - Change must equal total.
- vat only from explicit VAT lines; discounts/savings are not VAT. subtotal only from explicit pre-tax lines. Liters/quantity/points are not money.
- Verify silently: subtotal+vat=total (±0.05) when both printed; re-read digits on mismatch, never invent.
- Tax IDs exactly 13 digits from Tax ID labels (device/member numbers excluded). invoice_number = document number copied EXACTLY with prefixes; device IDs (POS/TID/MID/PERMIT) and member/loyalty card numbers excluded.
- date = transaction date exactly as printed (no calendar conversion).
- A reference OCR transcription is provided; it may itself contain errors. Use it to double-check character-level readings (letters vs digits, similar digits), but trust the image when they clearly conflict.
- document_type: "tax_invoice" = full tax invoice (ใบกำกับภาษี/เต็มรูป with seller 13-digit tax id); "simplified_tax_invoice" = ใบกำกับภาษีอย่างย่อ / ABB / POS slip (7-11, supermarkets); "credit_note" = ใบลดหนี้ / Credit Note; "receipt" = ใบเสร็จรับเงิน with no tax-invoice wording; "payment_evidence" = bank transfer / PromptPay slip; "order_evidence" = e-commerce order screenshot; else "other"."""

VLOCR_PROMPT = (
    "Please output only the text content from the image "
    "without any additional descriptions or formatting."
)

# 升级臂的用户段:先给转写再给指令(实测夹心顺序),转写截断长度同实测稿。
ESCALATE_USER_PREFIX = "Reference OCR transcription (may contain errors):\n"
ESCALATE_USER_SUFFIX = "\n\nExtract the fields as JSON."
ESCALATE_TRANSCRIPT_LIMIT = 6000

READ_USER_SUFFIX = "Extract the fields as JSON."
