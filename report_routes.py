# -*- coding: utf-8 -*-
"""
Mr.Pilot · v109.0 报表路由
==========================
4 个新路由(全部走统一 report_engine):
  GET  /api/reports/templates                  · 模板列表(给前端弹窗)
  POST /api/reports/export                     · 通用导出(任意 records 数组)
  GET  /api/reports/clients/{client_id}/export · 客户报表导出
  POST /api/reports/history/batch_export       · 单据记录批量导出

老路由 /api/ocr/export 和 /api/clients/{id}/export 在 app.py 内部改写
(本文件不重定义 · 避免冲突)。
"""

import io
import logging
import traceback
from typing import List, Optional, Any, Dict
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from report_engine import build_report, list_templates, default_filename, REPORT_TEMPLATES
from i18n_reports import i18n_get

# 复用 app.py 里的依赖(导入时会用到 · 避免循环 import 用 lazy import)

logger = logging.getLogger("mrpilot.reports")

router = APIRouter(prefix="/api/reports", tags=["reports-v109"])


# ============================================================
# Pydantic 模型(v1 兼容)
# ============================================================
class ExportRequest(BaseModel):
    template: str = "standard"
    lang: str = "zh"
    records: List[Dict[str, Any]] = []
    meta: Optional[Dict[str, Any]] = None


class HistoryBatchExportRequest(BaseModel):
    history_ids: List[str] = []
    template: str = "standard"
    lang: str = "zh"
    client_id: Optional[int] = None  # 可选 · 用于元信息


# ============================================================
# 工具:从 app.py 拉同步认证函数(避免循环 import)
# ============================================================
def _get_user(request: Request):
    """取当前用户 · 失败抛 401"""
    try:
        # lazy import · 避免循环
        from auth import get_current_user_from_request

        user = get_current_user_from_request(request)  # 注意:同步函数 · 不要 await
        if not user:
            raise HTTPException(status_code=401, detail="未登录或 token 失效")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"_get_user failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=401, detail=f"认证失败: {e}")


def _safe_filename(name: str) -> str:
    """RFC 5987 编码文件名 · 兼容中泰文(v108.3 学到的)"""
    # 防御性处理
    if not name:
        name = "report.xlsx"
    return f"attachment; filename=\"report.xlsx\"; filename*=UTF-8''{quote(name, safe='')}"


def _xlsx_response(data: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": _safe_filename(filename),
            "X-Report-Engine": "v109.0",
        },
    )


def _period_label(month: Optional[str], lang: str) -> str:
    """生成期间标签 · month=YYYY-MM | all | None"""
    if not month or month == "all":
        return i18n_get(lang, "month-all")
    return month


# ============================================================
# 路由 1 · 模板列表
# ============================================================
@router.get("/templates")
def get_templates(request: Request, lang: str = Query("zh", regex="^(zh|th|en|ja)$")):
    """前端模板选择弹窗用 · 返回 4 个内置模板 · 已根据 lang 翻译"""
    try:
        user = _get_user(request)  # 仅校验登录 · 不限权限
        templates = list_templates(lang)
        return {"ok": True, "templates": templates, "default": "input_vat"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_templates: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"模板列表失败: {e}")


# ============================================================
# 路由 2 · 通用导出(识别中心 / 内部用)
# ============================================================
@router.post("/export")
def export_records(req: ExportRequest, request: Request):
    """
    通用导出:前端把任意 records 数组传过来
    用于识别中心识别完后的导出
    """
    try:
        user = _get_user(request)

        if req.template not in REPORT_TEMPLATES:
            raise HTTPException(status_code=400, detail=f"未知模板: {req.template}")
        if not req.records:
            raise HTTPException(status_code=400, detail="无数据可导出")
        if req.lang not in ("zh", "th", "en", "ja"):
            req.lang = "zh"

        meta = dict(req.meta or {})
        if "doc_count" not in meta:
            meta["doc_count"] = len(req.records)
        if "period_label" not in meta:
            meta["period_label"] = i18n_get(req.lang, "month-all")
        if "client_name" not in meta:
            meta["client_name"] = i18n_get(req.lang, "client-default")

        data = build_report(req.template, req.records, meta, req.lang)
        fname = default_filename(
            req.template, meta.get("client_name", ""), meta.get("period_label", "")
        )
        return _xlsx_response(data, fname)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"export_records: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导出失败: {e}")


# ============================================================
# 路由 3 · 客户报表导出(替代 v107.3 的老路由)
# ============================================================
@router.get("/clients/{client_id}/export")
def export_client_report(
    client_id: int,
    request: Request,
    template: str = Query("input_vat", regex="^(input_vat|standard|erp|print)$"),
    lang: str = Query("zh", regex="^(zh|th|en|ja)$"),
    month: str = Query("all"),  # YYYY-MM 或 all
):
    """
    客户管理 → 导出客户当月/全部报表
    替代 /api/clients/{id}/export 的老 CSV 实现
    """
    try:
        user = _get_user(request)
        user_id = user.get("id")

        # lazy import db(用 db.py 真实函数名)
        import db as _db

        client = _db.get_client(user_id, client_id)
        if not client:
            raise HTTPException(status_code=404, detail=f"客户不存在: id={client_id}")

        # 拉用户全部历史 · 内存过滤 client_id + month
        all_rows = _db.list_ocr_history(user_id, limit=10000, offset=0) or []
        # list_ocr_history 可能返回 dict {records, total} 或纯 list · 兼容
        if isinstance(all_rows, dict):
            all_rows = all_rows.get("records") or all_rows.get("items") or []

        # 过滤 client_id
        rows = [r for r in all_rows if (r.get("client_id") == client_id)]

        # 过滤月份(YYYY-MM)
        if month and month != "all":

            def _match_month(r):
                d = r.get("invoice_date") or r.get("created_at") or ""
                d_str = str(d)[:7] if d else ""
                return d_str == month

            rows = [r for r in rows if _match_month(r)]

        if not rows:
            raise HTTPException(status_code=404, detail="该客户在所选期间内没有发票")

        meta = {
            "client_name": client.get("name") or "",
            "client_tax_id": client.get("tax_id") or "",
            "client_branch": client.get("branch") or "",
            "period_label": _period_label(month, lang),
            "doc_count": len(rows),
        }
        data = build_report(template, rows, meta, lang)
        fname = default_filename(
            template, client.get("name") or "", month if month != "all" else ""
        )
        return _xlsx_response(data, fname)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"export_client_report client={client_id}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"客户导出失败: {e}")


# ============================================================
# 路由 4 · 单据记录批量导出
# ============================================================
@router.post("/history/batch_export")
def batch_export_history(req: HistoryBatchExportRequest, request: Request):
    """
    单据记录页 · 多选后批量导出
    """
    try:
        user = _get_user(request)
        user_id = user.get("id")

        if not req.history_ids:
            raise HTTPException(status_code=400, detail="未选择任何记录")
        if req.template not in REPORT_TEMPLATES:
            raise HTTPException(status_code=400, detail=f"未知模板: {req.template}")
        if req.lang not in ("zh", "th", "en", "ja"):
            req.lang = "zh"

        # lazy import db
        import db as _db

        # 用 get_ocr_history_detail 单条拉 · 保证只查到自己的记录(内置 user_id 校验)
        rows = []
        for hid in req.history_ids:
            try:
                r = _db.get_ocr_history_detail(user_id, str(hid))
                if r:
                    rows.append(r)
            except Exception as one_e:
                logger.warning(f"batch_export skip {hid}: {one_e}")

        if not rows:
            raise HTTPException(status_code=404, detail="选中的记录不存在或无权限")

        meta: Dict[str, Any] = {
            "client_name": i18n_get(req.lang, "client-default"),
            "period_label": i18n_get(req.lang, "month-all"),
            "doc_count": len(rows),
        }
        # 可选:若传了 client_id 则查客户名
        if req.client_id:
            try:
                c = _db.get_client(user_id, req.client_id)
                if c:
                    meta["client_name"] = c.get("name") or meta["client_name"]
                    meta["client_tax_id"] = c.get("tax_id") or ""
                    meta["client_branch"] = c.get("branch") or ""
            except Exception as e:
                logger.warning(
                    f"[report_routes] batch_export client lookup failed (client_id={req.client_id}): {e}"
                )

        data = build_report(req.template, rows, meta, req.lang)
        fname = default_filename(req.template, meta.get("client_name", ""), "")
        return _xlsx_response(data, fname)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"batch_export_history: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"批量导出失败: {e}")
