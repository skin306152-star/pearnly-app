"""
services/auth/signup_core.py · 注册/登录共享 helper + 套餐/一次性邮箱常量

从 auth_signup.py 抽出(模块化深化 · 2026-06-01 · 纯搬家 0 逻辑改)。
含:PLAN_CONFIG / DISPOSABLE_EMAIL_DOMAINS 常量;邮箱归一化 / 一次性邮箱检测 /
真实 IP / 反薅闸 check_signup_abuse / 密码哈希 _hash_password / 行兼容取值 /
超管校验 / plan 查询 / 新用户建 tenant 等。auth_signup re-export 全部名字给
signup 路由 + oauth_create + auth_password_routes(lazy)+ account_merge 等消费者。
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request

logger = logging.getLogger("mrpilot.signup")


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
        from core import db as _db

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
        from core import auth as _a

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
        from core.auth import get_current_user_from_request

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
        from core import db as _db

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
# 用户加员工/查 tenant 数据时被拒(require_perm 对 no_tenant 一律 403)。
# 3 个注册路径(email signup / Google OAuth / LINE OAuth)统一调此函数。
# ============================================================
def _ensure_tenant_for_new_user(
    cur, user_id, plan: str, company_name: str = None, full_name: str = None, username: str = None
) -> Optional[str]:
    """新用户注册同事务建 tenant + 回填 user.tenant_id
    cur: 已开 commit=True 模式的 cursor(跟 user INSERT 同事务)
    返回 new_tenant_id · 失败返 None(不抛 · 不阻塞注册 · 该用户后续走 no_tenant 拒)
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

        # 平台业态套餐 · 新注册打「待选业态」标记 → 首进自动弹业态选择器(仅新租户)。
        # 这是所有注册路径(邮箱 / Google / LINE)创建租户的唯一汇合点 → 一处覆盖全部。
        # 失败不阻塞注册(标记缺失只是不弹,不致命)。
        try:
            from services.modules import store as _modules_store

            _modules_store.set_needs_onboarding(cur, tenant_id=str(new_tenant_id), value=True)
        except Exception as _e_onb:
            logger.warning(f"[platform-onboarding] set_needs_onboarding skip: {_e_onb}")

        # 权限整顿批1 · 新 owner 同事务写 membership(memberships=成员唯一真相 ·
        # docs/permissions/01)。失败不阻塞注册(resolver 有 users.role 存量兜底)。
        try:
            from services.authz.resolver import create_membership

            create_membership(
                cur, user_id=str(user_id), tenant_id=str(new_tenant_id), role_key="owner"
            )
        except Exception as _e_mb:
            logger.warning(f"[authz] signup create_membership skip: {_e_mb}")
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
