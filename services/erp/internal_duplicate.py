"""Serialize matching source invoices before allocating internal document numbers."""

import json

from services.erp.business_dates import standard
from services.intake_bridge.errors import SkipConversion


def guard(cur, *, tenant_id, workspace_id, direction, fields, history_id):
    bill = str(fields.get("bill_number") or fields.get("invoice_number") or "").strip()
    if not bill or bill.startswith("REC-"):
        return
    party = "seller" if direction == "purchase" else "buyer"
    identity = str(fields.get(party + "_tax") or fields.get(party + "_name") or "").strip()
    if not identity:
        return
    day = standard(fields.get("date"))
    key = json.dumps([str(tenant_id), int(workspace_id), direction, bill, identity, day])
    cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (key,))
    cur.execute(
        "SELECT h.pages FROM ocr_history h WHERE h.tenant_id=%s::uuid "
        "AND h.workspace_client_id=%s AND h.id<>%s::uuid "
        "AND h.source IN ('erp_web','line_erp') "
        "AND (EXISTS(SELECT 1 FROM purchase_docs d WHERE d.tenant_id=h.tenant_id "
        "AND d.ocr_history_id=h.id AND d.status='posted') "
        "OR EXISTS(SELECT 1 FROM sales_documents d WHERE d.tenant_id=h.tenant_id "
        "AND d.ocr_history_id=h.id AND d.status='issued')) "
        "AND COALESCE(NULLIF(h.pages->0->'fields'->>'bill_number',''), "
        "h.pages->0->'fields'->>'invoice_number')=%s",
        (tenant_id, workspace_id, history_id, bill),
    )
    for row in cur.fetchall():
        existing = (row.get("pages") or [{}])[0].get("fields") or {}
        other = str(existing.get(party + "_tax") or existing.get(party + "_name") or "").strip()
        if (
            existing.get("direction") == direction
            and other == identity
            and standard(existing.get("date")) == day
        ):
            raise SkipConversion("duplicate")
