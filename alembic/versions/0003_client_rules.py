"""P3 dead-rules engine: the client_rules table.

Revision ID: 0003_client_rules
Revises: 0002_knowledge_p2
Create Date: 2026-06-04

One row = one customer-tunable rule (docs/Pearnly_KB_P3_client_rules_表设计):
workspace_client_id NULL is a firm-wide default, a value scopes it to one
account set, and a client-specific row overrides the firm default for the same
(rule_type, subject). rule_body is per-type JSON validated at the write API.
Global hard checks (tax-id, VAT arithmetic, dedup, mandatory fields) are coded
in the engine and need no row here.
"""

from alembic import op

revision = "0003_client_rules"
down_revision = "0002_knowledge_p2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS client_rules (
            id                   bigserial PRIMARY KEY,
            tenant_id            uuid NOT NULL,
            workspace_client_id  bigint,
            rule_type            text NOT NULL CHECK (rule_type IN (
                                     'supplier_allowlist', 'supplier_force_review',
                                     'amount_limit', 'no_auto_push_category',
                                     'wht_rate', 'accounting_period', 'feature_toggle'
                                 )),
            subject_type         text NOT NULL CHECK (subject_type IN (
                                     'supplier', 'category', 'contract', 'global'
                                 )),
            subject_key          text,
            rule_body            jsonb NOT NULL DEFAULT '{}'::jsonb,
            severity             text CHECK (severity IS NULL OR severity IN (
                                     'high', 'medium', 'low'
                                 )),
            is_active            boolean NOT NULL DEFAULT true,
            effective_from       date,
            effective_to         date,
            origin               text NOT NULL DEFAULT 'manual' CHECK (origin IN (
                                     'manual', 'learned', 'imported', 'extracted'
                                 )),
            confidence           numeric,
            source_document_id   bigint,
            source_correction_id bigint,
            created_by           uuid,
            created_at           timestamptz NOT NULL DEFAULT now(),
            updated_by           uuid,
            updated_at           timestamptz NOT NULL DEFAULT now(),
            hit_count            int NOT NULL DEFAULT 0,
            accepted_count       int NOT NULL DEFAULT 0,
            dismissed_count      int NOT NULL DEFAULT 0
        )
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_client_rules_load
            ON client_rules (tenant_id, workspace_client_id, rule_type)
            WHERE is_active
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_client_rules_subject
            ON client_rules (tenant_id, workspace_client_id, subject_type, subject_key)
            WHERE is_active
        """)
    # One active rule per (tenant, workspace, type, subject); COALESCE so NULLs
    # collapse to a single comparable value inside the unique key.
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_client_rules_active
            ON client_rules (
                tenant_id, COALESCE(workspace_client_id, -1),
                rule_type, subject_type, COALESCE(subject_key, '')
            )
            WHERE is_active
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS client_rules")
