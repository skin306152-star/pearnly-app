# -*- coding: utf-8 -*-
"""
Pearnly · 银行对账路由模块(M10 · 上传/会话/匹配/候选/客户绑定/dev seed)(REFACTOR-B1 · 2026-05-25 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape / error code。

覆盖 11 个 API:
  POST   /api/bank-recon/upload                       · 上传银行对账单 · 同步解析 · 返 session_id
  GET    /api/bank-recon/sessions                     · 最近对账会话列表(client filter)
  GET    /api/bank-recon/stats                        · 对账中心首页当月概览
  GET    /api/bank-recon/sessions/{session_id}        · 会话详情 + 流水列表
  DELETE /api/bank-recon/sessions/{session_id}        · 删除会话(级联)
  POST   /api/bank-recon/sessions/{session_id}/match  · 触发匹配算法(最长 60s)
  POST   /api/bank-recon/tx/{tx_id}/override          · 手动指派匹配
  GET    /api/bank-recon/tx/{tx_id}/candidates        · 拉一条流水的候选发票
  PATCH  /api/bank-recon/sessions/{session_id}/client · 给会话绑客户(越权校验)

依赖:
  - db.*(bank recon session / transactions / candidates / dev seed)
  - auth.get_current_user_from_request
  - bank_recon_v2(parse/match · 函数内懒 import)
  - services.ocr.pipeline / legacy_adapter(多格式解析 · 函数内懒 import)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from core import db
from core import workspace_context as wc
from core.route_helpers import _tid
from services.authz.deps import require_perm

logger = logging.getLogger("mr-pilot")

router = APIRouter()


@router.post("/api/bank-recon/upload")
async def bank_recon_upload(request: Request, file: UploadFile = File(...)):
    """
    上传银行对账单 PDF · 同步解析 · 返回 session_id
    - 不做匹配(用户下一步手动触发,方便分步)
    - 失败返回 4xx 明确错误码
    """
    user = require_perm(request, "recon.create")
    filename = file.filename or "statement.pdf"
    # 2026-05-21 multi-format refactor: bank statement upload supports
    # PDF / image / Excel / CSV / Word. PDF goes through bank_recon_v2's
    # existing parser; tabular formats go through the unified pipeline
    # with document_type=bank_statement.
    from services.ocr.pipeline import (
        PDF_EXTENSIONS,
        IMAGE_EXTENSIONS,
        TABLE_EXTENSIONS,
    )

    _bank_all_exts = PDF_EXTENSIONS | IMAGE_EXTENSIONS | TABLE_EXTENSIONS
    _bank_fname_l = filename.lower()
    _bank_ext = "." + _bank_fname_l.rsplit(".", 1)[-1] if "." in _bank_fname_l else ""
    if _bank_ext not in _bank_all_exts:
        raise HTTPException(400, detail="bank_recon.unsupported_format")

    pdf_bytes = await file.read()
    if not pdf_bytes or len(pdf_bytes) < 50:
        raise HTTPException(400, detail="bank_recon.empty_file")
    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise HTTPException(413, detail="bank_recon.file_too_large")

    from services.recon import bank_recon_v2 as br
    import asyncio

    try:
        if _bank_ext in PDF_EXTENSIONS:
            # Existing flow: pdfplumber → Gemini fallback (handles scan + text PDFs)
            parsed = await asyncio.to_thread(br.parse_statement_pdf, pdf_bytes, filename)
        else:
            # New flow: route through unified pipeline with explicit document_type
            # so Excel/CSV/Word bank statements bypass OCR and the GL/Bank
            # validators reject mis-sourced amounts (e.g. 6091).
            from services.ocr.pipeline import (
                run_on_image_bytes as _bank_run_image,
                run_on_table_bytes as _bank_run_table,
            )
            from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

            if _bank_ext in IMAGE_EXTENSIONS:
                _pipe_res = await asyncio.to_thread(
                    _bank_run_image, pdf_bytes, document_type="bank_statement"
                )
            else:  # TABLE_EXTENSIONS
                _pipe_res = await asyncio.to_thread(
                    _bank_run_table, pdf_bytes, filename, None, None, "bank_statement"
                )
            _legacy = pipeline_result_to_legacy_dict(_pipe_res)
            parsed = br.parsed_from_pipeline_legacy(_legacy, filename)
    except Exception as e:
        logger.exception("[bank_recon] 解析异常")
        raise HTTPException(500, detail=f"bank_recon.parse_exception:{str(e)[:100]}")

    session_id = db.create_bank_recon_session(
        user_id=str(user["id"]),
        bank_code=parsed.bank_code,
        filename=filename,
        pages=parsed.pages,
        workspace_client_id=wc.active_workspace_for_request(
            request, _tid(user)
        ),  # PO-6a · 归当前套账
        tenant_id=_tid(user),
    )
    if not session_id:
        raise HTTPException(500, detail="bank_recon.create_session_failed")

    if parsed.parse_method == "gemini_vision_pending":
        # 轮 2 未接通 vision · 标记 "scanned not supported yet"
        db.mark_recon_parse_failed(
            session_id,
            "扫描件暂未支持 · 请上传带文字层的 PDF",
            user_id=str(user["id"]),
            tenant_id=_tid(user),
        )
        return {
            "session_id": session_id,
            "bank_code": parsed.bank_code,
            "parse_status": "parse_failed",
            "tx_count": 0,
            "error": "scanned_pdf_not_yet",
        }

    if not parsed.transactions:
        db.mark_recon_parse_failed(
            session_id,
            "没有解析到任何流水 · 可能格式不支持 · 请反馈给我们",
            user_id=str(user["id"]),
            tenant_id=_tid(user),
        )
        return {
            "session_id": session_id,
            "bank_code": parsed.bank_code,
            "parse_status": "parse_failed",
            "tx_count": 0,
            "error": "no_transactions_parsed",
        }

    ok = db.save_bank_recon_parse(
        session_id, parsed.as_dict(), user_id=str(user["id"]), tenant_id=_tid(user)
    )
    if not ok:
        db.mark_recon_parse_failed(
            session_id, "落库失败", user_id=str(user["id"]), tenant_id=_tid(user)
        )
        raise HTTPException(500, detail="bank_recon.save_failed")

    return {
        "session_id": session_id,
        "bank_code": parsed.bank_code,
        "account_last4": parsed.account_last4,
        "period_start": parsed.period_start,
        "period_end": parsed.period_end,
        "opening_balance": parsed.opening_balance,
        "closing_balance": parsed.closing_balance,
        "total_inflow": parsed.total_inflow,
        "total_outflow": parsed.total_outflow,
        "tx_count": len(parsed.transactions),
        "parse_status": "parsed",
    }


@router.get("/api/bank-recon/sessions")
async def bank_recon_list_sessions(request: Request, limit: int = 30):
    """最近对账会话列表
    v118.26.2 · 接 client_assignments filter(v28.1 铁律 · 员工只看分到的客户的对账)
    """
    user = require_perm(request, "recon.view")
    limit = max(1, min(int(limit), 100))
    restrict = db.get_visible_client_ids_for_user(user)
    return db.list_bank_recon_sessions(
        user["id"],
        limit,
        restrict_client_ids=restrict,
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
        tenant_id=_tid(user),
    )


# v118.26.0 · 对账中心首页统计 · 当月概览
@router.get("/api/bank-recon/stats")
async def bank_recon_stats(request: Request):
    """
    对账中心顶级菜单首页用 · 当月银行对账概览
    返回:
      pending  - 待对账(系统已推荐但人没确认 · suggested 状态)
      matched  - 已完成(matched 状态)
      unmatched - 未匹配(unmatched · 找不到候选)
      total_sessions - 当月会话总数(=0 时前端显示空态)
      last_activity_at - 最近一次操作时间(iso 字符串 · null 表示无)
    时区按 Asia/Bangkok 算「当月」
    """
    user = require_perm(request, "recon.view")
    return db.get_bank_recon_stats(
        user["id"],
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
        tenant_id=_tid(user),
    )


@router.get("/api/bank-recon/sessions/{session_id}")
async def bank_recon_session_detail(session_id: str, request: Request, filter: str = "all"):
    """会话详情 · 含流水列表 · 可按 match_status 过滤"""
    user = require_perm(request, "recon.view")
    session = db.get_bank_recon_session(
        user["id"],
        session_id,
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
        tenant_id=_tid(user),
    )
    if not session:
        raise HTTPException(404, detail="bank_recon.session_not_found")

    match_filter = filter if filter in ("matched", "suggested", "unmatched") else None
    txs = db.list_bank_recon_transactions(
        session_id, user["id"], match_filter=match_filter, limit=2000, tenant_id=_tid(user)
    )
    return {"session": session, "transactions": txs}


@router.delete("/api/bank-recon/sessions/{session_id}")
async def bank_recon_delete_session(session_id: str, request: Request):
    """删除对账会话(级联删流水和候选)"""
    user = require_perm(request, "recon.create")
    ok = db.delete_bank_recon_session(
        user["id"],
        session_id,
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
        tenant_id=_tid(user),
    )
    if not ok:
        raise HTTPException(404, detail="bank_recon.session_not_found")
    return {"ok": True}


@router.post("/api/bank-recon/sessions/{session_id}/match")
async def bank_recon_run_match(session_id: str, request: Request):
    """触发匹配算法 · 同步等结果(最长 60 秒)"""
    user = require_perm(request, "recon.create")
    session = db.get_bank_recon_session(
        user["id"],
        session_id,
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
        tenant_id=_tid(user),
    )
    if not session:
        raise HTTPException(404, detail="bank_recon.session_not_found")
    if session.get("parse_status") != "parsed":
        raise HTTPException(400, detail="bank_recon.not_parsed")

    from services.recon import bank_recon_v2 as br
    import asyncio

    try:
        stats = await asyncio.wait_for(
            asyncio.to_thread(
                br.run_matching_for_session, session_id, str(user["id"]), tenant_id=_tid(user)
            ),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(504, detail="bank_recon.match_timeout")

    return stats


@router.post("/api/bank-recon/tx/{tx_id}/override")
async def bank_recon_tx_override(tx_id: str, request: Request):
    """用户手动指派匹配 · body: {history_id?, status}"""
    user = require_perm(request, "recon.create")
    body = await request.json()
    status = (body.get("status") or "").strip()
    history_id = body.get("history_id")
    if status not in ("matched", "unmatched", "ignored"):
        raise HTTPException(400, detail="bank_recon.invalid_status")
    ok = db.override_tx_match(
        tx_id,
        str(user["id"]),
        history_id if status == "matched" else None,
        status,
        tenant_id=_tid(user),
    )
    if not ok:
        raise HTTPException(404, detail="bank_recon.tx_not_found")
    return {"ok": True}


# v118.26.2 · 拉一条流水的候选发票列表(JOIN 拿发票字段 · 给候选抽屉用)
@router.get("/api/bank-recon/tx/{tx_id}/candidates")
async def bank_recon_tx_candidates(tx_id: str, request: Request):
    """
    返回这条流水「跑过匹配后」落库的全部候选(已按 score 降序 · 最多 5 个)
    每项含发票字段(invoice_no / vendor / amount_total / invoice_date / filename)
    没跑过匹配的流水返回空数组 · 前端显示「请先点开始匹配」
    """
    user = require_perm(request, "recon.view")
    return {"candidates": db.get_tx_candidates(tx_id, str(user["id"]), tenant_id=_tid(user))}


# v118.26.2 · 给一份银行对账 session 绑客户(老板分客户给员工 → 流水进 client filter)
@router.patch("/api/bank-recon/sessions/{session_id}/client")
async def bank_recon_set_session_client(session_id: str, request: Request):
    """body: {client_id: int|null}
    鉴权:session 必须属于 user 且 client_id 必须在 visible 范围内(防越权)
    """
    user = require_perm(request, "recon.create")
    body = await request.json()
    cid = body.get("client_id")
    # 校验客户在 visible 范围
    if cid is not None:
        try:
            cid = int(cid)
        except (ValueError, TypeError):
            raise HTTPException(400, detail="bank_recon.invalid_client_id")
        visible = db.get_visible_client_ids_for_user(user)
        if visible is not None and cid not in visible:
            raise HTTPException(403, detail="client.no_access")
    ok = db.update_bank_recon_session_client(
        str(user["id"]),
        session_id,
        cid,
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
        tenant_id=_tid(user),
    )
    if not ok:
        raise HTTPException(404, detail="bank_recon.session_not_found")
    return {"ok": True, "client_id": cid}
