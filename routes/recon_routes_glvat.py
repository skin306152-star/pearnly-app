# -*- coding: utf-8 -*-
"""GL vs 销项税 对账路由组（/api/recon/gl-vat/* · 含计费 gl_vat_run·铁律#26）。

recon_routes 拆分·verbatim 抽出·0 逻辑改(仅装饰器对象名)。"""

import io
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core import db
from services.authz.deps import require_perm
from services.vat.vat_report_parser import parse_vat_report
from routes.recon_routes_shared import _user_key, _pdf_billing_units
from services.recon.gl_vat_reconciler import (
    parse_gl,
    reconcile_gl_vat,
    export_gl_vat_excel,
    detail_to_json,
    summary_to_json,
    detail_from_json,
    summary_from_json,
)

logger = logging.getLogger(__name__)

glvat_router = APIRouter()


_GLV_ERR = {
    "auth_required": {
        "zh": "未登录",
        "en": "Not logged in",
        "th": "ยังไม่ได้เข้าสู่ระบบ",
        "ja": "未ログイン",
    },
    "gl_parse_failed": {
        "zh": "GL 解析失败：{e}",
        "en": "Failed to parse GL: {e}",
        "th": "อ่านไฟล์ GL ไม่สำเร็จ: {e}",
        "ja": "GL 解析失敗: {e}",
    },
    "gl_no_revenue_rows": {
        "zh": "在文件里没找到收入科目数据。请确认右侧上传的是『总账 GL』(Excel/CSV · 至少含日期/科目/借方/贷方列)· 如果你的收入科目不是 4 开头,请调右侧『收入科目前缀』",
        "en": "No revenue account rows found. Please upload a General Ledger file (Excel/CSV with Date/Account/Debit/Credit columns) · If your revenue accounts don't start with '4', adjust the 'Revenue Account Prefix' on the right",
        "th": "ไม่พบรายการบัญชีรายได้ในไฟล์ · กรุณาอัปโหลดบัญชีแยกประเภท GL (Excel/CSV ที่มีคอลัมน์ วันที่/รหัสบัญชี/เดบิต/เครดิต) · หากบัญชีรายได้ไม่ขึ้นต้นด้วย 4 ให้ปรับ 'รหัสนำหน้าบัญชีรายได้' ด้านขวา",
        "ja": "ファイルに収益科目データが見つかりません · 右側に『総勘定元帳 GL』(日付/科目/借方/貸方列のある Excel/CSV) をアップロードしてください · 収益科目が 4 以外で始まる場合は右側の『収益科目接頭辞』を変更してください",
    },
    "vat_parse_failed": {
        "zh": "销项税报告解析失败：{e}",
        "en": "Failed to parse VAT report: {e}",
        "th": "อ่านรายงานภาษีขายไม่สำเร็จ: {e}",
        "ja": "売上税報告解析失敗: {e}",
    },
    "vat_no_rows": {
        "zh": "销项税报告中未找到任何数据行",
        "en": "No data rows found in VAT report",
        "th": "ไม่พบรายการในรายงานภาษีขาย",
        "ja": "売上税報告にデータ行が見つかりません",
    },
    "task_not_found": {
        "zh": "任务不存在",
        "en": "Task not found",
        "th": "ไม่พบงาน",
        "ja": "タスクが見つかりません",
    },
}


def _glv_err(key: str, lang: str = "th", **fmt) -> str:
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    msg = (_GLV_ERR.get(key) or {}).get(lang) or _GLV_ERR.get(key, {}).get("en") or key
    return msg.format(**fmt) if fmt else msg


@glvat_router.post("/gl-vat/run")
async def gl_vat_run(
    request: Request,
    # v118.35.0.3 · 多文件 · 旧的 gl_file/vat_file 单文件字段保留兼容(老前端
    # 还在用 / 测试 fixture / 外部脚本)· 新前端发 gl_files/vat_files 列表
    gl_file: Optional[UploadFile] = File(None),
    vat_file: Optional[UploadFile] = File(None),
    gl_files: Optional[List[UploadFile]] = File(None),
    vat_files: Optional[List[UploadFile]] = File(None),
    revenue_prefix: str = Form("4"),
    lang: str = Form("th"),
):
    """
    上传 GL 总账 + 销项税报告(各支持多文件),立即跑对账。
    - gl_files / vat_files: Excel / PDF / 图片 / CSV / Word / TXT · 多份
    - 兼容旧调用方:gl_file + vat_file 单文件字段
    - revenue_prefix: 收入科目代码前缀(默认 "4")
    - lang: 错误消息语言 zh/en/th/ja
    """
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, _glv_err("auth_required", lang))

    # 合并新旧字段 · 至少各 1 份
    gl_list: List[UploadFile] = list(gl_files or [])
    vat_list: List[UploadFile] = list(vat_files or [])
    if gl_file is not None:
        gl_list.append(gl_file)
    if vat_file is not None:
        vat_list.append(vat_file)
    if not gl_list or not vat_list:
        raise HTTPException(422, _glv_err("gl_parse_failed", lang, e="missing files"))

    # M3-3 修(2026-05-25):收入对账旧同步路径补 credits 前置检查 + 按量扣费 · 闭掉免费入口
    #   (与 bank /run、async /submit 一致 · 余额不足直接 402 · 不让付费 OCR 先跑)。
    _billing_glv = {"is_exempt": True, "pages_used_this_month": 0}
    try:
        from core import db as _db_credit_glv

        _tid_glv = user.get("tenant_id")
        _billing_glv = _db_credit_glv.get_billing_status_combined(str(user.get("id")), _tid_glv)
        if not _billing_glv.get("allowed") and not _billing_glv.get("is_exempt"):
            _est_cost = float(
                _db_credit_glv.estimate_pdf_cost_thb(
                    _billing_glv.get("pages_used_this_month", 0), len(gl_list) + len(vat_list)
                )
            )
            raise HTTPException(
                402,
                detail={
                    "code": "insufficient_balance",
                    "balance": _billing_glv.get("balance_thb", 0.0),
                    "estimated_cost": _est_cost,
                    "pages_used_this_month": _billing_glv.get("pages_used_this_month", 0),
                },
            )
    except HTTPException:
        raise
    except Exception as _be:
        logger.warning(f"[gl-vat.credits] pre-check skip: {_be}")

    # 读所有字节
    gl_data: List[tuple] = []
    vat_data: List[tuple] = []
    for f in gl_list:
        gl_data.append((await f.read(), f.filename or "gl.pdf"))
    for f in vat_list:
        vat_data.append((await f.read(), f.filename or "vat.pdf"))

    gl_name = "; ".join(fn for _, fn in gl_data)
    vat_name = "; ".join(fn for _, fn in vat_data)
    api_key = _user_key(user)

    # 1. 并行解析所有 GL 文件 + 合并 rows
    import asyncio

    loop = asyncio.get_event_loop()
    gl_results = await asyncio.gather(
        *[
            loop.run_in_executor(None, lambda b=b, n=n: parse_gl(b, n, revenue_prefix or "4"))
            for b, n in gl_data
        ]
    )
    gl_errors = [r.get("error") for r in gl_results if not r.get("ok") and r.get("error")]
    if gl_errors and not any(r.get("rows") for r in gl_results):
        # 所有 GL 都解析失败
        raise HTTPException(
            422, _glv_err("gl_parse_failed", lang, e="; ".join(filter(None, gl_errors))[:200])
        )
    merged_gl_rows = []
    for r in gl_results:
        merged_gl_rows.extend(r.get("rows") or [])
    if not merged_gl_rows:
        logger.warning(
            f"[gl-vat] GL parsed but 0 revenue rows · files={gl_name} · " f"prefix={revenue_prefix}"
        )
        raise HTTPException(422, _glv_err("gl_no_revenue_rows", lang))
    gl_result = {
        "ok": True,
        "rows": merged_gl_rows,
        "row_count": sum(r.get("row_count") or 0 for r in gl_results),
    }

    # 2. 并行解析所有 VAT 报表 + 合并 rows
    vat_results = await asyncio.gather(
        *[
            loop.run_in_executor(None, lambda b=b, n=n: parse_vat_report(b, n, api_key=api_key))
            for b, n in vat_data
        ]
    )
    vat_errors = [r.get("error") for r in vat_results if not r.get("ok") and r.get("error")]
    if vat_errors and not any(r.get("rows") for r in vat_results):
        raise HTTPException(
            422, _glv_err("vat_parse_failed", lang, e="; ".join(filter(None, vat_errors))[:200])
        )
    merged_vat_rows = []
    for r in vat_results:
        merged_vat_rows.extend(r.get("rows") or [])
    if not merged_vat_rows:
        raise HTTPException(422, _glv_err("vat_no_rows", lang))
    vat_result = {
        "ok": True,
        "rows": merged_vat_rows,
        "row_count": sum(r.get("row_count") or 0 for r in vat_results),
    }

    # M3-3 · 按量扣费(图片/PDF 按 OCR 页 · Excel/CSV 按字符估算 · 各格式各费率)· 豁免账号不扣
    if not _billing_glv.get("is_exempt"):
        try:
            from core import db as _db_chg_glv
            from services.ocr.pdf_utils import count_pdf_pages as _count_pages_glv

            _tid_chg_glv = user.get("tenant_id")
            _excel_exts = {".xlsx", ".xls", ".xlsm", ".csv", ".tsv", ".txt", ".docx", ".doc"}
            _pdf_units = 0
            _excel_units = 0
            for r, (b, fn) in list(zip(gl_results, gl_data)) + list(zip(vat_results, vat_data)):
                if not r.get("ok"):
                    continue
                if len(r.get("rows") or []) == 0:
                    continue
                ext = "." + (fn or "").lower().rsplit(".", 1)[-1] if "." in (fn or "") else ""
                if ext in _excel_exts:
                    _excel_units += _db_chg_glv._excel_char_count_estimate(b, fn)
                else:
                    _pdf_units += _pdf_billing_units(
                        _count_pages_glv(b) or 1, len(r.get("rows") or [])
                    )
            if _pdf_units > 0:
                asyncio.create_task(
                    asyncio.to_thread(
                        _db_chg_glv.charge_ocr_async,
                        str(user.get("id")),
                        _tid_chg_glv,
                        "pdf",
                        _pdf_units,
                        None,
                        f"收入对账 PDF · {_pdf_units} 页",
                    )
                )
            if _excel_units > 0:
                asyncio.create_task(
                    asyncio.to_thread(
                        _db_chg_glv.charge_ocr_async,
                        str(user.get("id")),
                        _tid_chg_glv,
                        "excel",
                        _excel_units,
                        None,
                        f"收入对账 Excel · {_excel_units} 字符",
                    )
                )
        except Exception as _ce:  # noqa: BLE001
            logger.warning(f"💳 gl-vat sync charge skip: {_ce}")

    # 3. 对账
    detail, summary = reconcile_gl_vat(gl_result["rows"], vat_result["rows"])

    # 4. 统计
    matched = sum(1 for r in detail if r.gl_amount is not None and (r.diff or 0) == 0)
    diff_cnt = sum(1 for r in detail if r.gl_amount is not None and (r.diff or 0) != 0)
    unmatched = sum(1 for r in detail if r.gl_amount is None)

    # 5. 落库
    detail_j = detail_to_json(detail)
    summary_j = summary_to_json(summary)
    task_id = db.create_gl_vat_task(
        user_id=str(user["id"]),
        tenant_id=user.get("tenant_id"),
        gl_filename=gl_name,
        vat_filename=vat_name,
        gl_row_count=gl_result.get("row_count") or len(gl_result["rows"]),
        vat_row_count=vat_result.get("row_count") or len(vat_result["rows"]),
        detail_json=detail_j,
        summary_json=summary_j,
        matched_count=matched,
        unmatched_count=unmatched,
        diff_count=diff_cnt,
    )

    return {
        "ok": True,
        "task_id": task_id,
        "gl_row_count": len(gl_result["rows"]),
        "vat_row_count": len(vat_result["rows"]),
        "stats": {
            "matched": matched,
            "diff": diff_cnt,
            "unmatched": unmatched,
            "total": len(detail),
        },
        "detail": detail_j,
        "summary": summary_j,
    }


@glvat_router.get("/gl-vat/tasks")
async def gl_vat_list_tasks(request: Request):
    """列出最近 GL 对账任务"""
    user = require_perm(request, "recon.view")
    if not user:
        raise HTTPException(401, "未登录")
    tasks = db.list_gl_vat_tasks(
        user_id=str(user["id"]),
        tenant_id=user.get("tenant_id"),
        limit=50,
    )
    return {"ok": True, "tasks": tasks}


@glvat_router.get("/gl-vat/{task_id}")
async def gl_vat_get_task(task_id: int, request: Request):
    """读取一份完整的 GL 对账结果（含明细 JSON）

    v118.35.0.29 P0 隔离 (体检 2026-05-21 风险 1):
    旧 db.get_gl_vat_task(task_id) 无任何权限校验 · 改成强制传 user_id + tenant_id ·
    跨 tenant 用户拿不到 task · 自然 404 (跟 task 不存在一样的响应 · 防枚举侧信道)
    """
    user = require_perm(request, "recon.view")
    if not user:
        raise HTTPException(401, _glv_err("auth_required", "th"))
    task = db.get_gl_vat_task(task_id, str(user["id"]), user.get("tenant_id"))
    if not task:
        raise HTTPException(404, _glv_err("task_not_found", "th"))
    return {
        "ok": True,
        "task_id": task["id"],
        "gl_filename": task.get("gl_filename"),
        "vat_filename": task.get("vat_filename"),
        "gl_row_count": task.get("gl_row_count"),
        "vat_row_count": task.get("vat_row_count"),
        "stats": {
            "matched": task.get("matched_count") or 0,
            "diff": task.get("diff_count") or 0,
            "unmatched": task.get("unmatched_count") or 0,
        },
        "detail": task.get("detail_json") or [],
        "summary": task.get("summary_json") or {},
        "created_at": str(task.get("created_at") or ""),
    }


@glvat_router.get("/gl-vat/{task_id}/export")
async def gl_vat_export(task_id: int, request: Request, lang: str = "th"):
    """下载 GL 对账 Excel · 表头按 lang 切换 zh/en/th/ja"""
    user = require_perm(request, "recon.export")
    if not user:
        raise HTTPException(401, "未登录")
    if lang not in ("th", "zh", "en", "ja"):
        lang = "th"

    # v118.35.0.29 P0 隔离修复(体检风险 1) · 强制 user_id + tenant_id scope
    task = db.get_gl_vat_task(task_id, str(user["id"]), user.get("tenant_id"))
    if not task:
        raise HTTPException(404, "任务不存在")

    detail = detail_from_json(task.get("detail_json") or [])
    summary = summary_from_json(task.get("summary_json") or {})
    excel_bytes = export_gl_vat_excel(detail, summary, lang=lang)

    # v118.32.5.5.2 · filename 走 ASCII safe + RFC 5987 utf-8 编码(兼容泰文/中文文件名)
    import urllib.parse

    base_vat = (task.get("vat_filename") or "vat").rsplit(".", 1)[0]
    ascii_safe = (
        "".join(c if c.isascii() and (c.isalnum() or c in "._-") else "_" for c in base_vat)[
            :40
        ].strip("_")
        or f"task_{task_id}"
    )
    ascii_name = f"GL_VAT_recon_{task_id}_{ascii_safe}.xlsx"
    utf8_quoted = urllib.parse.quote(f"GL_VAT_recon_{task_id}_{base_vat}.xlsx")
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={ascii_name}; filename*=UTF-8''{utf8_quoted}"
        },
    )


@glvat_router.delete("/gl-vat/{task_id}")
async def gl_vat_delete(task_id: int, request: Request):
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, "未登录")
    ok = db.delete_gl_vat_task(task_id, str(user["id"]))
    if not ok:
        raise HTTPException(404, "任务不存在或无权删除")
    return {"ok": True}


# v118.32.5.5.20 · 批量删除 GL 对账任务
class _GlBatchDeleteBody(BaseModel):
    ids: List[int]


@glvat_router.post("/gl-vat/tasks/batch_delete")
async def gl_vat_batch_delete(body: _GlBatchDeleteBody, request: Request):
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, "未登录")
    if not body.ids:
        return {"deleted": 0}
    deleted = db.delete_gl_vat_tasks_batch(body.ids, str(user["id"]))
    return {"deleted": int(deleted)}
