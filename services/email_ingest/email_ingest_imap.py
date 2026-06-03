# -*- coding: utf-8 -*-
"""email_ingest · IMAP 预设/常量 + MIME 解码 + 连接/搜索/抓取/标记已读 leaf。"""

import os
import email
import imaplib
import logging
from email.header import decode_header
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from services.ocr.entrypoints import SUPPORTED_OCR_EXTENSIONS
from services.email_ingest.email_ingest_crypto import decrypt_password

logger = logging.getLogger(__name__)

# IMAP 预设(主流服务默认配置 · 前端下拉选)
IMAP_PRESETS = {
    "gmail": {"host": "imap.gmail.com", "port": 993, "ssl": True},
    "outlook": {"host": "outlook.office365.com", "port": 993, "ssl": True},
    "yahoo": {"host": "imap.mail.yahoo.com", "port": 993, "ssl": True},
    "icloud": {"host": "imap.mail.me.com", "port": 993, "ssl": True},
    "qq": {"host": "imap.qq.com", "port": 993, "ssl": True},
    "163": {"host": "imap.163.com", "port": 993, "ssl": True},
    # 通用 · 用户自填
    "custom": {"host": "", "port": 993, "ssl": True},
}

# 支持的附件扩展名(与网页上传 OCR 入口保持一致)
_SUPPORTED_EXTS = SUPPORTED_OCR_EXTENSIONS

# 首次抓取时向前追溯多少天
INITIAL_DAYS_BACK = 7

# 单次最多处理多少封邮件
MAX_EMAILS_PER_RUN = 20


def _decode_mime(s) -> str:
    """解码 MIME 编码的邮件头(如 =?UTF-8?B?...?=)"""
    if s is None:
        return ""
    parts = decode_header(s)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            try:
                out.append(text.decode(enc or "utf-8", errors="replace"))
            except Exception:
                out.append(text.decode("utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _extract_attachments(msg) -> List[Tuple[str, bytes]]:
    """
    从 email.Message 中抽取支持的附件 · 返回 [(filename, content_bytes)]
    跳过内联图片(Content-Disposition=inline)和不支持的扩展名
    """
    results = []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        filename = part.get_filename()
        if not filename:
            continue
        filename = _decode_mime(filename)
        ext = os.path.splitext(filename.lower())[1]
        if ext not in _SUPPORTED_EXTS:
            continue
        disp = (part.get("Content-Disposition") or "").lower()
        if "inline" in disp and "attachment" not in disp:
            # 内联图片(如邮件签名)· 跳过
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        results.append((filename, payload))
    return results


def _connect_imap(account: Dict[str, Any]) -> Optional[imaplib.IMAP4]:
    """建 IMAP 连接 · 失败返回 None"""
    host = account["imap_host"]
    port = int(account.get("imap_port") or 993)
    use_ssl = bool(account.get("imap_use_ssl", True))
    try:
        if use_ssl:
            conn = imaplib.IMAP4_SSL(host, port, timeout=20)
        else:
            conn = imaplib.IMAP4(host, port, timeout=20)
        password = decrypt_password(account["password_enc"])
        if password is None:
            logger.error(f"[email_ingest] 账号密码解密失败 · account_id={account['id']}")
            return None
        conn.login(account["email_address"], password)
        return conn
    except Exception as e:
        logger.error(f"[email_ingest] IMAP 连接失败 {host}:{port} · {type(e).__name__}: {e}")
        return None


def _search_unread_with_attachments(
    conn: imaplib.IMAP4, folder: str, since_days: int
) -> List[bytes]:
    """搜未读邮件 · 返回 UID 列表"""
    try:
        conn.select(folder, readonly=False)
        since_date = (datetime.utcnow() - timedelta(days=since_days)).strftime("%d-%b-%Y")
        # UNSEEN = 未读 · SINCE 是日期下限 · HAS ATTACHMENT 不是所有服务器都支持 · 所以下载后再过滤附件
        status, data = conn.uid("SEARCH", None, f'(UNSEEN SINCE "{since_date}")')
        if status != "OK" or not data or not data[0]:
            return []
        return data[0].split()
    except Exception as e:
        logger.error(f"[email_ingest] IMAP 搜索失败: {type(e).__name__}: {e}")
        return []


def _fetch_email(conn: imaplib.IMAP4, uid: bytes):
    """根据 UID 取整封邮件 · 返回 email.Message 或 None"""
    try:
        status, data = conn.uid("FETCH", uid, "(RFC822)")
        if status != "OK" or not data or not data[0]:
            return None
        raw = data[0][1]
        return email.message_from_bytes(raw)
    except Exception as e:
        logger.error(f"[email_ingest] FETCH {uid} 失败: {type(e).__name__}: {e}")
        return None


def _mark_seen(conn: imaplib.IMAP4, uid: bytes):
    """标已读"""
    try:
        conn.uid("STORE", uid, "+FLAGS", "\\Seen")
    except Exception as e:
        logger.warning(f"[email_ingest] 标已读失败 uid={uid}: {e}")
