"""OCR 识别核心编排(同步路由 + 异步 worker 单一事实源)。

从 routes/ocr_recognize_routes.py 抽出函数体:校验→文件缓存→余额闸→pipeline→非票判定→
置信度→persist(内含扣费)→自动推送→成本日志→构建响应。**钱逻辑单一源**:网页同步上传
与缺口④异步 worker 共用此函数,杜绝两路计费/落库逻辑分叉。

不含(留各调用方按自身上下文做):
  · HTTP request 解析(user/client_id/ws 由调用方传入)
  · PDF 留底后台化(需事件循环 · 同步路由 create_task / worker 内联调度,见返回的 raw_pages)
返回 {"response": <净化后响应 dict>, "raw_pages": <未净化页·供留底>, "history_ids": [...]}。
校验/闸/引擎错按原样 raise HTTPException(同步路由直接透传;worker 捕获映射 job 失败)。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from core import db
from core import workspace_context as wc
from core.db import increment_user_monthly_usage
from core.route_helpers import _plan_permissions, _tid
from services.ocr.entrypoints import (
    content_hash as _ocr_content_hash,
    get_cached_history as _ocr_get_cached,
)
from services.ocr.recognize.cache import serve_cache_hit
from services.ocr.recognize.persist import persist_invoices
from services.ocr.recognize.autopush import dispatch_auto_push
from services.ocr.recognize.sanitize import strip_internal_fields
from services.ocr.invoice_no import format_warnings_for_groups

logger = logging.getLogger("mr-pilot")


def _page_confidence(p: dict) -> int:
    f = p.get("fields", {}) or {}
    s = 0
    if f.get("invoice_number"):
        s += 1
    if f.get("date"):
        s += 1
    if f.get("total_amount"):
        s += 1
    if f.get("seller_name") or f.get("seller_tax"):
        s += 1
    if f.get("buyer_name") or f.get("buyer_tax"):
        s += 1
    items = f.get("items") or []
    if items:
        s += 2
    # 文本路径补偿:subtotal + vat 双有 → 等价 items(发票结构完整)
    elif f.get("subtotal") and f.get("vat"):
        s += 2
    return s


def run_recognition_core(
    user: Dict[str, Any],
    content: bytes,
    file: Any,
    *,
    client_id: Optional[str] = None,
    ws_client_id: Optional[int] = None,
    staged: bool = False,
) -> Dict[str, Any]:
    """识别核心 · 同步(pipeline/persist/push 全同步)· 调用方负责读 content + 留底调度。

    staged=True(仅网页交互式上传):识别记录先以草稿落库,不进识别记录列表,
    待第4步完成/导出/推送调 /api/ocr/commit 才翻正式。后台/文件夹自动入口不传(即时可见)。
    """
    plan = user.get("plan", "free")

    # PO-4 · 缺套账时回落本租户默认套账(上传记录绝不漏归属写 NULL)。
    if ws_client_id is None:
        ws_client_id = wc.default_workspace_for_write(_tid(user))

    # 1. 基本校验(PDF + image + Excel + CSV + Word)
    from services.ocr.pipeline import PDF_EXTENSIONS, IMAGE_EXTENSIONS, TABLE_EXTENSIONS

    _all_exts = PDF_EXTENSIONS | IMAGE_EXTENSIONS | TABLE_EXTENSIONS
    _fname = (file.filename or "").lower()
    _ext = "." + _fname.rsplit(".", 1)[-1] if "." in _fname else ""
    if not _fname or _ext not in _all_exts:
        raise HTTPException(400, detail="ocr.unsupported_format")

    if len(content) == 0:
        raise HTTPException(400, detail="ocr.empty_file")

    # 2. 按套餐决定页数/大小上限
    p_perms = _plan_permissions(plan)
    max_pages = p_perms["max_pages_per_upload"]
    max_mb = p_perms["max_file_size_mb"]
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(400, detail={"code": "ocr.file_too_large", "mb": max_mb})

    # 3. 页数校验 — 仅 PDF 有意义。
    if _ext in PDF_EXTENSIONS:
        from services.ocr.pdf_utils import count_pdf_pages

        page_count = count_pdf_pages(content)
        if page_count == 0:
            raise HTTPException(400, detail="ocr.invalid_pdf")
        if page_count > max_pages:
            raise HTTPException(
                400, detail={"code": "ocr.too_many_pages", "max": max_pages, "actual": page_count}
            )
    else:
        page_count = 1

    # 4. 配额(v118.46 · 纯 credits 按量扣费)· 下游兼容默认值
    quota_info = {"mode": "credits", "monthly_quota": None, "used_this_month": 0}
    monthly_quota = None
    new_month_used = None

    # 4.5. 文件指纹缓存(必须先于余额闸:命中不产生新成本,余额 0 也复用)。
    file_hash = _ocr_content_hash(content)
    cached = _ocr_get_cached(user, file_hash, workspace_client_id=ws_client_id)
    if cached:
        resp = strip_internal_fields(
            serve_cache_hit(
                cached=cached,
                user=user,
                plan=plan,
                file=file,
                monthly_quota=monthly_quota,
                file_hash=file_hash,
            )
        )
        return {"response": resp, "raw_pages": [], "history_ids": []}

    # Credits 余额前置检查(1 次 SELECT)。
    _billing = {
        "allowed": True,
        "is_exempt": True,
        "balance_thb": 0.0,
        "pages_used_this_month": 0,
        "error_code": None,
    }
    try:
        _billing = db.get_billing_status_combined(str(user.get("id")), _tid(user))
        if not _billing.get("allowed") and not _billing.get("is_exempt"):
            if _ext in PDF_EXTENSIONS or _ext in IMAGE_EXTENSIONS:
                _est_cost = float(
                    db.estimate_pdf_cost_thb(_billing.get("pages_used_this_month", 0), page_count)
                )
            else:
                _chars = db._excel_char_count_estimate(content, file.filename or "")
                _est_cost = float(db.estimate_excel_cost_thb(_chars))
            raise HTTPException(
                402,
                detail={
                    "code": "insufficient_balance",
                    "balance": _billing.get("balance_thb", 0.0),
                    "estimated_cost": _est_cost,
                    "pages_used_this_month": _billing.get("pages_used_this_month", 0),
                },
            )
    except HTTPException:
        raise
    except Exception as _be:
        logger.warning(f"[credits] billing pre-check skip(error tolerated): {_be}")

    # v105 · Gemini 主 + Google Vision 备
    own_key = (user.get("gemini_api_key") or user.get("custom_gemini_api_key") or "").strip()
    api_key = own_key or None

    # OCR · 新 pipeline 唯一路径 · 按扩展名分派 PDF / image / table。
    _chg_kind = None  # 扣费参数 · 实际扣费在 history 落库后
    _chg_units = 0
    try:
        from services.ocr.entrypoints import run_pipeline_for_file as _run_ocr_controller
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
        from services.ocr.feedback.context import ocr_request_context

        # 反馈闭环 ② · 设请求级上下文(L2 few-shot 按租户取例;flag 关时无副作用)
        # 引擎策略由 OCR controller 统一套入:按 OCR_MODE + 租户套餐决定本次请求的模型档位。
        _plan_code = (_billing.get("subscription") or {}).get("plan_code")
        with ocr_request_context(str(user["id"]), _tid(user)):
            _pipe_res = _run_ocr_controller(
                content,
                file.filename or "upload",
                api_key=api_key,
                max_pages=max_pages,
                plan_code=_plan_code,
                is_exempt=bool(_billing.get("is_exempt")),
            )
        # 台账观测参数:实际用的模型(混模型时逗号并列)/是否触发升级臂
        _ocr_models = sorted(
            {m for p in _pipe_res.pages for m in (p.layer2_model, p.layer3_model) if m}
        )
        _l3_fired = any(p.layer3_input_tokens or p.layer3_output_tokens for p in _pipe_res.pages)
        result = pipeline_result_to_legacy_dict(_pipe_res)
        _pipeline_cost_thb = float(_pipe_res.estimated_cost_thb)
        logger.info(
            f"🆕 pipeline_v1 · file={file.filename} · ext={_ext} · pages={_pipe_res.page_count} "
            f"· cost=฿{_pipeline_cost_thb:.4f} · elapsed={_pipe_res.elapsed_ms}ms"
        )
        try:
            from services.ocr.observability import log_pipeline_timing

            log_pipeline_timing(_pipe_res, source="recognize", filename=file.filename or "")
        except Exception:
            pass

        # 算扣费参数(实际扣费挪到 history 落库后)。
        if not _billing.get("is_exempt"):
            try:
                if _ext in PDF_EXTENSIONS or _ext in IMAGE_EXTENSIONS:
                    _chg_kind = "pdf"
                    _chg_units = int(_pipe_res.page_count or page_count or 1)
                else:
                    _chg_kind = "excel"
                    _chg_units = db._excel_char_count_estimate(content, file.filename or "")
            except Exception as _ce:
                logger.warning(f"💳 扣费参数计算跳过: {_ce}")
    except HTTPException:
        raise
    except Exception as _pipe_err:
        err_name = type(_pipe_err).__name__
        if err_name == "Layer1PDFError" or isinstance(_pipe_err, ValueError):
            raise HTTPException(400, detail=f"ocr.invalid_file: {_pipe_err}")
        logger.exception(f"❌ pipeline_v1 失败: {err_name}: {_pipe_err}")
        # 引擎失败也记台账(status=failed,零成本行)——失败率才算得出。文件不合法(400)不算。
        # log_ocr_cost 内部全量捕获返回 bool,不会拖垮错误响应。
        db.log_ocr_cost(
            user_id=str(user["id"]),
            tenant_id=_tid(user),
            history_id=None,
            engine="pipeline_v1",
            pages=page_count,
            input_tokens=0,
            output_tokens=0,
            cost_thb=0.0,
            elapsed_ms=0,
            status="failed",
        )
        raise HTTPException(500, detail="ocr.engine_error")

    # 非发票检测:全部页都非发票 → 不入库不扣费。
    if result.get("pages"):
        _pages = result["pages"]
        all_not_invoice = True
        for p in _pages:
            f = p.get("fields") or {}
            is_not = f.get("is_not_invoice")
            if isinstance(is_not, str):
                is_not = is_not.strip().lower() == "true"
            if not is_not:
                all_not_invoice = False
                break
        if all_not_invoice and len(_pages) > 0:
            logger.warning(f"⚠️ Gemini 判定非发票 · 不入库 · file={file.filename}")
            raise HTTPException(400, detail="ocr.not_invoice")

    # 6. 配额更新(credits 模式恒不走 shared/monthly 分支 · 保留兼容)。
    qm = quota_info.get("mode")
    if qm == "shared" and user.get("tenant_id"):
        try:
            tu = db.increment_tenant_monthly_usage(str(user["tenant_id"]), page_count)
            if tu >= 0:
                new_month_used = tu
        except Exception as e:
            logger.warning(f"increment_tenant_monthly_usage failed: {e}")
    elif qm == "monthly" and monthly_quota is not None:
        new_month_used = increment_user_monthly_usage(str(user["id"]), page_count)

    # 7. 置信度:对非副本主页取每页独立得分,取最高。
    seen_invoice_numbers = set()
    primary_pages = []
    for p in result["pages"]:
        inv = (p.get("fields") or {}).get("invoice_number")
        is_copy = p.get("is_copy", False)
        if is_copy or (inv and inv in seen_invoice_numbers):
            p["is_duplicate"] = True
            continue
        if inv:
            seen_invoice_numbers.add(inv)
        p["is_duplicate"] = False
        primary_pages.append(p)

    # 兜底:多联发票全标副本 → 取得分最高页当主页。
    if not primary_pages and result["pages"]:
        unique_pages = []
        seen_inv = set()
        for p in result["pages"]:
            inv = (p.get("fields") or {}).get("invoice_number")
            if inv and inv in seen_inv:
                continue
            if inv:
                seen_inv.add(inv)
            unique_pages.append(p)
        if unique_pages:
            best_page = max(unique_pages, key=_page_confidence)
            best_page["is_duplicate"] = False
            primary_pages.append(best_page)
            logger.info(f"  ⚠️ 所有页都标副本 · 兜底选第 {best_page.get('page', '?')} 页作为主页")

    max_score = max((_page_confidence(p) for p in primary_pages), default=0)
    if max_score >= 6:
        confidence = "high"
    elif max_score >= 3:
        confidence = "medium"
    else:
        confidence = "low"
    logger.info(
        f"  识别置信度: {confidence} (最高得分 {max_score}, "
        f"主页 {len(primary_pages)}/{len(result['pages'])})"
    )

    _persist = persist_invoices(
        result=result,
        user=user,
        confidence=confidence,
        _billing=_billing,
        _chg_kind=_chg_kind,
        _chg_units=_chg_units,
        file=file,
        content=content,
        file_hash=file_hash,
        client_id=client_id,
        _ws_client_id=ws_client_id,
        staged=staged,
    )
    invoice_groups = _persist["invoice_groups"]
    invoice_count = _persist["invoice_count"]
    history_ids = _persist["history_ids"]
    duplicate_warnings = _persist["duplicate_warnings"]
    primary_history_id = _persist["primary_history_id"]
    primary_archive_name = _persist["primary_archive_name"]
    primary_category_tag = _persist["primary_category_tag"]

    auto_pushed = dispatch_auto_push(history_ids=history_ids, plan=plan, user=user)

    # 成本日志(pipeline-v1 自带完整成本 · 100% 埋点)。
    try:
        total_input_tokens = sum(int(p.get("input_tokens") or 0) for p in result.get("pages", []))
        total_output_tokens = sum(int(p.get("output_tokens") or 0) for p in result.get("pages", []))
        total_pages = int(result.get("page_count") or len(result.get("pages", [])) or 0)
        db.log_ocr_cost(
            user_id=str(user["id"]),
            tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
            history_id=primary_history_id,
            engine="pipeline_v1",
            pages=total_pages,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost_thb=_pipeline_cost_thb,
            elapsed_ms=int(result.get("elapsed_ms") or 0),
            model=",".join(_ocr_models),
            mode=_engine_mode,
            l3_fired=_l3_fired,
        )
        logger.info(
            f"💰 成本记录 · {total_pages} 页 · in={total_input_tokens} out={total_output_tokens} "
            f"· ≈THB {_pipeline_cost_thb:.4f}"
        )
    except Exception as _cost_err:
        logger.warning(f"成本记录写入失败(不影响识别): {_cost_err}")

    # 同页多票防静默漏:收集 pipeline 标出的"可能漏识别发票"页。
    missed_invoice_warnings: List[dict] = []
    for _pg in result.get("pages") or []:
        for _w in _pg.get("_validation_warnings") or []:
            if isinstance(_w, str) and _w.startswith("possible_missed_invoice"):
                missed_invoice_warnings.append({"page": _pg.get("page_number"), "reason": _w})

    # 同卖家批内发票号格式一致性:多张里格式偏离多数派的那张大概率读错
    # (同批 IV69100179/IV69100189 混进 IV69/00199)。揪出 → needs_review,
    # 不静默满分放过。只揪不改值(瞎补分隔符会把对的票改错,交人工核对)。
    invoice_format_warnings = format_warnings_for_groups(invoice_groups[:invoice_count])

    response = strip_internal_fields(
        {
            "filename": file.filename,
            "page_count": result["page_count"],
            "elapsed_ms": result["elapsed_ms"],
            "pages": result["pages"],
            "confidence": confidence,
            "missed_invoice_warnings": missed_invoice_warnings,
            "invoice_format_warnings": invoice_format_warnings,
            "needs_review": bool(missed_invoice_warnings or invoice_format_warnings),
            "history_id": primary_history_id,
            "history_ids": history_ids,
            "invoice_count": invoice_count,
            "invoices": [
                {
                    "history_id": history_ids[i] if i < len(history_ids) else None,
                    "fields": (invoice_groups[i] or {}).get("invoice_fields") or {},
                    "page_indices": (invoice_groups[i] or {}).get("page_indices") or [],
                    "page_count": len((invoice_groups[i] or {}).get("source_pages") or []),
                    "source_index": i + 1,
                    "source_total": invoice_count,
                }
                for i in range(min(invoice_count, len(history_ids) or invoice_count))
            ],
            "archive_name": primary_archive_name,
            "category_tag": primary_category_tag,
            "auto_pushed": auto_pushed,
            "duplicate_warnings": duplicate_warnings,
            # 归属透明:每张票按税号路由后的最终套账(前端对照当前所选套账,不一致就明示)
            "workspace_attribution": {
                "requested_workspace_id": int(ws_client_id) if ws_client_id is not None else None,
                "assignments": _persist.get("workspace_assignments") or [],
            },
            "quota": {
                "ip_used_today": None,
                "ip_daily_limit": None,
                "used_this_month": (
                    new_month_used
                    if new_month_used is not None
                    else int(user.get("used_this_month") or 0)
                ),
                "monthly_quota": monthly_quota,
            },
        }
    )
    return {"response": response, "raw_pages": result["pages"], "history_ids": history_ids}
