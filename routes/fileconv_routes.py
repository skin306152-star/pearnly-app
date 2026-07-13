# -*- coding: utf-8 -*-
"""K1b · 财务文件转换 HTTP 端点(PDF → 结构化结果 / xlsx)。

无状态两段式:上传的 PDF 直接跑 services.fileconv.convert.convert_pdf(K1a 引擎,纯函数
零服务端状态)——默认回 JSON 摘要(doc_type/status/conserved/stats/issues 前 N 条+总数),
`?format=xlsx` 时把同一份上传原样再跑一次转换直接回 xlsx 附件。两条路径各自独立调用、
互不依赖同一次请求的产物,免了任务表/临时文件/轮询(K1a 派单书:引擎幂等)。

全组挂 feature flag `pearnly_ai_m1`(闸关 → 404 fail-closed,同 workorder_routes 先例)。
权限复用 `tax.filing.view`——文件转换是会计工作台工具,权限边界与查看申报工单一致,
不为它新开一个维度(同 client_pool_routes 复用同一码的先例)。
"""

from __future__ import annotations

import io
import logging
from urllib.parse import quote

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

from core.route_helpers import authorize_pearnly_ai
from services.fileconv.convert import convert_image, convert_pdf
from services.fileconv.model import ConvertResult, Issue
from services.fileconv.xlsx_out import build_xlsx

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fileconv", tags=["fileconv"])

_PERM = "tax.filing.view"
_MAX_BYTES = 20 * 1024 * 1024
_ISSUES_PREVIEW = 50
_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# 图片扩展白名单:扫描件走 OCR(K1c);带文字层 PDF 走纯函数路。其余类型 415。
_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def _run_conversion(data: bytes, filename: str, tenant_id: str) -> ConvertResult:
    """按文件类型分流:图片 → OCR 桥;PDF(默认)→ 文字层引擎(无文字层内部再转 OCR)。"""
    name = (filename or "").lower()
    if name.endswith(_IMAGE_EXTS):
        return convert_image(data, source_name=filename or "upload.png", tenant_id=tenant_id)
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


def _xlsx_filename(source_name: str) -> str:
    stem = (source_name or "convert").rsplit(".", 1)[0] or "convert"
    safe = "".join(c if c not in '/\\:*?"<>|' else "_" for c in stem)
    return f"{safe}.xlsx"


def _content_disposition(filename: str) -> str:
    """泰文原名走 RFC 5987 filename*(HTTP 头只认 latin-1,裸塞泰文会 500),
    ASCII 兜底名给不认 filename* 的老客户端——同 vat_excel_routes 先例。"""
    encoded = quote(filename.encode("utf-8"))
    return f"attachment; filename=\"convert.xlsx\"; filename*=UTF-8''{encoded}"


@router.post("/convert")
async def convert_endpoint(
    request: Request,
    file: UploadFile = File(...),
    fmt: str = Query(None, alias="format", description="留空=JSON 摘要;xlsx=直接回附件"),
):
    """上传单份 PDF/图片 → 转换 + 守恒校验。`?format=xlsx` 回同一份文件的 xlsx 转换结果。"""
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
            headers={"Content-Disposition": _content_disposition(_xlsx_filename(file.filename))},
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
