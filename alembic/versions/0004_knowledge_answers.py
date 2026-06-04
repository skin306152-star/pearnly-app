"""P4 cited Q&A: the knowledge_answers record table.

Revision ID: 0004_knowledge_answers
Revises: 0003_client_rules
Create Date: 2026-06-04

One row per answered (or refused) question, keeping the cited chunks so an
answer can be reviewed against its sources later. no_answer marks a refusal
(no relevant chunks): the product never answers without a source.
"""

from alembic import op

revision = "0004_knowledge_answers"
down_revision = "0003_client_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_answers (
            id                  bigserial PRIMARY KEY,
            tenant_id           uuid NOT NULL,
            workspace_client_id bigint,
            question            text NOT NULL,
            answer              text NOT NULL,
            citations           jsonb NOT NULL DEFAULT '[]'::jsonb,
            model               text,
            no_answer           boolean NOT NULL DEFAULT false,
            created_by          uuid,
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_answers_tenant
            ON knowledge_answers (tenant_id, workspace_client_id, id)
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_answers")
