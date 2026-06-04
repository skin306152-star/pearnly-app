"""P1 knowledge document tables: bases, documents, ingest_jobs.

Revision ID: 0001_knowledge_p1
Revises:
Create Date: 2026-06-04

Type calibration follows docs/Pearnly_KB_主项目契约事实_2026-06-03.md:
primary keys are BIGSERIAL, tenant_id is UUID, workspace_client_id is BIGINT
(aligned with workspace_clients.id), and internal foreign keys reference those
BIGSERIAL ids as BIGINT. Embedding/chunk tables are P2 and not created here.

Table/index names are written literally rather than imported from schema.py:
a migration is a fixed historical snapshot and must not shift if a constant is
later renamed.
"""

from alembic import op

revision = "0001_knowledge_p1"
down_revision = "007_erp_adapter_mrerp_dms"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_bases (
            id                  bigserial PRIMARY KEY,
            tenant_id           uuid NOT NULL,
            workspace_client_id bigint,
            scope               text NOT NULL
                                CHECK (scope IN ('firm', 'workspace_client')),
            name                text NOT NULL,
            status              text NOT NULL DEFAULT 'active',
            created_by          uuid,
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id                  bigserial PRIMARY KEY,
            tenant_id           uuid NOT NULL,
            workspace_client_id bigint,
            knowledge_base_id   bigint NOT NULL
                                REFERENCES knowledge_bases (id),
            source_type         text NOT NULL,
            filename            text NOT NULL,
            mime_type           text,
            storage_path        text,
            checksum            text NOT NULL,
            status              text NOT NULL
                                CHECK (status IN (
                                    'uploaded', 'extracting', 'chunking',
                                    'embedding', 'ready', 'failed', 'deleted'
                                )),
            uploaded_by         uuid,
            error_code          text,
            created_at          timestamptz NOT NULL DEFAULT now(),
            updated_at          timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_ingest_jobs (
            id                  bigserial PRIMARY KEY,
            tenant_id           uuid NOT NULL,
            workspace_client_id bigint,
            document_id         bigint NOT NULL
                                REFERENCES knowledge_documents (id),
            status              text NOT NULL
                                CHECK (status IN (
                                    'queued', 'running', 'success',
                                    'failed', 'retrying'
                                )),
            progress            int NOT NULL DEFAULT 0,
            error_code          text,
            retry_count         int NOT NULL DEFAULT 0,
            max_retries         int NOT NULL DEFAULT 3,
            created_at          timestamptz NOT NULL DEFAULT now(),
            finished_at         timestamptz
        )
        """)
    # Tenant + workspace lead every isolation filter, so they lead the indexes.
    # The default-base lookup runs on every upload; index its exact match keys.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_bases_tenant_scope_name
            ON knowledge_bases (tenant_id, scope, name, workspace_client_id)
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_documents_tenant_base
            ON knowledge_documents (tenant_id, knowledge_base_id, status)
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_ingest_jobs_document
            ON knowledge_ingest_jobs (document_id)
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_ingest_jobs_tenant_status
            ON knowledge_ingest_jobs (tenant_id, status)
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_ingest_jobs")
    op.execute("DROP TABLE IF EXISTS knowledge_documents")
    op.execute("DROP TABLE IF EXISTS knowledge_bases")
