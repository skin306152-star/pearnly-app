"""Stocktake schema applied by the serialized Cloud Run schema gate."""

DDL = """
CREATE TABLE IF NOT EXISTS cowork_stocktakes (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    workspace_client_id BIGINT NOT NULL REFERENCES workspace_clients(id),
    name TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed')),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    closed_by UUID REFERENCES users(id),
    UNIQUE (id, tenant_id, workspace_client_id)
);
CREATE TABLE IF NOT EXISTS cowork_stocktake_items (
    id UUID PRIMARY KEY,
    stocktake_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    workspace_client_id BIGINT NOT NULL,
    product_code TEXT NOT NULL,
    product_name TEXT NOT NULL,
    barcode TEXT NOT NULL DEFAULT '',
    warehouse TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    unit TEXT NOT NULL,
    book_qty NUMERIC(20,6) NOT NULL,
    actual_qty NUMERIC(20,6) CHECK (actual_qty >= 0),
    version INTEGER NOT NULL DEFAULT 0,
    counted_by UUID REFERENCES users(id),
    counted_at TIMESTAMPTZ,
    FOREIGN KEY (stocktake_id, tenant_id, workspace_client_id)
        REFERENCES cowork_stocktakes(id, tenant_id, workspace_client_id),
    UNIQUE (stocktake_id, product_code, warehouse, location)
);
CREATE INDEX IF NOT EXISTS cowork_stocktakes_scope
    ON cowork_stocktakes (tenant_id, workspace_client_id, created_at DESC);
CREATE INDEX IF NOT EXISTS cowork_stocktake_barcode
    ON cowork_stocktake_items (stocktake_id, barcode);
CREATE TABLE IF NOT EXISTS cowork_stocktake_counts (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    workspace_client_id BIGINT NOT NULL,
    item_id UUID NOT NULL REFERENCES cowork_stocktake_items(id),
    previous_qty NUMERIC(20,6),
    actual_qty NUMERIC(20,6) NOT NULL,
    version INTEGER NOT NULL,
    counted_by UUID NOT NULL REFERENCES users(id),
    counted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(item_id, version)
);
"""


def migrate():
    from core import db
    from core.rls import apply_tenant_workspace_rls
    from services.stocktake.entry_schema import apply
    from services.stocktake.photo_schema import apply as apply_photos

    with db.get_cursor(commit=True) as cur:
        cur.execute(DDL)
        apply_tenant_workspace_rls(
            cur, "cowork_stocktakes", "cowork_stocktake_items", "cowork_stocktake_counts"
        )
        apply(cur)
        apply_photos(cur)
