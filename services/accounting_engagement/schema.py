"""accounting_engagements 启动期 schema。"""

from __future__ import annotations

import logging

from core.rls import apply_participant_tenant_rls

logger = logging.getLogger(__name__)

_TABLE = """
    CREATE TABLE IF NOT EXISTS accounting_engagements (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        firm_tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
        firm_workspace_client_id bigint REFERENCES workspace_clients(id) ON DELETE RESTRICT,
        merchant_tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
        merchant_workspace_client_id bigint REFERENCES workspace_clients(id) ON DELETE RESTRICT,
        status text NOT NULL DEFAULT 'pending_merchant'
            CHECK (status IN ('pending_merchant', 'pending_firm', 'active', 'suspended', 'ended')),
        is_primary boolean NOT NULL DEFAULT true,
        merchant_accepted_at timestamptz,
        firm_accepted_at timestamptz,
        active_from timestamptz,
        ended_at timestamptz,
        created_by_admin_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT ck_accounting_engagement_distinct_tenants
            CHECK (firm_tenant_id <> merchant_tenant_id),
        CONSTRAINT ck_accounting_engagement_active_ready CHECK (
            status <> 'active' OR (
                firm_workspace_client_id IS NOT NULL
                AND merchant_workspace_client_id IS NOT NULL
                AND merchant_accepted_at IS NOT NULL
                AND firm_accepted_at IS NOT NULL
                AND active_from IS NOT NULL
            )
        ),
        CONSTRAINT ck_accounting_engagement_ended_at CHECK (
            status <> 'ended' OR ended_at IS NOT NULL
        )
    )
    """

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_engagement_firm_status "
    "ON accounting_engagements (firm_tenant_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_engagement_merchant_status "
    "ON accounting_engagements (merchant_tenant_id, status)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_engagement_primary_merchant_open "
    "ON accounting_engagements (merchant_tenant_id) "
    "WHERE is_primary AND status <> 'ended'",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_engagement_firm_workspace_open "
    "ON accounting_engagements (firm_tenant_id, firm_workspace_client_id) "
    "WHERE firm_workspace_client_id IS NOT NULL AND status <> 'ended'",
)


def ensure_accounting_engagement_schema() -> None:
    """幂等建关系表、唯一约束与参与方 RLS。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        for ddl in _INDEXES:
            cur.execute(ddl)
        apply_participant_tenant_rls(
            cur,
            "accounting_engagements",
            left_column="firm_tenant_id",
            right_column="merchant_tenant_id",
        )
    logger.info("accounting_engagements schema ready")
