# -*- coding: utf-8 -*-
"""修正例库读写 + 编辑捕获入口。

写入走 get_cursor_rls(tenant/user 上下文),满足例库表的 tenant_or_user RLS。捕获全程非致命:
任何异常只告警,绝不影响用户保存。"""

import logging
from typing import Optional

from core import db
from services.ocr.feedback import diff

logger = logging.getLogger(__name__)


def record_corrections(
    user_id: str,
    tenant_id: Optional[str],
    seller_tax: Optional[str],
    seller_name: Optional[str],
    source_history_id: Optional[str],
    corrections: list,
) -> int:
    """逐条 upsert 修正例(同主体+字段+AI 原值重复出现 → use_count+1)。返回写入条数。"""
    if not corrections:
        return 0
    written = 0
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
        for c in corrections:
            cur.execute(
                """
                UPDATE ocr_correction_examples
                SET use_count = use_count + 1,
                    corrected_value = %s,
                    seller_name = COALESCE(%s, seller_name),
                    source_history_id = %s,
                    updated_at = NOW()
                WHERE COALESCE(tenant_id::text, user_id::text)
                          = COALESCE(%s::text, %s::text)
                  AND COALESCE(seller_tax, '') = COALESCE(%s, '')
                  AND field_name = %s
                  AND COALESCE(ai_value, '') = COALESCE(%s, '')
                """,
                (
                    c["corrected_value"],
                    seller_name,
                    source_history_id,
                    tenant_id,
                    user_id,
                    seller_tax,
                    c["field_name"],
                    c.get("ai_value"),
                ),
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO ocr_correction_examples (
                        tenant_id, user_id, seller_tax, seller_name,
                        field_name, ai_value, corrected_value, source_history_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        tenant_id,
                        user_id,
                        seller_tax,
                        seller_name,
                        c["field_name"],
                        c.get("ai_value"),
                        c["corrected_value"],
                        source_history_id,
                    ),
                )
            written += 1
    return written


def fetch_examples(
    user_id: str,
    tenant_id: Optional[str],
    seller_tax: Optional[str],
    limit: int = 20,
) -> list:
    """取该主体最常见的修正例(use_count 降序)。给消费侧拼 few-shot。"""
    if not seller_tax:
        return []
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
        cur.execute(
            """
            SELECT field_name, ai_value, corrected_value, use_count
            FROM ocr_correction_examples
            WHERE seller_tax = %s
            ORDER BY use_count DESC, updated_at DESC
            LIMIT %s
            """,
            (seller_tax, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def _read_ai_raw(user_id: str, tenant_id: Optional[str], record_id: str):
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
        cur.execute("SELECT ai_raw FROM ocr_history WHERE id = %s::uuid", (record_id,))
        row = cur.fetchone()
        return row["ai_raw"] if row else None


def record_correction_from_edit(
    user_id: str,
    tenant_id: Optional[str],
    record_id: str,
    corrected_pages: list,
) -> int:
    """编辑保存后调:读 AI 基线 → diff → 沉淀修正例。无基线/无修正 → 0。非致命。"""
    try:
        ai_raw = _read_ai_raw(user_id, tenant_id, record_id)
        if not ai_raw:
            return 0
        corrections = diff.compute_field_corrections(ai_raw, corrected_pages)
        if not corrections:
            return 0
        seller_tax, seller_name = diff.primary_seller(corrected_pages)
        if not seller_tax:
            seller_tax, seller_name = diff.primary_seller(ai_raw)
        return record_corrections(
            user_id, tenant_id, seller_tax, seller_name, record_id, corrections
        )
    except Exception as e:
        logger.warning(f"record_correction_from_edit skip (record={record_id}): {e}")
        return 0
