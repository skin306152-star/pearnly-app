# -*- coding: utf-8 -*-
"""
Mr.Pearnly · v109.3 商业模式核心
==============================
- 自由注册(7 天 trial · 50 张 / 3 客户)
- 套餐拦截(trial / free / pro / firm)
- 付费提交(KBank / PromptPay)+ 后台审核
- 后台用户管理 + 漏斗 + 待审核付款
"""

import re
import logging
import traceback
import json
from typing import Optional
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger("mrpilot.signup")

from services.auth.schema import _ensure_schema  # 启动期表迁移(模块化深化)

router = APIRouter(tags=["signup-v109.3"])


# ============================================================
# 套餐定义(单一权威源)
# ============================================================
# ============================================================
# v111.1 · 套餐定义重整(2026-05-04)
#
# 新模型 5 档:
#   trial    - 7 天试用 · 100 张/月 · 一次 15 文件
#   monthly  - ฿299/月 · 500 张/月 · 一次 30 文件
#   yearly   - ฿2,990/年 · 1500 张/月 · 一次 50 文件
#   lifetime - ฿9,900 一次买断 · 无限 · 自带 Gemini key · 一次 100 文件
#   admin    - super admin · 无限 · 一次 999 文件
#
# v118.46(2026-05-27 计费迁移收尾)· 全平台只剩 credits + admin 两档 ·
#   老套餐 trial/monthly/yearly/lifetime/free/pro/firm/enterprise + LEGACY_PLAN_MAP 全删 ·
#   _get_plan 非超管恒返 credits · 数据库残留老 plan 值无害(上层一律 credits)。
# ============================================================

# 注册共享 helper + 常量 → services/auth/signup_core.py(模块化深化 · 2026-06-01)· 下方 re-export 给消费者。
from services.auth.signup_core import (  # noqa: F401
    PLAN_CONFIG,
    DISPOSABLE_EMAIL_DOMAINS,
    normalize_email,
    is_disposable_email,
    get_client_ip_safe,
    get_ip_subnet24,
    check_signup_abuse,
    is_signup_globally_disabled,
    _now,
    _hash_password,
    _get_user_safe,
    _row_get,
    _row_count,
    _require_super_admin,
    _get_plan,
    _ensure_tenant_for_new_user,
    get_plan_features,
)


# ============================================================
# Pydantic
# ============================================================
class SignupRequest(BaseModel):
    email: str
    password: str
    verification_code: Optional[str] = None  # v118.27.6 · 邮箱验证码(必填 · 走 send_email_code 后)
    company_name: Optional[str] = None  # v118.9 · 选填 · 空时后端用 email 前缀兜底
    full_name: Optional[str] = None
    role: Optional[str] = None
    monthly_volume: Optional[str] = None
    country: str = "TH"
    phone: Optional[str] = None
    line_id: Optional[str] = None
    signup_source: Optional[str] = None
    invite_code: Optional[str] = None
    newsletter_opt_in: bool = True
    fingerprint: Optional[str] = None


# LineLinkRequest → auth_me_routes.py(模块化深化 · 2026-06-01)。


# ForgotPasswordRequest / ResetPasswordRequest → auth_password_routes.py(模块化深化 · 2026-06-01)。
class LoginRequest(BaseModel):
    username: str
    password: str
    remember: bool = False


class PaymentSubmitRequest(BaseModel):
    target_plan: str  # pro / firm
    payer_name: Optional[str] = None
    payer_note: Optional[str] = None
    # 截图通过 multipart 上传 · 见路由


# CLEANUP-PLAN-01 (2026-05-22) · AdminUpgradeRequest 整段删
# 老订阅模式 admin "升级套餐" pydantic model · credits 模式不再需要


# ============================================================
# 路由 · 注册
# ============================================================
@router.post("/api/auth/signup")
def signup(req: SignupRequest, request: Request):
    """新用户注册 · 自动 trial 7 天 · 自动登录 · 5 层防薅"""
    try:
        # 紧急止血:全局禁用注册
        if is_signup_globally_disabled():
            raise HTTPException(status_code=503, detail="signup_temporarily_disabled")

        from core import db as _db
        from core.auth import create_access_token

        # 校验
        email_raw = (req.email or "").strip().lower()
        if not email_raw or "@" not in email_raw or "." not in email_raw.split("@", 1)[1]:
            raise HTTPException(status_code=400, detail="email_invalid")
        if len(req.password or "") < 6:
            raise HTTPException(status_code=400, detail="password_too_short")
        country = (req.country or "TH").upper()
        if country not in ("TH", "CN", "JP", "EN", "US"):
            country = "TH"

        # v118.9 · company_name / full_name 改为选填(注册门槛降到最低 · 用户进入产品后在设置页可补全)
        # 空时用 email 前缀兜底 · 防 NULL · 防 fallback 显示完整 email
        email_prefix = email_raw.split("@", 1)[0] if email_raw else None
        company = (req.company_name or "").strip() or (email_prefix or "用户")
        full_name_safe = (req.full_name or "").strip() or None  # 姓名仍为选填 · 没有就 NULL

        # 防薅 1 · 临时邮箱拦截
        if is_disposable_email(email_raw):
            _log_risk(None, "disposable_email", request, {"email": email_raw})
            raise HTTPException(status_code=400, detail="disposable_email_not_allowed")

        # v118.27.6 · 邮箱验证码必校(走 /api/auth/send_email_code 拿到后才能注册)
        code_input = (req.verification_code or "").strip()
        if not code_input or not re.match(r"^\d{4,8}$", code_input):
            raise HTTPException(status_code=400, detail="verification_code_required")
        try:
            with _db.get_cursor(commit=True) as _cur_v276:
                _cur_v276.execute(
                    """
                    SELECT id, expires_at, used FROM email_codes
                    WHERE email = %s AND code = %s AND purpose = 'signup'
                    ORDER BY id DESC LIMIT 1
                """,
                    (email_raw, code_input),
                )
                _row_v276 = _cur_v276.fetchone()
                if not _row_v276:
                    raise HTTPException(status_code=400, detail="verification_code_invalid")
                _r_v276 = dict(_row_v276) if not isinstance(_row_v276, dict) else _row_v276
                if _r_v276.get("used"):
                    raise HTTPException(status_code=400, detail="verification_code_used")
                _cur_v276.execute("SELECT NOW() > %s AS expired", (_r_v276["expires_at"],))
                _exp_v276 = _cur_v276.fetchone()
                _expired_v276 = (
                    _exp_v276.get("expired")
                    if isinstance(_exp_v276, dict)
                    else (_exp_v276[0] if _exp_v276 else True)
                )
                if _expired_v276:
                    raise HTTPException(status_code=400, detail="verification_code_expired")
                # 标已用(防多账号复用同一 code)
                _cur_v276.execute(
                    "UPDATE email_codes SET used = TRUE, used_at = NOW() WHERE id = %s",
                    (_r_v276["id"],),
                )
        except HTTPException:
            raise
        except Exception as _e_v276:
            logger.error(f"[v118.27.6] verify code in signup: {_e_v276}")
            raise HTTPException(status_code=500, detail="verification_code_check_failed")

        # 防薅 2 · 邮箱归一化
        email_norm = normalize_email(email_raw)

        # 防薅 3-4-5 · IP / subnet / fingerprint 检查
        ip = get_client_ip_safe(request)
        subnet = get_ip_subnet24(ip)
        fingerprint = (req.fingerprint or "").strip()[:128] or None
        ua = request.headers.get("user-agent", "")[:512]

        abuse = check_signup_abuse(email_norm, ip, fingerprint)
        if abuse:
            _log_risk(
                None,
                abuse,
                request,
                {
                    "email_norm": email_norm,
                    "ip": ip,
                    "subnet": subnet,
                    "fingerprint": fingerprint,
                },
            )
            # 友好转译 · 不暴露具体规则
            if abuse == "email_already_registered":
                raise HTTPException(status_code=409, detail="email_already_registered")
            else:
                raise HTTPException(status_code=429, detail="rate_limited_try_later")

        with _db.get_cursor(commit=True) as cur:
            # 创建用户
            username = email_raw
            password_hash = _hash_password(req.password)

            # 邀请码处理 · v118.35.0.4 默认 credits(pay-as-you-go)· 不再 trial
            invite_plan = "credits"
            if req.invite_code:
                code = req.invite_code.strip().upper()
                if code in ("PARTNER2026", "VIP2026"):
                    invite_plan = "pro"
                elif code in ("FIRM2026",):
                    invite_plan = "firm"

            # v118.35.0.4 · credits 不设 trial 到期 · 走充值余额
            trial_exp = None
            plan_exp = None
            if invite_plan in ("pro", "firm"):
                plan_exp = _now() + timedelta(days=30)

            # 取 users 表实际有的列(避免插入不存在的字段触发 transaction abort)
            cur.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name='users' AND table_schema='public'
                """)
            cols_raw = cur.fetchall()
            existing_cols = set()
            for r in cols_raw:
                if isinstance(r, dict):
                    existing_cols.add(r.get("column_name"))
                else:
                    existing_cols.add(r[0])

            # 准备完整字段 · 但只用实际存在的
            all_fields = {
                "username": username,
                "password_hash": password_hash,
                "email": email_raw,
                "email_normalized": email_norm,
                "company_name": company,
                "full_name": full_name_safe,
                "user_role": (req.role or "").strip() or None,
                "monthly_volume": (req.monthly_volume or "").strip() or None,
                "phone": (req.phone or "").strip() or None,
                "signup_source": (req.signup_source or "").strip() or None,
                "newsletter_opt_in": bool(req.newsletter_opt_in),
                "plan": invite_plan,
                "trial_expires_at": trial_exp,
                "plan_expires_at": plan_exp,
                "signup_country": country,
                "line_id": (req.line_id or "").strip() or None,
                "signup_ip": ip,
                "signup_ip_subnet": subnet,
                "signup_fingerprint": fingerprint,
                "signup_user_agent": ua,
                "role": "owner",
                "is_super_admin": False,
                "is_active": True,  # v109.3.2 · 显式设 true · 防止 NULL 触发 403
            }
            # 过滤出只在表里实际存在的字段
            use_fields = {k: v for k, v in all_fields.items() if k in existing_cols}
            col_names = list(use_fields.keys())
            col_values = [use_fields[k] for k in col_names]

            # 时间字段单独加(用 NOW())
            created_clause = ""
            if "created_at" in existing_cols:
                col_names.append("created_at")
                created_clause = ""  # 直接在 SQL 里写 NOW()
            if "last_seen_at" in existing_cols:
                col_names.append("last_seen_at")

            placeholders = ", ".join(["%s"] * len(col_values))
            # 加上 NOW() 占位
            ts_placeholders = []
            if "created_at" in existing_cols:
                ts_placeholders.append("NOW()")
            if "last_seen_at" in existing_cols:
                ts_placeholders.append("NOW()")
            if ts_placeholders:
                placeholders = placeholders + ", " + ", ".join(ts_placeholders)

            col_sql = ", ".join(col_names)
            insert_sql = f"INSERT INTO users({col_sql}) VALUES ({placeholders}) RETURNING id"
            logger.info(f"signup insert · fields used: {len(use_fields)}/{len(all_fields)}")
            cur.execute(insert_sql, col_values)
            user_id = _row_count(cur.fetchone())

            # v118.26.2.5 · 同事务建 tenant + 回填 tenant_id(失败不阻塞)
            _new_tid = _ensure_tenant_for_new_user(
                cur,
                str(user_id),
                invite_plan,
                company_name=company,
                full_name=full_name_safe,
                username=username,
            )

            # 订阅日志(同一事务 · 不能 try/except)
            # v118.35.0.4 · credits + trial 都算自然注册 · 邀请码升级才算 invite_code
            cur.execute(
                """
                    INSERT INTO subscription_log(user_id, from_plan, to_plan, reason)
                    VALUES (%s, NULL, %s, %s)
                """,
                (
                    user_id,
                    invite_plan,
                    "signup" if invite_plan in ("credits", "trial") else "invite_code",
                ),
            )

            # v118.35.0.4 · credits 新公司初始化 0 余额 · pay-as-you-go 待充值
            if invite_plan == "credits" and _new_tid:
                try:
                    _db.ensure_tenant_credits(_new_tid)
                except Exception as ce:
                    logger.warning(f"[signup] ensure_tenant_credits skip: {ce}")

        # 自动创建 1 个示例客户(独立事务 · 失败不影响主注册)
        try:
            with _db.get_cursor(commit=True) as cur2:
                cur2.execute(
                    """
                    INSERT INTO clients(user_id, name, color, is_active, created_at)
                    VALUES (%s, %s, '#3b82f6', true, NOW())
                """,
                    (user_id, "ลูกค้าตัวอย่าง / Sample Client"),
                )
        except Exception as ce:
            logger.warning(f"signup sample client skip: {ce}")

        # v118.26.2.5 · token 带 tenant_id(若新建成功)· 用户首次登录就有 tenant
        token = create_access_token(
            user_id=str(user_id),
            username=username,
            plan=invite_plan,
            tenant_id=_new_tid,
            role="owner",
            is_super_admin=False,
            remember_me=False,
        )
        return {
            "ok": True,
            "user_id": str(user_id),
            "token": token,
            "plan": invite_plan,
            # v118.35.0.4 · credits 用户不走 LINE 防薅闸 · 直接 pay-as-you-go
            "needs_line_verify": invite_plan == "trial",
            "trial_expires_at": trial_exp.isoformat() if trial_exp else None,
            "plan_expires_at": plan_exp.isoformat() if plan_exp else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"signup failed: {e}\n{traceback.format_exc()}")
        # v118.35.0.18 · detail 改成固定 code · 走前端 i18n · 不再把 Python 异常对象拼给用户看
        raise HTTPException(status_code=500, detail="signup_error")


# ============================================================
# Google/LINE OAuth 建号 → services/auth/oauth_create.py(模块化深化 · 2026-06-01)。


def _log_risk(user_id, event_type, request, detail_dict=None):
    """记录风控事件"""
    try:
        from core import db as _db

        ip = get_client_ip_safe(request) if request else None
        fp = None
        if request:
            try:
                # 从请求 body 取 fingerprint(可选)
                pass
            except Exception:
                pass  # 占位 stub · fingerprint 提取未实现
        with _db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                    INSERT INTO risk_log(user_id, event_type, ip, fingerprint, detail)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, event_type, ip, fp, json.dumps(detail_dict or {}, ensure_ascii=False)),
            )
    except Exception as e:
        logger.warning(f"_log_risk skip: {e}")


# ============================================================
# LINE 绑定(防薅核心 · 解锁完整 trial 配额)
# ============================================================
# link_line(+dev) + get_my_plan → auth_me_routes.py(模块化深化 · 2026-06-01)· 下方 include。


# v118.35.0.11 · /api/payment/submit 路由永久下线 · credits 系统不再走升级模式 · 用户冲入是 /api/credits/topup/request
# CLEANUP-PLAN-01 (2026-05-22) · funnel 改瘦:删 by_plan / trial_expiring_soon / conversion_pct
#   credits 模式不再有"套餐"概念 · admin 只看用户增长 + 国家分布
# 超管风控/用户管理 8 路由 → auth_admin_routes.py(模块化深化 · 2026-06-01)· 下方 include。
# 密码路由组已抽到 auth_password_routes.py(模块化深化 · 2026-06-01)·
# re-export send_reset_link_for_employee 给 team_routes(不改其 import)。
from routes.auth_password_routes import (  # noqa: E402
    router as _password_router,
    send_reset_link_for_employee,  # noqa: F401 · re-export(team_routes 用)
)

router.include_router(_password_router)
from routes.auth_admin_routes import router as _admin_router  # noqa: E402

router.include_router(_admin_router)
from routes.auth_me_routes import router as _me_router  # noqa: E402

router.include_router(_me_router)


_ensure_schema()
