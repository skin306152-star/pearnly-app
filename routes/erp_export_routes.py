# -*- coding: utf-8 -*-
"""Pearnly · ERP 导出路由 · 下载 MR.ERP 批量导入格式的 Excel。

机器人推送(erp_push)生成同款 xlsx 并自动上传 MR.ERP;本路由把同一个生成器的
产物作为文件下载给用户——没开自动推送 / 不想把 MR.ERP 密码交给系统的用户,可下载
后自己登录 MR.ERP 的批量导入页上传。只读、不连 MR.ERP、不需凭据,故权限沿用推送的
_check_push_access(能推就能导)。
"""

from __future__ import annotations

import logging
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request, Response

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _tid
from routes.erp_routes_access import _check_push_access
from services.erp import mrerp_xlsx_generator
from services.erp.erp_payload import flatten_history_for_mrerp
from services.erp.erp_push import load_mrerp_mappings

logger = logging.getLogger("mr-pilot")

router = APIRouter()

_XLSX_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/api/erp/mrerp-xlsx/{history_id}")
async def download_mrerp_xlsx(history_id: str, request: Request):
    """下载一条发票的 MR.ERP 批量导入 Excel(用户自行上传到 MR.ERP 导入页)。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    tenant_id = _tid(user)
    history = db.get_ocr_history_detail(user["id"], history_id, tenant_id=tenant_id)
    if not history:
        raise HTTPException(404, detail="erp.history_not_found")

    flat = flatten_history_for_mrerp(history)
    if tenant_id:
        flat["tenant_id"] = tenant_id
    mappings = load_mrerp_mappings(tenant_id)

    # 与机器人同一道 preflight:不合格就别产出会被 MR.ERP 拒收的坏文件,
    # 直接回错误码告诉用户缺什么(缺客户映射 / 发票号超长 / 日期未来等)。
    ok, err_code, _warnings = mrerp_xlsx_generator.validate_history_for_sales_credit(flat, mappings)
    if not ok:
        raise HTTPException(422, detail=err_code or "erp.mrerp_not_ready")

    try:
        xlsx = mrerp_xlsx_generator.generate_xlsx([flat], mappings, sheet_kind="sales_credit")
    except Exception as e:
        logger.exception("download_mrerp_xlsx: generate_xlsx failed")
        raise HTTPException(500, detail="erp.mrerp_xlsx_failed") from e

    fname = mrerp_xlsx_generator.make_filename("sales_credit", history_id)
    return Response(
        content=xlsx,
        media_type=_XLSX_CT,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(fname)}"},
    )
