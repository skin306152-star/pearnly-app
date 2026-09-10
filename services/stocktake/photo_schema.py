"""Bounded, durable count evidence with the same tenant/workspace isolation."""

DDL = """
CREATE TABLE IF NOT EXISTS cowork_stocktake_photos (
    entry_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    workspace_client_id BIGINT NOT NULL,
    slot SMALLINT NOT NULL CHECK (slot BETWEEN 1 AND 5),
    content BYTEA NOT NULL CHECK (octet_length(content) BETWEEN 1 AND 1048576),
    digest TEXT NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (entry_id, slot),
    FOREIGN KEY (entry_id, tenant_id, workspace_client_id)
        REFERENCES cowork_stocktake_entries(id, tenant_id, workspace_client_id) ON DELETE CASCADE
);
"""


def apply(cur):
    from core.rls import apply_tenant_workspace_rls

    cur.execute(DDL)
    apply_tenant_workspace_rls(cur, "cowork_stocktake_photos")
