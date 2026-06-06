# -*- coding: utf-8 -*-
"""发票发送(PO-7 · docs/16 §L5)。

本期(不被 Google 卡)做两档:
- 邮件·官方代发:从 hello@pearnly.com(SMTP_FROM)发 PDF 附件,From 显示卖方名、Reply-To
  卖方邮箱(买家回信回卖方)。复用现成 SMTP 环境变量。
- LINE·我自己转发:不在此发,路由生成分享链接(services/sales/share.py),卖方自己转。

Gmail 私人发信 / LINE 官号推送 = 后续(集成审核 / 高敏),此模块只管官方代发 SMTP + 投递日志。
SQL 参数化,租户隔离靠调用方的 get_cursor_rls + WHERE tenant_id。
"""

from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional

logger = logging.getLogger("mr-pilot")


def smtp_configured() -> bool:
    return bool(
        os.environ.get("SMTP_HOST", "").strip()
        and os.environ.get("SMTP_USER", "").strip()
        and os.environ.get("SMTP_PASSWORD", "").strip()
    )


def send_email_with_pdf(
    *,
    to_email: str,
    subject: str,
    html_body: str,
    pdf_bytes: bytes,
    pdf_name: str,
    from_name: str,
    reply_to: Optional[str] = None,
) -> tuple[bool, str]:
    """官方代发:hello@pearnly.com 发带 PDF 附件的邮件。返回 (success, error)。

    From 地址 = SMTP_FROM(平台官方),显示名 = 卖方名;Reply-To = 卖方邮箱(给了才设)。
    """
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
    try:
        port = int(os.environ.get("SMTP_PORT", "587"))
    except ValueError:
        port = 587
    user = os.environ.get("SMTP_USER", "").strip()
    pwd = os.environ.get("SMTP_PASSWORD", "").strip()
    from_addr = os.environ.get("SMTP_FROM", user).strip()
    if not host or not user or not pwd:
        return (False, "smtp_not_configured")
    if not to_email:
        return (False, "recipient_required")
    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = formataddr((from_name or "Pearnly", from_addr))
        msg["To"] = to_email
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        part = MIMEApplication(pdf_bytes, _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=f"{pdf_name}.pdf")
        msg.attach(part)

        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.login(user, pwd)
            s.send_message(msg)
        return (True, "")
    except Exception as e:
        logger.error("sales send_email failed: %s: %s", type(e).__name__, e)
        return (False, str(e)[:240])


def record_send(
    cur,
    *,
    tenant_id: str,
    doc_id,
    channel: str,
    identity: str,
    recipient: Optional[str],
    status: str,
    error: Optional[str],
    created_by: Optional[str],
) -> None:
    """投递日志(每次发送一行)。失败也记,便于排查与重发。"""
    cur.execute(
        "INSERT INTO sales_document_sends "
        "(tenant_id, document_id, channel, identity, recipient, status, error, created_by) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (tenant_id, doc_id, channel, identity, recipient, status, (error or None), created_by),
    )
