# -*- coding: utf-8 -*-
"""LINE 图片票 OCR 前的快速路径(P1G-Perf · 省掉重复票的 Vision/Gemini/分类)。

两条 pre-OCR 短路,命中即发卡返回、绝不进识别管线:
  1. early_dup_short_circuit:同张图已建过单据(image_sha256 命中)→ 重发该单当前状态卡
     (posted / voided / draft),不重跑 Vision/Gemini/分类(治「重复票仍跑满 60s」)。
  2. handle_ocr_cache_hit:firm / 未开记账路写过 ocr_history 的同图 → 用缓存字段重建卡。

handle_ocr_cache_hit 从 line_image_ocr 抽出(该文件 500 行顶格,新增 early-dup 要先腾位),
逻辑等价搬家;early_dup_short_circuit 为本任务新增。
"""

from __future__ import annotations

import logging

from core import db
from services.exceptions.exception_checks import _async_run_exception_checks

logger = logging.getLogger("mr-pilot")


def early_dup_short_circuit(
    user_fresh: dict,
    line_user_id: str,
    file_hash: str,
    ws_client_id,
    lang: str,
    quote_token: str | None,
) -> bool:
    """同张图已建过单据 → 重发当前状态卡,跳过全部 OCR。命中返回 True(调用方据此 return)。"""
    tid = str(user_fresh["tenant_id"]) if user_fresh.get("tenant_id") else None
    if not (tid and ws_client_id and file_hash):
        return False
    try:
        from services.purchase import docs as docs_svc
        from services.purchase import image_dedup

        with db.get_cursor_rls(tid, commit=True) as cur:
            hit = image_dedup.find_recent(
                cur, tenant_id=tid, workspace_client_id=ws_client_id, image_sha256=file_hash
            )
            if not hit:
                return False
            detail = docs_svc.get_doc(
                cur, tenant_id=tid, workspace_client_id=ws_client_id, doc_id=hit["id"]
            )
            if not detail:
                return False
            status = (detail.get("doc") or {}).get("status")
            _push_state_card(
                cur,
                line_user_id,
                lang,
                detail,
                doc_id=hit["id"],
                ws=ws_client_id,
                tid=tid,
                created_by=str(user_fresh["id"]),
            )
        logger.info(
            "[line_ocr] early_dup_hit=true skipped_vision=true skipped_l2=true "
            "skipped_l3=true status=%s hash=%s... doc=%s",
            status,
            file_hash[:12],
            hit["id"],
        )
        return True
    except Exception as e:  # noqa: BLE001 — 短路失败绝不挡正常 OCR,回落即可
        logger.warning("[line_ocr] early_dup 短路失败(回落正常 OCR): %s", e)
        return False


def _push_state_card(cur, line_user_id, lang, detail, *, doc_id, ws, tid, created_by) -> None:
    """按单据真实状态 push 当前卡:posted 数据卡 / voided 终态卡 / draft 可确认卡。

    状态→卡映射复用 line_posted_card.build_state_card(与改错重发卡同一处);posted/draft 铸新 nonce
    供卡上动作(撤销/确认)并续接 active_doc(可直接说改错),void 终态无动作不铸不续。
    """
    from services.line_binding import line_client, line_posted_card

    status = (detail.get("doc") or {}).get("status")
    token = (
        "" if status == "void" else _mint(cur, tid=tid, ws=ws, doc_id=doc_id, created_by=created_by)
    )
    card = line_posted_card.build_state_card(
        detail, doc_id=doc_id, ws=ws, lang=lang, source="cache", token=token
    )
    if card is None:
        return
    line_client.push_messages(line_user_id, [card])
    if status != "void":
        _set_active(tid, ws, doc_id, line_user_id, cur)


def _mint(cur, *, tid, ws, doc_id, created_by) -> str:
    from services.line_binding import line_action_nonce as nonce

    try:
        return nonce.mint(
            cur, tenant_id=tid, workspace_client_id=ws, action_ref=doc_id, user_id=created_by
        )
    except Exception:  # noqa: BLE001 — 无 token 卡仍可看,动作走兼容链路
        return ""


def _set_active(tid, ws, doc_id, line_user_id, cur) -> None:
    try:
        from services.expense import line_correct

        line_correct._set_active(tid, ws, doc_id, line_user_id, cur=cur)
    except Exception:  # noqa: BLE001 — 续接是增益,失败不影响已发卡
        logger.warning("[line_ocr] early_dup set active 失败", exc_info=True)


def handle_ocr_cache_hit(
    user_fresh: dict,
    file_hash: str,
    cached: dict,
    line_user_id: str,
    lang: str,
    quote_token: str | None,
    ws_client_id,
) -> None:
    """文件指纹缓存命中(firm/未开记账路写过 ocr_history)→ 用缓存字段重建卡(不重 OCR/扣费)。

    从 line_image_ocr 等价搬家。重发的票 ingest 自带查重 → 出「可能重复」卡;不再发老式纯文字。
    """
    logger.info(f"[line_ocr] 命中文件缓存 (hash={file_hash[:12]}...) hid={cached['id']}")
    _cached_pages = cached.get("pages") or []
    _primary = next(
        (p for p in _cached_pages if not p.get("is_duplicate") and not p.get("is_copy")),
        None,
    )
    _primary = _primary or (_cached_pages[0] if _cached_pages else None)
    _cf = (_primary or {}).get("fields") or {}
    try:
        _exc_total_c = None
        _raw_t_c = _cf.get("total_amount")
        if _raw_t_c:
            try:
                _exc_total_c = float(str(_raw_t_c).replace(",", "").strip())
            except Exception as e:
                logger.warning(f"[line_cache] total_amount 解析失败: {e}")
        import asyncio

        asyncio.create_task(
            _async_run_exception_checks(
                history_id=str(cached["id"]),
                user_id=str(user_fresh["id"]),
                tenant_id=(
                    str(user_fresh.get("tenant_id")) if user_fresh.get("tenant_id") else None
                ),
                seller_name=_cf.get("seller_name"),
                invoice_no=_cf.get("invoice_number"),
                total_amount=_exc_total_c,
                confidence=cached.get("confidence"),
                duplicate=None,
                fields=_cf,
            )
        )
        logger.info(f"  🛡  [LINE Cache] 异常检测已入队 · hid={cached['id']}")
    except Exception as _e_lc:
        logger.warning(f"[line_ocr] 缓存异常检测入队失败: {_e_lc}")

    _tid_c = str(user_fresh["tenant_id"]) if user_fresh.get("tenant_id") else None
    try:
        from services.expense import line_l2
        from services.line_binding import line_booker
        from services.purchase.intake import line_expense_gate_open
        from services.purchase.line_ingest import ingest_line_image

        _ci = None
        if _cf and ws_client_id and _tid_c:
            with db.get_cursor_rls(_tid_c, commit=True) as cur:
                if line_expense_gate_open(cur, tenant_id=_tid_c):
                    _ci = ingest_line_image(
                        cur,
                        tenant_id=_tid_c,
                        workspace_client_id=ws_client_id,
                        fields=_cf,
                        confidence=cached.get("confidence"),
                        field_confidence=(_primary or {}).get("field_confidence"),
                        image_ref=None,
                        created_by=str(user_fresh["id"]),
                        api_key=line_l2.resolve_api_key(user_fresh),
                        image_sha256=file_hash,
                    )
        if _ci:
            _ci["source"] = "cache"
            line_booker.push_result_card(
                line_user_id,
                lang,
                _ci,
                quote_token=quote_token,
                ws_client_id=ws_client_id,
                tenant_id=_tid_c,
            )
    except Exception as _ce_card:
        logger.warning(f"[line_ocr] 缓存卡片重建失败: {_ce_card}")
