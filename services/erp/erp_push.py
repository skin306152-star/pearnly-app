# -*- coding: utf-8 -*-
"""
Pearnly · ERP 推送模块 (v0.6.0 · 支柱 3)

设计:
- 适配器(adapter)模式:不同的 ERP 走不同的 push 函数,但对外接口统一
- 标准化 payload:不管哪个适配器,都用统一的 JSON 结构
- 失败自动重试:1/5/30 分钟三次重试(放在调用方实现,这里只管单次)
- 推送日志:每次调用都写一条 erp_push_logs

支持的适配器:
- webhook:通用 HTTP POST(MVP)
- flowaccount:FlowAccount API(以后做)
"""

import json
import time
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# E1 verbatim 搬家 re-export(MR.ERP 连接测试 · 调用方/dispatch 测 0 改动)
from services.erp.erp_mrerp_listing import test_mrerp_endpoint  # noqa: E402,F401

# E1b verbatim 搬家 re-export(MR.ERP 客户/产品列表拉取 · erp_mrerp_listing<500)
from services.erp.erp_mrerp_crud import (  # noqa: E402,F401
    list_mrerp_customers,
    list_mrerp_products,
)

# E2 verbatim 搬家 re-export(payload 构造 + 通用 webhook + PUSH_TIMEOUT_SEC · ADAPTER_REGISTRY/调用方 0 改动)
from services.erp.erp_payload import (  # noqa: E402,F401
    PUSH_TIMEOUT_SEC,
    _apply_field_map,
    _iso,
    build_payload_with_idempotency,
    build_standard_payload,
    flatten_history_for_mrerp,
    push_flowaccount,
    push_webhook,
)

# E3 verbatim 搬家 re-export(MR.ERP DMS 推送/连接测试 · dms_routes/erp_routes/push_mrerp_history 0 改动)
from services.erp.erp_dms_push import (  # noqa: E402,F401
    _DMS_DEFAULT_URL,
    _DMS_FRIENDLY,
    _build_mrerp_dms_adapter,
    _dms_friendly,
    _dms_resolve_creds,
    _id_card_payload_from_dict,
    _mrerp_result_dict,
    push_mrerp_dms,
    push_mrerp_dms_id_card,
    test_mrerp_dms_endpoint,
)

# ============================================================
# 适配器分发器(stub · 真分发在 push_to_endpoint)
# ============================================================


def push_mrerp(endpoint_config: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, int, str]:
    """MR.ERP push entry · stub kept for ADAPTER_REGISTRY back-compat.

    The actual mrerp push lives in `push_mrerp_history(endpoint, history)`
    and is dispatched directly from `push_to_endpoint` (early-return for
    adapter='mrerp'), bypassing the (config, payload) shape entirely
    because MRERPAdapter needs the raw history + per-tenant mappings.

    The guard test `test_push_mrerp_is_still_a_refusal_stub` deliberately
    pins this stub down: if it ever stops returning the "not wired" body,
    the test fires — forcing the auditor to re-check whether
    push_to_endpoint's early-return is still in place. Don't remove the
    stub even after the real path lands."""
    return (
        False,
        0,
        (
            "mrerp push is not wired into push_to_endpoint yet; "
            "use MRERPAdapter.upload_invoice_batch directly"
        ),
    )


def load_mrerp_mappings(tenant_id: Optional[str]) -> Dict[str, Any]:
    """P1c · 取该 tenant 的 MR.ERP 主数据映射 bundle(clients/products/accounts/taxes)。
    无 tenant → 空 bundle(行为不变 · 从 push_mrerp_history 抽出)。"""
    try:
        from core import db as _db
    except Exception:
        return {"clients": [], "products": [], "accounts": [], "taxes": []}
    return (
        _db.get_mrerp_mappings_bundle(tenant_id)
        if tenant_id
        else {"clients": [], "products": [], "accounts": [], "taxes": []}
    )


def build_mrerp_adapter(config: Dict[str, Any]):
    """P1c · 从 endpoint.config 构造 MRERPAdapter(行为不变 · 从 push_mrerp_history 抽出)。

    返回 (adapter, err):
      - 成功 → (adapter, None)
      - 失败 → (None, {"http_status", "body", "error_msg"}) · caller 直接拼成 push 结果 dict
    单张(push_mrerp_history)和批量(push_dispatch.dispatch_endpoint_batch)共用此构造逻辑。
    """
    # lazy adapter import (Playwright may be missing on dev boxes).
    try:
        from services.erp.mrerp_adapter import MRERPAdapter
    except ImportError as e:
        return None, {
            "http_status": 0,
            "body": f"playwright_missing: {e}",
            "error_msg": f"ERR_PLAYWRIGHT_MISSING: {e}",
        }

    # credentials. Accept both shapes:
    #   enc_user/enc_pass (Fernet ciphertext via wizard POST encryption)
    #   plain_user/plain_pass (legacy plaintext or PATCH-not-yet-encrypted path)
    enc_user = (config.get("username_enc") or "").strip()
    enc_pass = config.get("password_enc") or ""
    plain_user = (config.get("username") or "").strip()
    plain_pass = config.get("password") or ""

    # If a plaintext field actually contains Fernet ciphertext (the wizard's
    # "edit saved endpoint" pre-fills with stored ciphertext), route it to
    # the decrypt path. Heuristic: gAAAAA* prefix.
    try:
        from core.kms_helper import is_encrypted as _is_enc

        if enc_user and not _is_enc(enc_user):
            plain_user, enc_user = enc_user, ""
        if enc_pass and not _is_enc(enc_pass):
            plain_pass, enc_pass = enc_pass, ""
    except ImportError:
        pass

    common_kwargs: Dict[str, Any] = dict(
        login_url=(config.get("system_url") or "https://www.mrerp4sme.com").strip(),
        comidyear=str(config.get("comidyear") or "6"),
        seldb=str(config.get("seldb") or "1"),
        headless=True,
        retry_attempts=2,
        retry_delays_seconds=(2.0,),
        enable_master_data_sync=True,
        master_data_auto_create=bool(config.get("master_data_auto_create", True)),
        seed_customer_code=(config.get("seed_customer_code") or None),
        seed_product_code=(config.get("seed_product_code") or None),
        # P1「开箱即用」· 通用销售商品码 · 配了 → 商品「匹配优先 + 通用兜底 · 不自动建」;
        # 未配 → 精确模式(逐行 auto-create · 老行为不变 · 保护现有付费用户)。
        generic_product_code=(config.get("generic_product_code") or None),
    )

    try:
        if enc_user and enc_pass:
            adapter = MRERPAdapter.from_encrypted(
                encrypted_username=enc_user,
                encrypted_password=enc_pass,
                **common_kwargs,
            )
        elif plain_user and plain_pass:
            adapter = MRERPAdapter(
                username=plain_user,
                password=plain_pass,
                **common_kwargs,
            )
        else:
            return None, {
                "http_status": 401,
                "body": "no_credentials",
                "error_msg": "ERR_NO_CREDS: username/password missing in endpoint.config",
            }
    except ValueError as e:
        return None, {
            "http_status": 401,
            "body": f"decrypt_failed: {e}",
            "error_msg": f"ERR_CRED_DECRYPT: {e}",
        }
    except Exception as e:
        logger.exception("build_mrerp_adapter: adapter construct failed")
        return None, {
            "http_status": 0,
            "body": f"adapter_construct: {type(e).__name__}: {e}",
            "error_msg": f"ERR_UNEXPECTED: adapter construct: {e}",
        }
    return adapter, None


def push_mrerp_history(
    endpoint: Dict[str, Any],
    history_record: Dict[str, Any],
) -> Dict[str, Any]:
    """A1 (Zihao 2026-05-19 拍板) · The real mrerp pusher.

    Unlike push_webhook / push_flowaccount which work on a "standard
    payload" dict, mrerp's adapter wants the raw history + per-tenant
    mappings. This function builds those, drives
    MRERPAdapter.upload_invoice_batch, and translates the ImportResult
    back into the dict shape push_to_endpoint promises its caller
    (success / http_status / response_body / error_msg / elapsed_ms /
    request_body / adapter / + optional mrerp_bill_no for success).

    Returns the same shape as push_to_endpoint so the calling routes
    (manual push / auto push / log retry / batch retry / retry worker)
    don't need to special-case mrerp at all — they just write the
    insert_push_log + update_history_push_status rows from this result.

    Never raises — every failure path returns a dict.
    """
    t0 = time.time()
    config = endpoint.get("config") or {}
    user_id = endpoint.get("user_id")
    endpoint_id = str(endpoint.get("id") or "")

    # ── flatten OCR pages -> top-level fields so MRERPAdapter._extract_buyer
    #    can find buyer_name (P1c · 抽到 flatten_history_for_mrerp · 行为不变).
    history_flat = flatten_history_for_mrerp(history_record)

    # ── tenant_id needed for mappings + product/customer sync attribution.
    try:
        from core import db as _db
    except Exception as e:
        logger.exception("push_mrerp_history: db import failed")
        return _mrerp_result_dict(
            False,
            0,
            "",
            error_msg=f"ERR_DB_IMPORT: {e}",
            elapsed_ms=int((time.time() - t0) * 1000),
            endpoint_id=endpoint_id,
            history_id=str(history_record.get("id") or ""),
        )

    tenant_id = _db.get_user_tenant_id(user_id) if user_id else None
    if tenant_id:
        history_flat["tenant_id"] = tenant_id

    mappings = load_mrerp_mappings(tenant_id)

    request_body = {
        "history_id": str(history_record.get("id") or ""),
        "invoice_no": history_record.get("invoice_no"),
        "tenant_id": tenant_id,
        "endpoint_id": endpoint_id,
        "adapter": "mrerp",
    }

    def _resp(
        success: bool, http_status: int, body, error_msg: Optional[str] = None, **extra
    ) -> Dict[str, Any]:
        body_str = (
            body if isinstance(body, str) else json.dumps(body, default=str, ensure_ascii=False)
        )
        return {
            "success": success,
            "http_status": http_status,
            "response_body": body_str[:4000],
            "error_msg": error_msg,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "request_body": request_body,
            "adapter": "mrerp",
            **extra,
        }

    # ── build adapter (P1c · 抽到 build_mrerp_adapter · 行为不变:含 playwright
    #    import / cred enc-plain 启发式 / construct;失败回 (None, err) → 同样的 _resp).
    adapter, build_err = build_mrerp_adapter(config)
    if build_err:
        return _resp(
            False,
            build_err["http_status"],
            build_err["body"],
            error_msg=build_err["error_msg"],
        )

    # adapter 已构造成功 → playwright 必可 import · 取异常类用于下方分类。
    from services.erp.mrerp_adapter import (
        MRERPAuthError,
        MRERPTechnicalError,
        MRERPBusinessError,
    )

    # ── run the batch (sync · MUST be off the event loop · the caller
    #    in app.py wraps push_to_endpoint with asyncio.to_thread).
    try:
        with adapter:
            result = adapter.upload_invoice_batch([history_flat], mappings)
    except MRERPAuthError as e:
        return _resp(False, 401, f"auth: {e}", error_msg=f"ERR_AUTH: {e}")
    except MRERPTechnicalError as e:
        return _resp(False, 0, f"technical: {e}", error_msg=f"ERR_TECHNICAL: {e}")
    except MRERPBusinessError as e:
        return _resp(False, 200, f"business: {e}", error_msg=f"ERR_BUSINESS: {e}")
    except Exception as e:
        logger.exception("push_mrerp_history: upload_invoice_batch raised")
        return _resp(
            False, 0, f"unexpected: {type(e).__name__}: {e}", error_msg=f"ERR_UNEXPECTED: {e}"
        )

    # ── translate ImportResult → response dict
    if result.all_success and result.success:
        s = result.success[0]
        body = {
            "ok": True,
            "mrerp_bill_no": s.mrerp_bill_no,
            "invoice_no": s.invoice_no,
            "elapsed_ms": result.elapsed_ms,
            "xlsx_size_bytes": result.xlsx_size_bytes,
        }
        return _resp(True, 200, body, mrerp_bill_no=s.mrerp_bill_no, invoice_no=s.invoice_no)

    # Failure (preflight reject, or report.php หมายเหตุ rejection)
    failed = result.failed[0] if result.failed else None
    reasons = failed.reasons if failed else ["ERR_UNKNOWN_UPLOAD_OUTCOME"]
    friendly = failed.reasons_friendly if failed else []
    screenshot = failed.evidence_screenshot if failed else None
    body = {
        "ok": False,
        "reasons": reasons,
        "reasons_friendly": friendly,
        "screenshot": screenshot,
        "elapsed_ms": result.elapsed_ms,
    }
    return _resp(False, 200, body, error_msg="; ".join(reasons)[:500])


ADAPTER_REGISTRY = {
    "webhook": push_webhook,
    "flowaccount": push_flowaccount,
    "mrerp": push_mrerp,
    "mrerp_dms": push_mrerp_dms,
}

# Adapters whose endpoint.config carries Fernet-encrypted credentials.
# UI must never round-trip the raw values; the test-connection +
# upload routes decrypt at the last moment.
ENCRYPTED_CRED_ADAPTERS = {"mrerp", "mrerp_dms"}


def push_to_endpoint(endpoint: Dict[str, Any], history_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    主入口:把一条 history 推到指定 endpoint。

    返回值统一格式:
    {
        "success": True/False,
        "http_status": 200,
        "response_body": "...",
        "error_msg": None | "...",
        "elapsed_ms": 234,
        "request_body": {推送的完整 JSON},
        "adapter": "webhook",
    }
    """
    adapter = endpoint.get("adapter", "webhook")
    config = endpoint.get("config") or {}

    # DMS guard (2026-05-31) · mrerp_dms is a car-sales ID-card→booking
    # adapter, NEVER an invoice-history target. Reject hard so the invoice
    # auto-push / manual-push paths can't misroute an invoice into DMS.
    # The real DMS flow is POST /api/dms/id-card-booking. Named guard:
    #     test_push_to_endpoint_rejects_mrerp_dms_invoice
    if adapter == "mrerp_dms":
        return {
            "success": False,
            "http_status": 0,
            "response_body": "",
            "error_msg": "ERR_DMS_NOT_INVOICE_ENDPOINT",
            "elapsed_ms": 0,
            "request_body": None,
            "adapter": adapter,
        }

    # A1 (Zihao 2026-05-19 拍板) · MR.ERP early-route.
    #
    # The legacy (config, payload) adapter shape doesn't fit MR.ERP because
    # the batch adapter needs the raw history dict + per-tenant mappings.
    # Route mrerp through push_mrerp_history (the real implementation)
    # before we build the standard payload — this completely bypasses the
    # push_mrerp stub in ADAPTER_REGISTRY, which exists only as a tripwire
    # for guard tests.
    #
    # Named guard test that locks this in:
    #     test_push_to_endpoint_route_calls_mrerp_adapter_not_stub
    if adapter == "mrerp":
        return push_mrerp_history(endpoint, history_record)

    push_fn = ADAPTER_REGISTRY.get(adapter)
    if push_fn is None:
        return {
            "success": False,
            "http_status": 0,
            "response_body": "",
            "error_msg": f"unknown adapter: {adapter}",
            "elapsed_ms": 0,
            "request_body": None,
            "adapter": adapter,
        }

    payload = build_payload_with_idempotency(history_record, str(endpoint.get("id") or ""))
    t0 = time.time()
    try:
        success, http_status, response_body = push_fn(config, payload)
        error_msg = None if success else (response_body[:500] if response_body else "push failed")
    except Exception as e:
        logger.exception(f"[ERP Push] adapter={adapter} 异常")
        success = False
        http_status = 0
        response_body = ""
        error_msg = f"{type(e).__name__}: {str(e)[:300]}"

    elapsed_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[ERP Push] adapter={adapter} success={success} "
        f"http={http_status} elapsed={elapsed_ms}ms "
        f"endpoint_name={endpoint.get('name')!r}"
    )

    return {
        "success": success,
        "http_status": http_status,
        "response_body": response_body,
        "error_msg": error_msg,
        "elapsed_ms": elapsed_ms,
        "request_body": payload,
        "adapter": adapter,
    }


# ============================================================
# 测试连接(给前端「测试连接」按钮用)
# ============================================================


def test_endpoint_connection(adapter: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    用一个最小化测试 payload 调一次,验证配置是否正确。
    """
    test_payload = {
        "source": "mrpilot",
        "version": "1.0",
        "test": True,
        "invoice_no": "TEST-PING",
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "total": "0.00",
        "seller": {"name": "Pearnly Test"},
        "buyer": {"name": "Pearnly Test"},
        "items": [],
        "metadata": {
            "filename": "test-ping.pdf",
            "test_purpose": "connection check from Pearnly",
        },
    }
    push_fn = ADAPTER_REGISTRY.get(adapter)
    if push_fn is None:
        return {
            "success": False,
            "http_status": 0,
            "response_body": "",
            "error_msg": f"unknown adapter: {adapter}",
        }

    t0 = time.time()
    try:
        success, http_status, response_body = push_fn(config, test_payload)
        error_msg = None if success else (response_body[:500] if response_body else "test failed")
    except Exception as e:
        success = False
        http_status = 0
        response_body = ""
        error_msg = f"{type(e).__name__}: {str(e)[:300]}"

    return {
        "success": success,
        "http_status": http_status,
        "response_body": response_body,
        "error_msg": error_msg,
        "elapsed_ms": int((time.time() - t0) * 1000),
    }
