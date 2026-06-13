# -*- coding: utf-8 -*-
"""VAT 报告解析 · Gemini OCR(扫描 PDF / 图片)· 拆页/切块并行防 504。"""

import io
import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

from services.recon.field_comparator import normalize_tax_id, normalize_branch
from services.ocr.gemini_models import flash as _flash

from services.vat.vat_parser_common import _to_float, PARSER_VERSION

logger = logging.getLogger(__name__)


# ======================================================================
# 3. Gemini OCR(扫描 PDF / 图片)
# ======================================================================

_GEMINI_PROMPT = """You are extracting data from a Thai Sales VAT Report (รายงานภาษีขาย).
This is a monthly report listing all sales tax invoices issued by a VAT-registered business.

⚠ STRICT RULES (must follow):
1. Output EXACTLY what is printed. Do NOT rewrite, normalize, translate, or "correct" any value.
2. For names: preserve the original spelling, spacing, prefixes (คุณ / นาย / นางสาว / บริษัท ... จำกัด), and language (Thai/English). If a name is "คุณสุพัชญ์ สันติวงษ์", output exactly that — do not change to "สุวพัชญ์" or any other variant.
3. For tax IDs: output exactly the 13 digits as printed. If 1-2 digits are unclear, look carefully — DO NOT guess. Output what is most likely printed.
4. For amounts: preserve all decimal places. "7,595.00" → 7595.00 (drop comma, keep decimals). NEVER round or truncate.
5. Read every row left-to-right top-to-bottom. Do not skip rows.

Extract ALL data rows. Skip page headers, signatures, summary/total rows.

For each row, return a JSON object with these fields:
- row_no: integer (sequence number ลำดับ)
- report_date: date "YYYY-MM-DD". If year is Buddhist Era (BE, > 2400), subtract 543. e.g. 01/03/2569 → "2026-03-01"
- report_invoice_no: tax invoice number (เลขที่ใบกำกับภาษี / เลขที่) — copy EXACTLY as printed
- report_ref_no: reference document number (เลขที่เอกสารอ้างอิง / เลขอ้างอิง) — copy EXACTLY as printed; empty string "" if column not present
- report_buyer_name: buyer name (Thai or English) — copy EXACTLY as printed, including all prefixes and spaces
- report_buyer_tax_id: 13-digit Thai tax ID, digits ONLY (drop dashes/spaces). Empty string "" for cash sale / individual buyer (ลูกค้าขายเงินสด/บุคคลธรรมดา)
- report_buyer_branch: "00000" if HQ (สำนักงานใหญ่/สนญ./head office), or 5-digit code, or empty string for individual
- report_amount_pre_vat: pre-VAT amount (มูลค่าสินค้าหรือบริการ) as number
- report_vat_amount: 7% VAT amount (จำนวนเงินภาษีมูลค่าเพิ่ม) as number
- report_amount: total = pre-VAT + VAT (use printed value if shown; compute only if missing)

Self-check before output: For each row, verify report_amount_pre_vat + report_vat_amount ≈ report_amount (±0.01). If not, re-read the row.

Return ONLY:
{"rows": [...], "meta": {"total_amount_pre_vat": number, "total_vat": number}}
"""


# v118.32.4.9.6 · 大 PDF 拆页 + 并行处理(防 Gemini 504)
# 真实国税局 33 行 PDF 单批 2 页 + 45s timeout 仍然 504 · 改单页一批 + 60s + 单次重试
# 单页一批保证 Gemini 处理负担最小 · 总并发 4 路 · 总耗时基本持平
_BATCH_PAGES = 1
_BATCH_WORKERS = 8


def parse_with_gemini_paged(file_bytes: bytes, api_key: Optional[str] = None) -> Dict[str, Any]:
    """PDF 专用:拆页 + 并行调 Gemini · 合并 rows + 重编 row_no
    页数 <= _BATCH_PAGES 时直接调 parse_with_gemini(整文件)"""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return parse_with_gemini(file_bytes, "application/pdf", api_key=api_key)

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        n_pages = len(reader.pages)
    except Exception as e:
        logger.warning(f"[vat_paged] 读页失败 · 回退整文件: {e}")
        return parse_with_gemini(file_bytes, "application/pdf", api_key=api_key)

    if n_pages <= _BATCH_PAGES:
        return parse_with_gemini(file_bytes, "application/pdf", api_key=api_key)

    # 拆批:每 _BATCH_PAGES 页一批
    batches: List[bytes] = []
    try:
        for start in range(0, n_pages, _BATCH_PAGES):
            w = PdfWriter()
            for j in range(start, min(start + _BATCH_PAGES, n_pages)):
                w.add_page(reader.pages[j])
            buf = io.BytesIO()
            w.write(buf)
            batches.append(buf.getvalue())
    except Exception as e:
        logger.warning(f"[vat_paged] 拆页失败 · 回退整文件: {e}")
        return parse_with_gemini(file_bytes, "application/pdf", api_key=api_key)

    logger.info(
        f"[vat_paged] PDF {n_pages} 页 → {len(batches)} 批 × {_BATCH_PAGES}p · 并行 {_BATCH_WORKERS}"
    )

    # 并行
    from concurrent.futures import ThreadPoolExecutor

    rows_all: List[Dict] = []
    meta_all: Dict[str, Any] = {"total_amount_pre_vat": 0.0, "total_vat": 0.0}
    paged_in_tok = 0
    paged_out_tok = 0
    succeeded = 0
    failed_msgs: List[str] = []

    def _one(b: bytes):
        return parse_with_gemini(b, "application/pdf", api_key=api_key)

    with ThreadPoolExecutor(max_workers=min(_BATCH_WORKERS, len(batches))) as ex:
        futures = [ex.submit(_one, b) for b in batches]
        for i, fut in enumerate(futures):
            try:
                r = fut.result()
                if r.get("ok"):
                    succeeded += 1
                    rows_all.extend(r.get("rows", []) or [])
                    m = r.get("meta") or {}
                    if isinstance(m.get("total_amount_pre_vat"), (int, float)):
                        meta_all["total_amount_pre_vat"] += m["total_amount_pre_vat"]
                    if isinstance(m.get("total_vat"), (int, float)):
                        meta_all["total_vat"] += m["total_vat"]
                    paged_in_tok += int(r.get("_input_tokens") or 0)
                    paged_out_tok += int(r.get("_output_tokens") or 0)
                else:
                    failed_msgs.append(f"批{i+1}/{len(batches)}: {(r.get('error') or '?')[:80]}")
            except Exception as e:
                failed_msgs.append(f"批{i+1}/{len(batches)}: {type(e).__name__}: {str(e)[:80]}")

    if succeeded == 0:
        return {
            "ok": False,
            "rows": [],
            "error": f"全部 {len(batches)} 批 OCR 均失败 · {'; '.join(failed_msgs[:3])}",
        }

    # 重编 row_no(每批从 1 开始 · 合并后重新连续编号)
    for i, r in enumerate(rows_all, 1):
        r["row_no"] = i

    warnings = []
    if failed_msgs:
        warnings.append(f"{len(failed_msgs)}/{len(batches)} 批失败 · 部分数据可能缺失")
        for m in failed_msgs[:3]:
            logger.warning(f"[vat_paged] {m}")

    return {
        "ok": True,
        "rows": rows_all,
        "meta": meta_all,
        "warnings": warnings,
        "parser_version": PARSER_VERSION,
        "row_count": len(rows_all),
        "method": f"gemini_paged_{_BATCH_PAGES}p_{len(batches)}b",
        "_input_tokens": paged_in_tok,
        "_output_tokens": paged_out_tok,
    }


# v118.32.4.5 · 大图智能 OCR(预压缩 + 必要时上下分块) · 失败返回 None 让上层回退
_IMG_MAX_LONG_EDGE = 1800  # 长边超过此值 → 等比缩放
_IMG_SPLIT_HEIGHT = 1100  # 高度超此值 → 上下切两块(报告图普遍 1500~2000px · Gemini 单次易 504)
_IMG_OVERLAP_PX = 100  # 切分时上下重叠像素(防止切到表格行中间)


def parse_with_gemini_image_smart(file_bytes: bytes, ext: str, api_key: Optional[str] = None):
    """JPG/PNG 报告 · 大图先缩放 · 高图再切块 · 并行 Gemini · 合并行
    返回 dict(success/fail) 或 None(走老路径)"""
    try:
        from PIL import Image
    except ImportError:
        return None

    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        W, H = img.size
        # 1. 等比缩放
        long_edge = max(W, H)
        if long_edge > _IMG_MAX_LONG_EDGE:
            ratio = _IMG_MAX_LONG_EDGE / long_edge
            new_w, new_h = int(W * ratio), int(H * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            W, H = new_w, new_h
            logger.info(f"[vat_img] 缩放: {long_edge}→{_IMG_MAX_LONG_EDGE}px")

        # 2. 单图还是切块?
        if H <= _IMG_SPLIT_HEIGHT:
            # 单张直接调
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85, optimize=True)
            return parse_with_gemini(buf.getvalue(), "image/jpeg", api_key=api_key)

        # 3. 上下切两块 · 中间留重叠区
        mid = H // 2
        top = img.crop((0, 0, W, mid + _IMG_OVERLAP_PX))
        bot = img.crop((0, mid - _IMG_OVERLAP_PX, W, H))
        bufs = []
        for sub in (top, bot):
            b = io.BytesIO()
            sub.save(b, format="JPEG", quality=85, optimize=True)
            bufs.append(b.getvalue())
        logger.info(f"[vat_img] 高图切块: {H}px → 2 块 · 并行")

        # 并行调 Gemini
        from concurrent.futures import ThreadPoolExecutor

        rows_all = []
        meta_all = {"total_amount_pre_vat": 0.0, "total_vat": 0.0}
        img_in_tok = 0
        img_out_tok = 0
        succeeded = 0
        failed_msgs = []

        def _one(b):
            return parse_with_gemini(b, "image/jpeg", api_key=api_key)

        with ThreadPoolExecutor(max_workers=2) as ex:
            futures = [ex.submit(_one, b) for b in bufs]
            for i, fut in enumerate(futures):
                try:
                    r = fut.result()
                    if r.get("ok"):
                        succeeded += 1
                        rows_all.extend(r.get("rows") or [])
                        m = r.get("meta") or {}
                        if isinstance(m.get("total_amount_pre_vat"), (int, float)):
                            meta_all["total_amount_pre_vat"] += m["total_amount_pre_vat"]
                        if isinstance(m.get("total_vat"), (int, float)):
                            meta_all["total_vat"] += m["total_vat"]
                        img_in_tok += int(r.get("_input_tokens") or 0)
                        img_out_tok += int(r.get("_output_tokens") or 0)
                    else:
                        failed_msgs.append(f"块{i+1}: {(r.get('error') or '?')[:80]}")
                except Exception as e:
                    failed_msgs.append(f"块{i+1}: {type(e).__name__}: {str(e)[:80]}")

        if succeeded == 0:
            return {"ok": False, "rows": [], "error": f"两块均失败: {'; '.join(failed_msgs[:2])}"}

        # 重叠区可能重复行 · 按 (date, invoice_no, amount) 去重
        seen = set()
        dedup = []
        for r in rows_all:
            key = (
                r.get("report_date"),
                r.get("report_invoice_no"),
                r.get("report_amount") or r.get("report_amount_pre_vat"),
            )
            if key in seen:
                continue
            seen.add(key)
            dedup.append(r)

        # 重编 row_no
        for i, r in enumerate(dedup, 1):
            r["row_no"] = i

        warnings = []
        if failed_msgs:
            warnings.append(f"{len(failed_msgs)}/2 块失败 · 部分数据可能缺失")

        return {
            "ok": True,
            "rows": dedup,
            "meta": meta_all,
            "warnings": warnings,
            "parser_version": PARSER_VERSION,
            "row_count": len(dedup),
            "method": "gemini_img_split",
            "_input_tokens": img_in_tok,
            "_output_tokens": img_out_tok,
        }
    except Exception as e:
        logger.warning(f"[vat_img] 智能 OCR 异常 · 回退老路径: {type(e).__name__}: {e}")
        return None


def parse_with_gemini(
    file_bytes: bytes, mime_type: str, api_key: Optional[str] = None
) -> Dict[str, Any]:
    try:
        import google.generativeai as genai
    except ImportError:
        return {"ok": False, "error": "google-generativeai 未安装", "rows": []}

    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return {"ok": False, "error": "Gemini API key 未配置", "rows": []}

    text = ""
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            _flash(),
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        )
        # v118.32.4.9.6 · timeout 45→60 + 超时/网络错误单次重试(真实国税局 PDF 504 修)
        response = None
        last_err = None
        for attempt in range(2):
            try:
                response = model.generate_content(
                    [
                        _GEMINI_PROMPT,
                        {"mime_type": mime_type, "data": file_bytes},
                    ],
                    request_options={"timeout": 60},
                )
                break
            except Exception as e:
                last_err = e
                err_name = type(e).__name__
                err_msg = str(e).lower()
                # 仅在超时/网络类错误上重试 · 4xx 业务错直接抛
                if attempt == 0 and (
                    "timeout" in err_msg
                    or "deadline" in err_msg
                    or "503" in err_msg
                    or "504" in err_msg
                    or err_name in ("DeadlineExceeded", "ServiceUnavailable")
                ):
                    logger.warning(f"[vat_gemini] 首次失败({err_name})· 2 秒后重试")
                    import time

                    time.sleep(2)
                    continue
                raise
        if response is None:
            raise last_err or RuntimeError("Gemini 无响应")
        text = (response.text or "").strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        raw_rows = data.get("rows", []) or []

        rows: List[Dict] = []
        for i, r in enumerate(raw_rows, 1):
            parsed = {
                "row_no": int(r.get("row_no") or i),
                "report_date": r.get("report_date") or "",
                "report_invoice_no": str(r.get("report_invoice_no") or "").strip(),
                "report_ref_no": str(
                    r.get("report_ref_no") or ""
                ).strip(),  # v118.32.5 · GL对账匹配键
                "report_buyer_name": str(r.get("report_buyer_name") or "").strip(),
                "report_buyer_tax_id": normalize_tax_id(r.get("report_buyer_tax_id") or ""),
                "report_buyer_branch": normalize_branch(r.get("report_buyer_branch") or ""),
                "report_amount_pre_vat": _to_float(r.get("report_amount_pre_vat")),
                "report_vat_amount": _to_float(r.get("report_vat_amount")),
                "report_amount": _to_float(r.get("report_amount")),
            }
            parsed["is_individual"] = not bool(parsed["report_buyer_tax_id"])
            # v118.32.5.5.2 · 过滤 Gemini 误抓的页眉/分隔行(WNF 报告:列名 / `<----...---->` / `===` 等)
            inv = parsed["report_invoice_no"]
            buyer = parsed["report_buyer_name"]
            amt = parsed["report_amount_pre_vat"] or parsed["report_amount"] or 0
            _is_garbage = (
                not re.search(r"[A-Za-z0-9]{2,}", inv)  # 发票号必须含 ≥2 字母数字
                or "ใบกำกับภาษี" in inv
                or "เลขที่" == inv  # 页眉关键词
                or "ลำดับ" in inv  # 表头"序号"
                or (
                    amt == 0
                    and parsed["report_vat_amount"] == 0
                    and not parsed["report_buyer_tax_id"]
                    and ("---" in inv or "===" in inv or "<--" in inv or "..." in inv)
                )
            )
            if _is_garbage:
                logger.info(f"[vat_gemini] 跳过非数据行 #{i} inv={inv!r} buyer={buyer[:30]!r}")
                continue
            rows.append(parsed)

        _usage = getattr(response, "usage_metadata", None)
        _in_tok = int(getattr(_usage, "prompt_token_count", 0) or 0)
        _out_tok = int(getattr(_usage, "candidates_token_count", 0) or 0)
        return {
            "ok": True,
            "rows": rows,
            "meta": data.get("meta", {}) or {},
            "warnings": [],
            "parser_version": PARSER_VERSION,
            "row_count": len(rows),
            "method": "gemini_ocr",
            "_input_tokens": _in_tok,
            "_output_tokens": _out_tok,
        }
    except json.JSONDecodeError as e:
        logger.error(f"[vat_gemini] JSON 解析失败: {e} · raw: {text[:300]}")
        return {"ok": False, "error": f"Gemini 返回非 JSON: {str(e)[:100]}", "rows": []}
    except Exception as e:
        logger.error(f"[vat_gemini] 失败: {e}")
        return {"ok": False, "error": str(e), "rows": []}
