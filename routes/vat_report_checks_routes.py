# -*- coding: utf-8 -*-
"""销项税报告三查(连号/买家分组/期间一致性)上传端点 · N1-a。"""

import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from services.vat.vat_excel_helpers import _require_user, _user_key
from services.vat.vat_report_checks import run_report_checks, to_jsonable
from services.vat.vat_report_parser import parse_vat_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vat_report_checks", tags=["vat-report-checks"])

# 上传封顶,与工单收料同口径(routes/workorder_routes._MAX_MATERIAL_BYTES = 20MB):销项报告
# 是单份 PDF/Excel,远小于此;封顶防超大文件整读进内存打爆(此前 report.read() 无上限)。
_MAX_REPORT_BYTES = 20 * 1024 * 1024


@router.post("/run")
async def run_report_checks_endpoint(request: Request, report: UploadFile = File(...)):
    """上传单份销项 VAT 报告 → 解析 → 三查(连号/买家分组/期间)→ JSON。"""
    user = _require_user(request)
    api_key = _user_key(user)

    # 封顶读法:最多读上限+1 字节,超限即 413,不把超大文件整读进内存。
    file_bytes = await report.read(_MAX_REPORT_BYTES + 1)
    if len(file_bytes) > _MAX_REPORT_BYTES:
        raise HTTPException(413, "报告文件过大 · 单文件不超过 20MB")
    parsed = parse_vat_report(file_bytes, report.filename or "report.pdf", api_key=api_key)
    if not parsed.get("ok"):
        raise HTTPException(422, parsed.get("error") or "报告解析失败")

    rows = parsed.get("rows") or []
    if not rows:
        raise HTTPException(422, "报告解析结果为空 · 请检查文件")

    result = run_report_checks(rows)
    logger.info(
        f"[vat_report_checks] rows={len(rows)} "
        f"buyers={len(result['buyer_summary']['buyers'])} "
        f"families={len(result['sequence']['families'])}"
    )
    return to_jsonable(result)
