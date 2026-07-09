# -*- coding: utf-8 -*-
"""Pearnly · ERP 批量推送 seam(P1c · Zihao 2026-05-26 拍板)

`dispatch_endpoint_batch(endpoint, histories)`:把**一个 endpoint** 的**多张** history
一次性推送,返回与 `erp_push.push_to_endpoint` 完全同 shape 的 per-history 结果列表
(顺序与入参 histories 对齐 · 一张一个 dict)。

为什么要批量(解 1000 张规模):MR.ERP 走 Playwright + 跨进程会话锁串行,
`push_to_endpoint` 每张一次浏览器登录 → 1000 张几小时。本 seam 让 MR.ERP 一批
一次 `upload_invoice_batch`(一次登录 + 一份 xlsx),再按 invoice_no 把
ImportResult.success/failed 回映射到每张 history。

通用层不写 `if adapter=='mrerp'` 的业务分支:adapter 差异只在本文件一处。
非 mrerp adapter 暂无批量能力 → 循环 `push_to_endpoint`(统一接口 · 行为不变)。

上层(app.py auto-push 编排 · P1d)只认这个统一接口 + 统一结果 shape,
负责 dedup / 写 push 日志 / stats / retry 队列(与逐张路径同源 · 铁律 #12)。
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _mrerp_history_invoice_no(history_flat: Dict[str, Any]) -> str:
    """与 mrerp_adapter 内部一致的 invoice_no 派生 · 用于把批量结果回映射到每张 history。"""
    try:
        from services.erp import mrerp_xlsx_generator

        return mrerp_xlsx_generator.derive_mrerp_invoice_no(history_flat) or "?"
    except Exception:
        return history_flat.get("invoice_number") or history_flat.get("invoice_no") or "?"


def _dispatch_mrerp_batch(
    endpoint: Dict[str, Any], histories: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """MR.ERP 批量:一次 build adapter + 一次 upload_invoice_batch,按 invoice_no 回映射。"""
    from services.erp import erp_push

    t0 = time.time()
    config = endpoint.get("config") or {}
    user_id = endpoint.get("user_id")
    endpoint_id = str(endpoint.get("id") or "")

    # tenant_id(批内同 endpoint → 同 user → 同 tenant)· 给 mappings + 主数据归属。
    tenant_id = None
    try:
        from core import db as _db

        tenant_id = _db.get_user_tenant_id(user_id) if user_id else None
    except Exception as e:
        logger.exception("dispatch_mrerp_batch: db import failed")
        return [
            _mrerp_resp(
                h,
                endpoint_id,
                tenant_id=None,
                success=False,
                http_status=0,
                body="",
                error_msg=f"ERR_DB_IMPORT: {e}",
                t0=t0,
            )
            for h in histories
        ]

    mappings = erp_push.load_mrerp_mappings(tenant_id)
    _gp = str(config.get("generic_product_code") or "").strip()  # 通用商品码 → provision_products
    if _gp:
        mappings = {**mappings, "_mrerp_generic_product": _gp}

    # flatten 全部 + 记每张的 invoice_no(回映射键)。
    flats: List[Dict[str, Any]] = []
    inv_nos: List[str] = []
    for h in histories:
        hf = erp_push.flatten_history_for_mrerp(h)
        if tenant_id:
            hf["tenant_id"] = tenant_id
        flats.append(hf)
        inv_nos.append(_mrerp_history_invoice_no(hf))

    # F6 银行佐证(L3)· 与单张路 push_mrerp_history 同源:批内取最早/最晚票面日期,一次性拉
    # 覆盖全批的银行流水窗口(与 _own_tax_id 一样"一批共用一份"的取法)。
    from services.erp.express_push.bank_evidence import attach_bank_index

    mappings = attach_bank_index(mappings, flats, user_id, "dispatch_mrerp_batch")

    # ★套账主体税号锚点(方向路由 + 匹配闸都要):单张路本就注入,批量路此前漏了 → 方向恒
    #   判不出全落销项、匹配闸也全放行。一端点通常绑一个账套 → 取首张能解析到的税号即代表本批。
    try:
        from services.erp.express_push.preflight import _own_tax_id

        for hf in flats:
            own_tax = _own_tax_id(endpoint, hf, tenant_id)
            if own_tax:
                mappings = {**mappings, "_own_tax_id": own_tax}
                break
    except Exception:
        logger.exception(
            "dispatch_mrerp_batch: own_tax_id resolve failed; 方向路由/匹配闸本批不启用"
        )

    # build adapter 一次。失败 → 全批同一个 err 结果。
    adapter, build_err = erp_push.build_mrerp_adapter(config)
    if build_err:
        return [
            _mrerp_resp(
                h,
                endpoint_id,
                tenant_id=tenant_id,
                success=False,
                http_status=build_err["http_status"],
                body=build_err["body"],
                error_msg=build_err["error_msg"],
                t0=t0,
            )
            for h in histories
        ]

    from services.erp.exceptions import (
        MRERPAuthError,
        MRERPTechnicalError,
        MRERPBusinessError,
    )

    # 一次性推全批(sync · 必须在事件循环外 · caller 用 to_thread 包)。
    try:
        with adapter:
            result = adapter.upload_routed_batch(flats, mappings)
    except MRERPAuthError as e:
        return _all_same(
            histories, inv_nos, endpoint_id, tenant_id, 401, f"auth: {e}", f"ERR_AUTH: {e}", t0
        )
    except MRERPTechnicalError as e:
        return _all_same(
            histories,
            inv_nos,
            endpoint_id,
            tenant_id,
            0,
            f"technical: {e}",
            f"ERR_TECHNICAL: {e}",
            t0,
        )
    except MRERPBusinessError as e:
        return _all_same(
            histories,
            inv_nos,
            endpoint_id,
            tenant_id,
            200,
            f"business: {e}",
            f"ERR_BUSINESS: {e}",
            t0,
        )
    except Exception as e:
        logger.exception("dispatch_mrerp_batch: upload_invoice_batch raised")
        return _all_same(
            histories,
            inv_nos,
            endpoint_id,
            tenant_id,
            0,
            f"unexpected: {type(e).__name__}: {e}",
            f"ERR_UNEXPECTED: {e}",
            t0,
        )

    # 按 invoice_no 回映射(成功优先;同号多张按出现顺序消费)。
    success_by_inv: Dict[str, list] = {}
    for s in result.success or []:
        success_by_inv.setdefault(s.invoice_no, []).append(s)
    failed_by_inv: Dict[str, list] = {}
    for f in result.failed or []:
        failed_by_inv.setdefault(f.invoice_no, []).append(f)

    out: List[Dict[str, Any]] = []
    for h, inv in zip(histories, inv_nos):
        s_list = success_by_inv.get(inv)
        if s_list:
            s = s_list.pop(0)
            body = {
                "ok": True,
                "mrerp_bill_no": s.mrerp_bill_no,
                "invoice_no": s.invoice_no,
                "elapsed_ms": result.elapsed_ms,
                "xlsx_size_bytes": result.xlsx_size_bytes,
            }
            out.append(
                _mrerp_resp(
                    h,
                    endpoint_id,
                    tenant_id=tenant_id,
                    success=True,
                    http_status=200,
                    body=body,
                    error_msg=None,
                    t0=t0,
                    mrerp_bill_no=s.mrerp_bill_no,
                    invoice_no=s.invoice_no,
                )
            )
            continue
        f_list = failed_by_inv.get(inv)
        f = f_list.pop(0) if f_list else None
        reasons = f.reasons if f else ["ERR_UNKNOWN_UPLOAD_OUTCOME"]
        body = {
            "ok": False,
            "reasons": reasons,
            "reasons_friendly": f.reasons_friendly if f else [],
            "screenshot": f.evidence_screenshot if f else None,
            "elapsed_ms": result.elapsed_ms,
        }
        out.append(
            _mrerp_resp(
                h,
                endpoint_id,
                tenant_id=tenant_id,
                success=False,
                http_status=200,
                body=body,
                error_msg="; ".join(reasons)[:500],
                t0=t0,
            )
        )
    return out


def _all_same(histories, inv_nos, endpoint_id, tenant_id, http_status, body, error_msg, t0):
    """批级失败(auth/technical/business/unexpected)→ 每张同一个错误结果。"""
    return [
        _mrerp_resp(
            h,
            endpoint_id,
            tenant_id=tenant_id,
            success=False,
            http_status=http_status,
            body=body,
            error_msg=error_msg,
            t0=t0,
        )
        for h in histories
    ]


def _mrerp_resp(
    history: Dict[str, Any],
    endpoint_id: str,
    *,
    tenant_id: Optional[str],
    success: bool,
    http_status: int,
    body: Any,
    error_msg: Optional[str],
    t0: float,
    **extra,
) -> Dict[str, Any]:
    """与 erp_push.push_mrerp_history._resp 同 shape 的 per-history 结果 dict。"""
    body_str = body if isinstance(body, str) else json.dumps(body, default=str, ensure_ascii=False)
    return {
        "success": success,
        "http_status": http_status,
        "response_body": body_str[:4000],
        "error_msg": error_msg,
        "elapsed_ms": int((time.time() - t0) * 1000),
        "request_body": {
            "history_id": str(history.get("id") or ""),
            "invoice_no": history.get("invoice_no"),
            "tenant_id": tenant_id,
            "endpoint_id": endpoint_id,
            "adapter": "mrerp",
        },
        "adapter": "mrerp",
        **extra,
    }


def dispatch_endpoint_batch(
    endpoint: Dict[str, Any], histories: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """统一批量推送入口。返回 per-history 结果列表(与 histories 同序 · 同 push_to_endpoint shape)。

    adapter 差异只在本函数内一处:mrerp 走真批量,其余循环 push_to_endpoint。
    """
    if not histories:
        return []
    adapter = endpoint.get("adapter", "webhook")
    if adapter == "mrerp":
        return _dispatch_mrerp_batch(endpoint, histories)

    # 非 mrerp:暂无批量能力 → 循环单张(统一接口 · 行为不变)。
    from services.erp import erp_push

    return [erp_push.push_to_endpoint(endpoint, h) for h in histories]
