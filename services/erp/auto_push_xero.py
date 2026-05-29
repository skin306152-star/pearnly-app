# -*- coding: utf-8 -*-
"""Pearnly · ERP 自动推送 · Xero 后台路径(REFACTOR-WA-B1 · 2026-05-29 R19 从 erp/auto_push 抽出 · 0 逻辑改)

OCR 完成 hook → _trigger_auto_push_all 调度的 Xero 自动推(失败只写日志不抛)。与 MR.ERP/智能分拣
路径(erp/auto_push)分域。auto_push 底部 re-import 当 facade(契约 auto_push._auto_push_xero_for_history)。
依赖:db(运行时)· erp_xero_routes._ensure_fresh_xero_token / xero_pusher(函数内 lazy import 解循环)。
"""

import logging

logger = logging.getLogger("mr-pilot")


# ============================================================
# v27.8.1.3 · Xero 后台自动推(OCR 完成 hook 调用)
# ============================================================
async def _auto_push_xero_for_history(user_id: str, tenant_id: str, history_id: str):
    """v27.8.1.3 · 自动推 Xero(后台 · 失败只写日志不抛)"""
    import time

    if not tenant_id:
        return
    t0 = time.time()
    try:
        history = db.get_ocr_history_detail(user_id, history_id, tenant_id=tenant_id)
        if not history:
            return
        st = (history.get("status") or "").lower()
        if st in ("exception", "exception_pending", "rejected"):
            return  # 异常未放行 · 不自动推
        # 客户映射
        mappings = db.get_mrerp_mappings_bundle(tenant_id)
        cid = history.get("client_id") or 0
        contact_name = None
        for m in mappings.get("clients") or []:
            if m.get("erp_type") == "xero" and int(m.get("client_id") or 0) == int(cid):
                contact_name = (m.get("erp_code") or "").strip()
                break
        if not contact_name:
            try:
                db.insert_push_log(
                    user_id=user_id,
                    endpoint_id=None,
                    history_id=history_id,
                    invoice_no=history.get("invoice_no"),
                    seller_name=history.get("seller_name"),
                    total_amount=history.get("total_amount"),
                    status="failed",
                    http_status=400,
                    request_body={"adapter": "xero_auto", "stage": "mapping"},
                    response_body=None,
                    error_msg="no_client_mapping",
                    attempt=1,
                    elapsed_ms=int((time.time() - t0) * 1000),
                    trigger="auto",
                )
            except Exception as e:
                logger.warning(f"[xero_auto] 写 push_log(no_mapping)失败: {e}")
            return
        # 拿 token + push
        try:
            from erp_xero_routes import _ensure_fresh_xero_token

            access_token, xero_org_id = _ensure_fresh_xero_token(tenant_id)
            from xero_pusher import (
                find_contact_by_name,
                build_invoice_payload,
                push_invoice,
            )

            contact = find_contact_by_name(access_token, xero_org_id, contact_name)
            if not contact:
                raise RuntimeError("contact_not_found")
            payload = build_invoice_payload(history, contact)
            result = push_invoice(access_token, xero_org_id, payload)
            ok = bool(result.get("success"))
            db.insert_push_log(
                user_id=user_id,
                endpoint_id=None,
                history_id=history_id,
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="success" if ok else "failed",
                http_status=result.get("http_status"),
                request_body={"adapter": "xero_auto"},
                response_body=str(result.get("invoice_id") or "")[:500],
                error_msg=(None if ok else str(result.get("error") or "")[:500]),
                attempt=1,
                elapsed_ms=int((time.time() - t0) * 1000),
                trigger="auto",
            )
            if ok:
                logger.info(f"[AutoPushXero] ok history={history_id[:8]} contact={contact_name}")
        except Exception as e:
            logger.warning(f"[AutoPushXero] failed history={history_id[:8]}: {e}")
            try:
                db.insert_push_log(
                    user_id=user_id,
                    endpoint_id=None,
                    history_id=history_id,
                    invoice_no=history.get("invoice_no"),
                    seller_name=history.get("seller_name"),
                    total_amount=history.get("total_amount"),
                    status="failed",
                    http_status=500,
                    request_body={"adapter": "xero_auto"},
                    response_body=None,
                    error_msg=str(e)[:500],
                    attempt=1,
                    elapsed_ms=int((time.time() - t0) * 1000),
                    trigger="auto",
                )
            except Exception as _le:
                logger.warning(f"[xero_auto] 写 push_log(exception)失败: {_le}")
    except Exception as e:
        logger.exception(f"[AutoPushXero] outer exception: {e}")


import db  # noqa: E402
