# -*- coding: utf-8 -*-
"""邮箱抓取(IMAP)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
db.py 在文件尾用 `from services.email_ingest.store import ...` re-export 这些函数 ·
所有 `db.xxx()` / `from db import xxx` 调用点保持不变。
"""

import logging
from typing import Optional, Dict, Any, List

from core import db

logger = logging.getLogger(__name__)


def get_email_account(user_id: str) -> Optional[Dict[str, Any]]:
    """读当前用户绑定的邮箱账号(第一版一人一个)· 返回完整行(含 password_enc)"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, email_address, imap_host, imap_port, imap_use_ssl,
                       password_enc, folder, filter_subject, filter_sender, mark_as_read,
                       enabled, last_check_at, last_error,
                       success_count, failure_count, last_fetched_at,
                       interval_min,
                       created_at, updated_at
                FROM email_ingest_accounts
                WHERE user_id = %s
                LIMIT 1
            """,
                (str(user_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_email_account failed: {e}")
        return None


def get_email_account_safe(user_id: str) -> Optional[Dict[str, Any]]:
    """前端用 · 不返回 password_enc · 返回 has_password 标志"""
    row = get_email_account(user_id)
    if not row:
        return None
    password_enc = row.pop("password_enc", None)
    row["has_password"] = bool(password_enc)
    return row


def upsert_email_account(
    user_id: str,
    email_address: str,
    imap_host: str,
    imap_port: int,
    imap_use_ssl: bool,
    password_enc: Optional[bytes],
    folder: str = "INBOX",
    filter_subject: Optional[str] = None,
    filter_sender: Optional[str] = None,
    mark_as_read: bool = True,
    enabled: bool = True,
    interval_min: int = 15,
) -> Optional[str]:
    """新增或更新邮箱账号 · 返回 id(若未传 password_enc 则保留旧密码)"""
    # 限制 interval_min 只能是 5/15/60 · 其他值兜底成 15
    if interval_min not in (5, 15, 60):
        interval_min = 15
    try:
        with db.get_cursor(commit=True) as cur:
            if password_enc is not None:
                cur.execute(
                    """
                    INSERT INTO email_ingest_accounts
                        (user_id, email_address, imap_host, imap_port, imap_use_ssl,
                         password_enc, folder, filter_subject, filter_sender,
                         mark_as_read, enabled, interval_min)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        email_address = EXCLUDED.email_address,
                        imap_host     = EXCLUDED.imap_host,
                        imap_port     = EXCLUDED.imap_port,
                        imap_use_ssl  = EXCLUDED.imap_use_ssl,
                        password_enc  = EXCLUDED.password_enc,
                        folder        = EXCLUDED.folder,
                        filter_subject= EXCLUDED.filter_subject,
                        filter_sender = EXCLUDED.filter_sender,
                        mark_as_read  = EXCLUDED.mark_as_read,
                        enabled       = EXCLUDED.enabled,
                        interval_min  = EXCLUDED.interval_min,
                        updated_at    = NOW()
                    RETURNING id
                """,
                    (
                        str(user_id),
                        email_address,
                        imap_host,
                        int(imap_port),
                        bool(imap_use_ssl),
                        password_enc,
                        folder,
                        filter_subject,
                        filter_sender,
                        bool(mark_as_read),
                        bool(enabled),
                        interval_min,
                    ),
                )
            else:
                # 不改密码的更新(用户只改配置)
                cur.execute(
                    """
                    INSERT INTO email_ingest_accounts
                        (user_id, email_address, imap_host, imap_port, imap_use_ssl,
                         password_enc, folder, filter_subject, filter_sender,
                         mark_as_read, enabled, interval_min)
                    VALUES (%s, %s, %s, %s, %s, ''::bytea, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        email_address = EXCLUDED.email_address,
                        imap_host     = EXCLUDED.imap_host,
                        imap_port     = EXCLUDED.imap_port,
                        imap_use_ssl  = EXCLUDED.imap_use_ssl,
                        folder        = EXCLUDED.folder,
                        filter_subject= EXCLUDED.filter_subject,
                        filter_sender = EXCLUDED.filter_sender,
                        mark_as_read  = EXCLUDED.mark_as_read,
                        enabled       = EXCLUDED.enabled,
                        interval_min  = EXCLUDED.interval_min,
                        updated_at    = NOW()
                    RETURNING id
                """,
                    (
                        str(user_id),
                        email_address,
                        imap_host,
                        int(imap_port),
                        bool(imap_use_ssl),
                        folder,
                        filter_subject,
                        filter_sender,
                        bool(mark_as_read),
                        bool(enabled),
                        interval_min,
                    ),
                )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_email_account failed: {e}")
        return None


def delete_email_account(user_id: str) -> bool:
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                DELETE FROM email_ingest_accounts WHERE user_id = %s
            """,
                (str(user_id),),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_email_account failed: {e}")
        return False


def list_enabled_email_accounts() -> List[Dict[str, Any]]:
    """定时任务用 · 列出所有启用的账号(含 password_enc 供解密)"""
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT id, user_id, email_address, imap_host, imap_port, imap_use_ssl,
                       password_enc, folder, filter_subject, filter_sender,
                       mark_as_read, last_check_at, last_fetched_at, interval_min
                FROM email_ingest_accounts
                WHERE enabled = TRUE
                ORDER BY last_check_at NULLS FIRST, created_at
            """)
            return [dict(r) for r in (cur.fetchall() or [])]
    except Exception as e:
        logger.error(f"list_enabled_email_accounts failed: {e}")
        return []


def update_email_account_status(
    account_id: str, success: bool, error_msg: Optional[str] = None, fetched_any: bool = False
):
    """每次抓取完更新账号状态"""
    try:
        with db.get_cursor(commit=True) as cur:
            if success:
                if fetched_any:
                    cur.execute(
                        """
                        UPDATE email_ingest_accounts
                        SET last_check_at   = NOW(),
                            last_fetched_at = NOW(),
                            last_error      = NULL,
                            success_count   = success_count + 1,
                            updated_at      = NOW()
                        WHERE id = %s
                    """,
                        (account_id,),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE email_ingest_accounts
                        SET last_check_at = NOW(),
                            last_error    = NULL,
                            updated_at    = NOW()
                        WHERE id = %s
                    """,
                        (account_id,),
                    )
            else:
                cur.execute(
                    """
                    UPDATE email_ingest_accounts
                    SET last_check_at   = NOW(),
                        last_error      = %s,
                        failure_count   = failure_count + 1,
                        updated_at      = NOW()
                    WHERE id = %s
                """,
                    (error_msg, account_id),
                )
    except Exception as e:
        logger.error(f"update_email_account_status failed: {e}")


def insert_email_ingest_log(
    account_id: str, user_id: str, stats: Dict[str, Any], trigger: str = "auto"
) -> Optional[str]:
    """写一条抓取日志"""
    import json as _json

    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO email_ingest_logs
                    (account_id, user_id, status, emails_scanned, attachments_found,
                     ocr_succeeded, ocr_failed, elapsed_ms, error_message, error_details, trigger)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                RETURNING id
            """,
                (
                    account_id,
                    user_id,
                    stats.get("status"),
                    int(stats.get("emails_scanned") or 0),
                    int(stats.get("attachments_found") or 0),
                    int(stats.get("ocr_succeeded") or 0),
                    int(stats.get("ocr_failed") or 0),
                    int(stats.get("elapsed_ms") or 0),
                    stats.get("error_message"),
                    _json.dumps(stats.get("error_details") or [], ensure_ascii=False),
                    trigger,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"insert_email_ingest_log failed: {e}")
        return None


def list_email_ingest_logs(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """前端用 · 最近的抓取日志"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, status, emails_scanned, attachments_found,
                       ocr_succeeded, ocr_failed, elapsed_ms,
                       error_message, trigger, created_at
                FROM email_ingest_logs
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """,
                (str(user_id), int(limit)),
            )
            return [dict(r) for r in (cur.fetchall() or [])]
    except Exception as e:
        logger.error(f"list_email_ingest_logs failed: {e}")
        return []


def is_email_uid_seen(account_id: str, uid: str) -> bool:
    """查这封邮件是否抓过"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM email_ingest_seen_uids
                WHERE account_id = %s AND uid = %s LIMIT 1
            """,
                (account_id, uid),
            )
            return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"is_email_uid_seen failed: {e}")
        return False


def mark_email_uid_seen(
    account_id: str,
    uid: str,
    history_id: Optional[str],
    subject: Optional[str],
    sender: Optional[str],
) -> bool:
    """标记这封邮件处理过 · history_id 可为空(无附件/OCR 失败场景)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO email_ingest_seen_uids
                    (account_id, uid, history_id, subject, sender)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (account_id, uid) DO NOTHING
            """,
                (account_id, uid, history_id, (subject or "")[:500], (sender or "")[:200]),
            )
            return True
    except Exception as e:
        logger.error(f"mark_email_uid_seen failed: {e}")
        return False
