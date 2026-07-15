# -*- coding: utf-8 -*-
"""Pearnly AI · 工单交付物 / 月度报表下载(N1 · 导航三门 P0-3 + M1-B1 交付包)。

拆成独立文件是 routes/workorder_routes.py 单文件<500 行铁律已在预算线上(见该文件
顶注);鉴权/归属校验复用它已有的 _authorize/_load_order/_C_VIEW/_client_name_for_order
(同一份判定,不重抄第二套)。2026-07 再拆一轮时把"交付物清单 + 交付物下载"两个端点
也并进本文件(而非另起新文件)——同属"下载已生成产物"这一类,与月度报表下载语义同构,
鉴权/客户名解析已经共用一套。

## 月度报表(BS/PL/TB)PDF/Excel

数据源:services/workorder/api.py::order_detail() 已经算好并对工单详情页暴露的
financials 字段(reconcile R6 的只读投影)——本路由不重算一个钱字段,不落任何新文件,
每次请求现场渲染(与工单详情页看到的数字同一份只读投影,不会"页面一个数、下载又一个数")。
表结构适配在 services/reports/financials_pdf.py,渲染引擎复用 K2 的
services.fileconv.pdf_out/xlsx_out(只调用,不改引擎——本文件里唯一确需的小改已收在
services/fileconv/model.py 新增 FINANCIALS_REPORT 常量 + pdf_out.py 的 stamp/title 映射,
理由见两处顶注)。

## 交付物清单 / 下载

N1-P1-6:交付文件名 "{客户名}_{账期}_{报表名}.{ext}"——RFC 5987 helper 已在
core.route_helpers,交付物 kind → 人读短名(泰文,与内部 markdown 标题呼应,不直出
内部 kind 字面量 pp30_draft.md 这种开发者黑话)。月度报表下载(/financials/download)
虽走独立端点不查交付物表,文件名同样经 _deliverable_download_name 拼(单源)。
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from core import db
from core.route_helpers import content_disposition, lang_or_default
from routes.workorder_routes import _C_VIEW, _authorize, _client_name_for_order, _load_order
from services.accounting import bridge_store
from services.audit import file_access as audit_file_access
from services.fileconv import pdf_out, xlsx_out
from services.reports.financials_pdf import build_financials_convert_result
from services.workorder import api, entries_export, storage, store

router = APIRouter()

# 键二导出翻码固定按 Express 桥(coa_erp_bridge · erp_type='express')。MR.ERP 分录导出桥
# 就绪但语料未到,不在此列(方案「不做」节)——按钮语义单指 Express,不给一个选而无实的 erp_type。
_EXPRESS_ERP_TYPE = "express"

_DELIVERABLE_LABEL_TH = {
    "pp30_draft": "แบบร่าง ภ.พ.30",
    "ledger_workpaper": "ใบงานประกอบบัญชี",
    "bank_workpaper": "เอกสารธนาคาร",
    "missing_doc_memo": "บันทึกเอกสารที่ขาด",
    "evidence_index": "ดัชนีหลักฐาน",
    "financials_report": "งบการเงิน",
    "shadow_workpaper": "ใบงานร่างบัญชีคู่",
    "entries_export": "รายการบัญชี Express",
}


def _deliverable_download_name(kind: str, path_name: str, *, client_name: str, period: str) -> str:
    """交付物下载文件名:能定位到客户名就拼"{客户名}_{账期}_{报表名}.{ext}",定位不到
    (客户查询失败等边缘情形)诚实退回落盘原名,不硬凑一个可能张冠李戴的名字。"""
    if not client_name:
        return path_name
    label = _DELIVERABLE_LABEL_TH.get(kind, kind)
    ext = Path(path_name).suffix or ".md"
    return f"{client_name}_{period or ''}_{label}{ext}"


@router.get("/api/workorder/orders/{work_order_id}/deliverables")
async def list_order_deliverables(work_order_id: str, request: Request):
    """交付物清单(kind + 关键数字 + 是否有可下载文件)。"""
    user, tenant_id = _authorize(request, _C_VIEW)
    with db.get_cursor() as cur:
        _load_order(cur, request, user, tenant_id, work_order_id)
        return {
            "deliverables": api.list_deliverables(
                cur, tenant_id=tenant_id, work_order_id=work_order_id
            )
        }


@router.get("/api/workorder/orders/{work_order_id}/deliverables/{kind}")
async def download_deliverable(work_order_id: str, kind: str, request: Request):
    """下载单个交付物文件。只放行库里登记过的 artifact_path,再做工单目录内含校验(防穿越)。

    N1-P1-6:文件名从落盘内部名(如 pp30_draft.md)换成"客户名_账期_报表名"——归档/转发
    给客户时不用手改文件名;取不到客户名(边缘态)诚实退回原名,不拼假名字。"""
    user, tenant_id = _authorize(request, _C_VIEW)
    with db.get_cursor() as cur:
        wo = _load_order(cur, request, user, tenant_id, work_order_id)
        artifact = api.deliverable_artifact_path(
            cur, tenant_id=tenant_id, work_order_id=work_order_id, kind=kind
        )
        client_name = _client_name_for_order(
            cur,
            tenant_id=tenant_id,
            user_id=str(user["id"]),
            workspace_client_id=wo["workspace_client_id"],
        )
    if not artifact:
        raise HTTPException(404, detail="workorder.deliverable_not_found")
    path = storage.resolve_within_order(tenant_id, work_order_id, artifact)
    if not path:
        raise HTTPException(404, detail="workorder.deliverable_not_found")
    download_name = _deliverable_download_name(
        kind, path.name, client_name=client_name, period=wo.get("period") or ""
    )
    # 落盘密文经 storage.read_bytes 解回明文再出流(FileResponse 会直吐密文,故换 Response)。
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    content = storage.read_bytes(path)
    audit_file_access.log_user_file_access(
        request,
        user,
        audit_file_access.DELIVERABLE_DOWNLOADED,
        target_type="deliverable",
        target_id=kind,
        details={"kind": kind, "ref": artifact, "work_order_id": work_order_id},
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": content_disposition(download_name, path.name)},
    )


@router.get("/api/workorder/orders/{work_order_id}/financials/download")
async def download_financials_report(
    work_order_id: str, request: Request, format: str = "pdf", lang: str = "th"
):
    """月度报表打印级 PDF / Excel。format=pdf|xlsx,lang 走当前 UI 语种(lang_or_default
    四语白名单兜底 th,同 fileconv_routes 口径)。"""
    if format not in ("pdf", "xlsx"):
        raise HTTPException(422, detail="workorder.financials_bad_format")
    lang = lang_or_default(lang)
    user, tenant_id = _authorize(request, _C_VIEW)
    with db.get_cursor() as cur:
        wo = _load_order(cur, request, user, tenant_id, work_order_id)
        fin = api.financials_projection(cur, tenant_id=tenant_id, work_order_id=work_order_id)
        client_name = _client_name_for_order(
            cur,
            tenant_id=tenant_id,
            user_id=str(user["id"]),
            workspace_client_id=wo["workspace_client_id"],
        )
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
    display_name = _deliverable_download_name(
        "financials_report", f"financials_{period}{ext}", client_name=client_name, period=period
    )
    fallback_name = f"financials_{work_order_id}{ext}"
    audit_file_access.log_user_file_access(
        request,
        user,
        audit_file_access.DELIVERABLE_DOWNLOADED,
        target_type="deliverable",
        target_id="financials_report",
        details={"kind": "financials_report", "format": format, "work_order_id": work_order_id},
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": content_disposition(display_name, fallback_name)},
    )


@router.get("/api/workorder/orders/{work_order_id}/entries-export")
async def export_entries(work_order_id: str, request: Request):
    """影子分录导出 Express xlsx(M1-3KEY 键二 · 只读派生)。事件回放取 gates.r5_shadow(不
    重算不落库),coa 码经 coa_erp_bridge(express)翻 Express 码——桥缺码留空 + 标 unmapped,
    禁臆造。冻结单可导(读侧派生,故走 _load_order 不走只读闸)。无影子分录 → 404
    workorder.no_shadow_entries(前端按钮 disabled + 人话)。"""
    user, tenant_id = _authorize(request, _C_VIEW)
    with db.get_cursor() as cur:
        wo = _load_order(cur, request, user, tenant_id, work_order_id)
        ws_id = wo["workspace_client_id"]
        events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
        shadow = api.shadow_draft(events)  # events→dict 只读投影(同 order_detail,不重算)
        bridge = bridge_store.load_bridge(
            cur, tenant_id=tenant_id, workspace_client_id=ws_id, erp_type=_EXPRESS_ERP_TYPE
        )
        erp_types = bridge_store.list_erp_types(cur, tenant_id=tenant_id, workspace_client_id=ws_id)
        client_name = _client_name_for_order(
            cur, tenant_id=tenant_id, user_id=str(user["id"]), workspace_client_id=ws_id
        )
    if not shadow or not shadow.get("entries"):
        raise HTTPException(404, detail="workorder.no_shadow_entries")
    period = wo.get("period") or ""
    content = entries_export.build_entries_xlsx(
        shadow,
        bridge,
        bridge_configured=_EXPRESS_ERP_TYPE in erp_types,
        period=period,
        client_name=client_name,
    )
    display_name = _deliverable_download_name(
        "entries_export", f"entries_{period}.xlsx", client_name=client_name, period=period
    )
    fallback_name = f"entries_{work_order_id}.xlsx"
    audit_file_access.log_user_file_access(
        request,
        user,
        audit_file_access.DELIVERABLE_DOWNLOADED,
        target_type="deliverable",
        target_id="entries_export",
        details={"kind": "entries_export", "work_order_id": work_order_id},
    )
    return Response(
        content=content,
        media_type=entries_export.XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": content_disposition(display_name, fallback_name)},
    )
