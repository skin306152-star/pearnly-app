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
from services.fileconv import pdf_out
from services.fileconv.convert import convert_image, convert_pdf
from services.fileconv.excel_in import convert_excel
from services.fileconv.model import ConvertResult, Issue
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
    _, tenant_id = authorize_pearnly_ai(request, _PERM, not_found="fileconv.not_found")

    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(413, detail="fileconv.file_too_large")
    if not data:
        raise HTTPException(400, detail="fileconv.empty_file")

    result = _run_conversion(data, file.filename, tenant_id)

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
