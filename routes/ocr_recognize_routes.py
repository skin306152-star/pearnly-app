"""
ocr_recognize_routes.py · POST /api/ocr/recognize 主路由(OCR 识别热路径)

从 app.py 抽出(REFACTOR-WB-app · 2026-06-01)。函数体三大段已拆到
services/ocr/recognize/{cache,persist,autopush}.py;本文件留薄编排 router。
v1 别名 meta_aliases_routes.v1_recognize 通过 `from ocr_recognize_routes import ocr_recognize` 调到。
⚠️ 高敏:登录鉴权 + credits 计费扣费 + OCR pipeline 热路径 + ERP 自动推送(铁律 #26)。
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from core import db
from core import workspace_context as wc
from core.db import increment_user_monthly_usage
from core.auth import get_current_user_from_request, get_client_ip
from core.route_helpers import _plan_permissions, _tid
from services.ocr.entrypoints import (
    content_hash as _ocr_content_hash,
    get_cached_history as _ocr_get_cached,
)
from services.ocr.recognize.cache import serve_cache_hit
from services.ocr.recognize.persist import persist_invoices
from services.ocr.recognize.autopush import dispatch_auto_push
from services.ocr.recognize.sanitize import strip_internal_fields

logger = logging.getLogger("mr-pilot")
router = APIRouter()


def _choose_engine(plan: str = None, user: dict = None) -> str:
    """v0.15 · 所有用户统一用 Gemini · plan/user 参数保留做兼容"""
    return "gemini"


@router.post("/api/ocr/recognize")
async def ocr_recognize(
    request: Request,
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None),  # v27.8.1.13a · 右上角客户切换器选中时自动归属
    # B1 相 1 (2026-05-26) · workspace 账套归属(在为哪家公司做账)· 可选 · Form 或 header
    # X-Workspace-Client-Id · 带不上 NULL · 非强制(缺失不拦上传)· 与 client_id(买方)独立。
    workspace_client_id: Optional[str] = Form(None),
):
    user = get_current_user_from_request(request)
    client_ip = get_client_ip(request)
    plan = user.get("plan", "free")

    # B1 相 1 · 解析 workspace 账套归属:优先 Form,回退 header;非数字/缺失 → None。
    _ws_raw = workspace_client_id or request.headers.get("X-Workspace-Client-Id")
    _ws_client_id = int(_ws_raw) if (_ws_raw and str(_ws_raw).strip().isdigit()) else None
    # PO-4 · 缺套账头/Form 时回落本租户默认套账(rollout-safe:上传记录绝不漏归属写 NULL,
    # 否则切套账后看不到本张票)。insert_ocr_history 内仍校验归属·非本租户→NULL·不拦上传。
    if _ws_client_id is None:
        _ws_client_id = wc.default_workspace_for_write(_tid(user))

    # 1. 基本校验 (2026-05-21 multi-format refactor: PDF + image + Excel + CSV + Word)
    from services.ocr.pipeline import (
        PDF_EXTENSIONS,
        IMAGE_EXTENSIONS,
        TABLE_EXTENSIONS,
    )

    _all_exts = PDF_EXTENSIONS | IMAGE_EXTENSIONS | TABLE_EXTENSIONS
    _fname = (file.filename or "").lower()
    _ext = "." + _fname.rsplit(".", 1)[-1] if "." in _fname else ""
    if not _fname or _ext not in _all_exts:
        raise HTTPException(400, detail="ocr.unsupported_format")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, detail="ocr.empty_file")

    # 2. 按套餐决定页数/大小上限 · v0.8 单一数据源
    p_perms = _plan_permissions(plan)
    max_pages = p_perms["max_pages_per_upload"]
    max_mb = p_perms["max_file_size_mb"]

    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(400, detail={"code": "ocr.file_too_large", "mb": max_mb})

    # 3. 页数校验 — only meaningful for PDFs. Excel/CSV/Word/image skip this.
    if _ext in PDF_EXTENSIONS:
        from services.ocr.pdf_utils import count_pdf_pages

        page_count = count_pdf_pages(content)
        if page_count == 0:
            raise HTTPException(400, detail="ocr.invalid_pdf")
        if page_count > max_pages:
            raise HTTPException(
                400,
                detail={
                    "code": "ocr.too_many_pages",
                    "max": max_pages,
                    "actual": page_count,
                },
            )
    else:
        page_count = 1  # images / single-CSV / single-DOCX count as 1 page

    # 4. 配额检查 · v0.15 · 新双轨:自带 key → 不限 · 否则扣 user.monthly_quota
    # === v118.46 · 纯 credits 按量扣费(2026-05-24 Zihao 拍板:全平台只此一个套餐)===
    #   OCR 准入只看「是否豁免 或 余额>0」· 旧 plan / monthly_quota / 自带 key / trial 反薅闸
    #   全部下线(0 起步·必须充值才能用 → 没有免费额度可薅 → 天然防薅)。
    #   旧函数 check_ocr_quota / _check_user_quota 不再用于 OCR 准入(保留供其它老路径兼容)。
    #   下游若干变量(quota_info / monthly_quota / used_month)给 credits-mode 默认值兼容。
    quota_info = {"mode": "credits", "monthly_quota": None, "used_this_month": 0}
    monthly_quota = None  # None = 不限月配额(credits 模式按余额扣)
    used_today = None
    used_month = 0

    # 4.5. 文件指纹缓存 · v0.8 改:所有 plan 都启用(按 user_id 隔离,不跨用户)
    # v92 · 缓存窗口从 24h 扩到 30 天(默认) · 月末复核上月票也能命中 · 省 Gemini 配额
    # v118.47 · 缓存必须先于余额闸:缓存命中不产生新 OCR 成本,余额为 0 也应可复用旧结果。
    file_hash = _ocr_content_hash(content)
    cached = _ocr_get_cached(user, file_hash, workspace_client_id=_ws_client_id)
    if cached:
        return strip_internal_fields(
            serve_cache_hit(
                cached=cached,
                user=user,
                plan=plan,
                file=file,
                monthly_quota=monthly_quota,
                file_hash=file_hash,
            )
        )

    # v118.35.0.21 · Credits 余额前置检查(v0.20 重做 · 1 次 SELECT · 修连接池超时)
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

    # 5. 选引擎(v103 · 永远走降级链 · _choose_engine 保留兼容)
    engine_name = _choose_engine(plan, user)

    # v105 · 简化引擎架构 · Gemini 主 + Google Vision 备
    own_key = (user.get("gemini_api_key") or user.get("custom_gemini_api_key") or "").strip()
    api_key = own_key or None

    # OCR · 新 pipeline 唯一路径(text_path layer 0 + Vision + Flash-Lite + Flash · 100% 埋点)
    # 2026-05-21 multi-format refactor: dispatch by extension to PDF /
    # image / table reader. PDF and image go through OCR; Excel/CSV/Word
    # bypass OCR via table_path.
    _chg_kind = None  # v118.46 · 扣费参数 · 算在此 · 实际扣费在 history 落库后
    _chg_units = 0
    try:
        from services.ocr.pipeline import (
            run_on_pdf_bytes as _pipeline_run_pdf,
            run_on_image_bytes as _pipeline_run_image,
            run_on_table_bytes as _pipeline_run_table,
        )
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

        if _ext in PDF_EXTENSIONS:
            _pipe_res = _pipeline_run_pdf(content, max_pages=max_pages, api_key=api_key)
        elif _ext in IMAGE_EXTENSIONS:
            _pipe_res = _pipeline_run_image(content, api_key=api_key)
        else:  # TABLE_EXTENSIONS — Excel / CSV / Word / TXT
            _pipe_res = _pipeline_run_table(
                content, filename=file.filename or "upload", api_key=api_key
            )
        result = pipeline_result_to_legacy_dict(_pipe_res)
        _pipeline_cost_thb = float(_pipe_res.estimated_cost_thb)
        logger.info(
            f"🆕 pipeline_v1 · file={file.filename} · ext={_ext} · pages={_pipe_res.page_count} "
            f"· cost=฿{_pipeline_cost_thb:.4f} · elapsed={_pipe_res.elapsed_ms}ms"
        )
        # Step0 观测(REFACTOR-WA-OCRPERF)· 结构化 per-page layer 计时 · 纯观测不改逻辑
        try:
            from services.ocr.observability import log_pipeline_timing

            log_pipeline_timing(_pipe_res, source="recognize", filename=file.filename or "")
        except Exception:
            pass

        # v118.46 · 算扣费参数(实际扣费挪到 history 落库后:才有 history_id + 已确认非发票通过)
        #   图片(PNG/JPG/扫描)与 PDF 统一按页/张扣;CSV/XLSX/DOCX/TXT 按字符。
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
        raise HTTPException(500, detail="ocr.engine_error")

    # ============================================================
    # v93 · 场景 2 · 非发票检测(Gemini Prompt 里新增 is_not_invoice 字段)
    # 如果全部页面都不是发票 · 直接报错 · 不入库 · 不扣配额
    # ============================================================
    if result.get("pages"):
        _pages = result["pages"]
        # 所有页都标记为 is_not_invoice=true 才算非发票(一份 PDF 可能混了封面 + 发票)
        all_not_invoice = True
        for p in _pages:
            f = p.get("fields") or {}
            is_not = f.get("is_not_invoice")
            # 兼容字符串 / 布尔
            if isinstance(is_not, str):
                is_not = is_not.strip().lower() == "true"
            if not is_not:
                all_not_invoice = False
                break
        if all_not_invoice and len(_pages) > 0:
            logger.warning(f"⚠️ Gemini 判定非发票 · 不入库 · file={file.filename}")
            raise HTTPException(400, detail="ocr.not_invoice")

    # 6. 更新配额 · v87 多租户支持:shared=扣租户 · monthly=扣用户(老) · admin/lifetime 不扣
    new_month_used = None
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

    # 7. 智能置信度
    #    策略:不再跨页"合并取第一个非空值",避免一页成功一页失败被误判为高
    #    改为:对所有【非副本】页取每页独立置信度,然后取最高
    def _page_confidence(p):
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
        # v118.20.4.2 · 文本路径补偿:subtotal + vat 双有 → 等价 items(发票结构完整)
        elif f.get("subtotal") and f.get("vat"):
            s += 2
        return s

    # 副本/签字页过滤(去重)
    # v105.1 修复:多联发票(底单/发票/收据)Gemini 可能把全部页标 is_copy · 导致主页 0
    # 改进:至少保留 1 页作为主页(取得分最高的)
    seen_invoice_numbers = set()
    primary_pages = []
    for p in result["pages"]:
        inv = (p.get("fields") or {}).get("invoice_number")
        is_copy = p.get("is_copy", False)
        # 副本 OR 同一发票号已经见过 → 标记为非主页
        if is_copy or (inv and inv in seen_invoice_numbers):
            p["is_duplicate"] = True
            continue
        if inv:
            seen_invoice_numbers.add(inv)
        p["is_duplicate"] = False
        primary_pages.append(p)

    # v105.1 · 兜底 · 如果一张主页都没有(多联发票全标副本) · 取第一张得分最高的当主页
    if not primary_pages and result["pages"]:
        # 同发票号去重 · 然后选得分最高
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

    # 对主页取最高置信度
    if primary_pages:
        max_score = max(_page_confidence(p) for p in primary_pages)
    else:
        max_score = 0

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
        _ws_client_id=_ws_client_id,
    )
    invoice_groups = _persist["invoice_groups"]
    invoice_count = _persist["invoice_count"]
    history_ids = _persist["history_ids"]
    duplicate_warnings = _persist["duplicate_warnings"]
    primary_history_id = _persist["primary_history_id"]
    primary_archive_name = _persist["primary_archive_name"]
    primary_category_tag = _persist["primary_category_tag"]

    auto_pushed = dispatch_auto_push(
        history_ids=history_ids,
        plan=plan,
        user=user,
    )

    # 写入成本日志 · pipeline-v1 自带完整成本(Vision per-page + Flash-Lite + Flash · 100% 埋点)
    try:
        # 汇总 token 用量
        total_input_tokens = sum(int(p.get("input_tokens") or 0) for p in result.get("pages", []))
        total_output_tokens = sum(int(p.get("output_tokens") or 0) for p in result.get("pages", []))
        total_pages = int(result.get("page_count") or len(result.get("pages", [])) or 0)
        cost_thb = _pipeline_cost_thb
        primary_engine = "pipeline_v1"
        # 写一条记录(以本次识别的主 history 为锚)
        db.log_ocr_cost(
            user_id=str(user["id"]),
            tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
            history_id=primary_history_id,
            engine=primary_engine,
            pages=total_pages,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost_thb=cost_thb,
            elapsed_ms=int(result.get("elapsed_ms") or 0),
        )
        logger.info(
            f"💰 成本记录 · {total_pages} 页 · in={total_input_tokens} out={total_output_tokens} · ≈THB {cost_thb:.4f}"
        )
    except Exception as _cost_err:
        logger.warning(f"成本记录写入失败(不影响识别): {_cost_err}")

    # REFACTOR-WA-OCRPERF Step1 · PDF 留底后台化:响应返回后才生成 searchable PDF + save_pdf
    #   + 回填 pdf_storage_path(前端 has_pdf 届时显示下载)。字段/响应字段一字不变;
    #   留底失败只是没下载(同原 try/except 降级)。sync CPU/disk 走 to_thread 不堵 event loop。
    if history_ids:
        try:
            # asyncio 在本函数是局部名(上方 384/1075 条件分支里有 import asyncio · 编译期即
            # 把 asyncio 标记为函数局部)· 那些分支没走时 asyncio 未绑定 → 这里显式 import 绑定,
            # 防 UnboundLocalError(实测:无 auto-push 端点的账号触发过 · prod E2E 抓到)。
            import asyncio

            _pdf_pages = result.get("pages") or []
            _pdf_uid = str(user["id"])
            _pdf_tid = _tid(user)
            _pdf_hids = list(history_ids)
            _pdf_content = content

            async def _bg_pdf_backfill():
                try:
                    from services.ocr.pdf_backfill import generate_and_save_pdf

                    rel, size = await asyncio.to_thread(
                        generate_and_save_pdf, _pdf_content, _pdf_pages, _pdf_uid
                    )
                    if rel:
                        await asyncio.to_thread(
                            db.update_ocr_history_pdf_storage,
                            _pdf_hids,
                            rel,
                            size,
                            _pdf_uid,
                            _pdf_tid,
                        )
                except Exception as _bge:
                    logger.warning(f"[ocrperf] PDF 后台留底/回填失败(已忽略): {_bge}")

            asyncio.create_task(_bg_pdf_backfill())
        except Exception as _sched_err:
            logger.warning(f"[ocrperf] PDF 后台任务调度失败(已忽略): {_sched_err}")

    # P0 修 (2026-05-26) · 同页多票防静默漏:收集 pipeline 标出的"可能漏识别发票"页
    # (_validation_warnings 里以 possible_missed_invoice 开头),回前端明确提示 +
    # 标记 needs_review · 让用户进人工核对 · 绝不静默成功。
    missed_invoice_warnings = []
    for _pg in result.get("pages") or []:
        for _w in _pg.get("_validation_warnings") or []:
            if isinstance(_w, str) and _w.startswith("possible_missed_invoice"):
                missed_invoice_warnings.append({"page": _pg.get("page_number"), "reason": _w})

    # strip_internal_fields:出口剥引擎/品牌标识 + 每页 _ 前缀 debug(DB 留底不动)。
    return strip_internal_fields(
        {
            "filename": file.filename,
            "page_count": result["page_count"],
            "elapsed_ms": result["elapsed_ms"],
            "pages": result["pages"],
            "confidence": confidence,
            # P0 修 · 可能漏识别发票(同页多票兜底)· 非空时前端必须提示用户人工核对
            "missed_invoice_warnings": missed_invoice_warnings,
            "needs_review": bool(missed_invoice_warnings),
            "history_id": primary_history_id,  # 兼容老前端
            "history_ids": history_ids,  # v0.11 · 全部 id 列表
            "invoice_count": invoice_count,  # v0.11 · 识别出几张发票
            # v118.27.5.1 · 多发票拆分修复 · 给前端每张独立 fields(导出/抽屉用)
            # 之前只返回扁平 pages · 前端 mergeFields 把多发票合并成 1 个 → 导出丢字段
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
            # v0.13 · 重复发票警告
            "duplicate_warnings": duplicate_warnings,
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
