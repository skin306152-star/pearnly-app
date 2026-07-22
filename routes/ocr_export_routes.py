"""
ocr_export_routes.py · OCR 配额查询 + 模板导出(REFACTOR-B1)

从 app.py 抽出 4 路由 + 3 Pydantic 模型 + 1 helper · 0 业务逻辑改:
    GET  /api/ocr/quota                 v0 OCR 配额查询(QuotaResponse)
    POST /api/ocr/export                v0 records → standard / sales_detail_th 模板导出
    POST /api/ocr/export-by-history-ids history_ids → 合并 pages → sales_detail_th 模板
    POST /api/v1/ocr/export             v1 alias · 转发 v0 ocr_export

E2E 闸:spec 16(OCR 真识别)间接 · 配额读取 + 导出走相同 _plan_permissions 链。
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _plan_permissions

logger = logging.getLogger(__name__)

router = APIRouter()


class QuotaResponse(BaseModel):
    plan: str
    ip_used_today: Optional[int] = None
    ip_daily_limit: Optional[int] = None
    monthly_quota: Optional[int] = None
    used_this_month: Optional[int] = None
    max_pages_per_upload: int
    max_file_size_mb: int


class ExportRequest(BaseModel):
    records: List[Any]
    lang: str = Field("zh", pattern="^(zh|en|th|ja)$")
    template: str = Field("standard")


# v118.27.7 · 让 sales_detail_th 也能从单据记录批量入口用
class ExportByHistoryIdsRequest(BaseModel):
    history_ids: List[str]
    lang: str = Field("zh", pattern="^(zh|en|th|ja)$")
    template: str = Field("sales_detail_th")
    client_id: Optional[Any] = None  # 接受 int / str / null · 兼容前端


@router.get("/api/ocr/quota", response_model=QuotaResponse)
async def get_quota(request: Request):
    user = get_current_user_from_request(request)
    # v118.11 · plan=NULL 防御兜底 · 同 _build_user_info
    plan = user.get("plan") or "free"
    p_perms = _plan_permissions(plan)
    monthly_quota = p_perms.get("monthly_quota")
    used_this_month = int(user.get("used_this_month") or 0) if monthly_quota is not None else None

    return QuotaResponse(
        plan=plan,
        ip_used_today=None,
        ip_daily_limit=None,
        monthly_quota=monthly_quota,
        used_this_month=used_this_month,
        max_pages_per_upload=p_perms["max_pages_per_upload"],
        max_file_size_mb=p_perms["max_file_size_mb"],
    )


def _enrich_records_by_invoice_no(records: List[Any], user: dict) -> None:
    """销售明细导出填「新建/复用」动作(向导内路 · 按 merged_fields.invoice_number 回查推送日志)。
    回查失败/无匹配一律静默降级(模板留 '-'),绝不阻断导出。"""
    try:
        from services.erp.export_actions import (
            apply_erp_actions,
            erp_actions_by_invoice_nos,
        )

        user_id = str(user.get("id"))
        tenant_id = user.get("tenant_id")
        tenant_id = str(tenant_id) if tenant_id else None
        nos = []
        for rec in records or []:
            mf = rec.get("merged_fields") if isinstance(rec, dict) else None
            if isinstance(mf, dict):
                no = str(mf.get("invoice_number") or "").strip()
                if no:
                    nos.append(no)
        if not nos:
            return
        actions = erp_actions_by_invoice_nos(user_id, nos, tenant_id)
        if not actions:
            return
        for rec in records or []:
            mf = rec.get("merged_fields") if isinstance(rec, dict) else None
            if isinstance(mf, dict):
                apply_erp_actions(mf, actions.get(str(mf.get("invoice_number") or "").strip()))
    except Exception as e:
        logger.warning(f"enrich records by invoice_no failed: {e}")


def _enrich_records_by_history_id(
    records: List[dict], hids: List[str], user_id: str, tenant_id: Optional[str]
) -> None:
    """销售明细导出填「新建/复用」动作(单据记录批量路 · 按 history_id 回查)。records 与 hids 同序。
    回查失败/无匹配一律静默降级,绝不阻断导出。"""
    try:
        from services.erp.export_actions import (
            apply_erp_actions,
            erp_actions_by_history_ids,
        )

        actions = erp_actions_by_history_ids(user_id, hids, tenant_id)
        if not actions:
            return
        for rec, hid in zip(records, hids):
            mf = rec.get("merged_fields") if isinstance(rec, dict) else None
            if isinstance(mf, dict):
                apply_erp_actions(mf, actions.get(str(hid)))
    except Exception as e:
        logger.warning(f"enrich records by history_id failed: {e}")


@router.post("/api/ocr/export")
async def ocr_export(req: ExportRequest, request: Request):
    user = get_current_user_from_request(request)
    if not req.records:
        raise HTTPException(400, detail="export.empty_records")
    template_name = (req.template or "standard").strip()

    # v118.27.5.3 · 模板分发
    if template_name == "standard":
        try:
            from services.excel.excel_export import build_xlsx, default_filename

            xlsx_bytes = build_xlsx(req.records, lang=req.lang)
            filename = default_filename()
        except Exception as e:
            logger.exception(f"Excel(standard)生成失败: {e}")
            raise HTTPException(500, detail="export.build_failed")
    elif template_name == "sales_detail_th":
        # 泰国销售明细模板(每商品 1 行 + Excel 公式)· 跟泰国本地销售清单习惯一致
        try:
            from services.excel.excel_template_th import (
                build_sales_detail_xlsx,
                sales_detail_filename,
            )

            # 按票号回查推送「新建/复用」动作填进 records(向导内导出无 history_id · 走票号匹配)
            _enrich_records_by_invoice_no(req.records, user)
            xlsx_bytes = build_sales_detail_xlsx(req.records, lang=req.lang)
            filename = sales_detail_filename()
        except Exception as e:
            logger.exception(f"Excel(sales_detail_th)生成失败: {e}")
            raise HTTPException(500, detail="export.build_failed")
    else:
        if user["plan"] == "free" and not user.get("can_use_custom_template"):
            raise HTTPException(403, detail="export.template_locked")
        raise HTTPException(400, detail="export.template_not_supported_yet")

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Filename": filename,
        },
    )


# ============================================================
# v118.27.7 · 单据记录批量入口走 sales_detail_th 模板
# 让我手上的 excel_template_th 也能从「单据记录批量导出」用 · 真正打通系统
# 流程:history_ids → db.get_ocr_history_detail → 合并 pages → records → excel_template_th
# ============================================================
def _merge_pages_to_fields(pages) -> dict:
    """把 history.pages(多页 OCR 结果)合并成一份 merged_fields(后端版 · 跟前端 mergeFields 等价)
    策略:同 key 谁非空用谁 · items 数组直接拼接(同张发票多页明细汇总)
    """
    if not pages or not isinstance(pages, list):
        return {}
    merged: dict = {}
    items: list = []
    for p in pages:
        if not isinstance(p, dict):
            continue
        f = p.get("fields") or {}
        if not isinstance(f, dict):
            continue
        for k, v in f.items():
            if k == "items":
                if isinstance(v, list):
                    items.extend(v)
                continue
            if v in (None, "", [], {}):
                continue
            if not merged.get(k):
                merged[k] = v
    if items:
        merged["items"] = items
    return merged


@router.post("/api/ocr/export-by-history-ids")
async def ocr_export_by_history_ids(req: ExportByHistoryIdsRequest, request: Request):
    """sales_detail_th 模板从单据记录 / 客户卡片入口走的接口
    其他模板(input_vat / standard / print)继续走 reports_router 的 batch_export
    """
    user = get_current_user_from_request(request)
    if not req.history_ids:
        raise HTTPException(400, detail="export.empty_records")
    template_name = (req.template or "sales_detail_th").strip()
    if template_name != "sales_detail_th":
        raise HTTPException(400, detail="export.template_not_supported_yet")

    user_id = str(user.get("id"))
    tenant_id = user.get("tenant_id")
    tenant_id = str(tenant_id) if tenant_id else None

    records = []
    hid_by_record: List[str] = []  # 与 records 同序 · 每条对应的 history_id(回查动作用)
    for hid in req.history_ids:
        try:
            h = db.get_ocr_history_detail(user_id, str(hid), tenant_id)
            if not h:
                continue
            mf = _merge_pages_to_fields(h.get("pages") or [])
            # 用冗余字段回填(ocr_history 表里专门存了这些 · 比 pages 更稳)
            if h.get("invoice_no") and not mf.get("invoice_number"):
                mf["invoice_number"] = h.get("invoice_no")
            if h.get("invoice_date") and not mf.get("date"):
                mf["date"] = h.get("invoice_date")
            if h.get("seller_name") and not mf.get("seller_name"):
                mf["seller_name"] = h.get("seller_name")
            if h.get("total_amount") and not mf.get("total_amount"):
                mf["total_amount"] = h.get("total_amount")
            records.append(
                {
                    "filename": h.get("filename") or f"history-{hid}",
                    "engine": "",
                    "merged_fields": mf,
                }
            )
            hid_by_record.append(str(hid))
        except Exception as e:
            logger.warning(f"export-by-history-ids · history {hid} 拉取失败: {e}")
            continue

    if not records:
        raise HTTPException(404, detail="export.no_data")

    # 按 history_id 回查推送「新建/复用」动作填进 records(客户/商品状态列)
    _enrich_records_by_history_id(records, hid_by_record, user_id, tenant_id)

    try:
        from services.excel.excel_template_th import build_sales_detail_xlsx, sales_detail_filename

        xlsx_bytes = build_sales_detail_xlsx(records, lang=req.lang)
        filename = sales_detail_filename()
    except Exception as e:
        logger.exception(f"sales_detail_th 生成失败: {e}")
        raise HTTPException(500, detail="export.build_failed")

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Filename": filename,
        },
    )


@router.post("/api/v1/ocr/export")
async def v1_export(req: ExportRequest, request: Request):
    """v1 alias · 转发 v0 ocr_export"""
    return await ocr_export(req, request)
