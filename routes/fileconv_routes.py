# -*- coding: utf-8 -*-
"""K1b/K2 · 财务文件转换 HTTP 端点(PDF/图片/Excel → 结构化结果 / xlsx / pdf)。

无状态两段式:上传的文件直接跑 services.fileconv 对应引擎(K1a PDF 纯函数 / K1c OCR /
K2 Excel,均零服务端状态)——默认回 JSON 摘要(doc_type/status/conserved/stats/issues
前 N 条+总数),`?format=xlsx|pdf` 时把同一份上传原样再跑一次转换直接回附件。各路径
各自独立调用、互不依赖同一次请求的产物,免了任务表/临时文件/轮询(K1a 派单书:引擎
幂等)。K2 的 PDF 出口带 `lang` 语种参数(同 accounting_books_routes 先例)。

全组挂 feature flag `pearnly_ai_m1`(闸关 → 404 fail-closed,同 workorder_routes 先例)。
权限复用 `tax.filing.view`——文件转换是会计工作台工具,权限边界与查看申报工单一致,
不为它新开一个维度。
"""

from __future__ import annotations

import io
import logging
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

from core.route_helpers import authorize_pearnly_ai, content_disposition, lang_or_default
from services.billing import account_status, pricing
from services.fileconv import pdf_out
from services.fileconv.convert import convert_image, convert_pdf
from services.fileconv.excel_in import convert_excel
from services.fileconv.model import ConvertResult, Issue, STATUS_OK
from services.fileconv.xlsx_out import build_xlsx
from services.ocr.entrypoints import policy_context_from_billing
from routes.recon_routes_shared import require_coverage_or_raise

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fileconv", tags=["fileconv"])

_PERM = "tax.filing.view"
_MAX_BYTES = 20 * 1024 * 1024
_ISSUES_PREVIEW = 50
_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_PDF_MEDIA_TYPE = "application/pdf"
# 转换分流白名单:图片走 OCR(K1c);Excel/CSV 走 K2(convert_excel 支持面);带文字层
# PDF(默认)走纯函数路。计费分类不用这两组 —— 归 pricing.EXCEL_BILLING_EXTS 单源。
_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
_EXCEL_EXTS = (".xlsx", ".xlsm", ".xls", ".csv")


def _fileconv_billing_gate(user: dict, tenant_id: str, data: bytes, filename: str):
    """余额闸(拦在模型花钱之前)· 返回 (billing, gate_units)。

    余额 ≤ 0 或不足以覆盖预估 → 402 同对账形状;查不出计费状态 → 503(fail-closed,
    与全站计费闸同一判据,见 account_status)。gate_units = (pdf_units, excel_chars)
    传给扣费段复用 —— 此前 gate 与 charge 各自把整簿 Excel 逐格读一遍(一次请求解析
    3 遍)。豁免不估价(units=None,豁免也不走扣费段)。
    """
    from core import db as _db_gate

    billing = _db_gate.get_billing_status_combined(str(user.get("id")), tenant_id)
    if account_status.lookup_failed(billing):
        raise HTTPException(503, detail={"code": account_status.LOOKUP_ERROR})
    if billing.get("is_exempt"):
        return billing, None
    units = pricing.estimate_recon_units([(data, filename)])
    require_coverage_or_raise(billing, *units)
    return billing, units


def _conversion_charge_units(result: ConvertResult, gate_units, filename: str):
    """转换成功后的扣费单位 (kind, units, description) · 复用预检估价,不重读文件。

    Excel/CSV 等字符档按字符(kind="excel");其余按页(kind="pdf" · 页数优先取转换
    结果 stats.pages(OCR 路真实页数),缺了退回预检读到的物理页数)。
    """
    pdf_units, excel_chars = gate_units
    if pricing.file_ext(filename) in pricing.EXCEL_BILLING_EXTS:
        return "excel", excel_chars, f"文件转换 Excel · {excel_chars} 字符"
    pages = int((result.stats or {}).get("pages") or 0)
    if pages <= 0:
        pages = max(1, int(pdf_units))
    return "pdf", pages, f"文件转换 PDF · {pages} 页"


def _run_conversion(
    data: bytes,
    filename: str,
    tenant_id: str,
    *,
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
) -> ConvertResult:
    """按文件类型分流:图片 → OCR 桥;Excel/CSV → K2;PDF(默认)→ 文字层引擎
    (无文字层内部再转 OCR)。"""
    name = (filename or "").lower()
    if name.endswith(_IMAGE_EXTS):
        return convert_image(
            data,
            source_name=filename or "upload.png",
            tenant_id=tenant_id,
            plan_code=plan_code,
            is_exempt=is_exempt,
        )
    if name.endswith(_EXCEL_EXTS):
        return convert_excel(data, source_name=filename or "upload.xlsx")
    return convert_pdf(
        data,
        source_name=filename or "upload.pdf",
        tenant_id=tenant_id,
        plan_code=plan_code,
        is_exempt=is_exempt,
    )


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
    billing, gate_units = _fileconv_billing_gate(user, tenant_id, data, file.filename)

    result = _run_conversion(
        data,
        file.filename,
        tenant_id,
        **policy_context_from_billing(billing),
    )

    # 转换成功后按同口径计费(豁免不扣 · fire-and-forget 与对账一致):PDF/图片按页 ·
    # Excel/CSV 按字符。拒绝件(OCR 读不出等)不收钱,同「失败不收钱」全站口径。
    if not billing.get("is_exempt") and result.status == STATUS_OK:
        import asyncio

        from core import db as _db_chg

        _kind, _units, _desc = _conversion_charge_units(result, gate_units, file.filename)
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
