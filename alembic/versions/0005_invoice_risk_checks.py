"""P5 OCR risk-check confluence: the invoice_risk_checks table.

Revision ID: 0005_invoice_risk_checks
Revises: 0004_knowledge_answers
Create Date: 2026-06-04

One row per risk check of one OCR history. history_id is UUID to match
ocr_history.id in the main project (docs/Pearnly_KB_主项目契约事实). findings is
the engine's output (a jsonb list of rule_id/severity/evidence). status is the
check run's own state; human_status tracks the accountant's later disposition.
"""

from alembic import op

revision = "0005_invoice_risk_checks"
down_revision = "0004_knowledge_answers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS invoice_risk_checks (
            id                  bigserial PRIMARY KEY,
            tenant_id           uuid NOT NULL,
            workspace_client_id bigint,
            history_id          uuid NOT NULL,
            risk_level          text NOT NULL CHECK (risk_level IN ('high', 'medium', 'low')),
            needs_human_review  boolean NOT NULL DEFAULT false,
            findings            jsonb NOT NULL DEFAULT '[]'::jsonb,
            status              text NOT NULL CHECK (status IN (
                                    'pending', 'success', 'failed', 'skipped'
                                )),
            human_status        text NOT NULL DEFAULT 'unreviewed',
            error_code          text,
            created_by          uuid,
            checked_at          timestamptz NOT NULL DEFAULT now(),
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_invoice_risk_checks_history
            ON invoice_risk_checks (tenant_id, history_id, id)
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS invoice_risk_checks")
