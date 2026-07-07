# -*- coding: utf-8 -*-
"""
Pearnly · ERP 连接测试 / 端点健康检查 / 客户·商品列表(向导 Step-3)+ listing 缓存路由。

从 erp_routes.py 抽出(REFACTOR-WB-modularize · 路由体一字未改)· 子模块自建 `router`,
erp_routes.py include_router 聚合 → app.py 的 include_router(erp_router) 不变。

⚠️ 铁律 #10(async tripwire):test-connection / customers / products 是 async 路由调
sync Playwright(MRERPAdapter via erp_push)· 路由体保留 `await asyncio.to_thread(...)`。
AsyncLoopOffloadTests(test_erp_test_connection_route_dispatch.py)守门。
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from services.erp import erp_push as _erp
from core.auth import get_current_user_from_request
from routes.erp_routes_access import _check_push_access
from services.erp._master_data_cache import TTLCache as _EndpointTestCache

logger = logging.getLogger("mr-pilot")

router = APIRouter()


class ErpTestConnectionRequest(BaseModel):
    adapter: str
    config: Dict[str, Any] = Field(default_factory=dict)


@router.post("/api/erp/test-connection")
async def erp_test_connection(req: ErpTestConnectionRequest, request: Request):
    """前端「测试连接」按钮 · 不写日志、不改任何状态

    v118.34.1 (Zihao 2026-05-19 拍板) · mrerp 必须直接走 MRERPAdapter.login
    + select_company,不能掉进 ADAPTER_REGISTRY → push_mrerp stub。
    v118.34.2 (2026-05-19) · 加路由级 try/except 兜底 + 接受 wizard 发的
    plaintext `{username, password}`(以前只接受 `{username_enc,
    password_enc}` 容易碰到的 ImportError 上浮成 500)。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    if req.adapter not in _erp.ADAPTER_REGISTRY:
        raise HTTPException(400, detail="erp.unknown_adapter")
    cfg = dict(req.config or {})
    cfg.pop("_token_set", None)

    # SSRF 防护:用户可控的 system_url 只许公网目标,挡内网/元数据探测(安全评估 2026-07-07)
    from services.erp.ssrf_guard import assert_public_config_url

    try:
        await assert_public_config_url(cfg)
    except ValueError as _sse:
        raise HTTPException(400, detail=f"erp.blocked_url:{_sse}")

    # mrerp: real login + company-picker scrape (rich shape with
    # ok / companies / error_friendly). Wizard JS already understands
    # this shape. test_mrerp_endpoint is contracted to NEVER raise but
    # the route still wraps the call so a bug in the helper can't
    # surface as a 500 to the UI — we'd rather render a friendly bar.
    #
    # v118.34.10 (Zihao 2026-05-19 拍板) · MUST use asyncio.to_thread:
    # MRERPAdapter uses Playwright's sync_api which explicitly refuses
    # to start when there's a running asyncio loop. FastAPI handlers
    # ARE the running loop, so a direct call raises
    # "Playwright Sync API inside the asyncio loop". to_thread offloads
    # to a worker thread (no running loop there), letting Playwright
    # initialise cleanly. Same applies to every other route in this
    # file that touches MRERPAdapter.
    import asyncio as _asyncio

    if req.adapter == "mrerp":
        try:
            return await _asyncio.to_thread(_erp.test_mrerp_endpoint, cfg)
        except Exception as e:
            logger.exception("erp_test_connection mrerp helper raised")
            return {
                "ok": False,
                "elapsed_ms": 0,
                "companies": [],
                "error_code": "ERR_UNEXPECTED",
                "error_friendly": {
                    "zh": f"服务器内部错误:{type(e).__name__}",
                    "en": f"Internal server error: {type(e).__name__}",
                    "th": f"ข้อผิดพลาดของเซิร์ฟเวอร์: {type(e).__name__}",
                    "zh_TW": f"伺服器內部錯誤:{type(e).__name__}",
                },
                "raw_error": f"{type(e).__name__}: {str(e)[:300]}",
            }

    # mrerp_dms: DMS login + master-data scrape (own never-raise helper).
    # 铁律 #10:Playwright sync API 必须 asyncio.to_thread 离开事件循环。
    if req.adapter == "mrerp_dms":
        try:
            return await _asyncio.to_thread(_erp.test_mrerp_dms_endpoint, cfg)
        except Exception as e:
            logger.exception("erp_test_connection mrerp_dms helper raised")
            return {
                "ok": False,
                "elapsed_ms": 0,
                "masters": {},
                "adapter": "mrerp_dms",
                "error_code": "ERR_UNEXPECTED",
                "error_friendly": {
                    "zh": f"服务器内部错误:{type(e).__name__}",
                    "en": f"Internal server error: {type(e).__name__}",
                    "th": f"ข้อผิดพลาดของเซิร์ฟเวอร์: {type(e).__name__}",
                    "zh_TW": f"伺服器內部錯誤:{type(e).__name__}",
                },
                "raw_error": f"{type(e).__name__}: {str(e)[:300]}",
            }

    # Other adapters: legacy ping. Keep the historical shape so
    # webhook / flowaccount UIs aren't broken. push_webhook uses
    # `requests.post` which is also sync I/O — to_thread either way.
    return await _asyncio.to_thread(_erp.test_endpoint_connection, req.adapter, cfg)


# C-1 (Zihao 2026-05-18 拍板) · 60-second TTL cache for per-endpoint
# health checks. Drives MRERPAdapter.login + select_company at most
# once per 60s per (user_id, endpoint_id); the wizard / cards UI hits
# this aggressively, so the cache keeps MR.ERP traffic sane.
_endpoint_test_cache = _EndpointTestCache(max_size=512, ttl_seconds=60.0)

# 问题 2 (Zihao 2026-05-19 拍板 · v118.34.24) · 客户/商品 listing 缓存 TTL
# 60s → 600s (10 分钟). 同一 tenant 10 分钟内 listing 基本不变 · 频繁拉
# 是性能杀手 + MR.ERP 压力源. wizard 重新打开会刷一次 (refresh=1)
# 也能用 refresh=1 query param 强制 bypass.
# Task 1 (Zihao 2026-05-18 拍板) — separate cache for the customers /
# products dropdown listings used by the wizard's Step 3.
_endpoint_customers_cache = _EndpointTestCache(max_size=512, ttl_seconds=600.0)

# Task 2 Phase 5 (Zihao 2026-05-18 拍板) — same TTL for product listing.
_endpoint_products_cache = _EndpointTestCache(max_size=512, ttl_seconds=600.0)


def flush_test_connection_caches():
    """v118.34.4 · 启动时清空 test-connection / 客户 / 商品 listing 缓存 ·
    REFACTOR-B1(2026-05-25):3 个缓存随 erp 路由搬到本模块 · app.py 启动钩子改调本函数
    (原先在 app.py 内直接 .clear() · 缓存搬走后裸名失效)。"""
    _endpoint_test_cache.clear()
    _endpoint_customers_cache.clear()
    _endpoint_products_cache.clear()


@router.post("/api/erp/endpoints/{endpoint_id}/test-connection")
async def erp_endpoint_test_connection(
    endpoint_id: str,
    request: Request,
    refresh: bool = False,
):
    """Per-endpoint health check. Loads the stored endpoint (with its
    Fernet-encrypted credentials), runs adapter-specific verification
    (MR.ERP: login + select_company + scrape companies dropdown), and
    returns a structured result the wizard / cards UI can render.

    Caches by (user_id, endpoint_id) for 60s. Pass `?refresh=1` to
    bypass the cache (used by the explicit "重新测试" button).

    Returns 200 with `{ok: bool, ...}` either way — the UI uses `ok`
    to decide the pill colour. Auth / not-found responses still HTTP
    error normally so the UI can show a generic toast.
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(404, detail="erp.endpoint_not_found")

    cache_key = (str(user["id"]), str(endpoint_id))
    if not refresh:
        cached = _endpoint_test_cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

    adapter = (ep.get("adapter") or "").strip().lower()
    config = ep.get("config") or {}
    # v118.34.2 (2026-05-19) · try/except wrapper mirrors the legacy
    # route so even a bug in test_mrerp_endpoint can't surface as a 500.
    # v118.34.10 · asyncio.to_thread keeps Playwright's sync API off
    # the FastAPI event loop (refuses to start otherwise).
    import asyncio as _asyncio

    try:
        if adapter == "mrerp":
            result = await _asyncio.to_thread(_erp.test_mrerp_endpoint, config)
        elif adapter == "mrerp_dms":
            result = await _asyncio.to_thread(_erp.test_mrerp_dms_endpoint, config)
        else:
            # webhook / flowaccount / etc — defer to the existing ping test.
            legacy = await _asyncio.to_thread(_erp.test_endpoint_connection, adapter, config)
            result = {
                "ok": bool(legacy.get("success")),
                "elapsed_ms": legacy.get("elapsed_ms", 0),
                "http_status": legacy.get("http_status"),
                "raw_error": legacy.get("error_msg"),
                "companies": [],
                "error_code": None if legacy.get("success") else "ERR_TECHNICAL",
                "error_friendly": None,
            }
    except Exception as e:
        logger.exception("erp_endpoint_test_connection helper raised")
        result = {
            "ok": False,
            "elapsed_ms": 0,
            "companies": [],
            "error_code": "ERR_UNEXPECTED",
            "error_friendly": {
                "zh": f"服务器内部错误:{type(e).__name__}",
                "en": f"Internal server error: {type(e).__name__}",
                "th": f"ข้อผิดพลาดของเซิร์ฟเวอร์: {type(e).__name__}",
                "zh_TW": f"伺服器內部錯誤:{type(e).__name__}",
            },
            "raw_error": f"{type(e).__name__}: {str(e)[:300]}",
        }

    from datetime import datetime as _dt

    result["last_tested_at"] = _dt.utcnow().isoformat() + "Z"
    result["cached"] = False
    _endpoint_test_cache.set(cache_key, result)
    return result


async def _fetch_listing_with_retry(
    fetch_fn,
    config: dict,
    *,
    listing_kind: str,
    max_attempts: int = 2,
    delay_seconds: float = 2.0,
) -> dict:
    """A3 (Zihao 2026-05-19 拍板) · transient-aware retry wrapper for
    /endpoints/:id/customers and /endpoints/:id/products.

    Retries up to `max_attempts` times with `delay_seconds` between
    attempts when the underlying fetch reports a transient error
    (ERR_TECHNICAL / ERR_UNEXPECTED / network exception from
    asyncio.to_thread). Non-transient errors (ERR_AUTH /
    ERR_CRED_DECRYPT / ERR_BUSINESS / ERR_NO_CREDS) break out of the
    loop immediately — those don't get better by retrying.

    Always returns a dict matching the underlying fetch's response
    shape; never raises.
    """
    import asyncio as _asyncio

    transient_codes = {"ERR_TECHNICAL", "ERR_UNEXPECTED", "ERR_NETWORK"}
    result: dict = {}
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            await _asyncio.sleep(delay_seconds)
            logger.info(
                "[listing-retry] %s attempt %d/%d after %.1fs delay",
                listing_kind,
                attempt,
                max_attempts,
                delay_seconds,
            )
        try:
            result = await _asyncio.to_thread(fetch_fn, config)
        except Exception as e:
            logger.exception(
                "[listing-retry] %s attempt %d raised",
                listing_kind,
                attempt,
            )
            result = {
                "ok": False,
                listing_kind: [],
                "error_code": "ERR_UNEXPECTED",
                "error_friendly": {
                    "zh": f"服务器内部错误:{type(e).__name__}",
                    "en": f"Internal server error: {type(e).__name__}",
                    "th": f"ข้อผิดพลาดของเซิร์ฟเวอร์: {type(e).__name__}",
                    "zh_TW": f"伺服器內部錯誤:{type(e).__name__}",
                },
                "raw_error": f"{type(e).__name__}: {str(e)[:300]}",
            }
        # Bug 2 (Zihao 2026-05-19 拍板 · v118.34.22) · 每次结果都打可观察 log ·
        # 包含失败截图路径(如果有). 让 journalctl/api/version 一眼看到 retry
        # 链路: 第几次 / 是否成功 / 截图 / 错误码.
        ok_flag = result.get("ok")
        code = result.get("error_code")
        raw = str(result.get("raw_error") or "")
        import re as _re

        shot_match = _re.search(r"screenshot=(\S+\.png)", raw, _re.IGNORECASE)
        shot_path = shot_match.group(1) if shot_match else None
        logger.info(
            "[listing-retry] %s attempt %d → ok=%s code=%s screenshot=%s",
            listing_kind,
            attempt,
            ok_flag,
            code,
            shot_path or "-",
        )
        if ok_flag:
            return result
        # Non-transient: bail out · the retry won't help.
        if code not in transient_codes:
            logger.info(
                "[listing-retry] %s attempt %d code=%s non-transient · bail out",
                listing_kind,
                attempt,
                code,
            )
            return result
        # Transient: loop will retry (unless we just exhausted attempts).
    # All retries exhausted; surface the last result.
    return result


@router.get("/api/erp/endpoints/{endpoint_id}/customers")
async def erp_endpoint_customers(
    endpoint_id: str,
    request: Request,
    refresh: bool = False,
):
    """Task 1 (Zihao 2026-05-18 拍板) · Fetch the MR.ERP customer
    listing for an endpoint so the wizard's Step-3 seed dropdown can
    show real options.

    Returns 200 with `{ok, customers: [{code, name, type_name, prefix}]}`
    or `{ok: false, error_code, error_friendly, raw_error}` on
    auth/network failure so the UI can degrade gracefully (fall back
    to a free-text input).

    Cached 60s per (user_id, endpoint_id). Pass `?refresh=1` to force.
    Only available for `adapter='mrerp'` endpoints.
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(404, detail="erp.endpoint_not_found")

    adapter = (ep.get("adapter") or "").strip().lower()
    if adapter != "mrerp":
        # Other adapters don't have a sensible customer-listing
        # equivalent; surface 200 with empty list so the wizard can
        # render gracefully.
        return {
            "ok": False,
            "customers": [],
            "error_code": "ERR_ADAPTER_NO_CUSTOMERS",
            "error_friendly": {
                "zh": "此适配器没有客户列表接口",
                "en": "This adapter does not expose a customer listing",
                "th": "อะแดปเตอร์นี้ไม่มี API รายชื่อลูกค้า",
                "zh_TW": "此適配器沒有客戶列表介面",
            },
            "elapsed_ms": 0,
        }

    cache_key = (str(user["id"]), str(endpoint_id), "customers")
    if not refresh:
        cached = _endpoint_customers_cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

    # A3 (Zihao 2026-05-19 拍板) · route-level retry + don't-cache-failures
    # for transient listing flakes.
    # Layered with the _fetch_listing's own wait_for_selector + reload
    # (handles slow renders) and gives one full retry cycle if a whole
    # nav round-trip times out (e.g. mid-deploy MR.ERP 5xx).
    result = await _fetch_listing_with_retry(
        _erp.list_mrerp_customers,
        ep.get("config") or {},
        listing_kind="customers",
    )
    from datetime import datetime as _dt

    result["last_fetched_at"] = _dt.utcnow().isoformat() + "Z"
    result["cached"] = False
    # Only cache success — sticky failure was the user-reported "first
    # click works, second click says '无法拉取客户列表'" bug.
    if result.get("ok"):
        _endpoint_customers_cache.set(cache_key, result)
    return result


@router.get("/api/erp/endpoints/{endpoint_id}/products")
async def erp_endpoint_products(
    endpoint_id: str,
    request: Request,
    refresh: bool = False,
):
    """Task 2 Phase 5 (Zihao 2026-05-18 拍板) · Fetch the MR.ERP
    product listing for an endpoint so the wizard's Step-3 seed-product
    dropdown can show real options. Mirrors the customers route + cache."""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(404, detail="erp.endpoint_not_found")

    adapter = (ep.get("adapter") or "").strip().lower()
    if adapter != "mrerp":
        return {
            "ok": False,
            "products": [],
            "error_code": "ERR_ADAPTER_NO_PRODUCTS",
            "error_friendly": {
                "zh": "此适配器没有商品列表接口",
                "en": "This adapter does not expose a product listing",
                "th": "อะแดปเตอร์นี้ไม่มี API รายการสินค้า",
                "zh_TW": "此適配器沒有商品列表介面",
            },
            "elapsed_ms": 0,
        }

    cache_key = (str(user["id"]), str(endpoint_id), "products")
    if not refresh:
        cached = _endpoint_products_cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

    # A3 (Zihao 2026-05-19 拍板) · route-level retry + don't-cache-failures
    # · mirror of customer listing route.
    result = await _fetch_listing_with_retry(
        _erp.list_mrerp_products,
        ep.get("config") or {},
        listing_kind="products",
    )
    from datetime import datetime as _dt

    result["last_fetched_at"] = _dt.utcnow().isoformat() + "Z"
    result["cached"] = False
    if result.get("ok"):
        _endpoint_products_cache.set(cache_key, result)
    return result


class ErpWizardProductsRequest(BaseModel):
    config: Dict[str, Any] = Field(default_factory=dict)


@router.post("/api/erp/wizard/products")
async def erp_wizard_products(req: ErpWizardProductsRequest, request: Request):
    """P1「开箱即用」(§3.4 step 3) · 连接向导「保存前」用内存「明文」凭据
    + 选定账套拉一次 MR.ERP 商品列表,顺带返回一个智能建议的「通用销售商品」
    码(`suggested_generic_code`)让向导预选 —— 新用户连一次就把通用商品配好,
    无需懂概念也不必到「高级设置」里手挑。

    与 saved-endpoint 的 /endpoints/{id}/products 区别:那条要已存 endpoint
    (拿存好的密文凭据),向导新建时还没 endpoint id,只能用表单里的明文。
    `list_mrerp_products` 已支持明文/密文双形态(见 erp_push.py)。

    铁律 #10/#13:`_fetch_listing_with_retry` 内部 `asyncio.to_thread` 调
    sync Playwright,本路由不裸调 —— AsyncLoopOffloadTests 守门。
    返回 200 + `{ok, products, suggested_generic_code, ...}`,失败也是 200 +
    `{ok: false, ...}` 让向导降级(用户可手填 / 跳过)。
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)
    cfg = dict(req.config or {})
    cfg.pop("_token_set", None)

    result = await _fetch_listing_with_retry(
        _erp.list_mrerp_products,
        cfg,
        listing_kind="products",
    )
    # 只在成功时算建议码;失败时不附,前端走降级。
    if result.get("ok"):
        try:
            from services.erp.mrerp_product_sync import suggest_generic_product_code

            result["suggested_generic_code"] = suggest_generic_product_code(
                result.get("products") or []
            )
        except Exception:
            logger.exception("suggest_generic_product_code raised")
            result["suggested_generic_code"] = None
    return result
