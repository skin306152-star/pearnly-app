# -*- coding: utf-8 -*-
"""Pearnly · ERP 端点 CRUD 路由(REFACTOR-WA-B1 · 2026-05-29 R18 从 erp_routes 拆出 · 0 逻辑改)

ERP endpoint 增删改查 + 高级设置(seed/generic 模板码)+ mrerp 凭据 Fernet 加密落地。
erp_routes 顶部 include_router 聚合 · app.py 单一 include 不变。_check_push_access 走 erp_routes_access。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from services.erp import erp_push as _erp
from core.auth import get_current_user_from_request
from core.route_helpers import _plan_permissions, _record_500
from routes.erp_routes_access import _check_push_access

logger = logging.getLogger("mr-pilot")

router = APIRouter()


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


def _strip_endpoint_for_response(ep: Dict[str, Any]) -> Dict[str, Any]:
    """返回前端时,把 token / 加密凭据 字段隐藏,避免泄漏"""
    out = dict(ep)
    cfg = dict(out.get("config") or {})
    # Agent 密钥哈希永不出库到前端(掩码尾段 agent_token_tail / 生成时间保留供 UI 显示)。
    cfg.pop("agent_token_hash", None)
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

        # P0「开箱即用」(Zihao 2026-05-26 拍板) · 退役 client_ids 必填校验。
        # 智能分拣按发票卖方税号路由,推送两条路径(_auto_push_history /
        # _auto_push_smart_routed)都不读 client_ids · 这道闸只会卡死买方
        # 客户列表为空的新用户(连接向导第 1 步永远过不去)。字段保留兼容
        # 老数据,新建默认 [] 保持 shape 一致。
        config = dict(req.config or {})
        # SSRF 防护:存端点前校验 system_url 只指公网,挡内网/元数据(安全评估 2026-07-07)
        from services.erp.ssrf_guard import assert_public_config_url

        try:
            await assert_public_config_url(config)
        except ValueError as _sse:
            raise HTTPException(400, detail=f"erp.blocked_url:{_sse}")
        if req.adapter == "mrerp" and not isinstance(config.get("client_ids"), list):
            config["client_ids"] = []

        # v118.34.13 · 加密凭据再落地 · wizard 发的是 plaintext。
        # 即使字段名叫 _enc · 不加密就 None-op 解密会炸。
        # 2026-05-31 · 从 == "mrerp" 改为 in ENCRYPTED_CRED_ADAPTERS · 让 mrerp_dms
        # 等所有带 Fernet 凭据的 adapter 共用这条加密路径(单一来源 · 防漂移)。
        if req.adapter in _erp.ENCRYPTED_CRED_ADAPTERS:
            try:
                from core.kms_helper import encrypt_str, is_encrypted

                # admin 两键(admin_*_enc)走同一加密清单(双凭据分权 · 单一来源防漂移)。
                for fld in (
                    "username_enc",
                    "password_enc",
                    "admin_username_enc",
                    "admin_password_enc",
                ):
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

        # DMS 防误推铁律(2026-05-31):mrerp_dms endpoint 的 auto_push 必须 false。
        # 发票自动推送按 db.list_erp_endpoints(auto_push_only=True) 选 endpoint,
        # 若 DMS endpoint auto_push=true 会被卷进发票自动推送 → 把 invoice history
        # 误推进 DMS(高危数据错投)。身份证没有自动推送这回事——网页与 LINE 两条路都要人确认。
        effective_auto_push = False if req.adapter == "mrerp_dms" else req.auto_push

        new_id = db.create_erp_endpoint(
            user["id"],
            req.name,
            req.adapter,
            config,
            is_default=req.is_default,
            auto_push=effective_auto_push,
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
        # SSRF 防护:PATCH 也是 system_url 写入边界,同样挡内网/元数据(安全评估 2026-07-07)
        from services.erp.ssrf_guard import assert_public_config_url

        try:
            await assert_public_config_url(new_cfg)
        except ValueError as _sse:
            raise HTTPException(400, detail=f"erp.blocked_url:{_sse}")
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

        # P0「开箱即用」(Zihao 2026-05-26 拍板) · client_ids 已退役(见 POST
        # 路由注释)· PATCH 不再拦"清空 client_ids" · 编辑连接不会再被卡。

        # P-3 · 加密镜像 POST 路由 (v118.34.13 一致)
        # 2026-05-31 · == "mrerp" → in ENCRYPTED_CRED_ADAPTERS(含 mrerp_dms)。
        if target_adapter in _erp.ENCRYPTED_CRED_ADAPTERS:
            try:
                from core.kms_helper import encrypt_str, is_encrypted

                # admin 两键(admin_*_enc)镜像 POST 路由,纳入同一加密清单。
                for fld in (
                    "username_enc",
                    "password_enc",
                    "admin_username_enc",
                    "admin_password_enc",
                ):
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

    # DMS 防误推铁律(2026-05-31):mrerp_dms 的 auto_push 后端兜底强制 false
    # (见 POST 路由同名注释)· 防发票自动推送误投进 DMS。
    if target_adapter == "mrerp_dms" and "auto_push" in fields:
        fields["auto_push"] = False

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
    # P1「开箱即用」· 通用销售商品码 · 配了 → 商品「匹配优先 + 通用兜底 · 不自动建」。
    generic_product_code: Optional[str] = None


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
    if "generic_product_code" in data:
        cfg["generic_product_code"] = data["generic_product_code"] or None
    ok = db.update_erp_endpoint(user["id"], endpoint_id, config=cfg)
    if not ok:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    return {
        "ok": True,
        "seed_customer_code": cfg.get("seed_customer_code"),
        "seed_product_code": cfg.get("seed_product_code"),
        "generic_product_code": cfg.get("generic_product_code"),
    }


_EXPRESS_ACC_KEYS = (
    "revenue_acc",
    "ar_acc",
    "vat_output_acc",
    "fallback_acc",
    "ap_acc",
    "vat_input_acc",
)


class ExpressAccountMapping(BaseModel):
    revenue_acc: Optional[str] = None
    ar_acc: Optional[str] = None
    vat_output_acc: Optional[str] = None
    fallback_acc: Optional[str] = None
    ap_acc: Optional[str] = None
    vat_input_acc: Optional[str] = None


@router.patch("/api/erp/endpoints/{endpoint_id}/express-accounts")
async def erp_endpoints_express_accounts(
    endpoint_id: str, req: ExpressAccountMapping, request: Request
):
    """Express「科目映射」· 服务端合并 6 个会计科目码进 config(销项 收入/应收/销项税 +
    采购 采购/应付/进项税)· 让 mapper 拼得出分录(否则 no_revenue_account 留人工)。

    **读 DB 原始 config 仅覆盖这 6 键**(同 /seed 套路 · 不碰 account_set/token/
    reported_accounts/已加密凭据,避开整体替换 config 的破坏)。空串 = 清空(回落无映射)。
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    if (ep.get("adapter") or "").lower() != "express":
        raise HTTPException(400, detail="erp.not_express_endpoint")
    cfg = dict(ep.get("config") or {})
    data = req.dict(exclude_unset=True)
    for k in _EXPRESS_ACC_KEYS:
        if k in data:
            v = str(data[k]).strip()[:40] if data[k] is not None else ""
            cfg[k] = v or None
    ok = db.update_erp_endpoint(user["id"], endpoint_id, config=cfg)
    if not ok:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    return {"ok": True, **{k: cfg.get(k) for k in _EXPRESS_ACC_KEYS}}


_AUTONOMY_LEVELS = ("manual", "standard", "auto")


class ExpressAutonomy(BaseModel):
    autonomy: str


@router.patch("/api/erp/endpoints/{endpoint_id}/express-autonomy")
async def erp_endpoints_express_autonomy(endpoint_id: str, req: ExpressAutonomy, request: Request):
    """Express 自治级别(per 连接)· 服务端只合并 config.autonomy(manual/standard/auto),
    不碰 account_set/科目/凭据。全人工=高置信也转人工复核 / 标准=高置信自动·低置信问 /
    全托管=尽量自动。默认 standard(见 services/erp/express_push/autonomy)。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    level = str(req.autonomy or "").strip().lower()
    if level not in _AUTONOMY_LEVELS:
        raise HTTPException(400, detail="erp.bad_autonomy")
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    if (ep.get("adapter") or "").lower() != "express":
        raise HTTPException(400, detail="erp.not_express_endpoint")
    cfg = dict(ep.get("config") or {})
    cfg["autonomy"] = level
    ok = db.update_erp_endpoint(user["id"], endpoint_id, config=cfg)
    if not ok:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    return {"ok": True, "autonomy": level}
