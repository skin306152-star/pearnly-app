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
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("mrpilot.signup")
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
def _ensure_schema():
    """v109.3.2 数据库迁移 · 每条独立事务 · 失败不影响后续"""
    try:
        import db as _db

        sqls = [
            # users 表新增字段(原有)
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'free'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_expires_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_country TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS line_id TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS line_user_id TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS line_verified_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS parent_user_id UUID",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS upgraded_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS company_name TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT",
            # v109.3.2 新增字段
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS user_role TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_volume TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_source TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS newsletter_opt_in BOOLEAN DEFAULT true",
            # 防薅字段
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_normalized TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_ip TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_ip_subnet TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_fingerprint TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_user_agent TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS risk_score INT DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT false",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS ban_reason TEXT",
            # 索引
            "CREATE INDEX IF NOT EXISTS idx_users_email_norm ON users(email_normalized)",
            "CREATE INDEX IF NOT EXISTS idx_users_signup_ip ON users(signup_ip, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_users_signup_subnet ON users(signup_ip_subnet, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_users_fingerprint ON users(signup_fingerprint, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_users_line_user_id ON users(line_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_signup_source ON users(signup_source, created_at DESC)",
            # v118.22.0.4 · 历史回填:旧版注册写的 role='user' → 'owner'(对齐全系统约定)
            # 影响:role='user' 的孤儿用户在 admin「客户」列表/雇员校验/cascade 删除等查询里被漏掉
            # 幂等:跑多少次都安全
            "UPDATE users SET role='owner' WHERE role='user'",
            # 订阅日志
            """CREATE TABLE IF NOT EXISTS subscription_log (
                id BIGSERIAL PRIMARY KEY,
                user_id UUID NOT NULL,
                from_plan TEXT,
                to_plan TEXT NOT NULL,
                changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                changed_by UUID,
                reason TEXT,
                amount_thb NUMERIC(10,2),
                note TEXT
            )""",
            "CREATE INDEX IF NOT EXISTS idx_sub_log_user ON subscription_log(user_id, changed_at DESC)",
            # 待审核付款
            """CREATE TABLE IF NOT EXISTS payment_pending (
                id BIGSERIAL PRIMARY KEY,
                user_id UUID NOT NULL,
                target_plan TEXT NOT NULL,
                amount_thb NUMERIC(10,2) NOT NULL,
                screenshot_path TEXT,
                payer_name TEXT,
                payer_note TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                reviewed_at TIMESTAMPTZ,
                reviewed_by UUID,
                review_note TEXT
            )""",
            "CREATE INDEX IF NOT EXISTS idx_pay_pending_status ON payment_pending(status, created_at DESC)",
            # 风控日志
            """CREATE TABLE IF NOT EXISTS risk_log (
                id BIGSERIAL PRIMARY KEY,
                user_id UUID,
                event_type TEXT NOT NULL,
                ip TEXT,
                fingerprint TEXT,
                detail TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )""",
            "CREATE INDEX IF NOT EXISTS idx_risk_log_event ON risk_log(event_type, created_at DESC)",
            # v109.3.2 · 密码重置请求
            """CREATE TABLE IF NOT EXISTS password_reset_log (
                id BIGSERIAL PRIMARY KEY,
                token TEXT NOT NULL UNIQUE,
                user_id UUID NOT NULL,
                email TEXT NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                used BOOLEAN DEFAULT false,
                used_at TIMESTAMPTZ,
                requester_ip TEXT,
                requester_fingerprint TEXT,
                delivery_method TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )""",
            "CREATE INDEX IF NOT EXISTS idx_pwreset_token ON password_reset_log(token)",
            "CREATE INDEX IF NOT EXISTS idx_pwreset_email ON password_reset_log(email, created_at DESC)",
            # v109.3.2 · 登录失败日志(锁账户)
            """CREATE TABLE IF NOT EXISTS login_failure_log (
                id BIGSERIAL PRIMARY KEY,
                email_or_username TEXT NOT NULL,
                ip TEXT,
                fingerprint TEXT,
                user_agent TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )""",
            "CREATE INDEX IF NOT EXISTS idx_login_fail_user ON login_failure_log(email_or_username, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_login_fail_ip ON login_failure_log(ip, created_at DESC)",
        ]
        # 关键改动 · 每条独立 cursor · 失败不污染后续
        for sql in sqls:
            try:
                with _db.get_cursor(commit=True) as cur:
                    cur.execute(sql)
            except Exception as one_e:
                logger.warning(f"schema migrate skip: {one_e}")
        logger.info("✓ v109.3.2 schema ensured")
    except Exception as e:
        logger.error(f"_ensure_schema failed: {e}\n{traceback.format_exc()}")


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
@router.get("/api/admin/users/funnel")
def admin_user_funnel(request: Request):
    """admin 用户增长 + 国家分布(credits 模式 · 不再有套餐分布)"""
    try:
        _require_super_admin(request)
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            # 今日/本周/本月新增
            cur.execute("SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE")
            today = _row_count(cur.fetchone())
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"
            )
            week = _row_count(cur.fetchone())
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE date_trunc('month', created_at) = date_trunc('month', NOW())"
            )
            month = _row_count(cur.fetchone())

            # 国家分布
            cur.execute("""
                    SELECT COALESCE(signup_country,'?') AS country, COUNT(*) AS n FROM users
                    GROUP BY 1 ORDER BY 2 DESC
                """)
            by_country = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    by_country.append({"country": r.get("country") or "?", "count": r.get("n", 0)})
                else:
                    by_country.append({"country": r[0], "count": r[1]})

        return {
            "ok": True,
            "new_today": today,
            "new_week": week,
            "new_month": month,
            "by_country": by_country,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_user_funnel: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# CLEANUP-PLAN-01 (2026-05-22) · 4 个老订阅 admin 路由整段删:
#   - GET  /api/admin/payments/pending       (payment_pending 表 · 老订阅付款审核 list)
#   - POST /api/admin/users/upgrade          (admin 升级用户套餐 · 写 users.plan)
#   - GET  /api/admin/payments/{id}/screenshot  (看付款截图)
#   - POST /api/admin/payments/{id}/review   (审批 = 升级 plan · 写 subscription_log)
# credits 模式不再有套餐升级 · 充值审核走 billing_routes.py admin_topup_list
# payment_pending / subscription_log 表保留(DB schema 改动留 REFACTOR-B3 Alembic 时再做)
# ============================================================


# ============================================================
# 后台 · 删除测试 demo 数据(一次性 · 保留 earn)
# ============================================================
@router.post("/api/admin/cleanup_demo")
def admin_cleanup_demo(request: Request):
    """删除 demo / demo_plus 等测试账号 + 数据 · 保留 earn / super_admin"""
    try:
        admin = _require_super_admin(request)
        import db as _db

        deleted = {"users": 0, "ocr_history": 0, "clients": 0}
        with _db.get_cursor(commit=True) as cur:
            # 找出要删的用户(demo / demo_plus / 任何 username 以 demo_ 开头)
            cur.execute("""
                    SELECT id, username FROM users
                    WHERE (username='demo' OR username LIKE 'demo_%')
                      AND COALESCE(is_super_admin, false) = false
                """)
            ids = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    ids.append(str(r.get("id")))
                else:
                    ids.append(str(r[0]))
            if not ids:
                return {"ok": True, "deleted": deleted, "message": "no demo accounts found"}

            placeholders = ",".join(["%s"] * len(ids))
            # 级联删
            try:
                cur.execute(f"DELETE FROM ocr_history WHERE user_id IN ({placeholders})", ids)
                deleted["ocr_history"] = cur.rowcount
            except Exception as e:
                logger.warning(f"cleanup ocr_history skip: {e}")
            try:
                cur.execute(f"DELETE FROM clients WHERE user_id IN ({placeholders})", ids)
                deleted["clients"] = cur.rowcount
            except Exception as e:
                logger.warning(f"cleanup clients skip: {e}")
            # 其他可能的关联表(安全 try)
            for tbl in [
                "ocr_cost_log",
                "subscription_log",
                "payment_pending",
                "push_log",
                "billing_balance_log",
            ]:
                try:
                    cur.execute(f"DELETE FROM {tbl} WHERE user_id IN ({placeholders})", ids)
                except Exception:
                    pass  # 表可能不存在 · 安全跳过
            # 最后删用户
            cur.execute(f"DELETE FROM users WHERE id IN ({placeholders})", ids)
            deleted["users"] = cur.rowcount
        return {"ok": True, "deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_cleanup_demo: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 后台 · 风控 · 可疑用户
# ============================================================
@router.get("/api/admin/risk/suspicious")
def admin_suspicious_users(request: Request):
    """后台看可疑用户(同 IP / 同指纹 / 临时邮箱 / 异常 OCR)
    v116 · 加返回 accounts 详细数组(含 user_id) · 给前端批量操作用"""
    try:
        _require_super_admin(request)
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            # 1. 同 IP 注册多个账号
            cur.execute("""
                    SELECT signup_ip, COUNT(*) AS n,
                           jsonb_agg(jsonb_build_object(
                               'user_id', id::text,
                               'email', COALESCE(email, username),
                               'plan', plan,
                               'is_banned', is_banned,
                               'created_at', created_at::text
                           ) ORDER BY created_at DESC) AS accounts,
                           MAX(created_at) AS last_signup
                    FROM users
                    WHERE signup_ip IS NOT NULL
                      AND created_at > NOW() - INTERVAL '7 days'
                    GROUP BY signup_ip
                    HAVING COUNT(*) > 1
                    ORDER BY n DESC
                    LIMIT 50
                """)
            same_ip = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    accounts = r.get("accounts") or []
                    same_ip.append(
                        {
                            "ip": r.get("signup_ip"),
                            "count": r.get("n", 0),
                            "accounts": accounts if isinstance(accounts, list) else [],
                            "last_signup": (
                                r.get("last_signup").isoformat() if r.get("last_signup") else None
                            ),
                        }
                    )
                else:
                    same_ip.append(
                        {
                            "ip": r[0],
                            "count": r[1],
                            "accounts": (r[2] or []),
                            "last_signup": r[3].isoformat() if r[3] else None,
                        }
                    )

            # 2. 同指纹注册多个账号
            cur.execute("""
                    SELECT signup_fingerprint, COUNT(*) AS n,
                           jsonb_agg(jsonb_build_object(
                               'user_id', id::text,
                               'email', COALESCE(email, username),
                               'plan', plan,
                               'is_banned', is_banned,
                               'created_at', created_at::text
                           ) ORDER BY created_at DESC) AS accounts
                    FROM users
                    WHERE signup_fingerprint IS NOT NULL
                      AND created_at > NOW() - INTERVAL '14 days'
                    GROUP BY signup_fingerprint
                    HAVING COUNT(*) > 1
                    ORDER BY n DESC
                    LIMIT 50
                """)
            same_fp = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    fp = r.get("signup_fingerprint") or ""
                    accounts = r.get("accounts") or []
                    same_fp.append(
                        {
                            "fingerprint": fp,
                            "fingerprint_short": fp[:20] + "..." if len(fp) > 20 else fp,
                            "count": r.get("n", 0),
                            "accounts": accounts if isinstance(accounts, list) else [],
                        }
                    )
                else:
                    fp = r[0] or ""
                    same_fp.append(
                        {
                            "fingerprint": fp,
                            "fingerprint_short": fp[:20] + "..." if len(fp) > 20 else fp,
                            "count": r[1],
                            "accounts": (r[2] or []),
                        }
                    )

            # 3. OCR 用量异常(单日 > 30 张)
            cur.execute("""
                    SELECT u.id, COALESCE(u.email, u.username) AS user_email, u.plan,
                           u.is_banned,
                           COUNT(o.id) AS today_count
                    FROM users u
                    JOIN ocr_history o ON o.user_id = u.id
                    WHERE o.created_at > NOW() - INTERVAL '24 hours'
                    GROUP BY u.id, u.email, u.username, u.plan, u.is_banned
                    HAVING COUNT(o.id) > 30
                    ORDER BY today_count DESC
                    LIMIT 30
                """)
            heavy = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    heavy.append(
                        {
                            "user_id": str(r.get("id")),
                            "email": r.get("user_email"),
                            "plan": r.get("plan"),
                            "is_banned": r.get("is_banned", False),
                            "ocr_today": r.get("today_count"),
                        }
                    )
                else:
                    heavy.append(
                        {
                            "user_id": str(r[0]),
                            "email": r[1],
                            "plan": r[2],
                            "is_banned": r[3],
                            "ocr_today": r[4],
                        }
                    )

            # 4. 风控事件最近 24h
            cur.execute("""
                    SELECT event_type, COUNT(*) AS n
                    FROM risk_log
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                    GROUP BY event_type
                    ORDER BY n DESC
                """)
            events_24h = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    events_24h.append({"event": r.get("event_type"), "count": r.get("n", 0)})
                else:
                    events_24h.append({"event": r[0], "count": r[1]})

        return {
            "ok": True,
            "same_ip_signups": same_ip,
            "same_fingerprint_signups": same_fp,
            "heavy_ocr_users": heavy,
            "risk_events_24h": events_24h,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_suspicious_users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/admin/users/{user_id}/ban")
def admin_ban_user(user_id: str, request: Request, reason: str = Query("")):
    try:
        admin = _require_super_admin(request)
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                    UPDATE users SET is_banned=true, ban_reason=%s WHERE id=%s
                """,
                (reason or "manual_ban", user_id),
            )
            cur.execute(
                """
                    INSERT INTO risk_log(user_id, event_type, detail)
                    VALUES (%s, 'admin_ban', %s)
                """,
                (user_id, json.dumps({"reason": reason, "by": str(admin.get("id"))})),
            )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_ban_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/admin/users/{user_id}/unban")
def admin_unban_user(user_id: str, request: Request):
    try:
        _require_super_admin(request)
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                    UPDATE users SET is_banned=false, ban_reason=NULL WHERE id=%s
                """,
                (user_id,),
            )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_unban_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# v116 · 风控批量封禁 · 一次封多个账号(同 IP / 同指纹下的群组)
class RiskBatchBanRequest(BaseModel):
    user_ids: List[str] = Field(..., min_length=1, max_length=100)
    reason: str = Field(default="risk_batch_ban", max_length=200)


@router.post("/api/admin/risk/batch-ban")
def admin_risk_batch_ban(req: RiskBatchBanRequest, request: Request):
    """v116 · 批量封禁(风控页用 · 同 IP/指纹群组一键封)"""
    try:
        admin = _require_super_admin(request)
        import db as _db

        banned = 0
        skipped = []
        with _db.get_cursor(commit=True) as cur:
            for uid in req.user_ids:
                try:
                    # 跳过超管自己 + 已经封禁的
                    cur.execute("SELECT is_super_admin, is_banned FROM users WHERE id=%s", (uid,))
                    row = cur.fetchone()
                    if not row:
                        skipped.append({"user_id": uid, "reason": "not_found"})
                        continue
                    is_super = row.get("is_super_admin") if isinstance(row, dict) else row[0]
                    if is_super:
                        skipped.append({"user_id": uid, "reason": "is_super_admin"})
                        continue
                    cur.execute(
                        """
                            UPDATE users SET is_banned=true, ban_reason=%s WHERE id=%s
                        """,
                        (req.reason, uid),
                    )
                    cur.execute(
                        """
                            INSERT INTO risk_log(user_id, event_type, detail)
                            VALUES (%s, 'admin_batch_ban', %s)
                        """,
                        (uid, json.dumps({"reason": req.reason, "by": str(admin.get("id"))})),
                    )
                    banned += 1
                except Exception as inner_e:
                    logger.warning(f"batch_ban {uid} failed: {inner_e}")
                    skipped.append({"user_id": uid, "reason": "error"})
        return {"ok": True, "banned": banned, "skipped": skipped}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_risk_batch_ban: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# v109.3.2 · 密码重置体系
# ============================================================


# 密码找回/重置/改密 + 发送器 → auth_password_routes.py(模块化深化 · 2026-06-01)。
# 下方 import 回 router 并 include · 并 re-export send_reset_link_for_employee(team_routes 用)。
@router.get("/api/admin/password_resets")
def admin_password_resets(request: Request):
    """后台 · 查看密码重置请求历史(应急客服)"""
    try:
        _require_super_admin(request)
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute("""
                SELECT
                    p.id, p.token, p.email, p.expires_at, p.used, p.used_at,
                    p.delivery_method, p.requester_ip, p.created_at,
                    u.username, u.full_name
                FROM password_reset_log p
                LEFT JOIN users u ON u.id = p.user_id
                ORDER BY p.created_at DESC
                LIMIT 100
            """)
            rows = cur.fetchall() or []
        out = []
        for r in rows:
            d = dict(r) if hasattr(r, "keys") else {}
            for k in ("expires_at", "used_at", "created_at"):
                if d.get(k):
                    try:
                        d[k] = d[k].isoformat()
                    except Exception:
                        d[k] = str(d[k])
            out.append(d)
        return {"items": out}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_password_resets: {e}")
        raise HTTPException(500, detail=str(e))


@router.get("/api/admin/signup_sources")
def admin_signup_sources(request: Request):
    """后台 · 注册来源渠道分析"""
    try:
        _require_super_admin(request)
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute("""
                SELECT
                    COALESCE(signup_source, 'unknown') AS source,
                    COUNT(*) AS user_count,
                    COUNT(*) FILTER (WHERE plan IN ('plus', 'pro', 'lifetime')) AS paid_count,
                    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') AS week_count
                FROM users
                WHERE signup_source IS NOT NULL OR created_at > NOW() - INTERVAL '90 days'
                GROUP BY COALESCE(signup_source, 'unknown')
                ORDER BY user_count DESC
            """)
            rows = cur.fetchall() or []
        out = []
        for r in rows:
            d = dict(r) if hasattr(r, "keys") else {}
            for k in ("user_count", "paid_count", "week_count"):
                if k in d:
                    d[k] = int(d[k] or 0)
            out.append(d)
        return {"items": out}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_signup_sources: {e}")
        raise HTTPException(500, detail=str(e))


# ============================================================
# 启动时执行 schema 迁移
# ============================================================
# 密码路由组已抽到 auth_password_routes.py(模块化深化 · 2026-06-01)·
# re-export send_reset_link_for_employee 给 team_routes(不改其 import)。
from auth_password_routes import (  # noqa: E402
    router as _password_router,
    send_reset_link_for_employee,  # noqa: F401 · re-export(team_routes 用)
)

router.include_router(_password_router)


_ensure_schema()
