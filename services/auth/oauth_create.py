"""
services/auth/oauth_create.py · Google / LINE OAuth 一键建账号

从 auth_signup.py 抽出(模块化深化 · 2026-06-01 · 纯搬家 0 逻辑改)。
🔴 高敏:OAuth 建号路径(铁律 #26)。oauth_routes 调本模块;auth_signup 的 helper
(normalize_email / _hash_password / _ensure_tenant_for_new_user / _log_risk)在函数内
lazy import 破循环。
"""

import logging
import secrets
import traceback
from typing import Any, Dict, Optional

logger = logging.getLogger("mrpilot.signup")


def _signup_helpers():
    """lazy 取 auth_signup 共享 helper(破循环 import)。"""
    from auth_signup import (
        is_signup_globally_disabled,
        normalize_email,
        _hash_password,
        _row_count,
        _ensure_tenant_for_new_user,
    )

    return (
        is_signup_globally_disabled,
        normalize_email,
        _hash_password,
        _row_count,
        _ensure_tenant_for_new_user,
    )


# v118.27.5.1 · Google OAuth 一键建账号
# 跳过密码 / 跳过 5 层防薅(Google 邮箱已验证) · 默认 trial 7 天
# 仅供 app.py 的 /api/auth/google/callback 在用户首次用 Google 登录且未注册时调用
# ============================================================
def create_user_via_google_oauth(
    email: str, full_name: str, google_sub: str, ip: str = None, ua: str = None
) -> Optional[Dict[str, Any]]:
    import db as _db

    (
        is_signup_globally_disabled,
        normalize_email,
        _hash_password,
        _row_count,
        _ensure_tenant_for_new_user,
    ) = _signup_helpers()

    try:
        # 紧急止血:全局禁用注册
        if is_signup_globally_disabled():
            logger.warning("[google_oauth_signup] global signup disabled · refused")
            return None

        email_raw = (email or "").strip().lower()
        if not email_raw or "@" not in email_raw or "." not in email_raw.split("@", 1)[1]:
            logger.warning(f"[google_oauth_signup] email_invalid: {email_raw}")
            return None

        email_norm = normalize_email(email_raw)
        email_prefix = email_raw.split("@", 1)[0]
        company = email_prefix or "User"
        full_name_safe = (full_name or "").strip() or None

        # v118.35.0.4 · 默认 credits(pay-as-you-go)· 不再 trial 7 天到期
        invite_plan = "credits"
        trial_exp = None
        ua_safe = (ua or "")[:512]

        with _db.get_cursor(commit=True) as cur:
            # 取 users 表实际有的列(防止插入不存在字段)
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

            all_fields = {
                "username": email_raw,
                # v118.27.5.2 · password_hash NOT NULL · 给随机不可用占位(用户走 OAuth 登录 · 永远不验密码)
                "password_hash": _hash_password("oauth_no_pw_" + secrets.token_urlsafe(32)),
                "email": email_raw,
                "email_normalized": email_norm,
                "company_name": company,
                "full_name": full_name_safe,
                "plan": invite_plan,
                "trial_expires_at": trial_exp,
                "signup_country": "TH",
                "signup_ip": ip,
                "signup_user_agent": ua_safe,
                "signup_source": "google_oauth",
                "google_sub": google_sub,
                "role": "owner",
                "is_super_admin": False,
                "is_active": True,
            }
            use_fields = {k: v for k, v in all_fields.items() if k in existing_cols}
            col_names = list(use_fields.keys())
            col_values = [use_fields[k] for k in col_names]

            ts_placeholders = []
            if "created_at" in existing_cols:
                col_names.append("created_at")
                ts_placeholders.append("NOW()")
            if "last_seen_at" in existing_cols:
                col_names.append("last_seen_at")
                ts_placeholders.append("NOW()")

            placeholders = ", ".join(["%s"] * len(col_values))
            if ts_placeholders:
                placeholders = placeholders + ", " + ", ".join(ts_placeholders)

            col_sql = ", ".join(col_names)
            insert_sql = f"INSERT INTO users({col_sql}) VALUES ({placeholders}) RETURNING id"
            logger.info(
                f"[google_oauth_signup] insert · fields used: {len(use_fields)}/{len(all_fields)}"
            )
            cur.execute(insert_sql, col_values)
            row = cur.fetchone()
            user_id = _row_count(row) if not isinstance(row, dict) else row.get("id")

            # v118.26.2.5 · 同事务建 tenant · v118.35.0.4 拿返回 tenant_id 给 credits 初始化用
            _new_tid_g = _ensure_tenant_for_new_user(
                cur,
                str(user_id),
                invite_plan,
                company_name=company,
                full_name=full_name_safe,
                username=email_raw,
            )

            # 订阅日志
            try:
                cur.execute(
                    """
                    INSERT INTO subscription_log(user_id, from_plan, to_plan, reason)
                    VALUES (%s, NULL, %s, 'google_oauth_signup')
                """,
                    (user_id, invite_plan),
                )
            except Exception as ce:
                logger.warning(f"[google_oauth_signup] subscription_log skip: {ce}")

            # v118.35.0.4 · credits 新公司初始化 0 余额
            if invite_plan == "credits" and _new_tid_g:
                try:
                    _db.ensure_tenant_credits(_new_tid_g)
                except Exception as ce:
                    logger.warning(f"[google_oauth_signup] ensure_tenant_credits skip: {ce}")

        # 自动建 1 个示例客户(独立事务 · 失败不影响主注册)
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
            logger.warning(f"[google_oauth_signup] sample client skip: {ce}")

        logger.info(f"[google_oauth_signup] created user_id={user_id} email={email_raw}")
        return _db.find_user_by_id(str(user_id))

    except Exception as e:
        logger.error(f"[google_oauth_signup] failed: {e}\n{traceback.format_exc()}")
        return None


# ============================================================
# v118.28.4 · LINE Login OAuth 一键建账号
# LINE email scope 需单独申请 · 没拿到时用 line_<sub>@line.local 占位 username
# 用户登录后可在 settings 改邮箱
# ============================================================
def create_user_via_line_oauth(
    line_uid: str,
    display_name: str = None,
    email: str = None,
    picture: str = None,
    ip: str = None,
    ua: str = None,
) -> Optional[Dict[str, Any]]:
    import db as _db

    (
        is_signup_globally_disabled,
        normalize_email,
        _hash_password,
        _row_count,
        _ensure_tenant_for_new_user,
    ) = _signup_helpers()

    try:
        if is_signup_globally_disabled():
            logger.warning("[line_oauth_signup] global signup disabled · refused")
            return None

        if not line_uid:
            logger.warning("[line_oauth_signup] no line_uid")
            return None

        # email 可选 · 没拿到用占位
        email_raw = (email or "").strip().lower() if email else ""
        if email_raw and "@" in email_raw and "." in email_raw.split("@", 1)[1]:
            username_use = email_raw
            email_for_db = email_raw
            email_norm = normalize_email(email_raw)
        else:
            # LINE 没给 email · 用 line_<sub前16位>@line.local 占位
            username_use = f"line_{line_uid[:16]}@line.local"
            email_for_db = None
            email_norm = None

        full_name_safe = (display_name or "").strip() or None
        company = full_name_safe or "LINE User"

        # v118.35.0.4 · 默认 credits(pay-as-you-go)· 不再 trial 7 天到期
        invite_plan = "credits"
        trial_exp = None
        ua_safe = (ua or "")[:512]

        with _db.get_cursor(commit=True) as cur:
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

            all_fields = {
                "username": username_use,
                "password_hash": _hash_password("oauth_no_pw_" + secrets.token_urlsafe(32)),
                "email": email_for_db,
                "email_normalized": email_norm,
                "company_name": company,
                "full_name": full_name_safe,
                "plan": invite_plan,
                "trial_expires_at": trial_exp,
                "signup_country": "TH",
                "signup_ip": ip,
                "signup_user_agent": ua_safe,
                "signup_source": "line_oauth",
                "line_uid": line_uid,
                "role": "owner",
                "is_super_admin": False,
                "is_active": True,
            }
            use_fields = {k: v for k, v in all_fields.items() if k in existing_cols}
            col_names = list(use_fields.keys())
            col_values = [use_fields[k] for k in col_names]

            ts_placeholders = []
            if "created_at" in existing_cols:
                col_names.append("created_at")
                ts_placeholders.append("NOW()")
            if "last_seen_at" in existing_cols:
                col_names.append("last_seen_at")
                ts_placeholders.append("NOW()")

            placeholders = ", ".join(["%s"] * len(col_values))
            if ts_placeholders:
                placeholders = placeholders + ", " + ", ".join(ts_placeholders)

            col_sql = ", ".join(col_names)
            insert_sql = f"INSERT INTO users({col_sql}) VALUES ({placeholders}) RETURNING id"
            logger.info(
                f"[line_oauth_signup] insert · fields used: {len(use_fields)}/{len(all_fields)}"
            )
            cur.execute(insert_sql, col_values)
            row = cur.fetchone()
            user_id = _row_count(row) if not isinstance(row, dict) else row.get("id")

            # v118.26.2.5 · 同事务建 tenant · v118.35.0.4 拿返回 tenant_id
            _new_tid_l = _ensure_tenant_for_new_user(
                cur,
                str(user_id),
                invite_plan,
                company_name=company,
                full_name=full_name_safe,
                username=username_use,
            )

            try:
                cur.execute(
                    """
                    INSERT INTO subscription_log(user_id, from_plan, to_plan, reason)
                    VALUES (%s, NULL, %s, 'line_oauth_signup')
                """,
                    (user_id, invite_plan),
                )
            except Exception as ce:
                logger.warning(f"[line_oauth_signup] subscription_log skip: {ce}")

            # v118.35.0.4 · credits 新公司初始化 0 余额
            if invite_plan == "credits" and _new_tid_l:
                try:
                    _db.ensure_tenant_credits(_new_tid_l)
                except Exception as ce:
                    logger.warning(f"[line_oauth_signup] ensure_tenant_credits skip: {ce}")

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
            logger.warning(f"[line_oauth_signup] sample client skip: {ce}")

        logger.info(f"[line_oauth_signup] created user_id={user_id} line_uid={line_uid}")
        return _db.find_user_by_id(str(user_id))

    except Exception as e:
        logger.error(f"[line_oauth_signup] failed: {e}\n{traceback.format_exc()}")
        return None
