# -*- coding: utf-8 -*-
"""
模板映射库(ADR-006 · S2)· 记住"某格式的列怎么对应",下次自动套。

按 (tenant_id, document_type, header_signature) 唯一。mapping_json 是与 bank_recon_v2
兼容的 col_map。新业务 DB 函数按铁律 #21/#23 放 services/ · 不进 db.py · 复用 db.get_cursor()。
建表走 Alembic 004;另带 ensure_table() 启动/首用自愈(对齐 recon_jobs 做法 · Zihao 拍板自动建)。
"""

from __future__ import annotations

import json as _json
import logging
from typing import Any, Dict, List, Optional

from core.db import get_cursor, get_cursor_rls

logger = logging.getLogger("importer.template_store")

VALID_DOC_TYPES = ("statement", "gl")

_DDL_TABLE = """
CREATE TABLE IF NOT EXISTS import_template_mappings (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL,
    document_type    TEXT NOT NULL,
    header_signature TEXT NOT NULL,
    template_name    TEXT,
    sheet_hint       TEXT,
    mapping_json     JSONB NOT NULL,
    sample_headers   JSONB,
    source           TEXT,
    created_by       UUID,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, document_type, header_signature)
)
"""
_DDL_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_import_tmpl_tenant_type "
    "ON import_template_mappings (tenant_id, document_type)"
)


def ensure_table() -> bool:
    """幂等建表(DDL 与 Alembic 004 一致)· 失败不致命。"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"ensure_table pgcrypto skip ({e})")
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(_DDL_TABLE)
            cur.execute(_DDL_INDEX)
            # B8 RLS wave4:tenant_id NOT NULL(无 user_id 列)→ 纯 tenant 隔离。
            # force=False:owner DDL/超管级联删(owner_users bypass)不破;业务连接 SET ROLE 后强制。
            from core.rls import apply_tenant_rls

            apply_tenant_rls(cur, "import_template_mappings")
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"ensure_table failed [{type(e).__name__}]: {e}")
        return False


def find_mapping(
    tenant_id: str, document_type: str, header_signature: str
) -> Optional[Dict[str, int]]:
    """命中返回 col_map(dict),否则 None。表不存在等异常 → None(交回上层走推断)。"""
    if not tenant_id or document_type not in VALID_DOC_TYPES or not header_signature:
        return None

    def _q():
        with get_cursor_rls(tenant_id=str(tenant_id)) as cur:
            cur.execute(
                """
                SELECT mapping_json FROM import_template_mappings
                WHERE tenant_id = %s::uuid AND document_type = %s AND header_signature = %s
                """,
                (str(tenant_id), document_type, header_signature),
            )
            row = cur.fetchone()
            return row["mapping_json"] if row else None

    try:
        return _q()
    except Exception as e:  # noqa: BLE001
        msg = str(e).lower()
        if "import_template_mappings" in msg and (
            "does not exist" in msg or "undefined" in msg or "relation" in msg
        ):
            ensure_table()
            try:
                return _q()
            except Exception:  # noqa: BLE001
                return None
        logger.error(f"find_mapping failed: {e}")
        return None


def save_mapping(
    tenant_id: str,
    document_type: str,
    header_signature: str,
    mapping: Dict[str, int],
    *,
    source: str = "user",
    template_name: str = "",
    sheet_hint: str = "",
    sample_headers: Optional[List[str]] = None,
    created_by: Optional[str] = None,
) -> bool:
    """upsert 映射(同 signature 覆盖)。"""
    if not tenant_id or document_type not in VALID_DOC_TYPES or not header_signature:
        return False
    if not isinstance(mapping, dict) or not mapping:
        return False

    def _upsert():
        with get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            cur.execute(
                """
                INSERT INTO import_template_mappings
                    (tenant_id, document_type, header_signature, template_name, sheet_hint,
                     mapping_json, sample_headers, source, created_by)
                VALUES (%s::uuid, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
                ON CONFLICT (tenant_id, document_type, header_signature)
                DO UPDATE SET mapping_json = EXCLUDED.mapping_json,
                              template_name = EXCLUDED.template_name,
                              sheet_hint = EXCLUDED.sheet_hint,
                              sample_headers = EXCLUDED.sample_headers,
                              source = EXCLUDED.source,
                              updated_at = now()
                """,
                (
                    str(tenant_id),
                    document_type,
                    header_signature,
                    template_name or None,
                    sheet_hint or None,
                    _json.dumps(mapping, ensure_ascii=False, default=str),
                    _json.dumps(sample_headers or [], ensure_ascii=False, default=str),
                    source,
                    str(created_by) if created_by else None,
                ),
            )
            return True

    try:
        return _upsert()
    except Exception as e:  # noqa: BLE001
        msg = str(e).lower()
        if "import_template_mappings" in msg and (
            "does not exist" in msg or "undefined" in msg or "relation" in msg
        ):
            if ensure_table():
                try:
                    return _upsert()
                except Exception as e2:  # noqa: BLE001
                    logger.error(f"save_mapping retry failed: {e2}")
                    return False
        logger.error(f"save_mapping failed: {e}")
        return False


def list_mappings(tenant_id: str, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        with get_cursor_rls(tenant_id=str(tenant_id)) as cur:
            if document_type:
                cur.execute(
                    """
                    SELECT id, document_type, header_signature, template_name, sheet_hint,
                           mapping_json, source, created_at
                    FROM import_template_mappings
                    WHERE tenant_id = %s::uuid AND document_type = %s
                    ORDER BY updated_at DESC
                    """,
                    (str(tenant_id), document_type),
                )
            else:
                cur.execute(
                    """
                    SELECT id, document_type, header_signature, template_name, sheet_hint,
                           mapping_json, source, created_at
                    FROM import_template_mappings
                    WHERE tenant_id = %s::uuid
                    ORDER BY updated_at DESC
                    """,
                    (str(tenant_id),),
                )
            out = []
            for r in cur.fetchall() or []:
                d = dict(r)
                for k in ("id",):
                    if d.get(k) is not None:
                        d[k] = str(d[k])
                if d.get("created_at") is not None and hasattr(d["created_at"], "isoformat"):
                    d["created_at"] = d["created_at"].isoformat()
                out.append(d)
            return out
    except Exception as e:  # noqa: BLE001
        logger.error(f"list_mappings failed: {e}")
        return []


def delete_mapping(tenant_id: str, mapping_id: str) -> bool:
    try:
        with get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            cur.execute(
                "DELETE FROM import_template_mappings WHERE id = %s::uuid AND tenant_id = %s::uuid",
                (str(mapping_id), str(tenant_id)),
            )
            return cur.rowcount > 0
    except Exception as e:  # noqa: BLE001
        logger.error(f"delete_mapping failed: {e}")
        return False
