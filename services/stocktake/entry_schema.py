"""Additive schema for scan-first counts; legacy snapshots remain unchanged."""

DDL = """
ALTER TABLE cowork_stocktakes ADD COLUMN IF NOT EXISTS count_mode TEXT NOT NULL
    DEFAULT 'legacy' CHECK (count_mode IN ('legacy', 'scan'));
CREATE UNIQUE INDEX IF NOT EXISTS cowork_stocktake_item_scope
    ON cowork_stocktake_items (id, stocktake_id, tenant_id, workspace_client_id);
CREATE TABLE IF NOT EXISTS cowork_stocktake_entries (
    id UUID PRIMARY KEY,
    stocktake_id UUID NOT NULL,
    item_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    workspace_client_id BIGINT NOT NULL,
    warehouse TEXT NOT NULL CHECK (length(trim(warehouse)) > 0),
    location TEXT NOT NULL DEFAULT '',
    quantity NUMERIC(20,6) NOT NULL CHECK (quantity >= 0),
    version INTEGER NOT NULL DEFAULT 0,
    voided BOOLEAN NOT NULL DEFAULT FALSE,
    counted_by UUID NOT NULL REFERENCES users(id),
    counted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (item_id, stocktake_id, tenant_id, workspace_client_id)
        REFERENCES cowork_stocktake_items(id, stocktake_id, tenant_id, workspace_client_id),
    UNIQUE (id, tenant_id, workspace_client_id)
);
CREATE INDEX IF NOT EXISTS cowork_stocktake_entries_task
    ON cowork_stocktake_entries (stocktake_id, counted_at DESC);
CREATE TABLE IF NOT EXISTS cowork_stocktake_entry_events (
    operation_id UUID PRIMARY KEY,
    entry_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    workspace_client_id BIGINT NOT NULL,
    version INTEGER NOT NULL,
    request JSONB NOT NULL,
    previous JSONB,
    current JSONB NOT NULL,
    actor_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (entry_id, tenant_id, workspace_client_id)
        REFERENCES cowork_stocktake_entries(id, tenant_id, workspace_client_id),
    UNIQUE (entry_id, version)
);
"""


def apply(cur):
    from core.rls import apply_tenant_workspace_rls

    cur.execute(DDL)
    apply_tenant_workspace_rls(cur, "cowork_stocktake_entries", "cowork_stocktake_entry_events")
