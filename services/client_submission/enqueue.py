"""商户正式单据确认事务内创建 Cowork 提交快照。"""

from __future__ import annotations

import hashlib
import json
from typing import Optional

from services.accounting_engagement import store as engagement_store
from services.accounting_engagement.errors import WORKSPACE_MISMATCH, EngagementError
from services.client_submission import store
from services.client_submission.errors import REVISION_CONFLICT, SubmissionError


def enqueue_confirmed_document(
    cur,
    *,
    merchant_tenant_id: str,
    merchant_workspace_client_id: int,
    source_document_type: str,
    source_document_id: str,
    source_revision: int,
    snapshot: dict,
    original_file_ref: Optional[str] = None,
) -> Optional[dict]:
    """有 active/suspended 关系才建 outbox；无关系或待确认不阻断商户自己的正式单据。"""
    if source_document_type not in {"purchase", "sales"}:
        raise ValueError("source_document_type must be purchase or sales")
    if int(source_revision) < 1:
        raise ValueError("source_revision must be positive")

    engagement = engagement_store.get_open_for_merchant(
        cur, merchant_tenant_id=str(merchant_tenant_id)
    )
    if not engagement or engagement.get("status") not in {"active", "suspended"}:
        return None
    if int(engagement.get("merchant_workspace_client_id") or 0) != int(
        merchant_workspace_client_id
    ):
        raise EngagementError(WORKSPACE_MISMATCH)
    if not engagement.get("firm_workspace_client_id"):
        raise EngagementError(WORKSPACE_MISMATCH)

    source_hash = _snapshot_hash(snapshot, original_file_ref)
    submission = store.create_pending(
        cur,
        engagement=engagement,
        source_document_type=source_document_type,
        source_document_id=str(source_document_id),
        source_revision=int(source_revision),
        source_hash=source_hash,
        snapshot=snapshot,
        original_file_ref=original_file_ref,
    )
    if submission and submission.get("source_hash") != source_hash:
        raise SubmissionError(REVISION_CONFLICT)
    return submission


def _snapshot_hash(snapshot: dict, original_file_ref: Optional[str]) -> str:
    canonical = json.dumps(
        {"snapshot": snapshot, "original_file_ref": original_file_ref},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
