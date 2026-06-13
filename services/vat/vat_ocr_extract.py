# -*- coding: utf-8 -*-
"""单张发票 OCR 抽取(8 字段)+ 7 项硬校验 + 并行调度 · vat_excel_export 拆分。"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from services.recon.field_comparator import parse_date
from services.recon.vat_recon_core import _to_float, _derive_period
from services.ocr.gemini_models import flash as _flash

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
# 单张发票 OCR · 只抽 8 字段(独立 prompt · 不做匹配)
# ════════════════════════════════════════════════════════════════════════
_INVOICE_PROMPT = """You are reading a Thai tax invoice (ใบกำกับภาษี) or its image.

Extract ONLY these 8 fields. Do NOT interpret · do NOT match · do NOT clean.

Output JSON ONLY:
{
  "buyer_tax_id": "13-digit Thai tax ID of the BUYER (ลูกค้า / ผู้ซื้อ) · digits only · empty string if missing",
  "buyer_name":   "Buyer name EXACTLY as printed (Thai/English/mixed) · keep prefixes like บริษัท ... จำกัด",
  "buyer_branch": "Branch · 'สำนักงานใหญ่' or 5-digit code (e.g. 00001) · empty string if cash customer",
  "invoice_no":   "Invoice number EXACTLY as printed · keep prefixes (INV/IV/TAX) · do NOT strip leading zeros",
  "invoice_date": "Date EXACTLY as printed · format DD/MM/YYYY · if Buddhist Era (e.g. 2569) keep that year",
  "period":       "If invoice header shows a tax period (e.g. 04/2026), copy it · else derive MM/YYYY from invoice_date · Gregorian only",
  "amount_pre_vat": "Net amount BEFORE VAT · number only · 2 decimals",
  "vat_amount":     "VAT amount · number only · 2 decimals",
  "total_amount":   "TOTAL including VAT · number only · 2 decimals"
}

STRICT RULES:
1. If a field is partially visible or unreadable · output "" · do NOT guess
2. Do NOT normalize prefixes · do NOT fuzzy-match · just copy what is printed
3. Cash customer (ลูกค้าขายเงินสด) → buyer_tax_id="" buyer_branch=""
4. Date: BE years (2500+) stay as printed · period: convert BE → Gregorian (BE-543)
5. Numbers: digits and dot only · no commas · no currency
"""


def _extract_invoice_via_pipeline(
    file_bytes: bytes, filename: str, api_key: Optional[str] = None
) -> Dict[str, Any]:
    """P1-1 · Excel/CSV/Word/TIFF 等表格/文档型销售发票 → 统一 pipeline(document_type=invoice)·
    映射成 VEX 8 字段。OCR 失败 / 非发票 / 无页 → ok=False(计入 OCR 失败数)。"""
    try:
        from services.ocr.pipeline import (
            IMAGE_EXTENSIONS,
            TABLE_EXTENSIONS,
            run_on_image_bytes as _run_image,
            run_on_table_bytes as _run_table,
        )
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "filename": filename, "error": f"pipeline 不可用: {e}"}

    ext_dot = "." + (filename or "").lower().rsplit(".", 1)[-1]
    try:
        if ext_dot in IMAGE_EXTENSIONS:
            pr = _run_image(file_bytes, api_key=api_key, document_type="invoice")
        elif ext_dot in TABLE_EXTENSIONS:
            pr = _run_table(
                file_bytes, filename=filename or "invoice", api_key=api_key, document_type="invoice"
            )
        else:
            return {"ok": False, "filename": filename, "error": f"不支持的格式 {ext_dot}"}
    except Exception as e:  # noqa: BLE001
        logger.error(f"[vex.pipeline] {filename} 失败: {type(e).__name__}: {e}")
        return {"ok": False, "filename": filename, "error": str(e)[:120]}

    legacy = pipeline_result_to_legacy_dict(pr)
    pages = legacy.get("pages") or []
    fld = (pages[0].get("fields") if pages else None) or {}
    if not pages or fld.get("is_not_invoice"):
        return {"ok": False, "filename": filename, "error": "未识别到销售发票内容"}

    # pipeline ThaiInvoice 字段 → VEX 8 字段(buyer_tax→buyer_tax_id 等 · date→period 推导)
    date_str = str(fld.get("date") or "").strip()
    return {
        "ok": True,
        "filename": filename,
        "buyer_tax_id": str(fld.get("buyer_tax") or "").strip(),
        "buyer_name": str(fld.get("buyer_name") or "").strip(),
        "buyer_branch": "",  # pipeline 不抽分公司 · 空 → P0-1 归一为总部 00000
        "invoice_no": str(fld.get("invoice_number") or "").strip(),
        "invoice_date": date_str,
        "period": _derive_period(date_str),
        "amount_pre_vat": _to_float(fld.get("subtotal")),
        "vat_amount": _to_float(fld.get("vat")),
        "total_amount": _to_float(fld.get("total_amount")),
        "_input_tokens": int(pages[0].get("input_tokens") or 0),
        "_output_tokens": int(pages[0].get("output_tokens") or 0),
        "_engine": "pipeline",
    }


def extract_invoice_fields(
    file_bytes: bytes, filename: str, api_key: Optional[str] = None
) -> Dict[str, Any]:
    """单张发票 OCR · 抽 8 字段
    返回:{ok, filename, buyer_tax_id, buyer_name, buyer_branch, invoice_no,
           invoice_date, period, amount_pre_vat, vat_amount, total_amount, error}
    """
    ext = (filename or "").lower().rsplit(".", 1)[-1]

    # v118.32.5.5.9 · text_path 快路径(电子 PDF · 跳 Gemini · 5-10x 提速)
    # BAKELAB / 多数泰国电子发票文字层完整 · 不需要 Gemini
    if ext == "pdf":
        try:
            from services.ocr.pdf_text_extractor import try_text_extraction

            tp = try_text_extraction(file_bytes, strict=False)
            if tp:
                fld: Dict[str, Any] = {}
                for p in tp.get("pages") or []:
                    for k, v in (p.get("fields") or {}).items():
                        if k not in fld and v:
                            fld[k] = v
                date_str = str(fld.get("date") or "").strip()
                # 从 date 推 period MM/YYYY(兼容佛历)
                period = ""
                if date_str:
                    m = re.match(r"(\d{1,2})[\-/.](\d{1,2})[\-/.](\d{2,4})", date_str)
                    if m:
                        y = int(m.group(3))
                        if y < 100:
                            y += 2000
                        if y > 2400:
                            y -= 543
                        period = f"{int(m.group(2)):02d}/{y}"
                logger.info(f"[vex.text_path] {filename} · 跳 Gemini · 0 cost")
                return {
                    "ok": True,
                    "filename": filename,
                    "buyer_tax_id": str(fld.get("buyer_tax") or "").strip(),
                    "buyer_name": str(fld.get("buyer_name") or "").strip(),
                    "buyer_branch": "",
                    "invoice_no": str(fld.get("invoice_number") or "").strip(),
                    "invoice_date": date_str,
                    "period": period,
                    "amount_pre_vat": _to_float(fld.get("subtotal")),
                    "vat_amount": _to_float(fld.get("vat")),
                    "total_amount": _to_float(fld.get("total_amount")),
                    "_input_tokens": 0,
                    "_output_tokens": 0,
                    "_engine": "text_path",
                }
        except Exception as _tpe:
            logger.info(
                f"[vex.text_path] {filename} 异常 fallback Gemini · {type(_tpe).__name__}: {_tpe}"
            )

    mime = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }.get(ext)
    if not mime:
        # P1-1(2026-05-25):Excel/CSV/Word/TIFF 等格式的销售发票走统一 pipeline(document_type=invoice)·
        #   映射成 VEX 8 字段 · 此前直接报"不支持的格式"(配合前端 UI 宣传支持但静默丢弃)。
        return _extract_invoice_via_pipeline(file_bytes, filename, api_key=api_key)

    try:
        import google.generativeai as genai
    except ImportError:
        return {"ok": False, "filename": filename, "error": "google-generativeai 未安装"}

    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return {"ok": False, "filename": filename, "error": "Gemini key 未配置"}

    text = ""
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            _flash(),
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.0,
            },
        )
        response = model.generate_content(
            [_INVOICE_PROMPT, {"mime_type": mime, "data": file_bytes}],
            request_options={"timeout": 30},
        )
        text = (response.text or "").strip()
        data = json.loads(text)
        _usage = getattr(response, "usage_metadata", None)
        _in_tok = int(getattr(_usage, "prompt_token_count", 0) or 0)
        _out_tok = int(getattr(_usage, "candidates_token_count", 0) or 0)
        return {
            "ok": True,
            "filename": filename,
            "buyer_tax_id": str(data.get("buyer_tax_id") or "").strip(),
            "buyer_name": str(data.get("buyer_name") or "").strip(),
            "buyer_branch": str(data.get("buyer_branch") or "").strip(),
            "invoice_no": str(data.get("invoice_no") or "").strip(),
            "invoice_date": str(data.get("invoice_date") or "").strip(),
            "period": str(data.get("period") or "").strip(),
            "amount_pre_vat": _to_float(data.get("amount_pre_vat")),
            "vat_amount": _to_float(data.get("vat_amount")),
            "total_amount": _to_float(data.get("total_amount")),
            "_input_tokens": _in_tok,
            "_output_tokens": _out_tok,
        }
    except json.JSONDecodeError as e:
        logger.warning(f"[vex.extract] {filename} JSON 解析失败: {e} · raw={text[:200]}")
        return {"ok": False, "filename": filename, "error": f"AI 返回格式异常: {str(e)[:60]}"}
    except Exception as e:
        logger.error(f"[vex.extract] {filename} 失败: {type(e).__name__}: {e}")
        return {"ok": False, "filename": filename, "error": str(e)[:120]}


# ════════════════════════════════════════════════════════════════════════
# v4.10.22 · OCR 准确率底线 · 7 项硬校验
# ════════════════════════════════════════════════════════════════════════


def _ocr_validate_invoice(inv: Dict) -> List[str]:
    """7 项 OCR 准确率底线校验 · 返回问题 key 列表(空=全通过)
    校验规则:发票号空 / 客户名空 / 税号非13位 / 日期格式异常 /
             含税金额为0 / VAT≠7% / 净额+VAT≠总额"""
    warns: List[str] = []
    # 1. 发票号空
    if not (inv.get("invoice_no") or "").strip():
        warns.append("w_invoice_no_empty")
    # 2. 客户名空
    if not (inv.get("buyer_name") or "").strip():
        warns.append("w_buyer_name_empty")
    # 3. 税号非 13 位(仅当非空时校验 · 只数数字位数)
    tax_digits = "".join(c for c in (inv.get("buyer_tax_id") or "") if c.isdigit())
    if tax_digits and len(tax_digits) != 13:
        warns.append("w_tax_id_bad_length")
    # 4. 日期格式异常(仅当非空时校验)
    date_str = (inv.get("invoice_date") or "").strip()
    if date_str and parse_date(date_str) is None:
        warns.append("w_date_parse_fail")
    # 5. 含税金额为 0 或缺失
    total = _to_float(inv.get("total_amount"))
    if total is None or total == 0.0:
        warns.append("w_total_zero")
    # 6. VAT ≠ 7%(净额 > 10 THB 才检查 · 容差 max(1 THB, 5%))
    pre = _to_float(inv.get("amount_pre_vat"))
    vat = _to_float(inv.get("vat_amount"))
    if pre is not None and vat is not None and pre > 10.0:
        expected_vat = round(pre * 0.07, 2)
        tol = max(1.0, expected_vat * 0.05)
        if abs(vat - expected_vat) > tol:
            warns.append("w_vat_rate_mismatch")
    # 7. 净额 + VAT ≠ 总额(三值都有 · 容差 0.02 THB)
    if pre is not None and vat is not None and total is not None and total > 0:
        computed = round(pre + vat, 2)
        if abs(computed - total) > 0.02:
            warns.append("w_amount_sum_mismatch")
    return warns


# P0-2 修(2026-05-25 销项税回归):Gemini SDK 的 request_options timeout 偶发不生效会让单张
#   图片/发票 OCR 永久挂起 → as_completed 一直等不到 → salesvat job 无限 running(TC08 卡 18min+)。
#   线程层加硬超时兜底:单文件超 PER_FILE_TIMEOUT 仍没回 → 落 ok=False(error_code=ocr_timeout)·
#   job 仍能完成(失败的文件计入 OCR 失败数)。Python 杀不掉挂起线程 → 任其后台跑完(pool 不等待)。
#   PER_FILE 取值高于各 OCR 自身 SDK 超时(发票 30s)· 正常情况 SDK 超时先生效 · 这里只兜真·挂死。
_VEX_OCR_PER_FILE_TIMEOUT = int(os.environ.get("VEX_OCR_PER_FILE_TIMEOUT_SEC", "75"))


def extract_invoices_parallel(
    invoice_files: List[Dict[str, Any]], api_key: Optional[str] = None, max_workers: int = 10
) -> List[Dict[str, Any]]:
    """v118.32.4.9.5 · 并行 10 路 OCR · 防止 1000 张串行跑死
    invoice_files: [{filename, bytes}]
    返回:同顺序的结果列表(每张带硬超时 · 超时落 ok=False 不阻塞整批)"""
    if not invoice_files:
        return []
    results: List[Optional[Dict]] = [None] * len(invoice_files)
    pool = ThreadPoolExecutor(max_workers=min(max_workers, len(invoice_files)))
    fut_to_idx = {
        pool.submit(extract_invoice_fields, f["bytes"], f["filename"], api_key=api_key): i
        for i, f in enumerate(invoice_files)
    }
    for fut, idx in fut_to_idx.items():
        fn = invoice_files[idx].get("filename") or f"invoice_{idx}"
        try:
            results[idx] = fut.result(timeout=_VEX_OCR_PER_FILE_TIMEOUT)
        except FuturesTimeout:
            logger.error(f"[vex.parallel] 单张 OCR 硬超时({_VEX_OCR_PER_FILE_TIMEOUT}s): {fn}")
            results[idx] = {
                "ok": False,
                "filename": fn,
                "error": f"OCR 超时(>{_VEX_OCR_PER_FILE_TIMEOUT}s)",
                "error_code": "ocr_timeout",
            }
        except Exception as e:
            logger.error(f"[vex.parallel] 单张抽取异常: {e}")
            results[idx] = {"ok": False, "filename": fn, "error": str(e)}
    pool.shutdown(wait=False)  # 不等挂起线程(Python 杀不掉)· 任其后台跑完 · job 不再卡死
    return [r or {"ok": False, "error": "worker_returned_none"} for r in results]


def _ocr_with_hard_timeout(fn, timeout_sec: int, on_timeout):
    """P0-2 · 在独立线程跑 fn · 超 timeout_sec 仍没返回 → 返回 on_timeout()(不阻塞调用方)。

    用于报告侧 OCR(merge_vat_reports 串行解析每份报告)· 兜 Gemini 调用偶发永久挂起。
    pool.shutdown(wait=False):挂起线程留后台 · 不拖住 job。
    """
    pool = ThreadPoolExecutor(max_workers=1)
    fut = pool.submit(fn)
    try:
        return fut.result(timeout=timeout_sec)
    except FuturesTimeout:
        return on_timeout()
    finally:
        pool.shutdown(wait=False)
