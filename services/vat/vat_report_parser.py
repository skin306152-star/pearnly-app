# -*- coding: utf-8 -*-
"""
v118.32.1 · Pearnly · VAT 报告多格式解析器(facade)
- .xlsx/.xls               → vat_parser_excel
- .pdf(电子版)            → vat_parser_pdf(pdfplumber · 零成本)
- .pdf(扫描)/.jpg/.png 等 → vat_parser_gemini(Gemini OCR)
- 其余(csv/docx/tiff 等)  → services/ocr/pipeline
"""

import re
import logging
from typing import List, Dict, Any, Optional

from services.recon.field_comparator import normalize_tax_id, normalize_branch

# v118.35.0.3 · 包装 pydantic ValidationError 为单行用户友好提示
from services.ocr.error_format import short_error as _short_err

from services.vat.vat_parser_common import _to_float, _filter_garbage_rows, PARSER_VERSION
from services.vat.vat_parser_excel import parse_excel
from services.vat.vat_parser_pdf import parse_pdf_text, _parse_vat_pdf_text_lines
from services.vat.vat_parser_gemini import (
    parse_with_gemini,
    parse_with_gemini_paged,
    parse_with_gemini_image_smart,
)

# re-export · 行为契约(tests/unit/test_vat_report_parser_contract.py 直接调 vp.<name>)
from services.vat.vat_parser_common import _hit, _map_columns, _build_row  # noqa: F401

logger = logging.getLogger(__name__)


# ======================================================================
# 统一入口 · 按后缀分发 + 自动 fallback
# ======================================================================


def _parse_vat_via_pipeline(
    file_bytes: bytes, filename: str, api_key: Optional[str] = None
) -> Dict[str, Any]:
    """v118.35.0.2 · Route VAT report through services/ocr/pipeline with
    document_type='vat_report'. Used for non-PDF/non-Excel/non-image formats
    (CSV / TSV / DOCX / DOC / TXT / TIFF / BMP / GIF / XLSM).

    Converts pipeline normalized JSON (VatReportDocument) → row dict format
    that downstream reconciliation code expects (report_date / report_invoice_no
    / report_buyer_name / report_buyer_tax_id / report_amount_pre_vat /
    report_vat_amount / report_amount / etc).
    """
    try:
        from services.ocr.pipeline import (
            run_on_image_bytes as _run_image,
            run_on_table_bytes as _run_table,
            IMAGE_EXTENSIONS,
            TABLE_EXTENSIONS,
        )
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
    except ImportError as e:
        return {"ok": False, "rows": [], "row_count": 0, "error": f"pipeline import failed: {e}"}

    ext_dot = "." + (filename or "").lower().rsplit(".", 1)[-1]
    try:
        if ext_dot in IMAGE_EXTENSIONS:
            pr = _run_image(file_bytes, api_key=api_key, document_type="vat_report")
        elif ext_dot in TABLE_EXTENSIONS:
            pr = _run_table(
                file_bytes, filename=filename or "vat", api_key=api_key, document_type="vat_report"
            )
        else:
            return {"ok": False, "rows": [], "row_count": 0, "error": f"pipeline 不支持 {ext_dot}"}
    except Exception as e:
        return {"ok": False, "rows": [], "row_count": 0, "error": _short_err(e)}

    legacy = pipeline_result_to_legacy_dict(pr)
    rows: List[Dict] = []
    row_no = 0
    for page in legacy.get("pages") or []:
        doc = (page or {}).get("document") or {}
        for e in doc.get("entries") or []:
            row_no += 1
            invoice_no = str(e.get("invoice_no") or "").strip()
            if not re.search(r"[A-Za-z0-9]{2,}", invoice_no):
                continue  # skip rows without a real invoice number
            parsed = {
                "row_no": (
                    int(e.get("seq_no") or row_no)
                    if str(e.get("seq_no") or "").isdigit()
                    else row_no
                ),
                "report_date": e.get("transaction_date") or "",
                "report_invoice_no": invoice_no,
                "report_ref_no": invoice_no,
                "report_buyer_name": str(e.get("customer_name") or "").strip(),
                "report_buyer_tax_id": normalize_tax_id(e.get("customer_tax") or ""),
                "report_buyer_branch": normalize_branch(e.get("customer_branch") or ""),
                "report_amount_pre_vat": _to_float(e.get("subtotal")),
                "report_vat_amount": _to_float(e.get("vat")),
                "report_amount": _to_float(e.get("total")),
            }
            parsed["is_individual"] = not bool(parsed["report_buyer_tax_id"])
            rows.append(parsed)

    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "meta": {},
        "warnings": [],
        "parser_version": PARSER_VERSION,
        "method": "pipeline_v1",
        "needs_review": legacy.get("_needs_review", False),
    }


def parse_vat_report(
    file_bytes: bytes,
    filename: str,
    api_key: Optional[str] = None,
    *,
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
    user_type: Optional[str] = None,
) -> Dict[str, Any]:
    """销项 VAT 报表解析(任意格式)。Facade → controller(task=vat_report)。"""
    from services.ocr import controller
    from services.ocr.contracts import OcrRequest

    return controller.run(
        OcrRequest(
            task="vat_report",
            file_bytes=file_bytes,
            filename=filename,
            api_key=api_key,
            plan_code=plan_code,
            is_exempt=is_exempt,
            user_type=user_type,
        )
    ).data


def _parse_vat_report_impl(
    file_bytes: bytes, filename: str, api_key: Optional[str] = None
) -> Dict[str, Any]:
    ext = (filename or "").lower().rsplit(".", 1)[-1]

    if ext in ("xlsx", "xls"):
        result = parse_excel(file_bytes)
    elif ext == "pdf":
        text_result = parse_pdf_text(file_bytes)
        result = None
        if text_result and text_result.get("rows"):
            # v118.32.5.5.3 · 先过滤再判定 · 过滤后 ≥ 3 行才信
            cleaned = _filter_garbage_rows(text_result["rows"])
            if len(cleaned) >= 3:
                text_result["rows"] = cleaned
                text_result["row_count"] = len(cleaned)
                logger.info(f"[vat] pdf_text 过滤后剩 {len(cleaned)} 行 · 用表抽取结果")
                result = text_result
            else:
                logger.info(f"[vat] pdf_text 表抽取过滤剩 {len(cleaned)} 行 · 试文字行 regex")
        # v118.32.5.5.4 · 表抽取走不通 · 试文字行 regex(不立刻回退 Gemini · 省 40 秒)
        if result is None:
            regex_rows = _parse_vat_pdf_text_lines(file_bytes)
            regex_cleaned = _filter_garbage_rows(regex_rows or [])
            if len(regex_cleaned) >= 3:
                logger.info(f"[vat] pdf_text_regex 抽到 {len(regex_cleaned)} 行 · 跳过 Gemini")
                result = {
                    "ok": True,
                    "rows": regex_cleaned,
                    "meta": {},
                    "warnings": [],
                    "parser_version": PARSER_VERSION,
                    "row_count": len(regex_cleaned),
                    "method": "pdf_text_regex",
                }
            else:
                logger.info(f"[vat] 文字行 regex 也只 {len(regex_cleaned)} 行 · 回退 Gemini")
                result = parse_with_gemini_paged(file_bytes, api_key=api_key)
    elif ext in ("jpg", "jpeg", "png", "webp"):
        # v118.32.4.5 · 大图预压缩 + 必要时上下分块(防 Gemini 504)
        result = parse_with_gemini_image_smart(file_bytes, ext, api_key=api_key)
        if result is None:
            mime = "image/jpeg" if ext == "jpg" else f"image/{ext}"
            result = parse_with_gemini(file_bytes, mime, api_key=api_key)
    elif ext in ("csv", "tsv", "docx", "doc", "txt", "tiff", "tif", "bmp", "gif", "xlsm"):
        # 2026-05-21 v118.35.0.2 · 新增格式走统一 pipeline · document_type=vat_report
        result = _parse_vat_via_pipeline(file_bytes, filename, api_key=api_key)
    else:
        return {
            "ok": False,
            "error": f"暂不支持 .{ext} · 请用 Excel / PDF / 图片 / CSV / Word 等格式",
            "rows": [],
        }

    # v118.32.5.5.3 · 所有路径出口统一过滤一次(Gemini 路径双保险)
    if result.get("ok") and result.get("rows"):
        before = len(result["rows"])
        result["rows"] = _filter_garbage_rows(result["rows"])
        result["row_count"] = len(result["rows"])
        if before != len(result["rows"]):
            logger.info(f"[vat] 最终过滤 {before} → {len(result['rows'])} 行")
    return result


# ── 销项发票:结构化(xlsx/csv 模板/导出)直读 · 免 OCR ───────────────────
# 发票与 VAT 报告行项结构相同,复用 parse_vat_report 行项解析后转成发票记录形状,
# 让 salesvat 两条路径(异步 worker / vat_excel /build)都能吃标准模板发票。
STRUCTURED_INVOICE_EXTS = (".xlsx", ".xls", ".xlsm", ".csv", ".tsv")


def report_row_to_invoice(row: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """行项解析结果(report_* 键)→ 发票 OCR 记录 shape(下游 build_excel/对账零改动)。"""
    return {
        "ok": True,
        "filename": filename,
        "buyer_tax_id": row.get("report_buyer_tax_id", ""),
        "buyer_name": row.get("report_buyer_name", ""),
        "buyer_branch": row.get("report_buyer_branch", ""),
        "invoice_no": row.get("report_invoice_no", ""),
        "invoice_date": row.get("report_date", ""),
        "amount_pre_vat": row.get("report_amount_pre_vat"),
        "vat_amount": row.get("report_vat_amount"),
        "total_amount": row.get("report_amount"),
    }


def parse_structured_invoices(files, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """xlsx/csv 发票文件列表 [(bytes, filename)] → 发票记录列表(行项直读)。"""
    out: List[Dict[str, Any]] = []
    for b, fn in files:
        rep = _parse_vat_report_impl(b, fn, api_key=api_key)
        for row in rep.get("rows") or []:
            out.append(report_row_to_invoice(row, fn))
    return out
