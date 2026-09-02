# -*- coding: utf-8 -*-
"""Schema shared by Alembic and production startup for ERP target projections."""

from __future__ import annotations

from core.rls import apply_tenant_rls

TABLES = (
    "erp_target_projection_snapshots",
    "erp_target_projection_heads",
    "erp_target_projection_items",
    "erp_target_refresh_requests",
)

DDL = (
    """
    CREATE TABLE IF NOT EXISTS erp_target_projection_snapshots (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        endpoint_id uuid NOT NULL REFERENCES erp_endpoints(id) ON DELETE CASCADE,
        scope_kind text NOT NULL CHECK (scope_kind IN ('endpoint', 'account_set')),
        scope_key text NOT NULL,
        revision bigint NOT NULL CHECK (revision > 0),
        account_sets_revision bigint NOT NULL CHECK (account_sets_revision > 0),
        master_revision bigint NOT NULL CHECK (master_revision > 0),
        form_schema_revision bigint NOT NULL CHECK (form_schema_revision > 0),
        capability_revision bigint NOT NULL CHECK (capability_revision > 0),
        source_hash text NOT NULL CHECK (source_hash ~ '^[0-9a-f]{64}$'),
        component_hashes jsonb NOT NULL,
        source_status text NOT NULL DEFAULT 'fresh' CHECK (source_status = 'fresh'),
        observed_at timestamptz NOT NULL,
        adapter text NOT NULL CHECK (adapter IN ('mrerp', 'express')),
        collector jsonb NOT NULL DEFAULT '{}'::jsonb,
        account_sets jsonb NOT NULL DEFAULT '[]'::jsonb,
        form_schema jsonb NOT NULL DEFAULT '{"fields":[]}'::jsonb,
        capabilities jsonb NOT NULL DEFAULT '{"actions":[]}'::jsonb,
        entity_counts jsonb NOT NULL DEFAULT '{}'::jsonb,
        created_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (tenant_id, endpoint_id, scope_kind, scope_key, revision),
        CHECK ((scope_kind = 'endpoint' AND scope_key = '@endpoint') OR
               (scope_kind = 'account_set' AND scope_key <> '' AND scope_key <> '@endpoint'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS erp_target_projection_heads (
        tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        endpoint_id uuid NOT NULL REFERENCES erp_endpoints(id) ON DELETE CASCADE,
        scope_kind text NOT NULL CHECK (scope_kind IN ('endpoint', 'account_set')),
        scope_key text NOT NULL,
        current_snapshot_id uuid,
        current_revision bigint NOT NULL DEFAULT 0 CHECK (current_revision >= 0),
        account_sets_revision bigint NOT NULL DEFAULT 0 CHECK (account_sets_revision >= 0),
        master_revision bigint NOT NULL DEFAULT 0 CHECK (master_revision >= 0),
        form_schema_revision bigint NOT NULL DEFAULT 0 CHECK (form_schema_revision >= 0),
        capability_revision bigint NOT NULL DEFAULT 0 CHECK (capability_revision >= 0),
        last_refresh_status text NOT NULL CHECK (
            last_refresh_status IN ('fresh', 'refreshing', 'stale', 'offline', 'error', 'unsupported')
        ),
        last_refresh_error_code text,
        last_refresh_source jsonb NOT NULL DEFAULT '{}'::jsonb,
        last_refresh_attempted_at timestamptz NOT NULL,
        last_observed_at timestamptz,
        updated_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, endpoint_id, scope_kind, scope_key),
        UNIQUE (current_snapshot_id),
        FOREIGN KEY (current_snapshot_id)
            REFERENCES erp_target_projection_snapshots(id) DEFERRABLE INITIALLY DEFERRED,
        CHECK ((current_revision = 0) = (current_snapshot_id IS NULL)),
        CHECK ((scope_kind = 'endpoint' AND scope_key = '@endpoint') OR
               (scope_kind = 'account_set' AND scope_key <> '' AND scope_key <> '@endpoint'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS erp_target_projection_items (
        snapshot_id uuid NOT NULL REFERENCES erp_target_projection_snapshots(id) ON DELETE CASCADE,
        tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        endpoint_id uuid NOT NULL REFERENCES erp_endpoints(id) ON DELETE CASCADE,
        entity_type text NOT NULL CHECK (
            entity_type IN ('products', 'customers', 'suppliers', 'units', 'branches', 'accounts')
        ),
        source_id text NOT NULL,
        label text NOT NULL,
        active boolean NOT NULL DEFAULT TRUE,
        attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
        PRIMARY KEY (snapshot_id, entity_type, source_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS erp_target_refresh_requests (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        endpoint_id uuid NOT NULL REFERENCES erp_endpoints(id) ON DELETE CASCADE,
        account_set_key text NOT NULL,
        adapter text NOT NULL CHECK (adapter IN ('mrerp', 'express')),
        status text NOT NULL DEFAULT 'requested' CHECK (
            status IN ('requested', 'leased', 'succeeded', 'failed')
        ),
        requested_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
        reason text NOT NULL,
        requested_at timestamptz NOT NULL DEFAULT now(),
        started_at timestamptz,
        completed_at timestamptz,
        lease_owner text,
        lease_expires_at timestamptz,
        error_code text,
        result_revision bigint,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        CHECK (account_set_key <> '')
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_erp_target_projection_snapshot_lookup "
    "ON erp_target_projection_snapshots (tenant_id, endpoint_id, scope_kind, scope_key, revision DESC)",
    "CREATE INDEX IF NOT EXISTS ix_erp_target_projection_items_lookup "
    "ON erp_target_projection_items (tenant_id, endpoint_id, entity_type, source_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_erp_target_refresh_active "
    "ON erp_target_refresh_requests (tenant_id, endpoint_id, account_set_key) "
    "WHERE status IN ('requested', 'leased')",
    "CREATE INDEX IF NOT EXISTS ix_erp_target_refresh_due "
    "ON erp_target_refresh_requests (adapter, status, requested_at)",
)


def apply_target_projection_schema(cur) -> None:
    for statement in DDL:
        cur.execute(statement)
    apply_tenant_rls(cur, *TABLES)


def ensure_target_projection_schema() -> None:
    from core import db

    with db.get_cursor(commit=True) as cur:
        apply_target_projection_schema(cur)


__all__ = ["DDL", "TABLES", "apply_target_projection_schema", "ensure_target_projection_schema"]
