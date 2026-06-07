"""tenant_modules — per-tenant module switches (POS 项目 · PO-A1 · docs/pos/03 §5).

Revision ID: 0021_tenant_modules
Revises: 0020_sales_doc_paper_lang
Create Date: 2026-06-07

A vision table that did not exist before: navigation / routes / capability blocks are
currently hardcoded all-on. tenant_modules lets each租户 turn modules on/off
('inventory' | 'pos' | 'sales' | ...) and stash business-type presets + capability flags
in config jsonb. Modules with no explicit row fall back to code defaults (see
services/modules/store.py) — existing tenants keep today's behavior, POS/inventory stay
hidden until onboarding.

Isolation: the actual, enforced guarantee is app-layer — every store.py statement carries
WHERE tenant_id (and db.get_cursor_rls sets app.current_tenant_id). The ENABLE RLS + policy
below is defense-in-depth for any future least-privilege role; it does NOT enforce on the
current connection because prod connects as `postgres` (rolbypassrls=true), verified
2026-06-07. Same effective model as the sales tables (0020 note). Mirrors the clients policy.

Dual-run: services/modules/store.ensure_table() runs the identical idempotent DDL on
startup (prod has no auto-migrate). Backward compatible — table is new, nothing else reads it.
"""

from alembic import op

revision = "0021_tenant_modules"
down_revision = "0020_sales_doc_paper_lang"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_modules (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            module_key text NOT NULL,
            enabled boolean NOT NULL DEFAULT FALSE,
            config jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, module_key)
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tenant_modules_tenant " "ON tenant_modules (tenant_id)"
    )
    op.execute("ALTER TABLE tenant_modules ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON tenant_modules")
    op.execute("""
        CREATE POLICY tenant_isolation ON tenant_modules
        FOR ALL
        USING (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.bypass_rls', true) = 'on'
        )
        WITH CHECK (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.bypass_rls', true) = 'on'
        )
        """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON tenant_modules")
    op.execute("DROP TABLE IF EXISTS tenant_modules")
