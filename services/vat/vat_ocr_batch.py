# -*- coding: utf-8 -*-
"""多发票批量 OCR(一次 Gemini 调用抽多张 · 减少 5x API)· vat_excel_export 拆分。"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from services.recon.vat_recon_core import _to_float
from services.vat.vat_ocr_extract import extract_invoice_fields, _VEX_OCR_PER_FILE_TIMEOUT

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
# v118.32.5 · 性能优化 B · 多发票批量 OCR（800+ 张场景，减少 5x API 调用）
# ════════════════════════════════════════════════════════════════════════
_INVOICE_BATCH_PROMPT = """You are reading {n} Thai tax invoices (ใบกำกับภาษี) attached in order: invoice_1, invoice_2, ..., invoice_{n}.

For EACH invoice, extract the SAME 8 fields. Do NOT interpret · do NOT match · do NOT clean.

Output JSON ONLY in this exact shape:
{{
  "invoices": [
    {{
      "index": 1,
      "buyer_tax_id": "...",
      "buyer_name":   "...",
      "buyer_branch": "...",
      "invoice_no":   "...",
      "invoice_date": "...",
      "period":       "...",
      "amount_pre_vat": 0.00,
      "vat_amount":     0.00,
      "total_amount":   0.00
    }},
    ... (one object per attached invoice, in same order)
  ]
}}

Field rules (identical to single-invoice mode):
- buyer_tax_id: 13-digit Thai tax ID of the BUYER · digits only · "" if missing
- buyer_name:   Buyer name EXACTLY as printed (keep prefixes like บริษัท ... จำกัด)
- buyer_branch: "สำนักงานใหญ่" or 5-digit code · "" if cash customer
- invoice_no:   Invoice number EXACTLY as printed · keep prefixes (INV/IV/TAX) · do NOT strip leading zeros
- invoice_date: Date EXACTLY as printed · format DD/MM/YYYY · keep BE year as printed
- period:       MM/YYYY (Gregorian only · BE-543 if Buddhist Era)
- amount_pre_vat / vat_amount / total_amount: number · 2 decimals · no commas

STRICT RULES:
1. Output exactly {n} objects in the same order as the attached files
2. If a field is partially visible or unreadable · output "" · do NOT guess
3. Cash customer → buyer_tax_id="" buyer_branch=""
4. Numbers: digits and dot only · no commas · no currency
"""


def _mime_for(filename: str) -> Optional[str]:
    ext = (filename or "").lower().rsplit(".", 1)[-1]
    return {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }.get(ext)


def extract_invoice_fields_batch(
    invoice_files: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    timeout: int = 90,
) -> List[Dict[str, Any]]:
    """一次 Gemini 调用抽取多张发票字段
    invoice_files: [{filename, bytes}]，建议 ≤ 5 张/批
    返回顺序与输入一致；任何一张失败/缺失 → 该 index 标记 ok=False
    """
    n = len(invoice_files)
    if n == 0:
        return []
    if n == 1:
        # 单张直接走原 single 流程，少一层包装
        f = invoice_files[0]
        return [extract_invoice_fields(f["bytes"], f["filename"], api_key=api_key)]

    # 校验 mime + 组装图片((bytes, mime) 列表 · 由 provider 决定如何编码)
    images = []
    for f in invoice_files:
        mime = _mime_for(f.get("filename") or "")
        if not mime:
            return [
                {
                    "ok": False,
                    "filename": x.get("filename"),
                    "error": "batch contains unsupported format",
                }
                for x in invoice_files
            ]
        images.append((f["bytes"], mime))

    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return [
            {"ok": False, "filename": f.get("filename"), "error": "Gemini key 未配置"}
            for f in invoice_files
        ]

    from services.ai_gateway import transport
    from services.ocr.gemini_models import flash, tier_for_model, try_with_fallback

    def _call(model_name: str):
        return transport.multimodal_to_json(
            _INVOICE_BATCH_PROMPT.format(n=n),
            images,
            tier=tier_for_model(model_name),
            api_key=key,
            temperature=0.0,
            response_mime=True,
            max_tokens=16384,
            timeout_s=timeout,
            max_retries=0,
            task="vat.invoice_batch",
        )

    # 便宜首读(flash)失败/没解析出任何发票 → 升级 OCR_FALLBACK_MODEL(=3.5-flash)再读一批。
    def _ok(r) -> bool:
        return bool(r) and r.ok and bool((r.data or {}).get("invoices"))

    res = try_with_fallback(_call, primary=flash(), ok=_ok, label="vex.batch")
    if res is None or not res.ok:
        kind = res.error_kind if res is not None else "all_models"
        logger.warning(f"[vex.batch] n={n} 失败: {kind}")
        return [
            {"ok": False, "filename": f.get("filename"), "error": f"AI 批量失败: {kind}"}
            for f in invoice_files
        ]
    items = (res.data or {}).get("invoices") or []
    _in_per = res.input_tokens // max(n, 1)
    _out_per = res.output_tokens // max(n, 1)

    out: List[Dict[str, Any]] = [None] * n  # type: ignore
    for r in items:
        try:
            idx = int(r.get("index", 0)) - 1
        except Exception:
            continue
        if not (0 <= idx < n):
            continue
        out[idx] = {
            "ok": True,
            "filename": invoice_files[idx].get("filename"),
            "buyer_tax_id": str(r.get("buyer_tax_id") or "").strip(),
            "buyer_name": str(r.get("buyer_name") or "").strip(),
            "buyer_branch": str(r.get("buyer_branch") or "").strip(),
            "invoice_no": str(r.get("invoice_no") or "").strip(),
            "invoice_date": str(r.get("invoice_date") or "").strip(),
            "period": str(r.get("period") or "").strip(),
            "amount_pre_vat": _to_float(r.get("amount_pre_vat")),
            "vat_amount": _to_float(r.get("vat_amount")),
            "total_amount": _to_float(r.get("total_amount")),
            "_input_tokens": _in_per,
            "_output_tokens": _out_per,
            "_batch_size": n,
        }
    # 漏掉的 index → 标 fail，调用方会 fallback 单张
    for i in range(n):
        if out[i] is None:
            out[i] = {
                "ok": False,
                "filename": invoice_files[i].get("filename"),
                "error": "batch_missing_index",
            }
    return out  # type: ignore


def extract_invoices_batched_parallel(
    invoice_files: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    batch_size: int = 5,
    max_workers: int = 4,
    auto_fallback_single: bool = True,
) -> List[Dict[str, Any]]:
    """v118.32.5 · 批量 + 并行：
    - 每批 batch_size 张走一次 Gemini
    - 多批并行 max_workers 路
    - 批失败时 auto_fallback_single 自动回退单张重试（保证不丢数据）
    """
    n = len(invoice_files)
    if n == 0:
        return []
    results: List[Optional[Dict]] = [None] * n
    batches: List[Tuple[int, List[Dict[str, Any]]]] = []
    for start in range(0, n, batch_size):
        chunk = invoice_files[start : start + batch_size]
        batches.append((start, chunk))

    def _run_batch(start: int, chunk: List[Dict[str, Any]]):
        out = extract_invoice_fields_batch(chunk, api_key=api_key)
        # fallback：批失败 / 批内部分失败 → 单张重试
        if auto_fallback_single:
            for j, r in enumerate(out):
                if not (r and r.get("ok")):
                    try:
                        f = chunk[j]
                        out[j] = extract_invoice_fields(f["bytes"], f["filename"], api_key=api_key)
                    except Exception as e:
                        logger.error(
                            f"[vex.batch] fallback 单张失败 {chunk[j].get('filename')}: {e}"
                        )
        for j, r in enumerate(out):
            results[start + j] = r

    # P0-2:每批加硬超时(批含 batch_size 张 + 可能的单张 fallback)· 挂起的批不阻塞整体 · job 能完成
    _batch_timeout = _VEX_OCR_PER_FILE_TIMEOUT * (batch_size + 1)
    pool = ThreadPoolExecutor(max_workers=max_workers)
    fut_to_batch = {pool.submit(_run_batch, s, c): (s, c) for (s, c) in batches}
    for fut, (s, c) in fut_to_batch.items():
        try:
            fut.result(timeout=_batch_timeout)
        except FuturesTimeout:
            logger.error(
                f"[vex.batch.parallel] 批硬超时({_batch_timeout}s) · start={s} · 落 ok=False"
            )
            for j, f in enumerate(c):
                if results[s + j] is None:
                    results[s + j] = {
                        "ok": False,
                        "filename": f.get("filename") or f"invoice_{s + j}",
                        "error": f"OCR 超时(>{_batch_timeout}s)",
                        "error_code": "ocr_timeout",
                    }
        except Exception as e:
            logger.error(f"[vex.batch.parallel] 批失败: {e}")
    pool.shutdown(wait=False)

    return [r or {"ok": False, "error": "worker_returned_none"} for r in results]
