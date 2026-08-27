"""client_submissions 事务级 DAL。"""

from __future__ import annotations

import json
from typing import Iterable, Optional

from services.client_submission.errors import ENGAGEMENT_NOT_ACTIVE

_COLUMNS = """
    id::text, product_scope, engagement_id::text,
    source_tenant_id::text, source_workspace_client_id,
    source_document_type, source_document_id, source_revision, source_hash,
    target_tenant_id::text, target_workspace_client_id,
    snapshot_json, original_file_ref, status, cowork_history_id::text,
    attempts, next_attempt_at, last_error, created_at, delivered_at, updated_at
"""

_S_COLUMNS = """
    s.id::text AS id, s.product_scope, s.engagement_id::text AS engagement_id,
    s.source_tenant_id::text AS source_tenant_id, s.source_workspace_client_id,
    s.source_document_type, s.source_document_id, s.source_revision, s.source_hash,
    s.target_tenant_id::text AS target_tenant_id, s.target_workspace_client_id,
    s.snapshot_json, s.original_file_ref, s.status, s.cowork_history_id::text AS cowork_history_id,
    s.attempts, s.next_attempt_at, s.last_error, s.created_at, s.delivered_at, s.updated_at
"""


def create_pending(
    cur,
    *,
    engagement: dict,
    source_document_type: str,
    source_document_id: str,
    source_revision: int,
    source_hash: str,
    snapshot: dict,
    original_file_ref: Optional[str],
) -> dict:
    cur.execute(
        f"""
        INSERT INTO client_submissions (
            engagement_id, source_tenant_id, source_workspace_client_id,
            source_document_type, source_document_id, source_revision, source_hash,
            target_tenant_id, target_workspace_client_id,
            snapshot_json, original_file_ref
        ) VALUES (
            %s::uuid, %s::uuid, %s,
            %s, %s, %s, %s,
            %s::uuid, %s,
            %s::jsonb, %s
        )
        ON CONFLICT (
            engagement_id, source_document_type, source_document_id, source_revision
        ) DO NOTHING
        RETURNING {_COLUMNS}
        """,
        (
            engagement["id"],
            engagement["merchant_tenant_id"],
            int(engagement["merchant_workspace_client_id"]),
            source_document_type,
            str(source_document_id),
            int(source_revision),
            source_hash,
            engagement["firm_tenant_id"],
            int(engagement["firm_workspace_client_id"]),
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True),
            original_file_ref,
        ),
    )
    row = cur.fetchone()
    if row:
        return dict(row)
    return get_by_revision(
        cur,
        engagement_id=engagement["id"],
        source_document_type=source_document_type,
        source_document_id=source_document_id,
        source_revision=source_revision,
    )


def get_by_revision(
    cur,
    *,
    engagement_id: str,
    source_document_type: str,
    source_document_id: str,
    source_revision: int,
) -> Optional[dict]:
    cur.execute(
        f"""
        SELECT {_COLUMNS} FROM client_submissions
        WHERE engagement_id = %s::uuid AND source_document_type = %s
          AND source_document_id = %s AND source_revision = %s
        """,
        (
            str(engagement_id),
            source_document_type,
            str(source_document_id),
            int(source_revision),
        ),
    )
    row = cur.fetchone()
    return dict(row) if row else None


_PARTICIPANT_COLUMNS = {
    "source": ("source_tenant_id", "source_workspace_client_id"),
    "target": ("target_tenant_id", "target_workspace_client_id"),
}


def _participant_filter(
    *, tenant_id: str, participant_side: str, workspace_client_ids: Optional[Iterable[int]]
) -> tuple[str, list]:
    try:
        tenant_column, workspace_column = _PARTICIPANT_COLUMNS[participant_side]
    except KeyError as error:
        raise ValueError("participant_side must be source or target") from error
    where = f"{tenant_column} = %s::uuid"
    params: list = [str(tenant_id)]
    if workspace_client_ids is not None:
        ids = sorted({int(item) for item in workspace_client_ids})
        where += f" AND {workspace_column} = ANY(%s::bigint[])"
        params.append(ids)
    return where, params


def list_for_tenant(
    cur,
    *,
    tenant_id: str,
    participant_side: str,
    workspace_client_ids: Optional[Iterable[int]] = None,
    limit: int = 100,
) -> list[dict]:
    where, params = _participant_filter(
        tenant_id=tenant_id,
        participant_side=participant_side,
        workspace_client_ids=workspace_client_ids,
    )
    params.append(min(max(int(limit), 1), 500))
    cur.execute(
        f"""
        SELECT {_COLUMNS} FROM client_submissions
        WHERE {where}
        ORDER BY created_at DESC LIMIT %s
        """,
        tuple(params),
    )
    return [dict(row) for row in cur.fetchall()]


def get_for_tenant(
    cur,
    *,
    tenant_id: str,
    submission_id: str,
    participant_side: str,
    workspace_client_ids: Optional[Iterable[int]] = None,
) -> Optional[dict]:
    where, params = _participant_filter(
        tenant_id=tenant_id,
        participant_side=participant_side,
        workspace_client_ids=workspace_client_ids,
    )
    cur.execute(
        f"""
        SELECT {_COLUMNS} FROM client_submissions
        WHERE id = %s::uuid AND {where}
        """,
        (str(submission_id), *params),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def list_due_ids(cur, *, limit: int = 20) -> list[str]:
    cur.execute(
        """
        SELECT s.id::text AS id
        FROM client_submissions s
        JOIN accounting_engagements e ON e.id = s.engagement_id
        WHERE e.status = 'active'
          AND s.attempts < 5
          AND (
              s.status = 'pending'
              OR (s.status = 'failed' AND s.next_attempt_at <= now())
          )
        ORDER BY s.created_at
        LIMIT %s
        """,
        (min(max(int(limit), 1), 100),),
    )
    return [str(row["id"]) for row in cur.fetchall()]


def get_for_delivery(cur, *, submission_id: str) -> Optional[dict]:
    cur.execute(
        f"""
        SELECT {_S_COLUMNS},
               e.status AS engagement_status,
               e.firm_tenant_id::text AS engagement_firm_tenant_id,
               e.firm_workspace_client_id AS engagement_firm_workspace_client_id,
               e.merchant_tenant_id::text AS engagement_merchant_tenant_id,
               e.merchant_workspace_client_id AS engagement_merchant_workspace_client_id
        FROM client_submissions s
        JOIN accounting_engagements e ON e.id = s.engagement_id
        WHERE s.id = %s::uuid
        FOR UPDATE OF s
        """,
        (str(submission_id),),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def mark_delivered(cur, *, submission_id: str, cowork_history_id: str) -> None:
    cur.execute(
        """
        UPDATE client_submissions
        SET status = 'delivered', cowork_history_id = %s::uuid,
            delivered_at = now(), next_attempt_at = NULL, last_error = NULL,
            updated_at = now()
        WHERE id = %s::uuid AND status IN ('pending', 'failed')
        """,
        (str(cowork_history_id), str(submission_id)),
    )


def mark_failed(
    cur,
    *,
    submission_id: str,
    error: str,
    retry_delay_seconds: Optional[int],
) -> None:
    if retry_delay_seconds is None:
        next_sql = "NULL"
        params = (str(error)[:500], str(submission_id))
    else:
        next_sql = "now() + (%s * interval '1 second')"
        params = (str(error)[:500], int(retry_delay_seconds), str(submission_id))
    cur.execute(
        f"""
        UPDATE client_submissions
        SET status = 'failed', attempts = attempts + 1,
            last_error = %s, next_attempt_at = {next_sql}, updated_at = now()
        WHERE id = %s::uuid AND status IN ('pending', 'failed')
        """,
        params,
    )


def supersede_ended(cur) -> int:
    cur.execute(
        """
        UPDATE client_submissions s
        SET status = 'superseded', next_attempt_at = NULL,
            last_error = %s, updated_at = now()
        FROM accounting_engagements e
        WHERE e.id = s.engagement_id AND e.status = 'ended'
          AND s.status IN ('pending', 'failed')
        """,
        (ENGAGEMENT_NOT_ACTIVE,),
    )
    return int(cur.rowcount or 0)
