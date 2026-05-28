"""
auth_email_code_routes.py · 邮箱验证码发送 / 校验路由(REFACTOR-B1)

从 app.py L3620-3920 抽出 · 0 业务逻辑改 · 纯路由 + helpers + Pydantic models 搬家:
    POST /api/auth/send_email_code   v118.27.6 发 6 位数字验证码(注册前必走)
    POST /api/auth/verify_email_code v118.27.6 校验验证码(不消耗 · 消耗在 signup 时)

包含的私有 helpers / 模型:
    - _smtp_send_email(to, subject, html) SMTP 发邮件
    - _build_verification_email_html(code, lang) 4 语品牌邮件模板
    - _RE_EMAIL_V276 邮件格式正则
    - SendEmailCodeRequest / VerifyEmailCodeRequest pydantic 模型

E2E 闸:spec 17(email-code-flow 4 端点 smoke)兜底。
"""

from __future__ import annotations

import logging
import os
import re as _re_v276
import secrets as _secrets
import smtplib as _smtplib
import ssl as _ssl
import traceback as _tb_v276
from email.mime.multipart import MIMEMultipart as _MIMEMulti
from email.mime.text import MIMEText as _MIMEText
from email.utils import formataddr as _formataddr

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

import db

logger = logging.getLogger(__name__)

router = APIRouter()


def _smtp_send_email(to_email: str, subject: str, html_body: str) -> tuple:
    """SMTP 发邮件 · 返回 (success: bool, error: str)"""
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
    try:
        port = int(os.environ.get("SMTP_PORT", "587"))
    except ValueError:
        port = 587
    user = os.environ.get("SMTP_USER", "").strip()
    pwd = os.environ.get("SMTP_PASSWORD", "").strip()
    from_addr = os.environ.get("SMTP_FROM", user).strip()
    from_name = os.environ.get("SMTP_FROM_NAME", "Pearnly").strip()

    if not host or not user or not pwd:
        return (False, "smtp_not_configured")
    try:
        msg = _MIMEMulti("alternative")
        msg["From"] = _formataddr((from_name, from_addr))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(_MIMEText(html_body, "html", "utf-8"))

        ctx = _ssl.create_default_context()
        with _smtplib.SMTP(host, port, timeout=15) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.login(user, pwd)
            s.send_message(msg)
        return (True, "")
    except Exception as e:
        logger.error(f"smtp send failed: {type(e).__name__}: {e}")
        return (False, str(e)[:240])


def _build_verification_email_html(code: str, lang: str) -> tuple:
    """v118.27.6.1 · 企业级品牌邮件模板 · hero 渐变 + 大验证码 + 公司 footer · 4 语"""
    lang = (lang or "zh").lower()[:2]
    L = {
        "zh": {
            "subject": "Pearnly · 您的验证码",
            "tagline": "AI 财务副驾驶",
            "title": "您的验证码",
            "lead": "用于创建 Pearnly 账户 · 10 分钟内有效",
            "ignore": "如非本人操作 · 请忽略此邮件 · 您的账户安全无风险",
            "brand_full": "Pearnly · 泰国会计自动化平台",
            "tos": "服务条款",
            "privacy": "隐私政策",
            "copyright": "© 2026 Pearnly. All rights reserved.",
        },
        "th": {
            "subject": "Pearnly · รหัสยืนยันของคุณ",
            "tagline": "ผู้ช่วย AI ด้านบัญชี",
            "title": "รหัสยืนยันของคุณ",
            "lead": "ใช้รหัสนี้เพื่อสมัครบัญชี Pearnly · ใช้ได้ 10 นาที",
            "ignore": "หากคุณไม่ได้ทำรายการนี้ · โปรดเพิกเฉยอีเมลฉบับนี้",
            "brand_full": "Pearnly · ระบบอัตโนมัติบัญชีไทย",
            "tos": "ข้อกำหนด",
            "privacy": "นโยบายความเป็นส่วนตัว",
            "copyright": "© 2026 Pearnly · สงวนลิขสิทธิ์",
        },
        "en": {
            "subject": "Pearnly · Your verification code",
            "tagline": "Your AI accounting co-pilot",
            "title": "Your verification code",
            "lead": "Use this code to create your Pearnly account · valid for 10 minutes",
            "ignore": "If you didn't request this · please ignore this email",
            "brand_full": "Pearnly · Accounting automation for Thailand",
            "tos": "Terms",
            "privacy": "Privacy",
            "copyright": "© 2026 Pearnly. All rights reserved.",
        },
        "ja": {
            "subject": "Pearnly · 確認コード",
            "tagline": "AI 会計コパイロット",
            "title": "確認コード",
            "lead": "Pearnly アカウント作成用 · 10 分間有効",
            "ignore": "心当たりのない場合 · このメールを無視してください",
            "brand_full": "Pearnly · タイ会計自動化プラットフォーム",
            "tos": "利用規約",
            "privacy": "プライバシーポリシー",
            "copyright": "© 2026 Pearnly. All rights reserved.",
        },
    }
    tt = L.get(lang, L["zh"])
    html = f"""<!doctype html><html><body style="margin:0;padding:0;background:#f1f5f9;">
<div style="font-family:Inter,-apple-system,'PingFang SC',Sarabun,'Hiragino Sans',sans-serif;max-width:560px;margin:0 auto;padding:32px 16px;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.08);">
    <tr><td style="background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 60%,#2563eb 100%);padding:44px 40px 38px;text-align:center;">
      <table border="0" cellpadding="0" cellspacing="0" align="center"><tr>
        <td style="vertical-align:middle;padding-right:10px;">
          <div style="display:inline-block;width:36px;height:36px;background:#fff;border-radius:8px;text-align:center;line-height:36px;font-weight:800;font-size:18px;color:#1e3a8a;font-family:Inter,sans-serif;">P</div>
        </td>
        <td style="vertical-align:middle;">
          <div style="font-weight:800;font-size:24px;color:#fff;letter-spacing:-0.3px;line-height:1;">Pearnly</div>
        </td>
      </tr></table>
      <div style="margin-top:12px;font-size:12px;color:#cbd5e1;letter-spacing:1.5px;text-transform:uppercase;font-weight:600;">{tt["tagline"]}</div>
    </td></tr>
    <tr><td style="padding:44px 40px 36px;">
      <h1 style="font-size:22px;color:#0f172a;margin:0 0 10px;font-weight:700;letter-spacing:-0.2px;">{tt["title"]}</h1>
      <p style="font-size:14px;color:#64748b;line-height:1.65;margin:0 0 28px;">{tt["lead"]}</p>
      <div style="background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);border:1px solid #bfdbfe;border-radius:12px;padding:32px 24px;text-align:center;">
        <div style="font-size:38px;font-weight:700;letter-spacing:10px;color:#1e3a8a;font-family:'SF Mono','Roboto Mono',Consolas,monospace;line-height:1;">{code}</div>
      </div>
      <p style="font-size:13px;color:#94a3b8;line-height:1.65;margin:28px 0 0;">{tt["ignore"]}</p>
    </td></tr>
    <tr><td style="background:#f8fafc;padding:24px 40px 28px;border-top:1px solid #e2e8f0;text-align:center;">
      <div style="font-size:12px;color:#475569;margin-bottom:6px;font-weight:600;">{tt["brand_full"]}</div>
      <div style="font-size:11px;color:#94a3b8;line-height:1.7;">
        Bangkok, Thailand · <a href="https://pearnly.com" style="color:#94a3b8;text-decoration:none;">pearnly.com</a><br>
        hello@pearnly.com · LINE @059oupmg · +66 86-889-2228
      </div>
      <div style="margin-top:12px;font-size:11px;">
        <a href="https://pearnly.com/terms" style="color:#94a3b8;text-decoration:none;margin:0 8px;">{tt["tos"]}</a>
        <span style="color:#cbd5e1;">·</span>
        <a href="https://pearnly.com/privacy" style="color:#94a3b8;text-decoration:none;margin:0 8px;">{tt["privacy"]}</a>
      </div>
      <div style="font-size:10px;color:#cbd5e1;margin-top:14px;">{tt["copyright"]}</div>
    </td></tr>
  </table>
</div>
</body></html>"""
    return (tt["subject"], html)


_RE_EMAIL_V276 = _re_v276.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class SendEmailCodeRequest(BaseModel):
    email: str
    purpose: str = "signup"
    lang: str = "zh"


class VerifyEmailCodeRequest(BaseModel):
    email: str
    code: str
    purpose: str = "signup"


@router.post("/api/auth/send_email_code")
def send_email_code(req: SendEmailCodeRequest, request: Request):
    """v118.27.6 · 发邮箱验证码 · 注册前必走"""
    try:
        email = (req.email or "").strip().lower()
        if not email or not _RE_EMAIL_V276.match(email):
            raise HTTPException(status_code=400, detail="email_invalid")
        if req.purpose not in ("signup",):
            raise HTTPException(status_code=400, detail="purpose_invalid")

        # 已注册则不发(防 enumerate 用 409 因为注册流程要明确告知)
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM users WHERE email_normalized = %s OR LOWER(email) = %s LIMIT 1",
                    (email, email),
                )
                if cur.fetchone():
                    raise HTTPException(status_code=409, detail="email_already_registered")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"send_email_code user check: {e}")

        # 限流 · 60s 内只能发 1 次 · 1 小时最多 5 次
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM email_codes
                    WHERE email = %s AND purpose = %s AND sent_at > NOW() - INTERVAL '60 seconds'
                    LIMIT 1
                """,
                    (email, req.purpose),
                )
                if cur.fetchone():
                    raise HTTPException(status_code=429, detail="resend_too_fast")

                cur.execute(
                    """
                    SELECT COUNT(*) AS n FROM email_codes
                    WHERE email = %s AND purpose = %s AND sent_at > NOW() - INTERVAL '1 hour'
                """,
                    (email, req.purpose),
                )
                row = cur.fetchone()
                n = row.get("n") if isinstance(row, dict) else (row[0] if row else 0)
                if n and int(n) >= 5:
                    raise HTTPException(status_code=429, detail="hourly_limit_reached")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"send_email_code rate limit: {e}")

        # 6 位数字
        code = "".join([_secrets.choice("0123456789") for _ in range(6)])

        # 写 DB(旧未用 code 全部失效)
        ip = ""
        try:
            ip = (request.client.host if request.client else "")[:64]
        except Exception as e:
            logger.warning(f"[email_code] 读取客户端 IP 失败: {e}")
        try:
            with db.get_cursor(commit=True) as cur:
                cur.execute(
                    """
                    UPDATE email_codes SET used = TRUE, used_at = NOW()
                    WHERE email = %s AND purpose = %s AND used = FALSE
                """,
                    (email, req.purpose),
                )
                cur.execute(
                    """
                    INSERT INTO email_codes (email, code, purpose, expires_at, sender_ip)
                    VALUES (%s, %s, %s, NOW() + INTERVAL '10 minutes', %s)
                """,
                    (email, code, req.purpose, ip),
                )
        except Exception as e:
            logger.error(f"send_email_code db insert: {e}")
            raise HTTPException(status_code=500, detail="db_error")

        # 发邮件
        subject, html = _build_verification_email_html(code, req.lang)
        ok, err = _smtp_send_email(email, subject, html)
        if not ok:
            try:
                with db.get_cursor(commit=True) as cur:
                    cur.execute(
                        """
                        UPDATE email_codes SET used = TRUE, used_at = NOW()
                        WHERE email = %s AND code = %s AND purpose = %s
                    """,
                        (email, code, req.purpose),
                    )
            except Exception as e:
                logger.warning(f"[email_code] 标记 code 已用失败: {e}")
            logger.error(f"send_email_code smtp failed for {email}: {err}")
            raise HTTPException(status_code=502, detail="email_delivery_failed")

        logger.info(f"[v118.27.6] verification code sent to {email}")
        return {"ok": True, "ttl_seconds": 600, "resend_after": 60}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"send_email_code: {e}\n{_tb_v276.format_exc()}")
        raise HTTPException(status_code=500, detail="server_error")


@router.post("/api/auth/verify_email_code")
def verify_email_code(req: VerifyEmailCodeRequest):
    """v118.27.6 · 仅校验验证码 · 不消耗(消耗在 signup 时一并)"""
    try:
        email = (req.email or "").strip().lower()
        code = (req.code or "").strip()
        if not email or not code:
            raise HTTPException(status_code=400, detail="missing_fields")
        if not _re_v276.match(r"^\d{4,8}$", code):
            raise HTTPException(status_code=400, detail="code_invalid")

        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, expires_at, used FROM email_codes
                WHERE email = %s AND code = %s AND purpose = %s
                ORDER BY id DESC LIMIT 1
            """,
                (email, code, req.purpose),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail="code_invalid")
            r = dict(row) if not isinstance(row, dict) else row
            if r.get("used"):
                raise HTTPException(status_code=400, detail="code_used")
            cur.execute("SELECT NOW() > %s AS expired", (r["expires_at"],))
            exp_row = cur.fetchone()
            expired = (
                exp_row.get("expired")
                if isinstance(exp_row, dict)
                else (exp_row[0] if exp_row else True)
            )
            if expired:
                raise HTTPException(status_code=400, detail="code_expired")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"verify_email_code: {e}")
        raise HTTPException(status_code=500, detail="server_error")
