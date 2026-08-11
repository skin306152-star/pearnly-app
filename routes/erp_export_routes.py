# -*- coding: utf-8 -*-
"""Pearnly · ERP 导出路由 · 下载 MR.ERP 批量导入格式的 Excel。

机器人推送(erp_push)生成同款 xlsx 并自动上传 MR.ERP;本路由把同一个生成器的产物
作为文件下载给用户——没开自动推送 / 不想把 MR.ERP 密码交给系统的用户,在「导出 Excel」
下拉选「MR.ERP 表格」批量下载,再自己登录 MR.ERP 的批量导入页上传。只读、不连 MR.ERP、
不需凭据,权限沿用推送的 _check_push_access(能推就能导)。
"""

from __future__ import annotations

import logging
from typing import List
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

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

# 一次导出的单据上限 · 无上限时 N 张票 = N 次单条详情查询,选中几千张能把库拖垮
MAX_BATCH_SIZE = 100


class MrerpXlsxBatchRequest(BaseModel):
    history_ids: List[str] = Field(..., min_items=1)


@router.post("/api/erp/mrerp-xlsx-batch")
async def download_mrerp_xlsx_batch(req: MrerpXlsxBatchRequest, request: Request):
    """把多张已识别发票打成一个 MR.ERP 批量导入 Excel 下载(用户自行上传 MR.ERP）。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    if len(req.history_ids) > MAX_BATCH_SIZE:
        raise HTTPException(400, detail="erp.batch_too_many")

    tenant_id = _tid(user)
    mappings = load_mrerp_mappings(tenant_id)

    # 逐张 preflight(与机器人同一道校验)· 合格的进文件,不合格的跳过并记首个错误码。
    # 全不合格 → 422 回首个错误码(缺客户映射 / 发票号超长 / 缺客户等)让用户知道要补什么。
    details = db.get_ocr_history_details_bulk(user["id"], req.history_ids, tenant_id=tenant_id)
    valid = []
    first_err = None
    for hid in req.history_ids:
        history = details.get(str(hid))
        if not history:
            continue
        flat = flatten_history_for_mrerp(history)
        if tenant_id:
            flat["tenant_id"] = tenant_id
        ok, err_code, _warnings = mrerp_xlsx_generator.validate_history_for_sales_credit(
            flat, mappings
        )
        if ok:
            valid.append(flat)
        elif first_err is None:
            first_err = err_code

    if not valid:
        raise HTTPException(422, detail=first_err or "erp.mrerp_not_ready")

    try:
        xlsx = mrerp_xlsx_generator.generate_xlsx(valid, mappings, sheet_kind="sales_credit")
    except Exception as e:
        logger.exception("download_mrerp_xlsx_batch: generate_xlsx failed")
        raise HTTPException(500, detail="erp.mrerp_xlsx_failed") from e

    fname = mrerp_xlsx_generator.make_filename("sales_credit", req.history_ids[0])
    return Response(
        content=xlsx,
        media_type=_XLSX_CT,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(fname)}"},
    )
