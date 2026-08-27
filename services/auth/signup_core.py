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

from services.auth.signup_identity import (  # noqa: F401
    DISPOSABLE_EMAIL_DOMAINS,
    get_client_ip_safe,
    get_ip_subnet24,
    is_disposable_email,
    normalize_email,
)

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


_SIGNUP_FIRM_ENTRY = "cowork"
_SIGNUP_ENTRANCES = frozenset({"main", "cowork", "erp"})


def _normalize_signup_entry(entry) -> Optional[str]:
    """归一化共享注册入口；未知值沿用 main 行为。"""
    if not entry:
        return None
    e = str(entry).strip().lower()
    return e if e in _SIGNUP_ENTRANCES else None


# ============================================================
# v118.26.2.5 · 新用户注册自动建 tenant
# 解决 v27.7 fix_orphan 留下的根因:signup 不建 tenant · 导致 tenant_id=NULL ·
# 用户加员工/查 tenant 数据时被拒(require_perm 对 no_tenant 一律 403)。
# 3 个注册路径(email signup / Google OAuth / LINE OAuth)统一调此函数。
# ============================================================
def _ensure_tenant_for_new_user(
    cur,
    user_id,
    plan: str,
    company_name: str = None,
    full_name: str = None,
    username: str = None,
    entry: Optional[str] = None,
) -> Optional[str]:
    """新用户注册同事务建 tenant + 回填 user.tenant_id。

    cur: 已开 commit=True 模式的 cursor(跟 user INSERT 同事务)
    普通入口保留失败返 None 的历史兼容；Cowork 的事务所身份创建失败则抛出并整笔回滚。
    """
    entry_norm = _normalize_signup_entry(entry)
    is_firm = entry_norm == _SIGNUP_FIRM_ENTRY
    is_erp_invite = entry_norm == "erp"
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

        if is_firm:
            cur.execute(
                """
                INSERT INTO tenants (
                    name, owner_user_id, tenant_type, monthly_quota,
                    used_this_month, status, member_count, tenant_type_v2
                ) VALUES (%s, %s, 'shared_api', %s, 0, 'active', 1, 'f_firm')
                RETURNING id
                """,
                (tenant_name, str(user_id), monthly_quota),
            )
        else:
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

        if is_firm:
            from services.firm import store as _firm_store
            from services.modules import presets as _module_presets

            profile = _firm_store.create_profile(
                cur, tenant_id=str(new_tenant_id), display_name=tenant_name
            )
            if profile is None:
                raise RuntimeError("create firm profile returned None")
            _module_presets.apply_preset(cur, tenant_id=str(new_tenant_id), business_type="firm")

        if not is_firm:
            # 普通新租户继续走现有业态 onboarding。
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

        # ERP 邀请创建的商户只拿 ERP 门；自由注册仍拿 main，事务所再加 cowork。
        from services.auth.entrance import COWORK, ERP, MAIN
        from services.auth.entrance_store import grant_entrance_safe

        primary_entrance = ERP if is_erp_invite else MAIN
        grant_entrance_safe(primary_entrance, str(new_tenant_id), cur=cur, context="signup")
        if is_firm:
            grant_entrance_safe(COWORK, str(new_tenant_id), cur=cur, context="signup")
        logger.info(
            "[ensure-tenant] tenant=%s user=%s plan=%s quota=%s firm=%s",
            str(new_tenant_id)[:8],
            str(user_id)[:8],
            plan,
            monthly_quota,
            is_firm,
        )
        return str(new_tenant_id)
    except Exception as e:
        if is_firm or is_erp_invite:
            raise
        logger.warning(f"[v118.26.2.5 ensure-tenant] fail user={user_id} plan={plan}: {e}")
        return None


def get_plan_features(plan: str) -> Dict[str, Any]:
    """v118.46 · 全平台只剩 credits + admin(老套餐已下线)· fallback credits"""
    return PLAN_CONFIG.get(plan, PLAN_CONFIG["credits"]).copy()
