# -*- coding: utf-8 -*-
"""K1b/K2 · 财务文件转换 HTTP 端点(PDF/图片/Excel → 结构化结果 / xlsx / pdf)。

无状态两段式:上传的文件直接跑 services.fileconv 对应引擎(K1a PDF 纯函数 / K1c OCR /
K2 Excel,均零服务端状态)——默认回 JSON 摘要(doc_type/status/conserved/stats/issues
前 N 条+总数),`?format=xlsx|pdf` 时把同一份上传原样再跑一次转换直接回附件。各路径
各自独立调用、互不依赖同一次请求的产物,免了任务表/临时文件/轮询(K1a 派单书:引擎
幂等)。K2 的 PDF 出口带 `lang` 语种参数(同 accounting_books_routes 先例)。

全组挂 feature flag `pearnly_ai_m1`(闸关 → 404 fail-closed,同 workorder_routes 先例)。
权限复用 `tax.filing.view`——文件转换是会计工作台工具,权限边界与查看申报工单一致,
不为它新开一个维度(同 client_pool_routes 复用同一码的先例)。
"""

from __future__ import annotations

import io
import logging
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

from core.route_helpers import authorize_pearnly_ai, content_disposition, lang_or_default
from services.billing import account_status
from services.fileconv import pdf_out
from services.fileconv.convert import convert_image, convert_pdf
from services.fileconv.excel_in import convert_excel
from services.fileconv.model import ConvertResult, Issue, STATUS_OK
from services.fileconv.xlsx_out import build_xlsx

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fileconv", tags=["fileconv"])

_PERM = "tax.filing.view"
_MAX_BYTES = 20 * 1024 * 1024
_ISSUES_PREVIEW = 50
_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_PDF_MEDIA_TYPE = "application/pdf"
# 图片扩展白名单:扫描件走 OCR(K1c);Excel/CSV 走 K2;带文字层 PDF(默认)走纯函数路。
_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
_EXCEL_EXTS = (".xlsx", ".xlsm", ".xls", ".csv")


def _ext(filename: str) -> str:
    return ("." + (filename or "").lower().rsplit(".", 1)[-1]) if "." in (filename or "") else ""


def _gate_units(data: bytes, filename: str):
    """预检估价单位:(pdf_units, excel_chars)。

    PDF 按物理页数(count_pdf_pages 便宜读数 · 读不出按 1)· 图片按 1 页 · Excel/CSV 按
    字符折算。估值口径 = 转换前文本量,与转换后的实际页数可能有小偏差;预检从宽。
    """
    from core import db as _db_chg
    from services.ocr.pdf_utils import count_pdf_pages as _count_pages

    ext = _ext(filename)
    if ext in _EXCEL_EXTS:
        return 0, int(_db_chg._excel_char_count_estimate(data, filename) or 0)
    if ext in _IMAGE_EXTS:
        return 1, 0
    return max(1, int(_count_pages(data) or 0)), 0


def _fileconv_billing_gate(user: dict, tenant_id: str, data: bytes, filename: str) -> dict:
    """余额闸(拦在模型花钱之前):余额 ≤ 0 或不足以覆盖预估 → 402 同对账形状。

    查不出计费状态 → 503(fail-closed,与全站计费闸同一判据,见 account_status)。
    返回 billing dict(含 is_exempt)供转换后扣费判断复用。
    """
    from core import db as _db_gate

    billing = _db_gate.get_billing_status_combined(str(user.get("id")), tenant_id)
    if account_status.lookup_failed(billing):
        raise HTTPException(503, detail={"code": account_status.LOOKUP_ERROR})
    if billing.get("is_exempt"):
        return billing
    pdf_units, excel_chars = _gate_units(data, filename)
    if not account_status.can_cover_estimate(billing, pdf_units, excel_chars):
        est_cost = float(
            _db_gate.estimate_recon_cost_thb(
                billing.get("pages_used_this_month", 0), pdf_units, excel_chars
            )
        )
        raise HTTPException(
            402,
            detail={
                "code": "insufficient_balance",
                "balance": billing.get("balance_thb", 0.0),
                "estimated_cost": est_cost,
                "pages_used_this_month": billing.get("pages_used_this_month", 0),
            },
        )
    return billing


def _conversion_charge_units(result: ConvertResult, data: bytes, filename: str):
    """转换成功后的扣费单位 (kind, units, description)。

    与对账处同参数形状:PDF/图片按页(kind="pdf" · 页数从转换结果 stats.pages 取,OCR 路
    真实页数 · 文字层路退回物理页数)· Excel/CSV 按字符(kind="excel")。
    """
    from core import db as _db_chg
    from services.ocr.pdf_utils import count_pdf_pages as _count_pages

    if _ext(filename) in _EXCEL_EXTS:
        units = int(_db_chg._excel_char_count_estimate(data, filename) or 0)
        return "excel", units, f"文件转换 Excel · {units} 字符"
    pages = int((result.stats or {}).get("pages") or 0)
    if pages <= 0:
        pages = max(1, int(_count_pages(data) or 0))
    return "pdf", pages, f"文件转换 PDF · {pages} 页"


def _run_conversion(data: bytes, filename: str, tenant_id: str) -> ConvertResult:
    """按文件类型分流:图片 → OCR 桥;Excel/CSV → K2;PDF(默认)→ 文字层引擎
    (无文字层内部再转 OCR)。"""
    name = (filename or "").lower()
    if name.endswith(_IMAGE_EXTS):
        return convert_image(data, source_name=filename or "upload.png", tenant_id=tenant_id)
    if name.endswith(_EXCEL_EXTS):
        return convert_excel(data, source_name=filename or "upload.xlsx")
    return convert_pdf(data, source_name=filename or "upload.pdf", tenant_id=tenant_id)


def _issue_out(issue: Issue) -> dict:
    return {
        "kind": issue.kind,
        "line_no": issue.line_no,
        "account": issue.account,
        "message": issue.message,
        "expected": issue.expected,
        "actual": issue.actual,
    }


def _safe_stem(source_name: str) -> str:
    stem = (source_name or "convert").rsplit(".", 1)[0] or "convert"
    return "".join(c if c not in '/\\:*?"<>|' else "_" for c in stem)


def _xlsx_filename(source_name: str) -> str:
    return f"{_safe_stem(source_name)}.xlsx"


def _pdf_filename(source_name: str) -> str:
    return f"{_safe_stem(source_name)}.pdf"


@router.post("/convert")
async def convert_endpoint(
    request: Request,
    file: UploadFile = File(...),
    fmt: str = Query(None, alias="format", description="留空=JSON 摘要;xlsx/pdf=直接回附件"),
    lang: Optional[str] = Query(None, description="仅 format=pdf 用;缺省 th"),
):
    """上传单份 PDF/图片/Excel → 转换 + 守恒校验。`?format=xlsx` 回 xlsx 附件,
    `?format=pdf` 回 K2 规范排版 PDF 附件(泰文文件名走 RFC 5987)。"""
    user, tenant_id = authorize_pearnly_ai(request, _PERM, not_found="fileconv.not_found")

    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(413, detail="fileconv.file_too_large")
    if not data:
        raise HTTPException(400, detail="fileconv.empty_file")

    # 余额闸(拦在模型花钱之前):负余额 / 不够付预估 → 402 同对账形状(前端失败卡据此出
    # 「去充值」)· 查不出计费状态 → 503(fail-closed)。此前 fileconv 全程无闸:负余额账号
    # 照跑、烧我方 Gemini、用户 0 扣费(生产实锤 2026-08-12)。
    billing = _fileconv_billing_gate(user, tenant_id, data, file.filename)

    result = _run_conversion(data, file.filename, tenant_id)

    # 转换成功后按同口径计费(豁免不扣 · fire-and-forget 与对账一致):PDF/图片按页 ·
    # Excel/CSV 按字符。拒绝件(OCR 读不出等)不收钱,同「失败不收钱」全站口径。
    if not billing.get("is_exempt") and result.status == STATUS_OK:
        import asyncio

        from core import db as _db_chg

        _kind, _units, _desc = _conversion_charge_units(result, data, file.filename)
        if _units > 0:
            asyncio.create_task(
                asyncio.to_thread(
                    _db_chg.charge_ocr_async,
                    str(user.get("id")),
                    tenant_id,
                    _kind,
                    _units,
                    None,
                    _desc,
                )
            )

    if fmt == "xlsx":
        xlsx_bytes = build_xlsx(result)
        return StreamingResponse(
            io.BytesIO(xlsx_bytes),
            media_type=_XLSX_MEDIA_TYPE,
            headers={
                "Content-Disposition": content_disposition(
                    _xlsx_filename(file.filename), "convert.xlsx"
                )
            },
        )

    if fmt == "pdf":
        pdf_bytes = pdf_out.render(result, lang=lang_or_default(lang))
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type=_PDF_MEDIA_TYPE,
            headers={
                "Content-Disposition": content_disposition(
                    _pdf_filename(file.filename), "convert.pdf"
                )
            },
        )

    logger.info(
        f"[fileconv] {file.filename} doc_type={result.doc_type} status={result.status} "
        f"conserved={result.conserved} issues={len(result.issues)}"
    )
    return {
        "doc_type": result.doc_type,
        "status": result.status,
        "conserved": result.conserved,
        "stats": result.stats,
        "issue_count": len(result.issues),
        "issues": [_issue_out(i) for i in result.issues[:_ISSUES_PREVIEW]],
    }
