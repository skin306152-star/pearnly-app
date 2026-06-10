"""
auth_password_routes.py · 密码找回 / 重置 / 改密 + 邮件 & LINE 发送器

从 auth_signup.py 抽出(模块化深化 · 2026-06-01 · 纯搬家 0 逻辑改)。
🔴 高敏:改密码路径(铁律 #26)。auth_signup include 本 router;
send_reset_link_for_employee(email/LINE 改密链接发送器)单一定义在此。
auth_signup 的 helper(_hash_password / normalize_email / _now / get_client_ip_safe)
在路由函数内 lazy import(破循环 · 同 oauth_routes 惯用法)。
"""

import os
import re
import secrets
import logging
import traceback
from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger("mrpilot.signup")
router = APIRouter()


class ForgotPasswordRequest(BaseModel):
    email: str
    fingerprint: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


def _send_password_reset_via_line(user: dict, reset_url: str) -> bool:
    """通过 LINE Bot 推送密码重置链接 · 返回是否成功"""
    try:
        line_user_id = user.get("line_user_id")
        if not line_user_id:
            return False
        try:
            from services.line_binding import line_client
        except ImportError:
            return False
        msg = (
            "🔑 Pearnly · 密码重置 / Password Reset\n\n"
            "您请求了密码重置 · 点击以下链接设置新密码:\n\n"
            f"{reset_url}\n\n"
            "⏰ 链接 15 分钟内有效\n"
            "❗ 如果不是您本人操作 · 请忽略此消息"
        )
        try:
            line_client.push_message(line_user_id, msg)
            return True
        except Exception as le:
            logger.warning(f"line push fail: {le}")
            return False
    except Exception as e:
        logger.warning(f"_send_password_reset_via_line error: {e}")
        return False


def _send_password_reset_via_email(email: str, reset_url: str, user_name: str = "") -> bool:
    """v118.26.2.3 · 优先用系统 SMTP(Gmail · 系统主邮件通道)· Resend API 作 fallback
    BUG fix:之前只用 Resend 但服务器没配 RESEND_API_KEY · 用户邮件永远收不到
    """
    subject = "🔑 Pearnly · Password Reset / 重置密码"
    html = f"""
        <div style="font-family:Inter,Sarabun,sans-serif;max-width:560px;margin:0 auto;padding:32px;background:#f8fafc;">
            <div style="background:#fff;border-radius:12px;padding:32px;box-shadow:0 4px 24px rgba(0,0,0,0.05);">
                <div style="display:inline-block;padding:6px 14px;background:#0a0e27;color:#fff;border-radius:8px;font-weight:700;font-size:14px;margin-bottom:24px;">Pearnly</div>
                <h1 style="font-size:22px;color:#0f172a;margin:0 0 12px 0;">Reset your password</h1>
                <p style="font-size:14px;color:#64748b;line-height:1.6;">Hi {user_name or 'there'} · 您好,</p>
                <p style="font-size:14px;color:#64748b;line-height:1.6;">We received a request to reset your Pearnly password. Click the button below to set a new one (valid 15 minutes).</p>
                <p style="font-size:14px;color:#64748b;line-height:1.6;">您请求了密码重置 · 点击下方按钮设置新密码(15 分钟内有效)。</p>
                <div style="text-align:center;margin:28px 0;">
                    <a href="{reset_url}" style="display:inline-block;padding:12px 32px;background:#1e3a8a;color:#fff;border-radius:10px;text-decoration:none;font-weight:600;font-size:14px;">Reset Password / 重置密码</a>
                </div>
                <p style="font-size:12px;color:#94a3b8;line-height:1.6;">If the button doesn't work, copy this link:<br><span style="word-break:break-all;color:#475569;">{reset_url}</span></p>
                <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
                <p style="font-size:11px;color:#94a3b8;line-height:1.6;">If you didn't request this, please ignore this email. 如非本人操作 · 请忽略此邮件。</p>
                <p style="font-size:11px;color:#94a3b8;">Need help? Email hello@pearnly.com or LINE @pearnly</p>
            </div>
        </div>
        """
    # 优先 · SMTP(系统主通道 · Gmail · 跟注册验证码一样)
    try:
        from app import _smtp_send_email

        ok, err = _smtp_send_email(email, subject, html)
        if ok:
            return True
        logger.warning(f"smtp pwd reset fail: {err}")
    except Exception as e:
        logger.warning(f"smtp pwd reset import/call err: {e}")

    # Fallback · Resend API(若服务器配了 RESEND_API_KEY)
    try:
        api_key = os.environ.get("RESEND_API_KEY", "").strip()
        if not api_key:
            return False
        try:
            import requests as _req
        except ImportError:
            return False
        from_addr = os.environ.get("RESEND_FROM", "Pearnly <noreply@pearnly.com>")
        r = _req.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": from_addr, "to": [email], "subject": subject, "html": html},
            timeout=10,
        )
        if r.status_code in (200, 201, 202):
            return True
        logger.warning(f"resend api {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        logger.warning(f"resend fallback fail: {e}")
        return False


# ============================================================
# v118.28.7 · 老板给员工发改密链接 · 老板永远拿不到密码
# 大厂惯例:Xero/QuickBooks/Stripe 超管完全不碰客户密码 · 此函数仅供老板调用
# 链接复用现有 password_reset_log 机制 · token 15 分钟 · 单次使用
# ============================================================
def send_reset_link_for_employee(
    user_id: str, request_host: str = "pearnly.com", actor_username: str = None
) -> Dict[str, Any]:
    """
    给员工发改密链接 · 不返回密码
    返回:{ok, channel, has_email, has_line, error}
    渠道任一(email/LINE)发送成功 → ok=True
    没渠道(目标既无 email 也无 line_user_id)→ ok=False · error=no_channel
    """
    from core import db as _db
    from services.auth.auth_signup import _now  # noqa: E402 · lazy 破循环

    out = {"ok": False, "channel": "none", "has_email": False, "has_line": False, "error": None}
    if not user_id:
        out["error"] = "no_user_id"
        return out
    try:
        target = _db.find_user_by_id(str(user_id))
        if not target:
            out["error"] = "not_found"
            return out

        has_email = bool(target.get("email"))
        has_line = bool(target.get("line_user_id"))
        out["has_email"] = has_email
        out["has_line"] = has_line

        if not has_email and not has_line:
            out["error"] = "no_channel"
            return out

        token = secrets.token_urlsafe(32)
        expires_at = _now() + timedelta(minutes=15)
        scheme = "https" if "localhost" not in (request_host or "") else "http"
        reset_url = f"{scheme}://{request_host}/reset?token={token}"

        delivery = "audit_only"
        sent_line = False
        sent_email = False

        if has_line:
            try:
                sent_line = _send_password_reset_via_line(dict(target), reset_url)
                if sent_line:
                    delivery = "line"
                    out["channel"] = "line"
            except Exception as e:
                logger.warning(f"send_reset_link_for_employee · line: {e}")

        if not sent_line and has_email:
            try:
                sent_email = _send_password_reset_via_email(
                    target.get("email"),
                    reset_url,
                    target.get("full_name") or target.get("username") or "",
                )
                if sent_email:
                    delivery = "email"
                    out["channel"] = "email"
            except Exception as e:
                logger.warning(f"send_reset_link_for_employee · email: {e}")

        try:
            with _db.get_cursor(commit=True) as cur:
                cur.execute(
                    """
                    INSERT INTO password_reset_log
                    (token, user_id, email, expires_at, requester_ip, requester_fingerprint, delivery_method)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        token,
                        str(target["id"]),
                        target.get("email") or "",
                        expires_at,
                        f"actor:{actor_username or '?'}:reason:owner_employee_reset"[:64],
                        "",
                        delivery,
                    ),
                )
        except Exception as e:
            logger.error(f"send_reset_link_for_employee · log: {e}")

        if sent_line or sent_email:
            out["ok"] = True
        else:
            out["error"] = "send_failed"
        return out
    except Exception as e:
        logger.error(f"send_reset_link_for_employee failed: {e}\n{traceback.format_exc()}")
        out["error"] = "exception"
        return out


@router.post("/api/auth/forgot_password")
def forgot_password(req: ForgotPasswordRequest, request: Request):
    """忘记密码 · 生成 token · LINE/邮件推送 · 始终返回 success(防 enumerate)"""
    from services.auth.auth_signup import (
        normalize_email,
        get_client_ip_safe,
        _now,
    )  # noqa: E402 · lazy 破循环

    try:
        from core import db as _db

        email_norm = normalize_email(req.email)
        ip = get_client_ip_safe(request)

        # 限流:同邮箱 1 小时只能 3 次
        try:
            with _db.get_cursor(commit=True) as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS n FROM password_reset_log
                    WHERE email = %s AND created_at > NOW() - INTERVAL '1 hour'
                """,
                    (email_norm,),
                )
                row = cur.fetchone()
                n = row.get("n") if isinstance(row, dict) else (row[0] if row else 0)
                if n and int(n) >= 3:
                    return {"ok": True}  # 不告诉对方限流
        except Exception as e:
            logger.warning(f"[password_reset] 频次检查失败 · 放行: {e}")

        # 找用户
        user = None
        try:
            with _db.get_cursor(commit=True) as cur:
                cur.execute(
                    """
                    SELECT id, username, email, full_name, line_user_id
                    FROM users
                    WHERE email_normalized = %s OR LOWER(email) = %s
                    LIMIT 1
                """,
                    (email_norm, email_norm),
                )
                user = cur.fetchone()
        except Exception as e:
            logger.warning(f"forgot_password user lookup: {e}")

        if not user:
            # 防 enumerate · 返回 ok
            return {"ok": True}

        # 生成 token
        token = secrets.token_urlsafe(32)
        expires_at = _now() + timedelta(minutes=15)

        # 决定推送方式
        host = request.headers.get("host", "pearnly.com")
        scheme = "https" if "localhost" not in host else "http"
        reset_url = f"{scheme}://{host}/reset?token={token}"

        delivery = "audit_only"
        sent_line = False
        sent_email = False

        # 优先 LINE
        if user.get("line_user_id"):
            sent_line = _send_password_reset_via_line(dict(user), reset_url)
            if sent_line:
                delivery = "line"

        # LINE 失败 · 试邮件
        if not sent_line:
            sent_email = _send_password_reset_via_email(
                user.get("email") or req.email,
                reset_url,
                user.get("full_name") or user.get("username") or "",
            )
            if sent_email:
                delivery = "email"

        # 写入 log(管理员可看 · 兜底)
        try:
            with _db.get_cursor(commit=True) as cur:
                cur.execute(
                    """
                    INSERT INTO password_reset_log
                    (token, user_id, email, expires_at, requester_ip, requester_fingerprint, delivery_method)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        token,
                        str(user["id"]),
                        user.get("email") or req.email,
                        expires_at,
                        ip,
                        (req.fingerprint or "")[:128],
                        delivery,
                    ),
                )
        except Exception as e:
            logger.error(f"forgot_password log insert: {e}")

        return {"ok": True}
    except Exception as e:
        logger.error(f"forgot_password: {e}\n{traceback.format_exc()}")
        # 即使内部异常也不暴露 · 返回 ok
        return {"ok": True}


@router.post("/api/auth/reset_password")
def reset_password(req: ResetPasswordRequest, request: Request):
    """凭 token 重置密码"""
    from services.auth.auth_signup import _hash_password, _now  # noqa: E402 · lazy 破循环

    try:
        from core import db as _db

        if not req.token or len(req.token) < 16:
            raise HTTPException(400, detail="invalid_token")
        if not req.new_password or len(req.new_password) < 8:
            raise HTTPException(400, detail="password_too_short")
        if not (re.search(r"[a-zA-Z]", req.new_password) and re.search(r"\d", req.new_password)):
            raise HTTPException(400, detail="password_too_weak")

        # 查 token
        with _db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                SELECT id, user_id, email, expires_at, used
                FROM password_reset_log
                WHERE token = %s
                LIMIT 1
            """,
                (req.token,),
            )
            log_row = cur.fetchone()

        if not log_row:
            raise HTTPException(400, detail="invalid_token")
        if log_row.get("used") if isinstance(log_row, dict) else log_row[4]:
            raise HTTPException(400, detail="token_already_used")
        exp_at = log_row.get("expires_at") if isinstance(log_row, dict) else log_row[3]
        if exp_at and exp_at < _now():
            raise HTTPException(400, detail="token_expired")

        user_id = log_row.get("user_id") if isinstance(log_row, dict) else log_row[1]

        # 改密
        new_hash = _hash_password(req.new_password)
        with _db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s, password_changed_at = NOW() WHERE id = %s",
                (new_hash, str(user_id)),
            )
            cur.execute(
                """
                UPDATE password_reset_log SET used = true, used_at = NOW()
                WHERE token = %s
            """,
                (req.token,),
            )
            # 同邮箱所有未用 token 也作废
            email_val = log_row.get("email") if isinstance(log_row, dict) else log_row[2]
            cur.execute(
                """
                UPDATE password_reset_log SET used = true, used_at = NOW()
                WHERE email = %s AND used = false
            """,
                (email_val,),
            )
            # 清空登录失败记录
            cur.execute(
                """
                DELETE FROM login_failure_log
                WHERE email_or_username = LOWER(%s)
                   OR email_or_username = LOWER((SELECT username FROM users WHERE id=%s))
            """,
                (email_val, str(user_id)),
            )

        return {"ok": True, "message": "password_reset_success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"reset_password: {e}\n{traceback.format_exc()}")
        raise HTTPException(500, detail="reset_failed")


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/api/me/change_password")
def change_password(req: ChangePasswordRequest, request: Request):
    """已登录用户改密码"""
    try:
        from core.auth import get_current_user_from_request, verify_password
        from services.auth.auth_signup import _hash_password  # noqa: E402 · lazy 破循环

        user = get_current_user_from_request(request)
        if not user:
            raise HTTPException(401, detail="unauthorized")

        if not verify_password(req.old_password, user.get("password_hash") or ""):
            raise HTTPException(400, detail="wrong_old_password")
        if not req.new_password or len(req.new_password) < 8:
            raise HTTPException(400, detail="password_too_short")
        if not (re.search(r"[a-zA-Z]", req.new_password) and re.search(r"\d", req.new_password)):
            raise HTTPException(400, detail="password_too_weak")

        from core import db as _db

        new_hash = _hash_password(req.new_password)
        with _db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s, password_changed_at = NOW() WHERE id = %s",
                (new_hash, str(user["id"])),
            )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"change_password: {e}")
        raise HTTPException(500, detail="change_failed")
