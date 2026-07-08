# -*- coding: utf-8 -*-
"""外流(Google 归档)schema 双跑入口(启动幂等建表 · 契约 05 §2.2)。

3 表(全按套账隔离 + RLS):
  export_google_credentials  Google OAuth 凭据(按 tenant+workspace_client·绝不跨套账串)
  export_oauth_states        OAuth 防 CSRF state(5 分钟过期)
  export_archived_docs       归档幂等台账(已成功归档的单据 → 重跑只补未成功)

凭据 token base64 存(token_version=1·P1 升 AES,与 erp_oauth_tokens 同档)。隔离真正生效
靠应用层 WHERE tenant_id + workspace_client_id;RLS 是最小权限角色兜底(prod 现 BYPASSRLS)。
失败仅告警不 raise(不挡主服务)。
"""

from __future__ import annotations

import logging

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS export_google_credentials (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        google_email text,
        access_token text NOT NULL,
        refresh_token text NOT NULL,
        expires_at timestamptz,
        scope text,
        token_version int NOT NULL DEFAULT 1,
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (tenant_id, workspace_client_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS export_oauth_states (
        state text PRIMARY KEY,
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        user_id uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS export_archived_docs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        doc_id uuid NOT NULL,
        drive_folder_id text,
        drive_url text,
        sheet_synced boolean NOT NULL DEFAULT FALSE,
        archived_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (tenant_id, workspace_client_id, doc_id)
    )
    """,
)

_ALTERS = (
    # return_to:回调最终跳转目标(哪个页面发起的连接 → 授权完回哪),复用同一份凭据服务多个
    # 集成入口(采购导出/POS)。默认值保原有行为(旧 state 行/没传参数一律回采购导出页)。
    "ALTER TABLE export_oauth_states "
    "ADD COLUMN IF NOT EXISTS return_to text NOT NULL DEFAULT 'purchase-export'",
)

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_export_creds_ws "
    "ON export_google_credentials (tenant_id, workspace_client_id)",
    "CREATE INDEX IF NOT EXISTS ix_export_states_created ON export_oauth_states (created_at)",
    "CREATE INDEX IF NOT EXISTS ix_export_archived_ws "
    "ON export_archived_docs (tenant_id, workspace_client_id)",
)

_RLS_TABLES = ("export_google_credentials", "export_oauth_states", "export_archived_docs")


def ensure_export_schema() -> None:  # NEW-DEBT-EXEMPT
    """幂等建外流 3 表 + 索引 + RLS(startup 调)。"""
    from core import db

    try:
        with db.get_cursor(commit=True) as cur:
            for ddl in _TABLES:
                cur.execute(ddl)
            for alter in _ALTERS:
                cur.execute(alter)
            for idx in _INDEXES:
                cur.execute(idx)
            apply_tenant_rls(cur, *_RLS_TABLES)
    except Exception as e:  # noqa: BLE001
        logger.warning("ensure_export_schema failed: %s", e)
