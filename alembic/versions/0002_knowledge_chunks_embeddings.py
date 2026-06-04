"""P2 retrieval tables: knowledge_chunks and knowledge_embeddings.

Revision ID: 0002_knowledge_p2
Revises: 0001_knowledge_p1
Create Date: 2026-06-04

The embedding dimension is fixed at 768: the P0.5 Thai spike selected
gemini-embedding-001 @768 (eval/thai_spike_result.md). A chunk's embedding is
kept in a separate table from its text so re-embedding with a different model is
an insert, not a destructive column change. Cosine distance (<=>) is the search
operator, so the ANN index uses vector_cosine_ops.
"""

from alembic import op

revision = "0002_knowledge_p2"
down_revision = "0001_knowledge_p1"
branch_labels = None
depends_on = None

EMBEDDING_DIM = 768


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id                  bigserial PRIMARY KEY,
            tenant_id           uuid NOT NULL,
            workspace_client_id bigint,
            document_id         bigint NOT NULL
                                REFERENCES knowledge_documents (id),
            chunk_index         int NOT NULL,
            text                text NOT NULL,
            char_count          int NOT NULL,
            metadata            jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS knowledge_embeddings (
            id                  bigserial PRIMARY KEY,
            tenant_id           uuid NOT NULL,
            workspace_client_id bigint,
            chunk_id            bigint NOT NULL
                                REFERENCES knowledge_chunks (id),
            embedding           vector({EMBEDDING_DIM}) NOT NULL,
            model               text NOT NULL,
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_tenant_document
            ON knowledge_chunks (tenant_id, document_id, chunk_index)
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_tenant
            ON knowledge_embeddings (tenant_id, workspace_client_id)
        """)
    # Approximate-nearest-neighbour index for cosine top-k search.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_vec
            ON knowledge_embeddings USING hnsw (embedding vector_cosine_ops)
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_embeddings")
    op.execute("DROP TABLE IF EXISTS knowledge_chunks")
