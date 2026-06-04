"""Data access for the knowledge document tables.

Every read and write is scoped to a tenant, and reads additionally honour the
caller's workspace-client visibility (None = owner/super-admin sees the whole
tenant, a list = the account sets a member may see, [] = firm-scoped rows only).
This is the application-layer half of the isolation; db.get_cursor_rls supplies
the row-level-security half on migration. Both run together by design — the
SQL filters explicitly even though RLS would also constrain it.

Functions operate on a caller-supplied cursor so a route can compose several
writes (create document + enqueue ingest job) inside one transaction. SQL is
always parameterised; identifiers are never interpolated from input.
"""

from __future__ import annotations

from typing import Optional

from psycopg2.extras import Json

from services.knowledge.access import AccessibleIds, workspace_filter
from services.knowledge.schema import (
    DOC_DELETED,
    DOC_UPLOADED,
    JOB_QUEUED,
    SCOPE_FIRM,
    SCOPE_WORKSPACE_CLIENT,
    IngestJob,
    KnowledgeAnswer,
    KnowledgeBase,
    KnowledgeDocument,
)

_DEFAULT_BASE_NAME = "Default"

_DOC_COLS = (
    "id, tenant_id, workspace_client_id, knowledge_base_id, source_type, "
    "filename, mime_type, storage_path, checksum, status, uploaded_by, "
    "error_code, created_at, updated_at"
)
_JOB_COLS = (
    "id, tenant_id, workspace_client_id, document_id, status, progress, "
    "error_code, retry_count, max_retries, created_at, finished_at"
)
_BASE_COLS = "id, tenant_id, workspace_client_id, scope, name, status, created_by, created_at"


def _uuid_or_none(value) -> Optional[str]:
    """Normalise a uuid column to a string, preserving NULL as None."""
    return str(value) if value else None


def _as_base(row: dict) -> KnowledgeBase:
    return KnowledgeBase(
        id=row["id"],
        tenant_id=str(row["tenant_id"]),
        workspace_client_id=row["workspace_client_id"],
        scope=row["scope"],
        name=row["name"],
        status=row["status"],
        created_by=_uuid_or_none(row["created_by"]),
        created_at=row["created_at"],
    )


def _as_document(row: dict) -> KnowledgeDocument:
    return KnowledgeDocument(
        id=row["id"],
        tenant_id=str(row["tenant_id"]),
        workspace_client_id=row["workspace_client_id"],
        knowledge_base_id=row["knowledge_base_id"],
        source_type=row["source_type"],
        filename=row["filename"],
        mime_type=row["mime_type"],
        storage_path=row["storage_path"],
        checksum=row["checksum"],
        status=row["status"],
        uploaded_by=_uuid_or_none(row["uploaded_by"]),
        error_code=row["error_code"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _as_job(row: dict) -> IngestJob:
    return IngestJob(
        id=row["id"],
        tenant_id=str(row["tenant_id"]),
        workspace_client_id=row["workspace_client_id"],
        document_id=row["document_id"],
        status=row["status"],
        progress=row["progress"],
        error_code=row["error_code"],
        retry_count=row["retry_count"],
        max_retries=row["max_retries"],
        created_at=row["created_at"],
        finished_at=row["finished_at"],
    )


def get_or_create_default_base(
    cur, *, tenant_id: str, workspace_client_id: Optional[int]
) -> KnowledgeBase:
    """Return the tenant's default base for this scope, creating it on first use.

    A document must belong to a base. The sandbox upload path does not yet expose
    base management, so it lands documents in one default base per (tenant,
    workspace client); firm-wide uploads (no workspace client) share the firm base.
    """
    scope = SCOPE_WORKSPACE_CLIENT if workspace_client_id is not None else SCOPE_FIRM
    cur.execute(
        f"SELECT {_BASE_COLS} FROM knowledge_bases "
        "WHERE tenant_id = %s AND scope = %s AND name = %s "
        "AND workspace_client_id IS NOT DISTINCT FROM %s",
        (tenant_id, scope, _DEFAULT_BASE_NAME, workspace_client_id),
    )
    existing = cur.fetchone()
    if existing is not None:
        return _as_base(existing)
    cur.execute(
        "INSERT INTO knowledge_bases "
        "(tenant_id, workspace_client_id, scope, name, status) "
        f"VALUES (%s, %s, %s, %s, 'active') RETURNING {_BASE_COLS}",
        (tenant_id, workspace_client_id, scope, _DEFAULT_BASE_NAME),
    )
    return _as_base(cur.fetchone())


def list_bases(cur, *, tenant_id: str, accessible_ids: AccessibleIds) -> list[KnowledgeBase]:
    where, params = workspace_filter(accessible_ids)
    cur.execute(
        f"SELECT {_BASE_COLS} FROM knowledge_bases "
        "WHERE tenant_id = %s" + where + " ORDER BY id",
        [tenant_id, *params],
    )
    return [_as_base(r) for r in cur.fetchall()]


def get_base(
    cur, *, tenant_id: str, base_id: int, accessible_ids: AccessibleIds
) -> Optional[KnowledgeBase]:
    where, params = workspace_filter(accessible_ids)
    cur.execute(
        f"SELECT {_BASE_COLS} FROM knowledge_bases " "WHERE tenant_id = %s AND id = %s" + where,
        [tenant_id, base_id, *params],
    )
    row = cur.fetchone()
    return _as_base(row) if row is not None else None


def create_document(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: Optional[int],
    knowledge_base_id: int,
    source_type: str,
    filename: str,
    mime_type: Optional[str],
    storage_path: Optional[str],
    checksum: str,
    uploaded_by: Optional[str],
) -> KnowledgeDocument:
    cur.execute(
        "INSERT INTO knowledge_documents "
        "(tenant_id, workspace_client_id, knowledge_base_id, source_type, "
        " filename, mime_type, storage_path, checksum, status, uploaded_by) "
        f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING {_DOC_COLS}",
        (
            tenant_id,
            workspace_client_id,
            knowledge_base_id,
            source_type,
            filename,
            mime_type,
            storage_path,
            checksum,
            DOC_UPLOADED,
            uploaded_by,
        ),
    )
    return _as_document(cur.fetchone())


def get_document(
    cur,
    *,
    tenant_id: str,
    document_id: int,
    accessible_ids: AccessibleIds,
    include_deleted: bool = False,
) -> Optional[KnowledgeDocument]:
    """Fetch one document. A soft-deleted tombstone reads as absent by default."""
    where, params = workspace_filter(accessible_ids)
    sql = f"SELECT {_DOC_COLS} FROM knowledge_documents " "WHERE tenant_id = %s AND id = %s" + where
    args: list = [tenant_id, document_id, *params]
    if not include_deleted:
        sql += " AND status <> %s"
        args.append(DOC_DELETED)
    cur.execute(sql, args)
    row = cur.fetchone()
    return _as_document(row) if row is not None else None


def list_documents(
    cur,
    *,
    tenant_id: str,
    accessible_ids: AccessibleIds,
    knowledge_base_id: Optional[int] = None,
    include_deleted: bool = False,
) -> list[KnowledgeDocument]:
    where, params = workspace_filter(accessible_ids)
    sql = f"SELECT {_DOC_COLS} FROM knowledge_documents WHERE tenant_id = %s" + where
    args: list = [tenant_id, *params]
    if knowledge_base_id is not None:
        sql += " AND knowledge_base_id = %s"
        args.append(knowledge_base_id)
    if not include_deleted:
        sql += " AND status <> %s"
        args.append(DOC_DELETED)
    sql += " ORDER BY id DESC"
    cur.execute(sql, args)
    return [_as_document(r) for r in cur.fetchall()]


def update_document_status(
    cur,
    *,
    tenant_id: str,
    document_id: int,
    status: str,
    error_code: Optional[str] = None,
) -> Optional[KnowledgeDocument]:
    """Move a document to a new lifecycle status, returning the updated row.

    Returns None if no document matched, so the caller need not re-read to learn
    the fresh state (status, error_code, updated_at).
    """
    cur.execute(
        "UPDATE knowledge_documents "
        "SET status = %s, error_code = %s, updated_at = now() "
        f"WHERE tenant_id = %s AND id = %s RETURNING {_DOC_COLS}",
        (status, error_code, tenant_id, document_id),
    )
    row = cur.fetchone()
    return _as_document(row) if row is not None else None


def soft_delete_document(
    cur, *, tenant_id: str, document_id: int, accessible_ids: AccessibleIds
) -> bool:
    """Tombstone a document (status -> deleted). Returns whether a row matched.

    Visibility is enforced here too: a member cannot delete a document outside
    the account sets they may see, even by guessing its id.
    """
    where, params = workspace_filter(accessible_ids)
    cur.execute(
        "UPDATE knowledge_documents SET status = %s, updated_at = now() "
        "WHERE tenant_id = %s AND id = %s AND status <> %s" + where,
        [DOC_DELETED, tenant_id, document_id, DOC_DELETED, *params],
    )
    return cur.rowcount > 0


def create_ingest_job(
    cur, *, tenant_id: str, workspace_client_id: Optional[int], document_id: int
) -> IngestJob:
    cur.execute(
        "INSERT INTO knowledge_ingest_jobs "
        "(tenant_id, workspace_client_id, document_id, status) "
        f"VALUES (%s, %s, %s, %s) RETURNING {_JOB_COLS}",
        (tenant_id, workspace_client_id, document_id, JOB_QUEUED),
    )
    return _as_job(cur.fetchone())


def complete_ingest_job(
    cur,
    *,
    tenant_id: str,
    job_id: int,
    status: str,
    progress: int,
    error_code: Optional[str] = None,
) -> Optional[IngestJob]:
    """Mark a job terminal (success/failed) with its final progress.

    Returns the updated row, or None if no job matched.
    """
    cur.execute(
        "UPDATE knowledge_ingest_jobs "
        "SET status = %s, progress = %s, error_code = %s, finished_at = now() "
        f"WHERE tenant_id = %s AND id = %s RETURNING {_JOB_COLS}",
        (status, progress, error_code, tenant_id, job_id),
    )
    row = cur.fetchone()
    return _as_job(row) if row is not None else None


_ANSWER_COLS = (
    "id, tenant_id, workspace_client_id, question, answer, citations, model, "
    "no_answer, created_at"
)


def _as_answer(row: dict) -> KnowledgeAnswer:
    return KnowledgeAnswer(
        id=row["id"],
        tenant_id=str(row["tenant_id"]),
        workspace_client_id=row["workspace_client_id"],
        question=row["question"],
        answer=row["answer"],
        citations=row["citations"] or [],
        model=row["model"],
        no_answer=row["no_answer"],
        created_at=row["created_at"],
    )


def create_answer(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: Optional[int],
    question: str,
    answer: str,
    citations: list,
    model: Optional[str],
    no_answer: bool,
    created_by: Optional[str],
) -> KnowledgeAnswer:
    cur.execute(
        "INSERT INTO knowledge_answers "
        "(tenant_id, workspace_client_id, question, answer, citations, model, "
        " no_answer, created_by) "
        f"VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING {_ANSWER_COLS}",
        (
            tenant_id,
            workspace_client_id,
            question,
            answer,
            Json(citations),
            model,
            no_answer,
            created_by,
        ),
    )
    return _as_answer(cur.fetchone())


def get_answer(
    cur, *, tenant_id: str, answer_id: int, accessible_ids: AccessibleIds
) -> Optional[KnowledgeAnswer]:
    where, params = workspace_filter(accessible_ids)
    cur.execute(
        f"SELECT {_ANSWER_COLS} FROM knowledge_answers " "WHERE tenant_id = %s AND id = %s" + where,
        [tenant_id, answer_id, *params],
    )
    row = cur.fetchone()
    return _as_answer(row) if row is not None else None


def get_latest_ingest_job(cur, *, tenant_id: str, document_id: int) -> Optional[IngestJob]:
    cur.execute(
        f"SELECT {_JOB_COLS} FROM knowledge_ingest_jobs "
        "WHERE tenant_id = %s AND document_id = %s ORDER BY id DESC LIMIT 1",
        (tenant_id, document_id),
    )
    row = cur.fetchone()
    return _as_job(row) if row is not None else None
