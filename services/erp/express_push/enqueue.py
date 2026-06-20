# -*- coding: utf-8 -*-
"""置信闸门 + 入队(Express adapter 的"推送"动作 = 写待领取队列,不跑服务器 Playwright)。

push_to_endpoint 命中 adapter=='express' → 调 enqueue_express。它不自己写 erp_push_logs:
返回一个标准 push 结果 dict,由现有调用方(手动 /api/erp/push、自动 _auto_push_history)
照常落库一行。借由 classify_push_status 的 express 哨兵,这一行落成:
  · pending(高置信 + 映射成功)→ 进队列等本地 Agent lease(error_msg=EXPRESS_QUEUED 哨兵)
  · manual (低置信 / 映射判脏 / 账套白名单拒)→ 留人工(error_msg=EXPRESS_MANUAL:<reason>)

置信复用 services/expense/confidence.grade;金额/分录复用确定性引擎(mapper);
全程 try/except,绝不拖垮采购/OCR 主流程。特性开关 off → 直接短路(failed · 不入队)。
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional

from services.erp.express_push import account_set_allowed, express_push_enabled
from services.erp.express_push.mapper import build_express_payload

logger = logging.getLogger(__name__)

# error_msg 哨兵 · 让现有 classify_push_status 把这一行落成 pending / manual(单一状态源 · 铁律 #12)。
QUEUED_SENTINEL = "EXPRESS_QUEUED"
MANUAL_PREFIX = "EXPRESS_MANUAL"


def _result(
    *,
    success: bool,
    error_msg: Optional[str],
    request_body: Optional[Dict[str, Any]],
    response_body: Optional[str],
    http_status: int,
    t0: float,
) -> Dict[str, Any]:
    return {
        "success": success,
        "http_status": http_status,
        "response_body": response_body,
        "error_msg": error_msg,
        "elapsed_ms": int((time.time() - t0) * 1000),
        "request_body": request_body,
        "adapter": "express",
    }


def _manual(reason: str, request_body: Dict[str, Any], t0: float) -> Dict[str, Any]:
    return _result(
        success=False,
        error_msg=f"{MANUAL_PREFIX}: {reason}",
        request_body=request_body,
        response_body=json.dumps({"queued": False, "manual_reason": reason}, ensure_ascii=False),
        http_status=0,
        t0=t0,
    )


def _category_of(flat: Dict[str, Any]) -> str:
    fields = flat.get("fields") if isinstance(flat.get("fields"), dict) else {}
    return str(flat.get("category") or (fields or {}).get("category") or "").strip()


def enqueue_express(endpoint: Dict[str, Any], history: Dict[str, Any]) -> Dict[str, Any]:
    """对一条 history 跑置信闸门 + 映射 → 返回标准 push 结果(pending / manual / 短路)。"""
    t0 = time.time()
    config = endpoint.get("config") or {}

    if not express_push_enabled():
        return _result(
            success=False,
            error_msg="ERR_EXPRESS_DISABLED",
            request_body={"adapter": "express"},
            response_body=None,
            http_status=0,
            t0=t0,
        )

    # 账套白名单(代码级拒写非 DATAT)· 不入队,留人工。
    account_set = str(config.get("account_set") or "").strip()
    if not account_set_allowed(account_set):
        return _manual(
            f"account_set_not_allowed:{account_set or 'none'}",
            {"adapter": "express", "account_set": account_set},
            t0,
        )

    try:
        from core import db
        from services.erp.erp_payload import flatten_history_for_mrerp

        flat = flatten_history_for_mrerp(history)
        user_id = endpoint.get("user_id")
        tenant_id = db.get_user_tenant_id(user_id) if user_id else None
        mappings = db.get_mrerp_mappings_bundle(tenant_id) if tenant_id else {}
        category = _category_of(flat)

        mres = build_express_payload(flat, config=config, mappings=mappings, category=category)
        if not mres.ok:
            return _manual(mres.reason, {"adapter": "express", "manual_reason": mres.reason}, t0)
        payload = mres.payload

        # 防御性复核白名单(mapper 已带 account_set · 这里再钉一次,与 Agent lease 同口径)。
        if not account_set_allowed(payload.get("account_set")):
            return _manual("account_set_not_allowed", payload, t0)

        verdict = _grade(history, payload, bool(category))
        if verdict is not None and verdict.action != "post":
            reason = "low_confidence:" + ",".join(verdict.reasons)
            return _manual(reason, payload, t0)

        # 高置信 + 映射成功 → 入队(pending)等本地 Agent。
        return _result(
            success=False,
            error_msg=QUEUED_SENTINEL,
            request_body=payload,
            response_body=json.dumps(
                {
                    "queued": True,
                    "doctype": payload.get("doctype"),
                    "account_set": payload.get("account_set"),
                    "total_amount": payload.get("total_amount"),
                },
                ensure_ascii=False,
            ),
            http_status=202,
            t0=t0,
        )
    except Exception as e:
        logger.exception("enqueue_express failed")
        return _manual(f"enqueue_error:{type(e).__name__}", {"adapter": "express"}, t0)


def _grade(history: Dict[str, Any], payload: Dict[str, Any], has_category: bool):
    """置信判级(复用 confidence.grade · express 推送方向恒为 purchase)。失败返 None 放行。"""
    try:
        from services.expense import confidence

        fields = history.get("fields") if isinstance(history.get("fields"), dict) else {}
        supplier = payload.get("supplier") or {}
        return confidence.grade(
            amount=payload.get("total_amount"),
            vendor_name=supplier.get("name") or "",
            invoice_number=payload.get("ref_no") or "",
            document_type=str((fields or {}).get("document_type") or "tax_invoice"),
            direction="purchase",
            confidence_band=str(history.get("confidence") or ""),
            has_category=has_category,
            require_category=False,
        )
    except Exception:
        logger.exception("express confidence grade failed; passing through")
        return None
