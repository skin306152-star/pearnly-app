"""把一条已确认快照写入精确 Cowork workspace 的现有复核历史。"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation

from core import thai_date
from services.client_submission.errors import TARGET_MISMATCH, SubmissionError

SOURCE = "erp_client_submission"


def deliver_to_cowork(cur, submission: dict) -> str:
    _validate_target(submission)
    owner_user_id = _target_owner(cur, submission)
    snapshot = submission.get("snapshot_json") or {}
    pages = _pages(snapshot)
    fields = _fields(snapshot, pages)

    cur.execute(
        """
        INSERT INTO ocr_history (
            user_id, tenant_id, filename, page_count, file_hash,
            pages, confidence, elapsed_ms,
            invoice_no, invoice_date, seller_name, total_amount,
            source, source_ref, workspace_client_id, ai_raw, staged
        ) VALUES (
            %s::uuid, %s::uuid, %s, %s, %s,
            %s::jsonb, 'high', 0,
            %s, %s, %s, %s,
            %s, %s, %s, %s::jsonb, TRUE
        )
        RETURNING id::text AS id
        """,
        (
            owner_user_id,
            submission["target_tenant_id"],
            _filename(submission, snapshot),
            max(len(pages), 1),
            submission["source_hash"],
            json.dumps(pages, ensure_ascii=False, sort_keys=True),
            _value(fields, "invoice_number", "invoice_no", "document_number"),
            _date(_value(fields, "date_raw", "date", "invoice_date", "document_date")),
            _value(fields, "seller_name", "vendor_name", "customer_name"),
            _amount(_value(fields, "total_amount", "grand_total")),
            SOURCE,
            submission["id"],
            int(submission["target_workspace_client_id"]),
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True),
        ),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError("cowork history insert returned no id")
    return str(row["id"] if isinstance(row, dict) else row[0])


def _validate_target(submission: dict) -> None:
    exact = (
        submission.get("engagement_status") == "active"
        and str(submission.get("target_tenant_id"))
        == str(submission.get("engagement_firm_tenant_id"))
        and int(submission.get("target_workspace_client_id") or 0)
        == int(submission.get("engagement_firm_workspace_client_id") or 0)
        and str(submission.get("source_tenant_id"))
        == str(submission.get("engagement_merchant_tenant_id"))
        and int(submission.get("source_workspace_client_id") or 0)
        == int(submission.get("engagement_merchant_workspace_client_id") or 0)
    )
    if not exact:
        raise SubmissionError(TARGET_MISMATCH)


def _target_owner(cur, submission: dict) -> str:
    cur.execute(
        """
        SELECT t.owner_user_id::text AS user_id
        FROM tenants t
        JOIN accounting_firm_profiles p ON p.tenant_id = t.id
        JOIN workspace_clients w ON w.tenant_id = t.id
        WHERE t.id = %s::uuid AND t.status = 'active'
          AND p.status = 'active' AND w.id = %s AND w.is_active
          AND t.owner_user_id IS NOT NULL
        """,
        (submission["target_tenant_id"], int(submission["target_workspace_client_id"])),
    )
    row = cur.fetchone()
    if not row:
        raise SubmissionError(TARGET_MISMATCH)
    return str(row["user_id"] if isinstance(row, dict) else row[0])


def _pages(snapshot: dict) -> list:
    pages = snapshot.get("pages") if isinstance(snapshot, dict) else None
    if isinstance(pages, list) and pages:
        return pages
    fields = snapshot.get("fields") if isinstance(snapshot, dict) else None
    return [{"fields": fields if isinstance(fields, dict) else snapshot}]


def _fields(snapshot: dict, pages: list) -> dict:
    direct = snapshot.get("fields") if isinstance(snapshot, dict) else None
    if isinstance(direct, dict):
        return direct
    first = pages[0] if pages and isinstance(pages[0], dict) else {}
    fields = first.get("fields")
    return fields if isinstance(fields, dict) else {}


def _filename(submission: dict, snapshot: dict) -> str:
    named = snapshot.get("filename") if isinstance(snapshot, dict) else None
    if named:
        return str(named)[:255]
    return f"{submission['source_document_type']}-{submission['source_document_id']}"[:255]


def _value(fields: dict, *keys):
    for key in keys:
        value = fields.get(key)
        if value not in (None, ""):
            return str(value).strip() or None
    return None


def _date(value):
    return thai_date.gregorian_from_printed(value)


def _amount(value):
    try:
        return Decimal(str(value).replace(",", "").strip()) if value not in (None, "") else None
    except (InvalidOperation, ValueError):
        return None
