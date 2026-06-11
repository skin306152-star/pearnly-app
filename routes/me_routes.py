from __future__ import annotations

"""
me_routes.py · 当前用户身份/资料路由(/api/me 家族)
REFACTOR-B1 · 第二十会话从 app.py 抽出 · 0 业务逻辑改 · 纯后端搬家

包含 3 路由 + 2 model + 1 helper(verbatim · 一起搬 · 它们彼此是唯一消费者):
    GET  /api/me            → UserInfo(response_model)· 调 _build_user_info
    GET  /api/v1/me         → 委托 get_me(v1 别名)
    PUT  /api/me/profile    → ProfileUpdate · 更新用户 profile 字段

    UserInfo(BaseModel)     → /api/me 的 response_model
    ProfileUpdate(BaseModel)→ /api/me/profile 入参
    _build_user_info(user)  → DB user dict → UserInfo dict(纯 response 整形 · 唯一 code 消费者是 get_me)

⚠️ 铁律 #15 敏感区(UserInfo / _build_user_info 字段错位曾致 /api/me 500):
   本次为 **verbatim 整体搬家 · 零字段增删改**。配套 test_me_routes_contract.py 快照 UserInfo
   全字段集 + _build_user_info 返回 key 集 · 任何字段漂移当场 fail。

留在 app.py(不搬 · 故意):
    /api/me/lang · /api/me/needs_email · /api/me/line_complete_email · /api/line/binding*
    —— 这些与 LINE 绑定 / 邮箱验证码基础设施纠缠(send/verify_email_code · LINE webhook)· 留待专项。
    _check_user_quota / _calc_trial_days_left / _ensure_user_profile_columns 等留 app.py(OCR/启动用)。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _plan_permissions

logger = logging.getLogger("mr-pilot")

router = APIRouter()


class UserInfo(BaseModel):
    # v118.35.0.15 · credits 全站统一后 · 所有老 plan/quota 字段改 Optional ·
    # _build_user_info() 已不再返回 plan/monthly_quota/trial_expires_at/
    # plan_expires_at/plan_days_left/tenant_quota/tenant_used 8 字段(v0.11) ·
    # 这里也跟着改成 Optional · 避免 Pydantic ResponseValidationError 500 ·
    # 配额改由 credits 系统(/api/me/credits)接管
    id: str
    username: str
    # v0.15.5 · 明确账号类型(monthly / lifetime / lifetime_pending)· 前端显隐判断用
    account_type: str = "monthly"
    used_this_month: int = 0
    # IP 限流(v0.8 废弃,仅兼容旧前端)
    ip_used_today: Optional[int] = None
    ip_daily_limit: Optional[int] = None
    # 精细化权限(全开 · credits 模型不再区分套餐)
    can_edit_fields: bool = True
    can_verify_tax: bool = True
    can_use_gemini: bool = True
    can_use_typhoon: bool = True
    can_use_custom_template: bool = True
    can_view_history: bool = True
    can_push_erp: bool = True
    can_manage_api_keys: bool = False
    # v0.15 · 买断标识
    has_own_gemini_key: bool = False
    # v0.8
    rd_daily_limit: Optional[int] = None
    can_extract_items: bool = True
    can_auto_push_erp: bool = False
    endpoints_limit: int = 1
    can_archive: bool = True
    can_customize_archive: bool = False
    zip_batch_limit: int = 10
    can_use_email_ingest: bool = False
    can_use_folder_watch: bool = False
    can_use_smart_alert: bool = False
    # 兼容旧字段(不再使用但前端可能仍引用)
    can_use_automation: bool = False
    # 配额(全部默认 0)
    typhoon_quota_monthly: int = 0
    typhoon_used_this_month: int = 0
    history_retention_days: int = 365
    custom_template_limit: int = 0
    # v22 · 多租户
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    tenant_type: Optional[str] = None  # shared_api / byo_api / admin
    tenant_status: Optional[str] = None  # active / warning / suspended / frozen
    role: Optional[str] = None  # owner / member
    is_super_admin: bool = False
    # v118.8.4 · 公司名 + 真实姓名(注册时填的) · 顶栏归属感用
    company_name: Optional[str] = None
    full_name: Optional[str] = None
    # v118.27.6 · Google 头像 URL(OAuth 注册同步)
    avatar_url: Optional[str] = None
    # v110.7 · 欢迎向导 profile 字段
    monthly_volume: Optional[str] = None
    country: Optional[str] = None
    line_id: Optional[str] = None
    phone: Optional[str] = None
    line_verified: bool = False
    profile_filled: bool = True
    # v118.35.0.11 · credits 新加 4 字段
    email: Optional[str] = None
    invited_by: Optional[str] = None
    is_billing_exempt: bool = False
    active_tenant_id: Optional[str] = None
    # === 老字段全部 Optional · _build_user_info 已不返回 · credits 系统接管 ===
    plan: Optional[str] = None  # v0.11 删 · 仅保 Optional 兼容老前端
    monthly_quota: Optional[int] = None  # v0.11 删
    effective_plan: Optional[str] = None  # v0.11 删
    plan_expires_at: Optional[str] = None  # v0.11 删
    plan_days_left: Optional[int] = None  # v0.11 删
    trial_expires_at: Optional[str] = None  # v0.11 删
    trial_days_left: Optional[float] = None  # v0.11 删
    tenant_quota: Optional[int] = None  # v0.11 删
    tenant_used: Optional[int] = None  # v0.11 删
    expires_at: Optional[str] = None  # v0.11 删


# ============================================================
# 辅助:把 DB user 转成 UserInfo
# ============================================================
def _build_user_info(user, ip_used=None, ip_limit=None) -> dict:
    # v118.35.0.11 · credits 统一后 · 老 plan / effective_plan / monthly_quota /
    # plan_expires_at / plan_days_left / trial_expires_at / tenant_quota /
    # tenant_used 字段全部从返回值删除 · 不再做员工继承老板 plan 的 DB 查询 ·
    # 不再算 plan_days_left / trial_days_left 这些套餐到期天数.
    # 配额改由 credits 系统(tenant_credits.balance_thb + monthly_page_usage)
    # 接管 · 前端读 /api/me/credits 拿余额和本月用量 · 设置页只显示用户名 +
    # 计费方式(按使用量计费)+ 价格说明小字.
    role = user.get("role") or "owner"
    is_super = bool(user.get("is_super_admin"))

    # v22 · 多租户:查用户所属租户(显示 tenant_name + tenant_type 给顶栏用)
    tenant_info = None
    if user.get("tenant_id"):
        try:
            tenant_info = db.get_tenant(str(user["tenant_id"]))
        except Exception as _te:
            logger.warning(f"_build_user_info: get_tenant failed: {_te}")
            tenant_info = None

    p_perms = _plan_permissions(None)

    # 自带 key 标识(设置页 API Key 输入框显隐用 · 跟 plan 解耦)
    has_own_key = bool((user.get("gemini_api_key") or "").strip())
    account_type = "lifetime" if has_own_key else "monthly"

    return {
        "id": str(user["id"]),
        "username": user["username"],
        "email": user.get("email") or None,
        "invited_by": user.get("invited_by"),
        "is_billing_exempt": bool(user.get("is_billing_exempt", False)),
        "active_tenant_id": str(user["active_tenant_id"]) if user.get("active_tenant_id") else None,
        "account_type": account_type,  # v0.15.5 · 明确的账号类型 · 供前端显示判断
        "used_this_month": int(user.get("used_this_month", 0) or 0),
        "ip_used_today": ip_used,
        "ip_daily_limit": ip_limit,
        # 基础能力
        "can_edit_fields": p_perms["can_edit_fields"],
        "can_verify_tax": p_perms["can_verify_tax"],
        "rd_daily_limit": p_perms.get("rd_daily_limit"),
        "can_extract_items": p_perms.get("can_extract_items", True),
        # 引擎
        "can_use_gemini": True,
        "can_use_typhoon": True,
        # 历史
        "can_view_history": p_perms["can_view_history"],
        "history_retention_days": p_perms["history_retention_days"],
        # ERP
        "can_push_erp": p_perms["can_push_erp"],
        "can_auto_push_erp": p_perms["can_auto_push_erp"],
        "endpoints_limit": p_perms["endpoints_limit"],
        # 归档
        "can_archive": p_perms["can_archive"],
        "can_customize_archive": p_perms["can_customize_archive"],
        "zip_batch_limit": p_perms["zip_batch_limit"],
        # 自动化
        "can_use_email_ingest": p_perms.get("can_use_email_ingest", False),
        "can_use_folder_watch": p_perms.get("can_use_folder_watch", False),
        "can_use_smart_alert": p_perms.get("can_use_smart_alert", False),
        # 次级
        "can_use_custom_template": p_perms.get("can_use_custom_template", False),
        "custom_template_limit": p_perms.get("custom_template_limit", 0),
        "typhoon_quota_monthly": p_perms.get("typhoon_quota_monthly", 0) or 0,
        "typhoon_used_this_month": user.get("typhoon_used_this_month", 0) or 0,
        "can_manage_api_keys": p_perms.get("can_manage_api_keys", False),
        # v118.35.0.11 · 删除 expires_at / plan_expires_at / plan_days_left /
        #               trial_expires_at / trial_days_left / tenant_quota /
        #               tenant_used · credits 系统接管 · 前端读 /api/me/credits
        "line_verified": bool(user.get("line_user_id") or user.get("line_verified_at")),
        # v0.15 · 新增:买断标识(前端根据此决定显示 API Key 输入框)
        "has_own_gemini_key": has_own_key,
        # v22 · 多租户:供前端显示租户信息 + 判断超管
        "tenant_id": str(user["tenant_id"]) if user.get("tenant_id") else None,
        "tenant_name": tenant_info.get("name") if tenant_info else None,
        "tenant_type": tenant_info.get("tenant_type") if tenant_info else None,
        "tenant_status": tenant_info.get("status") if tenant_info else None,
        "role": role,
        "is_super_admin": is_super,
        # v118.8.4 · 公司名 + 真实姓名(注册时填的) · 顶栏归属感 + 设置页显示
        # v118.12 · 员工的 company_name 应继承自 tenant(他不该自己有公司)
        "company_name": (tenant_info.get("name") if tenant_info else None)
        or user.get("company_name")
        or None,
        "full_name": user.get("full_name") or None,
        # v118.27.6 · Google 头像 URL(OAuth 注册时同步)
        "avatar_url": user.get("avatar_url") or None,
        # v110.7 · 欢迎向导用 · 暴露原始 profile 字段(role 已在上方 · 此处 raw 用于判断"是否填过")
        "monthly_volume": user.get("monthly_volume") or None,
        "country": user.get("country") or None,
        "line_id": user.get("line_id") or None,
        "phone": user.get("phone") or None,
        # v118.12.5 · onboarding wizard 暂时下架(没真实现个性化推荐 · 弹了也是噪音)
        # 永远返回 true · 前端 wizard 不弹 · 后续要恢复直接改回判断逻辑
        "profile_filled": True,
    }


@router.get("/api/me", response_model=UserInfo)
async def get_me(request: Request):
    user = get_current_user_from_request(request)
    return _build_user_info(user, None, None)


@router.get("/api/v1/me")
async def v1_me(request: Request):
    return await get_me(request)


# v110.7 · 用户完善资料 endpoint(欢迎向导 + 设置页共用)
class ProfileUpdate(BaseModel):
    role: Optional[str] = None
    monthly_volume: Optional[str] = None
    country: Optional[str] = None
    line_id: Optional[str] = None
    phone: Optional[str] = None
    # v118.10 · 让用户在设置页能补全姓名 / 公司名(注册时已变成选填)
    full_name: Optional[str] = None
    company_name: Optional[str] = None


@router.put("/api/me/profile")
async def update_me_profile(payload: ProfileUpdate, request: Request):
    """
    v110.7 · 更新当前用户的 profile 字段
    所有字段可选 · 只更新 payload 中明确提供的字段(None 表示不动)
    空字符串 / 仅空白 · 视为清空(写入 NULL)
    v118.10 · 新增 full_name + company_name(让设置页能补全)
    """
    user = get_current_user_from_request(request)

    fields = []
    values = []

    def _add(col, raw, max_len, transform=None):
        # raw 是 None 表示"不更新此字段"; 空字符串表示"清空"
        if raw is None:
            return
        v = (raw or "").strip()
        if transform:
            v = transform(v)
        v = v[:max_len] if v else ""
        fields.append(f"{col} = %s")
        values.append(v if v else None)

    _add("role", payload.role, 32)
    _add("monthly_volume", payload.monthly_volume, 16)
    _add("country", payload.country, 8, transform=lambda s: s.upper())
    _add("line_id", payload.line_id, 64, transform=lambda s: s.lstrip("@"))
    _add("phone", payload.phone, 32)
    # v118.10 · 新增字段
    _add("full_name", payload.full_name, 64)
    _add("company_name", payload.company_name, 200)

    if not fields:
        return {"ok": True, "updated": 0}

    values.append(user["id"])
    sql = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"

    try:
        with db.get_cursor() as cur:
            cur.execute(sql, tuple(values))
    except Exception as e:
        logger.error(f"v110.7 update profile failed for user {user.get('id')}: {e}")
        raise HTTPException(500, detail={"code": "profile.update_failed", "msg": str(e)})

    return {"ok": True, "updated": len(fields)}
