# -*- coding: utf-8 -*-
"""
v118.32.x · Pearnly · VAT 差异 AI 分析(懒加载 · 用户点开行才调 Gemini)
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

_PROMPT = """You are a Thai accounting expert helping a senior accountant reconcile output VAT.
Given ONE row of discrepancy between an issued tax invoice and a sales VAT report, give:

1. A SHORT one-sentence root-cause hypothesis (in Chinese · 中文)
2. ONE recommended action (in Chinese · 中文) · choose between:
   - "更正报告" (ask client to fix the report)
   - "接受差异" (precision diff · accept as-is)
   - "重开发票" (re-issue the invoice)
   - "标记客户问题" (flag for follow-up · root cause needs investigation)
3. A 1-sentence draft email to send the client (in Thai · ภาษาไทย · polite formal tone)

Return ONLY JSON, no markdown:
{
  "cause": "...",
  "action": "更正报告" | "接受差异" | "重开发票" | "标记客户问题",
  "email_th": "..."
}

Row data:
"""


def analyze_diff(row: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    """对一行 reconciliation_row 跑 AI 分析 · 返回 {cause, action, email_th}"""
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return {"ok": False, "error": "Gemini API key 未配置"}

    # 构建 row 的简化描述给 Gemini
    diff_fields = row.get("diff_fields") or {}
    if isinstance(diff_fields, str):
        try:
            diff_fields = json.loads(diff_fields)
        except Exception:
            diff_fields = {}

    summary = {
        "status": row.get("status"),
        "diff_categories": row.get("diff_categories"),
        "pair_confidence": row.get("pair_confidence"),
        "invoice": {
            "no": row.get("invoice_no"),
            "date": str(row.get("invoice_date") or ""),
            "buyer": row.get("buyer_name") or row.get("seller_name"),
            "tax_id": row.get("buyer_tax_id"),
            "amount": row.get("total_amount"),
        },
        "report": {
            "no": row.get("report_invoice_no"),
            "date": row.get("report_date"),
            "buyer": row.get("report_buyer_name"),
            "tax_id": row.get("report_buyer_tax_id"),
            "amount": row.get("report_amount"),
            "vat": row.get("report_vat_amount"),
        },
        "field_diff": diff_fields,
    }

    from services.ai_gateway import transport

    prompt = _PROMPT + json.dumps(summary, ensure_ascii=False, indent=2)
    out = transport.text_to_json(
        prompt,
        tier="flash",
        api_key=key,
        temperature=0.3,
        response_mime=True,
        max_tokens=4096,
        timeout_s=120,
        max_retries=0,
        task="vat.diff_analyze",
    )
    if not out.ok:
        logger.error(f"[ai_analyze] 失败: {out.error_kind}")
        return {"ok": False, "error": f"AI 分析失败: {out.error_kind}"}
    data = out.data
    return {
        "ok": True,
        "cause": data.get("cause", ""),
        "action": data.get("action", ""),
        "email_th": data.get("email_th", ""),
    }
