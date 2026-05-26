# -*- coding: utf-8 -*-
"""
Pearnly · ERP 推送 API 路由模块(REFACTOR-B1 · 2026-05-25 抽出)

ERP 推送(支柱 3)· endpoints CRUD / test-connection / customers / products /
push / logs / stats / retry / batch · 15 路由 + _check_push_access + 6 model +
_strip_endpoint_for_response + _fetch_listing_with_retry。从 app.py 整片搬过来 ·
纯搬家 · 不改业务逻辑 / URL / response shape / 错误码。

⚠️ 铁律 #10(async tripwire):test-connection / customers / products / push 是
async 路由调 sync Playwright(MRERPAdapter via erp_push)· 路由体内保留
`await asyncio.to_thread(...)` / `run_in_executor`(局部 import asyncio as _asyncio)·
不能在 asyncio loop 里直接跑 Playwright sync API。
AsyncLoopOffloadTests(test_erp_test_connection_route_dispatch.py)守门。

自动推送后台 helper(_auto_push_history / _auto_push_xero_for_history /
_trigger_auto_push_all)留在 app.py(由 OCR hook 触发 · 非路由 · 复用 _erp)·
不在本模块。

依赖:
  - db.*(推送日志 / endpoint / 重试队列等)
  - erp_push as _erp(adapter 注册 + push_to_endpoint + test_* + list_*)
  - auth.get_current_user_from_request
  - route_helpers._plan_permissions(push 准入闸)· _tid(取 tenant_id)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import db
import erp_push as _erp
from auth import get_current_user_from_request
from route_helpers import _plan_permissions, _record_500, _tid

logger = logging.getLogger("mr-pilot")

router = APIRouter()


def _check_push_access(user: dict):
    """所有 plan 都可用 ERP 推送(v0.8)· Free 有数量限制,无自动推"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_push_erp"):
        raise HTTPException(403, detail="erp.upgrade_required")


class ErpEndpointCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    adapter: str = Field(..., description="webhook | mr_erp | flowaccount")
    config: Dict[str, Any] = Field(default_factory=dict, description="适配器配置:url/token/...")
    is_default: bool = False
    auto_push: bool = False


class ErpEndpointUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    config: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    auto_push: Optional[bool] = None
    enabled: Optional[bool] = None


class ErpTestConnectionRequest(BaseModel):
    adapter: str
    config: Dict[str, Any] = Field(default_factory=dict)


def _strip_endpoint_for_response(ep: Dict[str, Any]) -> Dict[str, Any]:
    """返回前端时,把 token / 加密凭据 字段隐藏,避免泄漏"""
    out = dict(ep)
    cfg = dict(out.get("config") or {})
    if "token" in cfg and cfg["token"]:
        t = str(cfg["token"])
        cfg["token"] = (t[:4] + "***" + t[-4:]) if len(t) > 10 else "***"
        cfg["_token_set"] = True
    # P1-B / C-1 · MR.ERP endpoints store Fernet-encrypted creds. The
    # UI must never see them — replace with sentinel flags so the
    # wizard knows credentials are present without exposing the values.
    for sensitive in ("username_enc", "password_enc"):
        if sensitive in cfg and cfg[sensitive]:
            cfg[sensitive] = "***"
            cfg[f"_{sensitive}_set"] = True
    out["config"] = cfg
    return out


@router.get("/api/erp/endpoints")
async def erp_endpoints_list(request: Request):
    user = get_current_user_from_request(request)
    _check_push_access(user)
    items = db.list_erp_endpoints(user["id"])
    return {"items": [_strip_endpoint_for_response(it) for it in items]}


@router.post("/api/erp/endpoints")
async def erp_endpoints_create(req: ErpEndpointCreate, request: Request):
    """v118.34.13 (Zihao 2026-05-19 拍板) · 加 try/except + 500 现场记录 +
    mrerp 凭据先 Fernet 加密再存盘。之前 wizard 把 plaintext 塞进
    username_enc/password_enc 字段名(假签名)· DB 存的是明文 ·
    回头 test-connection 解密就 InvalidToken。现在路由识别 mrerp ·
    走 kms_helper.encrypt_str 转 ciphertext 再落地。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    p = _plan_permissions(user.get("plan", "free"))

    try:
        # v0.8 · 数量限制
        ep_limit = p.get("endpoints_limit", 1)
        if ep_limit != -1:
            existing = db.list_erp_endpoints(user["id"])
            if len(existing) >= ep_limit:
                raise HTTPException(
                    403,
                    detail={
                        "code": "erp.endpoint_limit_reached",
                        "limit": ep_limit,
                    },
                )

        # v0.8 · 自动推送权限
        if req.auto_push and not p.get("can_auto_push_erp"):
            raise HTTPException(403, detail="erp.auto_push_plus_required")

        if req.adapter not in _erp.ADAPTER_REGISTRY:
            raise HTTPException(400, detail="erp.unknown_adapter")

        # Bug 1 (Zihao 2026-05-19 拍板 · v118.34.22) · 拒绝没绑客户的 mrerp endpoint
        # 落库 · 否则推送时 ERR_NO_CLIENT 一连串失败. 前端 wizard Step 1 也加了
        # 一道闸 · 这里是双保险(API 直接打过来 / 老 wizard 残留状态).
        config = dict(req.config or {})
        if req.adapter == "mrerp":
            client_ids = config.get("client_ids") or []
            if not isinstance(client_ids, list) or not client_ids:
                raise HTTPException(
                    400,
                    detail={
                        "code": "erp.endpoint_no_clients",
                        "message_zh": "这个 ERP 连接还没绑任何 Pearnly 客户 · 请在向导第 1 步至少选 1 个客户",
                        "message_en": "No Pearnly clients linked to this ERP connection · pick at least one in wizard Step 1",
                    },
                )

        # v118.34.13 · 加密 mrerp 凭据再落地 · wizard 发的是 plaintext。
        # 即使字段名叫 _enc · 不加密就 None-op 解密会炸。
        if req.adapter == "mrerp":
            try:
                from kms_helper import encrypt_str, is_encrypted

                for fld in ("username_enc", "password_enc"):
                    v = config.get(fld)
                    if v and isinstance(v, str) and not is_encrypted(v):
                        config[fld] = encrypt_str(v)
            except ImportError as e:
                # kms_helper 不可用(env 缺 KMS_KEY)· 记录并报清晰错误,
                # 别让 500 给用户看一片空白。
                _record_500(
                    path="/api/erp/endpoints",
                    method="POST",
                    detail=f"kms_helper unavailable: {e}",
                )
                raise HTTPException(
                    500,
                    detail="erp.kms_key_missing · server KMS_KEY env not set",
                )
            except Exception as e:
                _record_500(
                    path="/api/erp/endpoints",
                    method="POST",
                    detail=f"encrypt failed: {type(e).__name__}: {e}",
                )
                raise HTTPException(
                    500,
                    detail=f"erp.encrypt_failed: {type(e).__name__}",
                )

        new_id = db.create_erp_endpoint(
            user["id"],
            req.name,
            req.adapter,
            config,
            is_default=req.is_default,
            auto_push=req.auto_push,
        )
        if not new_id:
            # db.create_erp_endpoint swallowed the underlying DB error
            # and returned None. Pull the last DB-side error out of the
            # module global if available, otherwise mark as opaque.
            last = getattr(db, "_last_create_endpoint_error", None) or "unknown"
            _record_500(
                path="/api/erp/endpoints",
                method="POST",
                detail=f"db.create_erp_endpoint returned None · {last}",
            )
            raise HTTPException(
                500,
                detail=f"erp.create_failed · {str(last)[:200]}",
            )
        ep = db.get_erp_endpoint(user["id"], new_id)
        return _strip_endpoint_for_response(ep) if ep else {"id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        # Last-resort capture so /api/version's last_500_traceback
        # shows the real stack instead of opaque "create_failed".
        _record_500(
            path="/api/erp/endpoints",
            method="POST",
            detail=f"{type(e).__name__}: {str(e)[:200]}",
        )
        logger.exception("[erp_endpoints_create] unhandled error")
        raise HTTPException(500, detail=f"erp.create_failed: {type(e).__name__}: {str(e)[:200]}")


@router.patch("/api/erp/endpoints/{endpoint_id}")
async def erp_endpoints_update(endpoint_id: str, req: ErpEndpointUpdate, request: Request):
    """P-3 (Zihao 2026-05-19 拍板 · v118.34.21) · PATCH 路由现在镜像 POST
    路由的 Fernet 加密逻辑:wizard 编辑已有 endpoint 重新输入密码时,JS 把
    新密码塞进 username_enc/password_enc 字段名(假签名)· 这条路径之前不
    走加密 → DB 落明文 → test-connection 解密 InvalidToken → ERR_CRED_DECRYPT.

    现在:如果目标 endpoint adapter=='mrerp' 且 PATCH config 携带
    username_enc/password_enc · 用 kms_helper.is_encrypted 判断是不是真
    ciphertext;明文就 encrypt_str 转一次再 update。已是 ciphertext
    (gAAAAA*)的不动 · 防止 double-encrypt。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    # 如果 config 里 token 是 "***" 占位符,说明用户没改 token,要保留旧值
    fields = {k: v for k, v in req.dict(exclude_unset=True).items() if v is not None}

    # 先查目标 endpoint 的 adapter · PATCH 不带 adapter · 必须从已有数据看
    existing_ep = db.get_erp_endpoint(user["id"], endpoint_id)
    target_adapter = (existing_ep.get("adapter") or "").strip().lower() if existing_ep else ""

    if "config" in fields:
        new_cfg = dict(fields["config"] or {})
        token = str(new_cfg.get("token", ""))
        if token and ("***" in token or token == ""):
            if existing_ep:
                old_token = (existing_ep.get("config") or {}).get("token", "")
                if old_token:
                    new_cfg["token"] = old_token
        # 清掉前端塞的标记字段
        new_cfg.pop("_token_set", None)
        new_cfg.pop("_username_enc_set", None)
        new_cfg.pop("_password_enc_set", None)

        # Bug 1 (v118.34.22) · 镜像 POST 的 client_ids 验证 · PATCH 改 client_ids
        # 为空也得拦下 · 否则用户误删可能 silent regression 全推送失败.
        if target_adapter == "mrerp" and "client_ids" in new_cfg:
            cids = new_cfg.get("client_ids") or []
            if not isinstance(cids, list) or not cids:
                raise HTTPException(
                    400,
                    detail={
                        "code": "erp.endpoint_no_clients",
                        "message_zh": "这个 ERP 连接不能没有 Pearnly 客户 · 至少留 1 个",
                        "message_en": "ERP connection must have at least one Pearnly client",
                    },
                )

        # P-3 · MR.ERP 加密镜像 POST 路由 (v118.34.13 一致)
        if target_adapter == "mrerp":
            try:
                from kms_helper import encrypt_str, is_encrypted

                for fld in ("username_enc", "password_enc"):
                    v = new_cfg.get(fld)
                    if v and isinstance(v, str) and not is_encrypted(v):
                        new_cfg[fld] = encrypt_str(v)
            except ImportError as e:
                _record_500(
                    path=f"/api/erp/endpoints/{endpoint_id}",
                    method="PATCH",
                    detail=f"kms_helper unavailable: {e}",
                )
                raise HTTPException(
                    500,
                    detail="erp.kms_key_missing · server KMS_KEY env not set",
                )
            except Exception as e:
                _record_500(
                    path=f"/api/erp/endpoints/{endpoint_id}",
                    method="PATCH",
                    detail=f"encrypt failed: {type(e).__name__}: {e}",
                )
                raise HTTPException(
                    500,
                    detail=f"erp.encrypt_failed: {type(e).__name__}",
                )

        fields["config"] = new_cfg

    # v0.8 · auto_push 权限
    if fields.get("auto_push"):
        p = _plan_permissions(user.get("plan", "free"))
        if not p.get("can_auto_push_erp"):
            raise HTTPException(403, detail="erp.auto_push_plus_required")

    ok = db.update_erp_endpoint(user["id"], endpoint_id, **fields)
    if not ok:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    return _strip_endpoint_for_response(ep) if ep else {"ok": True}


@router.delete("/api/erp/endpoints/{endpoint_id}")
async def erp_endpoints_delete(endpoint_id: str, request: Request):
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ok = db.delete_erp_endpoint(user["id"], endpoint_id)
    if not ok:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    return {"ok": True}


class ErpSeedUpdate(BaseModel):
    seed_customer_code: Optional[str] = None
    seed_product_code: Optional[str] = None


@router.patch("/api/erp/endpoints/{endpoint_id}/seed")
async def erp_endpoints_update_seed(endpoint_id: str, req: ErpSeedUpdate, request: Request):
    """per-endpoint「高级设置」· 只更新自动创建买方/商品的种子模板码。

    关键(2026-05-26 Zihao 拍板 task 3):服务端合并现有 config · **不碰已加密凭据**。
    前端拿不到明文凭据(被 _strip_endpoint_for_response 抹成 ***)· 故不能走整体替换
    config 的 PATCH(会把 *** 当明文再加密 → 凭据损坏)。这里读 DB 原始 config
    (含真实密文)· 仅覆盖 seed_* 两键 · 原样写回 · username_enc/password_enc 不变。
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    cfg = dict(ep.get("config") or {})
    data = req.dict(exclude_unset=True)
    if "seed_customer_code" in data:
        cfg["seed_customer_code"] = data["seed_customer_code"] or None
    if "seed_product_code" in data:
        cfg["seed_product_code"] = data["seed_product_code"] or None
    ok = db.update_erp_endpoint(user["id"], endpoint_id, config=cfg)
    if not ok:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    return {
        "ok": True,
        "seed_customer_code": cfg.get("seed_customer_code"),
        "seed_product_code": cfg.get("seed_product_code"),
    }


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

    # Other adapters: legacy ping. Keep the historical shape so
    # webhook / flowaccount UIs aren't broken. push_webhook uses
    # `requests.post` which is also sync I/O — to_thread either way.
    return await _asyncio.to_thread(_erp.test_endpoint_connection, req.adapter, cfg)


# C-1 (Zihao 2026-05-18 拍板) · 60-second TTL cache for per-endpoint
# health checks. Drives MRERPAdapter.login + select_company at most
# once per 60s per (user_id, endpoint_id); the wizard / cards UI hits
# this aggressively, so the cache keeps MR.ERP traffic sane.
from services.erp._master_data_cache import TTLCache as _EndpointTestCache  # noqa: E402

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


class ErpPushRequest(BaseModel):
    history_id: str
    endpoint_id: Optional[str] = Field(None, description="不传则用默认端点")


@router.post("/api/erp/push")
async def erp_push(req: ErpPushRequest, request: Request):
    """手动触发推送一条历史记录到指定 endpoint"""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    # 1) 拿历史记录
    history = db.get_ocr_history_detail(user["id"], req.history_id, tenant_id=_tid(user))
    if not history:
        raise HTTPException(404, detail="erp.history_not_found")

    # 2) 选 endpoint
    if req.endpoint_id:
        endpoint = db.get_erp_endpoint(user["id"], req.endpoint_id)
        if not endpoint:
            raise HTTPException(404, detail="erp.endpoint_not_found")
    else:
        endpoint = db.get_default_erp_endpoint(user["id"])
        if not endpoint:
            raise HTTPException(400, detail="erp.no_default_endpoint")

    if not endpoint.get("enabled", True):
        raise HTTPException(400, detail="erp.endpoint_disabled")

    # 批 2 改动 2 (Zihao 2026-05-19 拍板 · v118.34.34) · 推送去重 check.
    # 同 history × endpoint 已经 success 过 → 写 skipped_dup log + 静默
    # 返回原成功的 bill_no. 防同张发票被自动 + 手动 + 重试反复推到 MR.ERP.
    existing = db.has_recent_successful_push(
        req.history_id,
        endpoint["id"],
        user["id"],
    )
    if existing:
        log_id = db.insert_push_log(
            user_id=user["id"],
            endpoint_id=endpoint["id"],
            history_id=req.history_id,
            invoice_no=history.get("invoice_no"),
            seller_name=history.get("seller_name"),
            total_amount=history.get("total_amount"),
            status="skipped_dup",
            http_status=200,
            request_body={
                "adapter": endpoint.get("adapter"),
                "skipped_reason": "already_success",
                "prior_log_id": str(existing.get("id")),
            },
            response_body=existing.get("response_body"),
            error_msg=None,
            attempt=1,
            elapsed_ms=0,
            trigger="manual",
        )
        logger.info(
            "[push-dedup] skipped manual push · history=%s endpoint=%s " "(prior log=%s)",
            req.history_id[:8],
            endpoint["id"][:8],
            str(existing.get("id"))[:8],
        )
        if not log_id:
            # ERP-2:防重日志没写进去(如 status CHECK 约束)· 不静默假装成功 · 显性告知
            logger.warning(
                "[push-dedup] skipped_dup log NOT persisted (insert returned None) · history=%s",
                str(req.history_id)[:8],
            )
        return {
            "ok": True,
            "log_id": log_id,
            "log_write_failed": not log_id,
            "http_status": 200,
            "skipped_dup": True,
            "prior_log_id": str(existing.get("id")),
            "endpoint_name": endpoint.get("name"),
        }

    # 3) 推送 · v118.34.10 · asyncio.to_thread keeps push_to_endpoint
    # (which may call Playwright via push_mrerp once C-1 wires it,
    # plus uses sync `requests` for webhook adapters) off the event loop.
    import asyncio as _asyncio

    result = await _asyncio.to_thread(_erp.push_to_endpoint, endpoint, history)

    # 4) 写日志
    log_id = db.insert_push_log(
        user_id=user["id"],
        endpoint_id=endpoint["id"],
        history_id=req.history_id,
        invoice_no=history.get("invoice_no"),
        seller_name=history.get("seller_name"),
        total_amount=history.get("total_amount"),
        status="success" if result["success"] else "failed",
        http_status=result.get("http_status"),
        request_body=result.get("request_body"),
        response_body=result.get("response_body"),
        error_msg=result.get("error_msg"),
        attempt=1,
        elapsed_ms=result.get("elapsed_ms", 0),
    )

    # 5) 更新 endpoint 统计 + history 推送状态
    db.update_endpoint_stats(endpoint["id"], result["success"])
    db.update_history_push_status(req.history_id, "success" if result["success"] else "failed")

    # v118.25 · 手动推送失败 · 也进重试队列(给用户"扔出去就不管"的体验)
    # 批 1 改动 3 (v118.34.33) · 用户数据错(ERR_NO_CLIENT 等)不入重试 ·
    # retry 没意义 + 污染队列.
    if not result["success"] and log_id:
        if db.is_user_data_error(result.get("error_msg")):
            logger.info(
                "[push] user-data error · NOT scheduling retry · log=%s err=%r",
                str(log_id)[:8],
                (result.get("error_msg") or "")[:80],
            )
        else:
            first_delay = db.get_erp_retry_delay_sec(0)
            if first_delay is not None:
                db.schedule_log_retry(str(log_id), first_delay)

    return {
        "ok": result["success"],
        "log_id": log_id,
        "http_status": result.get("http_status"),
        "error_msg": result.get("error_msg"),
        "elapsed_ms": result.get("elapsed_ms"),
        "endpoint_name": endpoint.get("name"),
    }


@router.get("/api/erp/logs/{log_id}/debug-xlsx")
async def erp_log_debug_xlsx(log_id: str, request: Request):
    """v27.8.1.5 · 推送失败时下载 Pearnly 这次生成的 xlsx · 用户拖给 ERP 服务方诊断
    只有同 tenant 用户能下 · 没存 _debug_xlsx_b64 → 404"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT pl.id, pl.user_id, pl.history_id, pl.request_body, pl.invoice_no,
                       u.tenant_id::text AS tid
                FROM push_logs pl
                LEFT JOIN users u ON u.id = pl.user_id
                WHERE pl.id = %s LIMIT 1
            """,
                (log_id,),
            )
            row = cur.fetchone()
    except Exception as e:
        raise HTTPException(500, detail=f"db.error:{e}")
    if not row:
        raise HTTPException(404, detail="log.not_found")
    # 同 tenant 才能下
    if str(row.get("tid") or "") != str(tid or ""):
        raise HTTPException(403, detail="log.cross_tenant")
    rb = row.get("request_body") or {}
    if isinstance(rb, str):
        try:
            import json as _json

            rb = _json.loads(rb)
        except Exception:
            rb = {}
    b64 = rb.get("_debug_xlsx_b64") if isinstance(rb, dict) else None
    if not b64:
        raise HTTPException(404, detail="log.no_debug_xlsx")
    import base64 as _b64

    try:
        xlsx_bytes = _b64.b64decode(b64)
    except Exception:
        raise HTTPException(500, detail="log.decode_failed")
    from fastapi.responses import Response as _Resp

    safe_inv = (row.get("invoice_no") or "unknown").replace("/", "_").replace(" ", "_")[:40]
    fname = f"pearnly_debug_{safe_inv}_{log_id[:8]}.xlsx"
    return _Resp(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/api/erp/history/{history_id}/push_status")
async def erp_history_push_status(history_id: str, request: Request):
    """P0-2 · 查询某张发票是否已成功推送到 ERP"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    result = db.list_push_logs(user["id"], history_id=history_id, status_filter="success", limit=1)
    items = result.get("items", [])
    if items:
        item = items[0]
        return {
            "pushed": True,
            "pushed_at": str(item["created_at"]),
            "push_log_id": str(item["id"]),
        }
    return {"pushed": False, "pushed_at": None, "push_log_id": None}


@router.get("/api/erp/logs")
async def erp_logs(
    request: Request,
    history_id: Optional[str] = None,
    endpoint_id: Optional[str] = None,
    status: Optional[str] = None,
    trigger: Optional[str] = None,
    adapter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """批 3 改动 6 (v118.34.34) · 新增 adapter 参数 · 让前端按 ERP 类型筛日志."""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    return db.list_push_logs(
        user["id"],
        history_id=history_id,
        endpoint_id=endpoint_id,
        status_filter=status,
        trigger_filter=trigger,
        adapter_filter=adapter,
        limit=min(limit, 200),
        offset=max(0, offset),
    )


@router.get("/api/erp/exceptions")
async def erp_exceptions(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """ERP 推送异常队列(Zihao 2026-05-26)· 派生自 erp_push_logs(铁律 #12 单一源)。

    每个 (history×endpoint) 最近一条仍 failed 的推送 → 一条可处理异常行:
    带 state(needs_action/retrying/failed)+ category(customer_mismatch/product_mismatch/
    no_client/verify_unavailable/other)+ 发票号/卖方/买方/已归属客户/端点名/错误码。
    支持搜索(q)+ category 过滤 + 分页。返回 {items, total, categories}。通用层 · 不写死 MR.ERP。
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)
    return db.list_push_exceptions(
        user["id"], q=q, category=category, limit=min(limit, 200), offset=max(0, offset)
    )


@router.get("/api/erp/logs/{log_id}")
async def erp_log_detail(log_id: str, request: Request):
    """单条日志完整详情 · 含请求体/响应体"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    detail = db.get_push_log_detail(user["id"], log_id)
    if not detail:
        raise HTTPException(404, detail="log.not_found")
    return detail


@router.get("/api/erp/stats/today")
async def erp_stats_today(request: Request):
    """今日推送统计"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    return db.get_push_stats_today(user["id"])


@router.post("/api/erp/logs/{log_id}/retry")
async def erp_retry_push(log_id: str, request: Request):
    """一键重试失败的推送"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    log = db.get_push_log_detail(user["id"], log_id)
    if not log:
        raise HTTPException(404, detail="log.not_found")
    if log["status"] == "success":
        raise HTTPException(400, detail="log.already_success")
    if not log.get("history_id") or not log.get("endpoint_id"):
        raise HTTPException(400, detail="log.missing_refs")

    history = db.get_ocr_history_detail(user["id"], log["history_id"], tenant_id=_tid(user))
    endpoint = db.get_erp_endpoint(user["id"], log["endpoint_id"])
    if not history:
        raise HTTPException(404, detail="history.not_found")
    if not endpoint:
        raise HTTPException(404, detail="erp.endpoint_not_found")

    # v118.34.10 · asyncio.to_thread keeps push_to_endpoint off the loop.
    import asyncio as _asyncio

    result = await _asyncio.to_thread(_erp.push_to_endpoint, endpoint, history)

    # 写新一条日志(attempt 递增)
    new_log_id = db.insert_push_log(
        user_id=user["id"],
        endpoint_id=endpoint["id"],
        history_id=log["history_id"],
        invoice_no=history.get("invoice_no"),
        seller_name=history.get("seller_name"),
        total_amount=history.get("total_amount"),
        status="success" if result["success"] else "failed",
        http_status=result.get("http_status"),
        request_body=result.get("request_body"),
        response_body=result.get("response_body"),
        error_msg=result.get("error_msg"),
        attempt=(log.get("attempt") or 1) + 1,
        elapsed_ms=result.get("elapsed_ms", 0),
        trigger="retry",
    )
    db.update_endpoint_stats(endpoint["id"], result["success"])
    db.update_history_push_status(log["history_id"], "success" if result["success"] else "failed")

    # v118.25 · 手动重试结果同步到原 log 的 retry 状态
    # 成功 → 清队列(终止自动重试)· 失败 → 也清队列(用户已经手动管了 · 不再交给 worker)
    if log.get("next_retry_at"):
        db.clear_retry_schedule(log["id"])

    return {
        "ok": result["success"],
        "log_id": new_log_id,
        "http_status": result.get("http_status"),
        "error_msg": result.get("error_msg"),
        "elapsed_ms": result.get("elapsed_ms"),
    }


# v118.25.1 · 批量重推:从推送日志列表多选 → 一次性触发多条重推
class ErpBatchRetryRequest(BaseModel):
    log_ids: List[str] = Field(..., description="要重推的 log id 列表 · 上限 50")


@router.post("/api/erp/logs/batch-retry")
async def erp_batch_retry(req: ErpBatchRetryRequest, request: Request):
    """批量重推:对每个 log_id 跑一次手动重试逻辑 · 返回成功/失败计数"""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    if not req.log_ids:
        raise HTTPException(400, detail="erp.batch_empty")
    if len(req.log_ids) > 50:
        raise HTTPException(400, detail={"code": "erp.batch_too_many", "max": 50})

    succeeded = 0
    failed = 0
    skipped = 0  # 已成功 / 关联实体丢失等
    details: List[Dict[str, Any]] = []

    for log_id in req.log_ids:
        try:
            log = db.get_push_log_detail(user["id"], log_id)
            if not log:
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "not_found"})
                continue
            if log["status"] == "success":
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "already_success"})
                continue
            if not log.get("history_id") or not log.get("endpoint_id"):
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "missing_refs"})
                continue

            history = db.get_ocr_history_detail(user["id"], log["history_id"], tenant_id=_tid(user))
            endpoint = db.get_erp_endpoint(user["id"], log["endpoint_id"])
            if not history or not endpoint:
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "ref_deleted"})
                continue

            # v118.34.10 · asyncio.to_thread keeps push_to_endpoint off the loop.
            import asyncio as _asyncio

            result = await _asyncio.to_thread(_erp.push_to_endpoint, endpoint, history)
            db.insert_push_log(
                user_id=user["id"],
                endpoint_id=endpoint["id"],
                history_id=log["history_id"],
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="success" if result["success"] else "failed",
                http_status=result.get("http_status"),
                request_body=result.get("request_body"),
                response_body=result.get("response_body"),
                error_msg=result.get("error_msg"),
                attempt=(log.get("attempt") or 1) + 1,
                elapsed_ms=result.get("elapsed_ms", 0),
                trigger="retry",
            )
            db.update_endpoint_stats(endpoint["id"], result["success"])
            db.update_history_push_status(
                log["history_id"], "success" if result["success"] else "failed"
            )
            # 跟单个手动重推一样:用户已经亲自管了 · 把原 log 的自动重试队列摘掉
            if log.get("next_retry_at"):
                db.clear_retry_schedule(log["id"])

            if result["success"]:
                succeeded += 1
                details.append({"log_id": log_id, "result": "success"})
            else:
                failed += 1
                details.append(
                    {"log_id": log_id, "result": "failed", "error": result.get("error_msg")}
                )
        except Exception as e:
            failed += 1
            details.append({"log_id": log_id, "result": "failed", "error": str(e)})

    return {
        "total": len(req.log_ids),
        "succeeded": succeeded,
        "failed": failed,
        "skipped": skipped,
        "details": details,
    }


class ErpBatchDeleteRequest(BaseModel):
    log_ids: List[str] = Field(..., description="要删除的 log id 列表 · 上限 200")


@router.post("/api/erp/logs/batch-delete")
async def erp_batch_delete(req: ErpBatchDeleteRequest, request: Request):
    """Bug 6 (Zihao 2026-05-19 拍板 · v118.34.23) · 批量删除推送日志.
    确认操作不可撤销 · 弹窗确认在 JS 侧 · 这里只管严格 user_id-scoped delete.
    返回 {total, deleted, skipped} · skipped = 不在该用户 scope 内的."""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    if not req.log_ids:
        raise HTTPException(400, detail="erp.batch_empty")
    if len(req.log_ids) > 200:
        raise HTTPException(400, detail={"code": "erp.batch_too_many", "max": 200})

    requested = len(req.log_ids)
    deleted = db.delete_push_logs(user["id"], req.log_ids)
    return {
        "total": requested,
        "deleted": deleted,
        "skipped": max(0, requested - deleted),
    }
