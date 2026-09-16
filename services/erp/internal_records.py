"""Pearnly internal draft/save flow shared by web and LINE."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from uuid import UUID

from fastapi import HTTPException

from core import db
from services.auth.entrance import require_erp_portal
from services.authz.deps import actor_has_perm, check_workspace_scope
from services.intake_bridge import convert

SOURCES = frozenset({"erp_web", "line_erp"})


def authorize(user, workspace_id, direction, *, confirm=False):
    require_erp_portal(user)
    if user.get("entry") != "erp" or direction not in {"purchase", "sales"}:
        raise HTTPException(403, detail="authz.entrance_scope")
    check_workspace_scope(None, user, workspace_id)
    permissions = [f"{direction}.doc.create"]
    if confirm:
        permissions.append(f"{direction}.doc.approve")
    if not all(actor_has_perm(None, user, code) for code in permissions):
        raise HTTPException(403, detail="authz.forbidden")


def workspace(cur, user, workspace_id):
    cur.execute(
        "SELECT id, name, tax_id FROM workspace_clients WHERE id = %s "
        "AND tenant_id = %s::uuid AND is_active = TRUE FOR SHARE",
        (workspace_id, str(user["tenant_id"])),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, detail="workspace.not_found")
    return dict(row)


def _decimal(value, *, positive=False):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or (positive and number == 0):
            raise ValueError
        return number
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(422, detail="erp.invalid_amount") from None


def normalized_fields(fields, direction, subject, history_id, *, strict=True):
    from services.erp.business_dates import business_fields

    result = business_fields(fields)
    result.pop("document_number", None)
    original = str(result.get("invoice_number") or "")
    result["bill_number"] = result.get("bill_number") or (
        "" if original.startswith("REC-") else original
    )
    prefix = "buyer" if direction == "purchase" else "seller"
    declared_tax = re.sub(r"\D", "", str(fields.get(f"{prefix}_tax") or ""))
    own_tax = re.sub(r"\D", "", str(subject.get("tax_id") or ""))
    if declared_tax and own_tax and declared_tax != own_tax:
        raise HTTPException(409, detail="erp.workspace_mismatch")
    items = []
    for value in result.get("items") or []:
        if not isinstance(value, dict):
            raise HTTPException(422, detail="erp.declaration_required")
        name = str(value.get("name") or "").strip()
        if not name:
            raise HTTPException(422, detail="erp.declaration_required")
        qty = _decimal(value.get("qty"), positive=True)
        price = _decimal(value.get("price"), positive=True)
        items.append(
            {
                **value,
                "name": name,
                "qty": str(qty),
                "price": str(price),
                "subtotal": str((qty * price).quantize(Decimal("0.01"))),
            }
        )
    if strict and not items:
        raise HTTPException(422, detail="erp.declaration_required")
    subtotal = sum((Decimal(item["subtotal"]) for item in items), Decimal("0"))
    vat = _decimal(result.get("vat") or "0")
    if result.get("manual_layout") == 1:
        from services.erp.manual_totals import apply

        subtotal, vat = apply(result, items, _decimal)
    prefix = "buyer" if direction == "purchase" else "seller"
    result.update(
        {
            "direction": direction,
            "items": items,
            "subtotal": str(subtotal),
            "vat": str(vat),
            "total_amount": str(subtotal + vat),
            "invoice_number": str(result.get("invoice_number") or f"REC-{history_id}").strip(),
            f"{prefix}_name": subject["name"],
            f"{prefix}_tax": subject.get("tax_id") or "",
        }
    )
    return result


def save_draft(user, *, history_id, workspace_id, direction, fields, source="erp_web"):
    """A client-generated id makes create/retry idempotent, without a new draft table."""
    from services.erp.business_dates import standard

    history_id = str(UUID(str(history_id)))
    authorize(user, workspace_id, direction)
    if source not in SOURCES:
        raise HTTPException(403, detail="authz.entrance_scope")
    with db.get_cursor_rls(str(user["tenant_id"]), user_id=str(user["id"]), commit=True) as cur:
        subject = workspace(cur, user, workspace_id)
        clean = normalized_fields(fields, direction, subject, history_id, strict=False)
        pages = json.dumps([{"page_number": 1, "fields": clean}], ensure_ascii=False)
        cur.execute(
            "INSERT INTO ocr_history (id, user_id, tenant_id, workspace_client_id, filename, "
            "page_count, pages, confidence, elapsed_ms, source, source_ref, staged, "
            "invoice_no, invoice_date, seller_name, total_amount) "
            "VALUES (%s::uuid,%s::uuid,%s::uuid,%s,'manual',1,%s::jsonb,'high',0,%s,'manual',TRUE,%s,%s,%s,%s) "
            "ON CONFLICT (id) DO NOTHING",
            (
                history_id,
                str(user["id"]),
                str(user["tenant_id"]),
                workspace_id,
                pages,
                source,
                clean["invoice_number"],
                standard(clean["date"]),
                clean.get("seller_name"),
                clean["total_amount"],
            ),
        )
        cur.execute(
            "SELECT staged, workspace_client_id, pages, source FROM ocr_history WHERE id = %s::uuid "
            "AND tenant_id = %s::uuid AND user_id = %s::uuid FOR UPDATE",
            (history_id, str(user["tenant_id"]), str(user["id"])),
        )
        row = cur.fetchone()
        if (
            not row
            or row.get("source") not in SOURCES
            or int(row["workspace_client_id"]) != int(workspace_id)
        ):
            raise HTTPException(404, detail="history.not_found")
        previous = (row.get("pages") or [{}])[0].get("fields") or {}
        if previous.get("direction") != direction:
            raise HTTPException(409, detail="erp.direction_changed")
        if not row["staged"]:
            comparable = {k: v for k, v in previous.items() if k != "document_number"}
            old_items = comparable.get("items") or []
            new_items = clean.get("items") or []
            if len(old_items) != len(new_items):
                raise HTTPException(409, detail="erp.formal_document_locked")
            comparable["items"] = [
                {
                    k: (new.get(k) if k in {"product_id", "code", "unit"} and not new.get(k) else v)
                    for k, v in old.items()
                    if k not in {"product_id", "code", "unit"} or k in new
                }
                for old, new in zip(old_items, new_items)
            ]
            if comparable == clean:
                return {"history_id": history_id, "fields": previous, "status": "saved"}
            raise HTTPException(409, detail="erp.formal_document_locked")
        retained_pages = row.get("pages") or [{}]
        retained_pages[0]["fields"] = clean
        pages = json.dumps(retained_pages, ensure_ascii=False)
        cur.execute(
            "UPDATE ocr_history SET pages=%s::jsonb, invoice_no=%s, invoice_date=%s, "
            "seller_name=%s, total_amount=%s, updated_at=NOW() WHERE id=%s::uuid",
            (
                pages,
                clean["invoice_number"],
                standard(clean["date"]),
                clean.get("seller_name"),
                clean["total_amount"],
                history_id,
            ),
        )
    return {"history_id": history_id, "fields": clean, "status": "draft"}


def confirm(user, *, history_ids, workspace_id, direction):
    authorize(user, workspace_id, direction, confirm=True)
    ids = list(dict.fromkeys(str(UUID(str(value))) for value in history_ids))
    if not ids:
        raise HTTPException(422, detail="erp.declaration_required")
    with db.get_cursor_rls(str(user["tenant_id"]), user_id=str(user["id"]), commit=True) as cur:
        subject = workspace(cur, user, workspace_id)
        cur.execute(
            "SELECT id, pages, source FROM ocr_history WHERE id=ANY(%s::uuid[]) "
            "AND tenant_id=%s::uuid AND user_id=%s::uuid AND workspace_client_id=%s "
            "ORDER BY id FOR UPDATE",
            (ids, str(user["tenant_id"]), str(user["id"]), workspace_id),
        )
        rows = cur.fetchall()
        if len(rows) != len(ids) or any(row.get("source") not in SOURCES for row in rows):
            raise HTTPException(404, detail="history.not_found")
        for row in rows:
            fields = (row.get("pages") or [{}])[0].get("fields") or {}
            if fields.get("direction") != direction:
                raise HTTPException(409, detail="erp.direction_changed")
            clean = normalized_fields(fields, direction, subject, str(row["id"]))
            pages = row["pages"]
            pages[0]["fields"] = clean
            cur.execute(
                "UPDATE ocr_history SET pages=%s::jsonb WHERE id=%s::uuid AND staged=TRUE",
                (json.dumps(pages, ensure_ascii=False), str(row["id"])),
            )
        result = convert.convert_histories(
            cur, tenant_id=str(user["tenant_id"]), user_id=str(user["id"]), history_ids=ids
        )
        failed = [row for row in result["skipped"] if row.get("reason") != "already_converted"]
        if failed:
            raise HTTPException(409, detail={"code": "erp.confirm_failed", "histories": failed})
        cur.execute(
            "UPDATE ocr_history SET staged=FALSE, updated_at=NOW() WHERE id=ANY(%s::uuid[]) "
            "AND tenant_id=%s::uuid AND user_id=%s::uuid",
            (ids, str(user["tenant_id"]), str(user["id"])),
        )
    return {"ok": True, "status": "saved", **result}


def list_drafts(user, *, workspace_id, direction):
    authorize(user, workspace_id, direction)
    with db.get_cursor_rls(str(user["tenant_id"]), user_id=str(user["id"])) as cur:
        workspace(cur, user, workspace_id)
        cur.execute(
            "SELECT id, pages, source, source_ref FROM ocr_history "
            "WHERE tenant_id=%s::uuid AND user_id=%s::uuid AND workspace_client_id=%s "
            "AND staged=TRUE AND source IN ('erp_web','line_erp') "
            "AND pages->0->'fields'->>'direction'=%s ORDER BY updated_at DESC LIMIT 100",
            (str(user["tenant_id"]), str(user["id"]), workspace_id, direction),
        )
        return [
            {
                "id": str(row["id"]),
                "fields": (row["pages"] or [{}])[0].get("fields") or {},
                "source": row["source"],
                "source_ref": row.get("source_ref"),
            }
            for row in cur.fetchall()
        ]
