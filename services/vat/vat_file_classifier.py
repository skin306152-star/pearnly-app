# -*- coding: utf-8 -*-
"""
v118.32.x · Pearnly · 屏 B 文件智能分类
混合文件 → 判断每个是「税务发票」还是「VAT 报告」
策略:
  1. 文件名/路径快速规则(零成本)
  2. 不确定 → Gemini 1 次轻量调用(只看首页)
"""

import os
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 文件名关键词
_INVOICE_HINTS = [
    r"\binvoice\b",
    r"\binv\b",
    r"ใบกำกับ",
    r"tax_?inv",
    r"\bIV\d",
    r"\bINV\d",
    r"receipt",
]
_REPORT_HINTS = [
    r"\breport\b",
    r"รายงาน",
    r"\bvat\b",
    r"sales_tax",
    r"sale_vat",
    r"ภาษีขาย",
    r"pp30",
    r"ภ\.พ\.30",
]


def _filename_guess(filename: str) -> Optional[str]:
    """根据文件名猜类型 · 返回 'invoice' / 'vat_report' / None"""
    fn = (filename or "").lower()
    # 下划线是正则单词字符 · 会让 \binvoice\b 在 "invoice_2026" 处失效 ·
    # 额外比一份「下划线转空格」的版本(同时保留原串 · 兼容 sales_tax 这类含下划线的 hint)
    fn_spaced = fn.replace("_", " ")

    def _hit(hints):
        return any(
            re.search(p, fn, re.IGNORECASE) or re.search(p, fn_spaced, re.IGNORECASE) for p in hints
        )

    if _hit(_INVOICE_HINTS):
        return "invoice"
    if _hit(_REPORT_HINTS):
        return "vat_report"
    return None


_GEMINI_CLASSIFY_PROMPT = """Look at this Thai accounting document. Classify it as ONE of:

- "invoice": A single tax invoice (ใบกำกับภาษี). Usually 1 page. Shows one transaction:
   seller header, single buyer info, list of items with prices, total + 7% VAT.

- "vat_report": A sales VAT report (รายงานภาษีขาย / sale VAT report). A multi-row table
   listing MANY invoices in one document. Header says "รายงานภาษีขาย" / monthly summary.

- "unknown": If neither.

⚠ STRICT RULES:
1. tax_id MUST be exactly 13 digits as printed. Look at the document header area carefully.
   - If unclear / partially obscured: output the digits you can read with high confidence; pad missing with "" — do NOT guess.
   - The seller/issuer tax ID is usually under the company name at the TOP of the document.
2. name: copy EXACTLY as printed (Thai or English). Preserve prefixes like "บริษัท ... จำกัด".
3. year/month: read the document date. Convert Buddhist Era (BE) to Gregorian: BE - 543 = AD. 03/2569 → year=2026, month=3.

Also extract:
- "tax_id": SELLER (for invoice) / ISSUER (for report) — 13-digit Thai tax ID, digits ONLY.
            Empty string "" if not visible or unreadable.
- "name":   Seller/issuer company name (Thai or English), exactly as printed.
- "year":   Gregorian year (4 digits).
- "month":  Month 1-12.

Return ONLY:
{"type": "invoice"|"vat_report"|"unknown", "confidence": 0.0-1.0, "tax_id": "...", "name": "...", "year": 2026, "month": 3}
"""


def _excel_quick_meta(file_bytes: bytes):
    """v118.32.4.4 · Excel 头部轻量扫:税号(13 位数字) + 期间(MM/YYYY) + 卖方名
    不走 Gemini · 仅看前 30 行 · 失败返回全空"""
    try:
        import openpyxl
        import io

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
        ws = wb.active
        tax_id, year, month, name = "", None, None, ""
        company_kw = ("บริษัท", "ห้างหุ้นส่วน", "co.", "ltd.", "company")
        for i, row in enumerate(ws.iter_rows(min_row=1, max_row=30, values_only=True), 1):
            cells = [str(c) for c in row if c is not None]
            if not cells:
                continue
            text = " ".join(cells)
            cleaned = re.sub(r"[\s\-]", "", text)
            # 1. 13 位连续数字 = 税号(优先第一个出现的 · 通常是页眉的卖方税号)
            if not tax_id:
                m = re.search(r"(\d{13})(?!\d)", cleaned)
                if m:
                    tax_id = m.group(1)
            # 2. 期间 MM/YYYY 或 MM/2569(佛历)
            if not (year and month):
                m = re.search(r"(?<!\d)(\d{1,2})\s*/\s*(\d{4})(?!\d)", text)
                if m:
                    mm, yy = int(m.group(1)), int(m.group(2))
                    if 1 <= mm <= 12 and 2020 <= yy <= 2030:
                        month, year = mm, yy
                    elif 1 <= mm <= 12 and 2500 <= yy <= 2600:
                        month, year = mm, yy - 543
            # 3. 卖方名:含公司关键词的最长一段(第一行的标题不算)
            if not name and i >= 2:
                low = text.lower()
                if any(k in low for k in company_kw):
                    name = text.strip()[:120]
            if tax_id and year and month and name:
                break
        return tax_id, year, month, name
    except Exception as e:
        logger.warning(f"[excel_meta] 提取失败: {type(e).__name__}: {e}")
        return "", None, None, ""


def classify_with_gemini(
    file_bytes: bytes, mime_type: str, api_key: Optional[str] = None
) -> Dict[str, Any]:
    """用 Gemini 看首页判断 · 返回 {type, confidence, tax_id, name, year, month}"""
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return {"ok": False, "error": "Gemini key 未配置", "type": "unknown"}

    from services.ai_gateway import transport

    out = transport.multimodal_to_json(
        _GEMINI_CLASSIFY_PROMPT,
        [(file_bytes, mime_type)],
        tier="flash",
        api_key=key,
        temperature=0.0,
        response_mime=True,
        max_tokens=8192,
        timeout_s=25,
        max_retries=0,
        task="vat.file_classify",
    )
    if not out.ok:
        logger.warning(f"[classify] failed: {out.error_kind}")
        return {"ok": False, "error": f"AI 分类失败: {out.error_kind}", "type": "unknown"}
    data = out.data
    return {
        "ok": True,
        "type": data.get("type", "unknown"),
        "confidence": float(data.get("confidence") or 0.5),
        "tax_id": re.sub(r"[^0-9]", "", str(data.get("tax_id") or ""))[:13],
        "name": str(data.get("name") or "").strip(),
        "year": int(data.get("year") or 0) or None,
        "month": int(data.get("month") or 0) or None,
    }


def classify_file(
    file_bytes: bytes,
    filename: str,
    api_key: Optional[str] = None,
    always_use_gemini: bool = False,
    fast_mode_invoice: bool = True,
) -> Dict[str, Any]:
    """
    分类入口
    优先用文件名规则(零成本) · 不确定 → Gemini
    always_use_gemini=True 时跳过规则直接 Gemini · 用于 UUID 命名等无信息文件名

    v118.32.5.3 · fast_mode_invoice=True（默认）:
      文件名提示 invoice 时 · 直接返回 type=invoice · 跳过 Gemini 调用
      理由:
        - 单一报告场景下(屏 B 最常见 · 10 张发票+1 份 VAT) · 发票的 tax_id 不会用
          ("v118.32.4.9.1 · 单一报告=真理源" 逻辑强制把发票归到唯一报告)
        - 跳过 N 次 Gemini classify 调用 · 10 张发票 ≈ 节省 25-30 秒
      代价:
        - 多 VAT 报告场景 · 发票无 tax_id 无法自动匹配到对应报告组
        - 调用方需 fast_mode_invoice=False 重试 · 见 recon_routes._batch_classify
    """
    ext = (filename or "").lower().rsplit(".", 1)[-1]

    # MIME 类型推断
    mime_map = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
    }
    mime = mime_map.get(ext)

    # Excel 一定是 VAT 报告(发票不会用 Excel 来开)
    # v118.32.4.4 · 轻量扫前 30 行抽税号/期间 · 避免 Excel 卡"无法分组"
    if ext in ("xlsx", "xls"):
        tax_id, year, month, name = _excel_quick_meta(file_bytes)
        return {
            "ok": True,
            "type": "vat_report",
            "confidence": 0.9,
            "tax_id": tax_id,
            "name": name,
            "year": year,
            "month": month,
            "method": "ext_excel" + ("+meta" if tax_id else ""),
        }

    # 不支持的格式
    if not mime:
        return {"ok": False, "type": "unknown", "error": f"不支持的格式 .{ext}"}

    # 文件名快速规则
    if not always_use_gemini:
        guess = _filename_guess(filename)
        if guess == "invoice":
            # v118.32.5.3 · 关键优化：文件名清楚是发票 + 默认快速模式 → 跳 Gemini
            # 发票 tax_id 后续 OCR 阶段会重新抽 · 不需要 classify 阶段抽
            if fast_mode_invoice:
                return {
                    "ok": True,
                    "type": "invoice",
                    "confidence": 0.95,
                    "tax_id": "",
                    "name": "",
                    "year": None,
                    "month": None,
                    "method": "filename_only",
                }
            # 兼容模式:文件名提示 invoice 还是跑 Gemini 提取 tax_id(多 VAT 报告场景)
            r = classify_with_gemini(file_bytes, mime, api_key=api_key)
            if r.get("ok"):
                r["type"] = "invoice"
                r["method"] = "filename+gemini"
            return r
        # v118.32.4.9.2 · 文件名提示 vat_report 时也强信号维持
        # 避免合成 / 单页 / 表格不清晰的报告被 Gemini 误判成发票
        # VAT 报告必须跑 Gemini · 需要 tax_id/year/month 用于分组
        if guess == "vat_report":
            r = classify_with_gemini(file_bytes, mime, api_key=api_key)
            if r.get("ok"):
                r["type"] = "vat_report"
                r["method"] = "filename+gemini"
            return r

    # Gemini 完整分类(包括类型推断)
    r = classify_with_gemini(file_bytes, mime, api_key=api_key)
    if r.get("ok"):
        r["method"] = "gemini"
    return r
