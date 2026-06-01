# -*- coding: utf-8 -*-
"""
Mr.Pearnly · v109.3 商业模式核心
==============================
- 自由注册(7 天 trial · 50 张 / 3 客户)
- 套餐拦截(trial / free / pro / firm)
- 付费提交(KBank / PromptPay)+ 后台审核
- 后台用户管理 + 漏斗 + 待审核付款
"""

import os
import re
import logging
import traceback
import secrets
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

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

PLAN_CONFIG = {
    # === v118.35.0.4 新注册默认 · pay-as-you-go credits ===
    # 月配额不卡(走 tenant_credits.balance_thb 真扣费) · 但保留 features 让
    # 现有 quota/features 链路不空 · features.ocr_per_period=999999 占位 ·
    # 真实计量由 credits 系统在 OCR 端点按余额扣
    "credits": {
        "ocr_per_period": 999999,
        "max_upload_files": 500,
        "max_pages_per_file": 50,
        "max_mb_per_file": 100,
        "clients_max": 999,
        "seats_max": 5,
        "automation": True,
        "advanced_templates": True,
        "batch_export": True,
        "line_bot": True,
        "duration_days": None,
        "needs_own_key": False,
        "price_thb": 0,
        "billing": "credits",
    },
    "admin": {
        "ocr_per_period": 999999,
        "max_upload_files": 9999,  # v118.27.8.1.15 · 999→9999 · admin 必须 >= lifetime(1000)· 内部不变式
        "max_pages_per_file": 999,
        "max_mb_per_file": 500,
        "clients_max": 999999,
        "seats_max": 999999,
        "automation": True,
        "advanced_templates": True,
        "batch_export": True,
        "line_bot": True,
        "duration_days": None,
        "needs_own_key": False,
        "price_thb": 0,
        "billing": "admin",
    },
}


# ============================================================
# 防薅羊毛 · 5 层防御
# ============================================================
# 临时邮箱黑名单(常见 60+ 域名 · 持续维护)
DISPOSABLE_EMAIL_DOMAINS = {
    "tempmail.com",
    "tempmail.net",
    "10minutemail.com",
    "10minutemail.net",
    "guerrillamail.com",
    "guerrillamail.net",
    "guerrillamail.org",
    "mailinator.com",
    "mailinator.net",
    "mailinator.org",
    "throwawaymail.com",
    "yopmail.com",
    "yopmail.net",
    "yopmail.fr",
    "trashmail.com",
    "trashmail.net",
    "trashmail.de",
    "fakeinbox.com",
    "sharklasers.com",
    "grr.la",
    "guerrillamailblock.com",
    "mintemail.com",
    "tempinbox.com",
    "spambox.us",
    "spam4.me",
    "mailcatch.com",
    "maildrop.cc",
    "mailnesia.com",
    "getairmail.com",
    "getnada.com",
    "inboxkitten.com",
    "mvrht.com",
    "tempmailaddress.com",
    "temp-mail.org",
    "temp-mail.io",
    "tempr.email",
    "dispostable.com",
    "discard.email",
    "discardmail.com",
    "moakt.com",
    "tempemail.co",
    "fakemail.net",
    "fakemailgenerator.com",
    "throwaway.email",
    "burnermail.io",
    "emailondeck.com",
    "harakirimail.com",
    "spamgourmet.com",
    "deadaddress.com",
    "anonbox.net",
    "spamcorptastic.com",
    "spamfree24.org",
    "armyspy.com",
    "cuvox.de",
    "dayrep.com",
    "einrot.com",
    "fleckens.hu",
    "gustr.com",
    "jourrapide.com",
    "rhyta.com",
    "superrito.com",
    "teleworm.us",
    "mohmal.com",
    "mailtothis.com",
    "mytemp.email",
}


def normalize_email(email: str) -> str:
    """
    邮箱归一化(防 + alias 和点号绕过)
    a+1@gmail.com → a@gmail.com
    a.b@gmail.com → ab@gmail.com
    """
    if not email or "@" not in email:
        return (email or "").lower().strip()
    local, _, domain = email.lower().strip().partition("@")
    domain = domain.strip()
    # 移除 + alias
    if "+" in local:
        local = local.split("+", 1)[0]
    # Gmail 特殊:点号忽略
    if domain in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")
        domain = "gmail.com"  # 统一
    return f"{local}@{domain}"


def is_disposable_email(email: str) -> bool:
    """检测临时邮箱"""
    if not email or "@" not in email:
        return False
    domain = email.lower().split("@", 1)[1].strip()
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return True
    # 子域也算(如 mail.tempmail.com)
    parts = domain.split(".")
    for i in range(len(parts)):
        sub = ".".join(parts[i:])
        if sub in DISPOSABLE_EMAIL_DOMAINS:
            return True
    return False


def get_client_ip_safe(request: Request) -> str:
    """取真实 IP(过 Cloudflare)"""
    headers = request.headers
    # CF-Connecting-IP 是 Cloudflare 设置的真实 IP
    ip = headers.get("cf-connecting-ip") or headers.get("x-forwarded-for") or ""
    if ip:
        ip = ip.split(",")[0].strip()
    if not ip:
        try:
            ip = request.client.host
        except Exception:
            ip = "unknown"
    return ip


def get_ip_subnet24(ip: str) -> str:
    """取 IPv4 /24 网段(过同 IP 段批量注册)"""
    try:
        if ":" in ip:
            return ip  # IPv6 不做处理
        parts = ip.split(".")
        if len(parts) != 4:
            return ip
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    except Exception:
        return ip


def check_signup_abuse(email_norm: str, ip: str, fingerprint: str = None) -> Optional[str]:
    """
    防薅检查 · 返回错误代码或 None(通过)

    检查项:
    1. 同 IP 24 小时 ≥ 3 个账号 → 拒绝
    2. 同 /24 网段 24 小时 ≥ 10 个 → 拒绝
    3. 同浏览器指纹 7 天 ≥ 2 个 → 拒绝
    4. 同归一化邮箱已存在 → 拒绝(覆盖 + alias 攻击)
    """
    try:
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            # 1. 归一化邮箱重复
            cur.execute(
                """
                    SELECT 1 FROM users
                    WHERE LOWER(COALESCE(email_normalized, '')) = %s
                       OR LOWER(COALESCE(email, '')) = %s
                       OR LOWER(username) = %s
                    LIMIT 1
                """,
                (email_norm, email_norm, email_norm),
            )
            if cur.fetchone():
                return "email_already_registered"

            # 2. 同 IP 24h 上限
            cur.execute(
                """
                    SELECT COUNT(*) FROM users
                    WHERE signup_ip = %s
                      AND created_at > NOW() - INTERVAL '24 hours'
                """,
                (ip,),
            )
            same_ip = _row_count(cur.fetchone(), 0)
            if same_ip >= 3:
                return "ip_rate_limit"

            # 3. 同 /24 段 24h 上限
            subnet = get_ip_subnet24(ip)
            if subnet != ip:  # 仅 IPv4
                cur.execute(
                    """
                        SELECT COUNT(*) FROM users
                        WHERE signup_ip_subnet = %s
                          AND created_at > NOW() - INTERVAL '24 hours'
                    """,
                    (subnet,),
                )
                same_subnet = _row_count(cur.fetchone(), 0)
                if same_subnet >= 10:
                    return "subnet_rate_limit"

            # 4. 同浏览器指纹 7 天上限
            if fingerprint and len(fingerprint) > 8:
                cur.execute(
                    """
                        SELECT COUNT(*) FROM users
                        WHERE signup_fingerprint = %s
                          AND created_at > NOW() - INTERVAL '7 days'
                    """,
                    (fingerprint,),
                )
                same_fp = _row_count(cur.fetchone(), 0)
                if same_fp >= 2:
                    return "device_rate_limit"

        return None
    except Exception as e:
        logger.error(f"check_signup_abuse: {e}")
        return None  # 检查失败时不拦截 · 不影响真用户


def is_signup_globally_disabled() -> bool:
    """紧急止血:全局关闭注册"""
    try:
        v = os.environ.get("DISABLE_SIGNUP", "").strip().lower()
        return v in ("1", "true", "yes")
    except Exception:
        return False


# ============================================================
# DB Schema 迁移(启动时自动跑)
# ============================================================
# _ensure_schema(启动期表迁移)→ services/auth/schema.py(模块化深化 · 2026-06-01)· 顶部 import 回 · 文件末尾调用。


# ============================================================
# 工具
# ============================================================
def _now():
    return datetime.now(timezone.utc)


def _hash_password(password: str) -> str:
    """
    优先用 auth 模块的 hash 函数(保证跟 verify_password 一致)
    依次尝试:hash_password / get_password_hash / make_password
    全失败时 fallback 到 bcrypt(passlib) · 都不行才用 sha256
    """
    try:
        import auth as _a

        for fn_name in (
            "hash_password",
            "get_password_hash",
            "make_password",
            "create_password_hash",
            "password_hash",
        ):
            fn = getattr(_a, fn_name, None)
            if callable(fn):
                return fn(password)
    except Exception:
        pass  # auth 模块无可用 hash 函数 · 走下一兜底
    # 第二选 · passlib bcrypt(项目大概率装了)
    try:
        from passlib.context import CryptContext

        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return ctx.hash(password)
    except Exception:
        pass  # passlib 未装 · 走下一兜底
    # 终极 fallback(可能跟 verify_password 不兼容 · 看 log 警告)
    logger.warning("⚠ Using sha256 fallback for password hashing - verify_password may not match!")
    salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"sha256${salt}${h}"


def _get_user_safe(request: Request):
    try:
        from auth import get_current_user_from_request

        u = get_current_user_from_request(request)
        return u
    except Exception:
        return None


def _row_get(row, key, idx=0, default=None):
    """兼容 dict cursor 和 tuple cursor"""
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(key, default)
    try:
        return row[idx]
    except (IndexError, TypeError, KeyError):
        return default


def _row_count(row, default=0):
    """取 COUNT(*) 或 RETURNING id · dict 列名通常是 'count'/'id' · tuple 是 [0]"""
    if row is None:
        return default
    if isinstance(row, dict):
        # 优先 count · 其次 id · 最后取第一个值
        if "count" in row:
            return row["count"] if row["count"] is not None else default
        if "id" in row:
            return row["id"]
        if len(row) >= 1:
            v = list(row.values())[0]
            return v if v is not None else default
        return default
    try:
        return row[0] if row[0] is not None else default
    except (IndexError, TypeError):
        return default


def _require_super_admin(request: Request):
    u = _get_user_safe(request)
    if not u or not u.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="super_admin required")
    return u


def _get_plan(user_id: str) -> str:
    """v118.46 · 计费迁移收尾(2026-05-27 Zihao 拍板「全迁充值版」)·
    全平台只剩「充值 / 按量扣费」一种(credits)· 老套餐 trial/monthly/yearly/lifetime/free 全下线。
    非超管一律返回 'credits'、super_admin 返回 'admin'。
    功能权限早已扁平化(route_helpers._plan_permissions 忽略 plan · 人人全开),
    OCR 准入只看 credits 余额(app.py v118.46)· 故 plan 不再分档、不再有到期降级逻辑。
    """
    try:
        import db as _db

        with _db.get_cursor() as cur:
            cur.execute(
                "SELECT COALESCE(is_super_admin, false) AS sa FROM users WHERE id=%s",
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return "credits"
            sa = row.get("sa") if isinstance(row, dict) else row[0]
            return "admin" if sa else "credits"
    except Exception as e:
        logger.error(f"_get_plan failed: {e}")
        return "credits"


# ============================================================
# v118.26.2.5 · 新用户注册自动建 tenant
# 解决 v27.7 fix_orphan 留下的根因:signup 不建 tenant · 导致 tenant_id=NULL ·
# 用户加员工/查 tenant 数据时被 _require_owner_or_super 拦或懒建。
# 3 个注册路径(email signup / Google OAuth / LINE OAuth)统一调此函数。
# ============================================================
def _ensure_tenant_for_new_user(
    cur, user_id, plan: str, company_name: str = None, full_name: str = None, username: str = None
) -> Optional[str]:
    """新用户注册同事务建 tenant + 回填 user.tenant_id
    cur: 已开 commit=True 模式的 cursor(跟 user INSERT 同事务)
    返回 new_tenant_id · 失败返 None(不抛 · 让 _require_owner_or_super 懒建兜底)
    """
    try:
        # tenant.name 优先级:company > full_name > username > user_<8>
        tenant_name = (company_name or "").strip()
        if not tenant_name:
            tenant_name = (full_name or "").strip()
        if not tenant_name:
            tenant_name = (username or "").strip()
        if not tenant_name:
            tenant_name = f"user_{str(user_id)[:8]}"
        tenant_name = tenant_name[:100]

        # PLAN_CONFIG 拿真实配额(防 fix_orphan 那种 monthly_quota=0 复发)
        features = PLAN_CONFIG.get(plan) or PLAN_CONFIG.get("credits") or {}
        monthly_quota = int(features.get("ocr_per_period") or 100)

        # 建 tenant(同事务)
        cur.execute(
            """
            INSERT INTO tenants (
                name, owner_user_id, tenant_type, monthly_quota,
                used_this_month, status, member_count
            ) VALUES (%s, %s, 'shared_api', %s, 0, 'active', 1)
            RETURNING id
        """,
            (tenant_name, str(user_id), monthly_quota),
        )
        row = cur.fetchone()
        if row:
            new_tenant_id = row["id"] if isinstance(row, dict) else row[0]
        else:
            return None
        if not new_tenant_id:
            return None

        # 回填 user.tenant_id
        cur.execute(
            "UPDATE users SET tenant_id = %s WHERE id = %s AND tenant_id IS NULL",
            (str(new_tenant_id), str(user_id)),
        )
        logger.info(
            f"[v118.26.2.5 ensure-tenant] +tenant {str(new_tenant_id)[:8]}.. user={str(user_id)[:8]}.. plan={plan} quota={monthly_quota}"
        )
        return str(new_tenant_id)
    except Exception as e:
        logger.warning(f"[v118.26.2.5 ensure-tenant] fail user={user_id} plan={plan}: {e}")
        return None


def get_plan_features(plan: str) -> Dict[str, Any]:
    """v118.46 · 全平台只剩 credits + admin(老套餐已下线)· fallback credits"""
    return PLAN_CONFIG.get(plan, PLAN_CONFIG["credits"]).copy()


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


class LineLinkRequest(BaseModel):
    line_user_id: str
    line_display_name: Optional[str] = None


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

        import db as _db
        from auth import create_access_token

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
        import db as _db

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
@router.post("/api/me/link_line")
def link_line(req: LineLinkRequest, request: Request):
    """
    用户绑定 LINE userId · 解锁完整配额

    流程:
    1. 前端通过 LINE OAuth 拿到 userId(由 LINE Login API 返回)
    2. 调本接口 · 把 userId 跟当前用户绑定
    3. 校验:同一 LINE userId 不能绑两个账号(防薅核心)
    """
    try:
        u = _get_user_safe(request)
        if not u:
            raise HTTPException(status_code=401, detail="unauthorized")

        line_user_id = (req.line_user_id or "").strip()
        if not line_user_id or len(line_user_id) < 8:
            raise HTTPException(status_code=400, detail="line_user_id_invalid")

        import db as _db

        with _db.get_cursor(commit=True) as cur:
            # 检查 LINE userId 是否已被其他账号绑定
            cur.execute(
                """
                    SELECT id FROM users WHERE line_user_id = %s AND id <> %s LIMIT 1
                """,
                (line_user_id, u.get("id")),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="line_already_linked_other_account")

            cur.execute(
                """
                    UPDATE users SET
                        line_user_id = %s,
                        line_verified_at = NOW(),
                        line_id = COALESCE(line_id, %s)
                    WHERE id = %s
                """,
                (line_user_id, req.line_display_name or None, u.get("id")),
            )

        return {"ok": True, "line_user_id": line_user_id, "verified": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"link_line: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# DEV · 模拟 LINE 绑定(0→1 阶段 · LINE OAuth 还没接前用)
# 真 LINE Login API 接入后这个删掉 · 改用真实 OAuth
# ============================================================
@router.post("/api/me/link_line_dev")
def link_line_dev(request: Request):
    """开发期间用 · 模拟绑定一个随机 LINE userId · 让 trial 配额解锁"""
    try:
        u = _get_user_safe(request)
        if not u:
            raise HTTPException(status_code=401, detail="unauthorized")

        # 生成一个伪随机 ID(防止同一用户多次绑出多个不同 ID)
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute("SELECT line_user_id FROM users WHERE id=%s", (u.get("id"),))
            row = cur.fetchone()
            existing = None
            if row:
                existing = row.get("line_user_id") if isinstance(row, dict) else row[0]
            if existing:
                return {"ok": True, "line_user_id": existing, "already_linked": True}

            fake_id = f"DEV_{secrets.token_hex(10)}"
            cur.execute(
                """
                    UPDATE users SET line_user_id=%s, line_verified_at=NOW()
                    WHERE id=%s
                """,
                (fake_id, u.get("id")),
            )
        return {"ok": True, "line_user_id": fake_id, "dev_mode": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"link_line_dev: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 路由 · 当前套餐 + 配额
# ============================================================
@router.get("/api/me/plan")
def get_my_plan(request: Request):
    """前端取当前套餐 + 配额 + 使用情况"""
    try:
        u = _get_user_safe(request)
        if not u:
            raise HTTPException(status_code=401, detail="unauthorized")

        user_id = u.get("id")
        plan = _get_plan(user_id)
        features = get_plan_features(plan)

        import db as _db

        used = 0
        clients_count = 0
        line_verified = False
        with _db.get_cursor(commit=True) as cur:
            # 取用户详情(包括 LINE 绑定状态)
            cur.execute(
                """
                    SELECT trial_expires_at, plan_expires_at, company_name, email,
                           line_id, line_user_id, line_verified_at, signup_country,
                           is_banned, ban_reason
                    FROM users WHERE id=%s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if isinstance(row, dict):
                trial_exp = row.get("trial_expires_at")
                plan_exp = row.get("plan_expires_at")
                company = row.get("company_name")
                email = row.get("email")
                line_id = row.get("line_id")
                line_user_id = row.get("line_user_id")
                line_verified_at = row.get("line_verified_at")
                country = row.get("signup_country")
                is_banned = row.get("is_banned")
                ban_reason = row.get("ban_reason")
            elif row:
                (
                    trial_exp,
                    plan_exp,
                    company,
                    email,
                    line_id,
                    line_user_id,
                    line_verified_at,
                    country,
                    is_banned,
                    ban_reason,
                ) = row
            else:
                trial_exp = plan_exp = company = email = None
                line_id = line_user_id = line_verified_at = country = None
                is_banned = False
                ban_reason = None

            line_verified = bool(line_user_id and line_verified_at)

            # 被封停 · 直接报错
            if is_banned:
                raise HTTPException(status_code=403, detail=f"account_banned: {ban_reason or ''}")

            # v111.1 · 去掉 LINE 双轨制 · features 直接用 PLAN_CONFIG · 不再覆盖

            # OCR 用量 · v111.1 trial 也按月统计(以前是累计)
            cur.execute(
                """
                    SELECT COUNT(*) FROM ocr_history
                    WHERE user_id=%s
                      AND date_trunc('month', created_at) = date_trunc('month', NOW())
                """,
                (user_id,),
            )
            used = _row_count(cur.fetchone(), 0)

            # 客户数
            try:
                cur.execute(
                    "SELECT COUNT(*) FROM clients WHERE user_id=%s AND COALESCE(is_active,true)=true",
                    (user_id,),
                )
                clients_count = _row_count(cur.fetchone(), 0)
            except Exception as e:
                logger.warning(f"[admin_user_detail] clients 计数失败: {e}")

        # v111.1 · trial 7 天倒计时
        days_left = None
        if plan == "trial":
            from datetime import datetime, timedelta

            base_exp = trial_exp
            if not base_exp:
                # 没设 trial_expires_at · 用 created_at + 7 天兜底
                created_at_for_calc = u.get("created_at") if isinstance(u, dict) else None
                if created_at_for_calc and isinstance(created_at_for_calc, str):
                    try:
                        created_at_for_calc = datetime.fromisoformat(
                            created_at_for_calc.replace("Z", "+00:00")
                        )
                    except Exception:
                        created_at_for_calc = None
                if created_at_for_calc:
                    base_exp = created_at_for_calc + timedelta(days=7)
            if base_exp:
                delta = base_exp - _now()
                days_left = max(0, int(delta.total_seconds() // 86400))
                if delta.total_seconds() < 86400 and delta.total_seconds() > 0:
                    days_left = round(delta.total_seconds() / 86400, 2)

        # v111.1 · monthly / yearly 剩余天数 · lifetime 永久(返回 -1 标识)
        plan_days_left = None
        if plan == "lifetime":
            plan_days_left = -1  # 前端显示"永久"
        elif plan in ("monthly", "yearly") and plan_exp:
            delta = plan_exp - _now()
            plan_days_left = max(0, int(delta.total_seconds() // 86400))

        return {
            "ok": True,
            "plan": plan,
            "features": features,
            "line_verified": line_verified,
            "needs_line_verify": False,  # v111.1 · 新模型不再依赖 LINE 解锁
            "usage": {
                "ocr_used": used,
                "ocr_limit": features.get("ocr_per_period", 0),
                "clients_used": clients_count,
                "clients_limit": features.get("clients_max", 0),
            },
            # v111.1 · 暴露上传限制(前端 getMaxFiles 用)
            "limits": {
                "max_upload_files": features.get("max_upload_files", 5),
                "max_pages_per_file": features.get("max_pages_per_file", 50),
                "max_mb_per_file": features.get("max_mb_per_file", 100),
            },
            "trial_days_left": days_left,
            "plan_days_left": plan_days_left,
            "trial_expires_at": trial_exp.isoformat() if trial_exp else None,
            "plan_expires_at": plan_exp.isoformat() if plan_exp else None,
            "profile": {
                "company_name": company,
                "email": email,
                "line_id": line_id,
                "country": country,
            },
            "payment_info": {
                "bank": "Kasikorn Bank",
                "bank_th": "ธนาคารกสิกรไทย",
                "account_no": "011-1-83212-9",
                "promptpay": "+66 85-064-2609",
                "line_id": "@Pearnly",
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_my_plan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# v118.35.0.11 · /api/payment/submit 路由永久下线 · credits 系统不再走升级模式 · 用户冲入是 /api/credits/topup/request
# CLEANUP-PLAN-01 (2026-05-22) · funnel 改瘦:删 by_plan / trial_expiring_soon / conversion_pct
#   credits 模式不再有"套餐"概念 · admin 只看用户增长 + 国家分布
# 超管风控/用户管理 8 路由 → auth_admin_routes.py(模块化深化 · 2026-06-01)· 下方 include。
# 密码路由组已抽到 auth_password_routes.py(模块化深化 · 2026-06-01)·
# re-export send_reset_link_for_employee 给 team_routes(不改其 import)。
from auth_password_routes import (  # noqa: E402
    router as _password_router,
    send_reset_link_for_employee,  # noqa: F401 · re-export(team_routes 用)
)

router.include_router(_password_router)
from auth_admin_routes import router as _admin_router  # noqa: E402

router.include_router(_admin_router)


_ensure_schema()
