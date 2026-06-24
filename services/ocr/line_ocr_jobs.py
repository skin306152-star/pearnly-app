# -*- coding: utf-8 -*-
"""Durable LINE OCR job store and worker."""

from __future__ import annotations

import json
import logging
from typing import Optional

from core import db

logger = logging.getLogger("mr-pilot")

_TABLE = """
CREATE TABLE IF NOT EXISTS line_ocr_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid,
    user_id text NOT NULL DEFAULT '',
    line_user_id text NOT NULL,
    message_id text NOT NULL,
    lang text NOT NULL DEFAULT 'th',
    filename text,
    quote_token text,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'queued',
    attempts int NOT NULL DEFAULT 0,
    max_attempts int NOT NULL DEFAULT 3,
    last_error text,
    next_retry_at timestamptz,
    started_at timestamptz,
    finished_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
)
"""

_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_line_ocr_job_message "
    "ON line_ocr_jobs (line_user_id, message_id)",
    "CREATE INDEX IF NOT EXISTS ix_line_ocr_jobs_due "
    "ON line_ocr_jobs (status, next_retry_at, created_at)",
    "CREATE INDEX IF NOT EXISTS ix_line_ocr_jobs_tenant "
    "ON line_ocr_jobs (tenant_id, status, created_at)",
)

_DELAYS = (60, 300, 1800)


def ensure_table() -> None:
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, "line_ocr_jobs")


def _row(row) -> dict:
    return dict(row) if row else {}


def _payload(bound_user: Optional[dict]) -> str:
    if not bound_user:
        return "{}"
    keep = {
        "id": bound_user.get("id"),
        "tenant_id": bound_user.get("tenant_id"),
        "preferred_lang": bound_user.get("preferred_lang"),
    }
    return json.dumps(keep, ensure_ascii=False, default=str)


def _insert_job(
    *,
    bound_user: dict,
    line_user_id: str,
    message_id: str,
    lang: str,
    filename: str = None,
    quote_token: str = None,
) -> Optional[dict]:
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO line_ocr_jobs
                (tenant_id, user_id, line_user_id, message_id, lang,
                 filename, quote_token, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (line_user_id, message_id) DO UPDATE SET
                updated_at = now()
            RETURNING id, status, attempts, max_attempts
            """,
            (
                bound_user.get("tenant_id"),
                str(bound_user.get("id") or ""),
                line_user_id,
                message_id,
                lang or bound_user.get("preferred_lang") or "th",
                filename,
                quote_token,
                _payload(bound_user),
            ),
        )
        return _row(cur.fetchone())


def enqueue_job(
    *,
    bound_user: dict,
    line_user_id: str,
    message_id: str,
    lang: str,
    filename: str = None,
    quote_token: str = None,
) -> Optional[dict]:
    """Insert the webhook message as a durable job. Returns existing row on retry."""
    try:
        return _insert_job(
            bound_user=bound_user,
            line_user_id=line_user_id,
            message_id=message_id,
            lang=lang,
            filename=filename,
            quote_token=quote_token,
        )
    except Exception as e:
        try:
            ensure_table()
            return _insert_job(
                bound_user=bound_user,
                line_user_id=line_user_id,
                message_id=message_id,
                lang=lang,
                filename=filename,
                quote_token=quote_token,
            )
        except Exception as retry_e:
            logger.warning(
                "[line_ocr_jobs] enqueue failed, falling back to memory task: %s; retry=%s",
                e,
                retry_e,
            )
        return None


def claim_job(job_id) -> Optional[dict]:
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE line_ocr_jobs
               SET status = 'running',
                   attempts = attempts + 1,
                   started_at = now(),
                   updated_at = now()
             WHERE id = %s
               AND status IN ('queued', 'retrying', 'failed')
               AND attempts < max_attempts
            RETURNING *
            """,
            (job_id,),
        )
        return _row(cur.fetchone()) or None


def claim_due(limit: int = 3) -> list[dict]:
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE line_ocr_jobs j
               SET status = 'running',
                   attempts = attempts + 1,
                   started_at = now(),
                   updated_at = now()
             WHERE j.id IN (
                   SELECT id
                     FROM line_ocr_jobs
                    WHERE attempts < max_attempts
                      AND (
                          (
                              status IN ('queued', 'retrying')
                              AND (next_retry_at IS NULL OR next_retry_at <= now())
                          )
                          OR (
                              status = 'running'
                              AND started_at < now() - interval '10 minutes'
                          )
                      )
                    ORDER BY COALESCE(next_retry_at, created_at), created_at
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
             )
            RETURNING *
            """,
            (int(limit),),
        )
        return [_row(r) for r in (cur.fetchall() or [])]


def mark_succeeded(job_id) -> None:
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE line_ocr_jobs
               SET status = 'succeeded',
                   finished_at = now(),
                   next_retry_at = NULL,
                   updated_at = now()
             WHERE id = %s
            """,
            (job_id,),
        )


def mark_failed(job_id, *, attempts: int, max_attempts: int, error: str) -> None:
    delay = None
    idx = max(0, int(attempts or 1) - 1)
    if idx < len(_DELAYS):
        delay = _DELAYS[idx]
    retry = delay is not None and int(attempts or 0) < int(max_attempts or 1)
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE line_ocr_jobs
               SET status = %s,
                   attempts = CASE WHEN %s THEN attempts ELSE max_attempts END,
                   last_error = %s,
                   next_retry_at = CASE
                       WHEN %s THEN now() + make_interval(secs => %s)
                       ELSE NULL
                   END,
                   finished_at = CASE WHEN %s THEN finished_at ELSE now() END,
                   updated_at = now()
             WHERE id = %s
            """,
            (
                "retrying" if retry else "failed",
                retry,
                str(error or "")[:2000],
                retry,
                int(delay or 0),
                retry,
                job_id,
            ),
        )


def _bound_user_for(row: dict, provided: Optional[dict]) -> Optional[dict]:
    if provided:
        return provided
    from services.line_binding import store

    return store.get_user_by_line_user_id(row["line_user_id"])


async def _process_claimed(row: dict, bound_user: Optional[dict] = None) -> bool:
    user = _bound_user_for(row, bound_user)
    if not user:
        mark_failed(
            row["id"],
            attempts=row.get("attempts") or 1,
            max_attempts=row.get("max_attempts") or 1,
            error="line user is no longer bound",
        )
        return False
    from services.ocr.line_image_ocr import process_line_image_serial

    try:
        ok = await process_line_image_serial(
            bound_user=user,
            line_user_id=row["line_user_id"],
            message_id=row["message_id"],
            lang=row.get("lang") or user.get("preferred_lang") or "th",
            filename=row.get("filename"),
            quote_token=row.get("quote_token"),
        )
    except Exception as e:
        mark_failed(
            row["id"],
            attempts=row.get("attempts") or 1,
            max_attempts=row.get("max_attempts") or 1,
            error=str(e),
        )
        return False
    if ok is False:
        mark_failed(
            row["id"],
            attempts=row.get("max_attempts") or row.get("attempts") or 1,
            max_attempts=row.get("max_attempts") or 1,
            error="line OCR returned failed",
        )
        return False
    mark_succeeded(row["id"])
    return True


async def process_job(job_id, *, bound_user: Optional[dict] = None) -> bool:
    row = claim_job(job_id)
    if not row:
        return False
    return await _process_claimed(row, bound_user)


async def process_due(limit: int = 3) -> dict:
    rows = claim_due(limit=limit)
    done = 0
    failed = 0
    for row in rows:
        if await _process_claimed(row):
            done += 1
        else:
            failed += 1
    return {"claimed": len(rows), "succeeded": done, "failed": failed}
