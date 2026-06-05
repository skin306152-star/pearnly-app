"""Chunk + embedding persistence and cosine top-k retrieval.

Kept apart from dal.py (which owns documents/jobs/bases) so each file stays under
the line budget and single-purpose. Search is tenant-scoped and honours the same
workspace-client visibility as the document reads; a member never retrieves a
chunk from an account set they cannot see, and deleted documents never surface.

Vectors are written and queried as pgvector literals with an explicit ::vector
cast, since psycopg2 has no native adapter for the extension type. Similarity is
1 - cosine_distance, so a higher score is a closer match.
"""

from __future__ import annotations

from typing import Optional, Sequence

from psycopg2.extras import execute_values

from services.knowledge import embedding
from services.knowledge.access import AccessibleIds, workspace_filter
from services.knowledge.models import Chunk
from services.knowledge.schema import DOC_DELETED, SearchHit

DEFAULT_TOP_K = 5


def store_chunks(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: Optional[int],
    document_id: int,
    chunks: Sequence[Chunk],
) -> list[int]:
    """Insert chunks, returning their new ids aligned to the input order."""
    if not chunks:
        return []
    rows = [
        (tenant_id, workspace_client_id, document_id, c.ordinal, c.text, c.char_count)
        for c in chunks
    ]
    execute_values(
        cur,
        "INSERT INTO knowledge_chunks "
        "(tenant_id, workspace_client_id, document_id, chunk_index, text, char_count) "
        "VALUES %s RETURNING id, chunk_index",
        rows,
    )
    id_by_index = {r["chunk_index"]: r["id"] for r in cur.fetchall()}
    return [id_by_index[c.ordinal] for c in chunks]


def store_embeddings(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: Optional[int],
    chunk_ids: Sequence[int],
    vectors: Sequence[Sequence[float]],
    model: str,
) -> None:
    rows = [
        (tenant_id, workspace_client_id, chunk_id, embedding.to_pgvector(vector), model)
        for chunk_id, vector in zip(chunk_ids, vectors)
    ]
    execute_values(
        cur,
        "INSERT INTO knowledge_embeddings "
        "(tenant_id, workspace_client_id, chunk_id, embedding, model) VALUES %s",
        rows,
        template="(%s, %s, %s, %s::vector, %s)",
    )


def search_chunks(
    cur,
    *,
    tenant_id: str,
    accessible_ids: AccessibleIds,
    query_vector: Sequence[float],
    limit: int = DEFAULT_TOP_K,
) -> list[SearchHit]:
    where, params = workspace_filter(accessible_ids, alias="e")
    vector_literal = embedding.to_pgvector(query_vector)
    cur.execute(
        "SELECT c.id AS chunk_id, c.document_id, d.filename, c.text, "
        "1 - (e.embedding <=> %s::vector) AS score "
        "FROM knowledge_embeddings e "
        "JOIN knowledge_chunks c ON c.id = e.chunk_id "
        "JOIN knowledge_documents d ON d.id = c.document_id "
        "WHERE e.tenant_id = %s AND d.status <> %s"
        + where
        + " ORDER BY e.embedding <=> %s::vector LIMIT %s",
        [vector_literal, tenant_id, DOC_DELETED, *params, vector_literal, limit],
    )
    return [
        SearchHit(
            chunk_id=r["chunk_id"],
            document_id=r["document_id"],
            filename=r["filename"],
            text=r["text"],
            score=float(r["score"]),
        )
        for r in cur.fetchall()
    ]


def get_chunk_context(
    cur,
    *,
    tenant_id: str,
    accessible_ids: AccessibleIds,
    chunk_id: int,
    radius: int = 1,
) -> Optional[dict]:
    """Fetch one cited chunk plus its neighbours, for the source-preview modal.

    Returns the matched chunk's text and up to `radius` chunks on each side (same
    document, by ordinal) so the UI can show it in context with the hit highlighted.
    Tenant + workspace scoped and deleted-document aware — same visibility as search;
    returns None when the chunk isn't visible to the caller.
    """
    where, params = workspace_filter(accessible_ids, alias="c")
    cur.execute(
        "SELECT c.id, c.document_id, c.chunk_index, c.text, d.filename "
        "FROM knowledge_chunks c JOIN knowledge_documents d ON d.id = c.document_id "
        "WHERE c.id = %s AND c.tenant_id = %s AND d.status <> %s" + where,
        [chunk_id, tenant_id, DOC_DELETED, *params],
    )
    target = cur.fetchone()
    if not target:
        return None
    # Neighbours share the document (already visibility-checked above) — scope by
    # tenant + document + ordinal window.
    cur.execute(
        "SELECT chunk_index, text FROM knowledge_chunks "
        "WHERE tenant_id = %s AND document_id = %s AND chunk_index BETWEEN %s AND %s "
        "ORDER BY chunk_index",
        [
            tenant_id,
            target["document_id"],
            target["chunk_index"] - radius,
            target["chunk_index"] + radius,
        ],
    )
    hit_index = target["chunk_index"]
    segments = [
        {
            "chunk_index": r["chunk_index"],
            "text": r["text"],
            "matched": r["chunk_index"] == hit_index,
        }
        for r in cur.fetchall()
    ]
    return {
        "chunk_id": target["id"],
        "document_id": target["document_id"],
        "filename": target["filename"],
        "chunk_index": hit_index,
        "segments": segments,
    }
