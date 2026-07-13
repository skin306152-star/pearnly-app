# -*- coding: utf-8 -*-
"""Pearnly AI · 月度报表(BS/PL/TB)打印级 PDF / Excel 下载(N1 · 导航三门 P0-3)。

拆成独立文件是 routes/workorder_routes.py 单文件<500 行铁律已在预算线上(见该文件
顶注);鉴权/归属校验复用它已有的 _authorize/_load_order/_C_VIEW/_client_name_for_order
(同一份判定,不重抄第二套)。

数据源:services/workorder/api.py::order_detail() 已经算好并对工单详情页暴露的
financials 字段(reconcile R6 的只读投影)——本路由不重算一个钱字段,不落任何新文件,
每次请求现场渲染(与工单详情页看到的数字同一份只读投影,不会"页面一个数、下载又一个数")。
表结构适配在 services/reports/financials_pdf.py,渲染引擎复用 K2 的
services.fileconv.pdf_out/xlsx_out(只调用,不改引擎——本文件里唯一确需的小改已收在
services/fileconv/model.py 新增 FINANCIALS_REPORT 常量 + pdf_out.py 的 stamp/title 映射,
理由见两处顶注)。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from core import db
from core.route_helpers import content_disposition
from routes.workorder_routes import _C_VIEW, _authorize, _client_name_for_order, _load_order
from services.fileconv import pdf_out, xlsx_out
from services.reports.financials_pdf import FILE_LABEL, build_financials_convert_result
from services.workorder import api

router = APIRouter()


@router.get("/api/workorder/orders/{work_order_id}/financials/download")
async def download_financials_report(
    work_order_id: str, request: Request, format: str = "pdf", lang: str = "th"
):
    """月度报表打印级 PDF / Excel。format=pdf|xlsx,lang 走当前 UI 语种(缺省 th,同
    fileconv_routes 的 _lang() 兜底口径)。"""
    if format not in ("pdf", "xlsx"):
        raise HTTPException(422, detail="workorder.financials_bad_format")
    user, tenant_id = _authorize(request, _C_VIEW)
    with db.get_cursor() as cur:
        wo = _load_order(cur, request, user, tenant_id, work_order_id)
        detail = api.order_detail(cur, tenant_id=tenant_id, work_order_id=work_order_id)
        client_name = _client_name_for_order(
            cur,
            tenant_id=tenant_id,
            user_id=str(user["id"]),
            workspace_client_id=wo["workspace_client_id"],
        )
    fin = (detail or {}).get("financials")
    if not fin:
        raise HTTPException(404, detail="workorder.financials_not_available")
    period = wo.get("period") or ""
    source_name = f"{client_name} {period}".strip() if client_name else period
    result = build_financials_convert_result(fin, period=period, source_name=source_name, lang=lang)
    if format == "pdf":
        content = pdf_out.render(result, lang=lang)
        media_type = "application/pdf"
        ext = ".pdf"
    else:
        content = xlsx_out.build_xlsx(result)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = ".xlsx"
    display_name = (
        f"{client_name}_{period}_{FILE_LABEL['th']}{ext}"
        if client_name
        else f"financials_{period}{ext}"
    )
    fallback_name = f"financials_{work_order_id}{ext}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": content_disposition(display_name, fallback_name)},
    )
