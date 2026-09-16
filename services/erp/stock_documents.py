"""Internal IR/IS documents; the stockcard derives balances from saved documents."""

import json
import hashlib
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from core import db
from services.erp import business_dates, internal_records
from services.erp.document_numbers import allocate
from services.erp.team_access import record_creator_scope

SCHEMA = """CREATE TABLE IF NOT EXISTS erp_stock_documents (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL,
 direction text NOT NULL CHECK(direction IN ('in','out')), doc_no text NOT NULL,
 doc_date date NOT NULL, fields jsonb NOT NULL, created_by uuid NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(tenant_id,doc_no))"""


def ensure_schema():
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(SCHEMA)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_erp_stock_documents_workspace ON erp_stock_documents(tenant_id,workspace_client_id,doc_date)"
        )
        apply_tenant_rls(cur, "erp_stock_documents")


def authorize(user, workspace_id, direction, *, save=False):
    if direction not in ("in", "out"):
        raise HTTPException(422, "erp.invalid_direction")
    if not save:
        from services.auth.entrance import require_erp_portal
        from services.authz.deps import check_workspace_scope, actor_has_perm

        require_erp_portal(user)
        check_workspace_scope(None, user, workspace_id)
        if user.get("entry") != "erp" or not actor_has_perm(None, user, "stockcard.report.view"):
            raise HTTPException(403, "authz.forbidden")
        return
    internal_records.authorize(
        user, workspace_id, "purchase" if direction == "in" else "sales", confirm=save
    )


def clean_fields(fields):
    clean = business_dates.business_fields(fields)
    clean.pop("document_number", None)
    items = []
    for item in clean.get("items") or []:
        name = str(item.get("name") or "").strip()
        if not name:
            raise HTTPException(422, "erp.declaration_required")
        qty = internal_records._decimal(item.get("qty"), positive=True)
        price = internal_records._decimal(item.get("price") or "0")
        items.append(
            {
                **item,
                "name": name,
                "qty": str(qty),
                "price": str(price),
                "subtotal": str((qty * price).quantize(Decimal("0.01"))),
            }
        )
    if not items or len(items) > 500:
        raise HTTPException(422, "erp.declaration_required")
    clean["items"] = items
    clean["total_amount"] = str(sum((Decimal(i["subtotal"]) for i in items), Decimal("0")))
    return clean


def _save(user, *, workspace_id, direction, document_id, fields, attachment=None, paths):
    authorize(user, workspace_id, direction, save=True)
    document_id = str(UUID(str(document_id)))
    clean = clean_fields(fields)
    for key in ("attachment_path", "attachment_name", "attachment_sha"):
        clean.pop(key, None)
    if attachment:
        clean["attachment_name"] = attachment[0]
        clean["attachment_sha"] = hashlib.sha256(attachment[1]).hexdigest()
    input_sha = hashlib.sha256(
        json.dumps(clean, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    tid = str(user["tenant_id"])
    with db.get_cursor_rls(tid, user_id=str(user["id"]), commit=True) as cur:
        internal_records.workspace(cur, user, workspace_id)
        cur.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("stock-save:" + document_id,)
        )
        cur.execute("SELECT * FROM erp_stock_documents WHERE id=%s", (document_id,))
        old = cur.fetchone()
        if old:
            if (
                str(old["tenant_id"]) != tid
                or old["workspace_client_id"] != workspace_id
                or str(old["created_by"]) != str(user["id"])
            ):
                raise HTTPException(404, "erp.not_found")
            if old["direction"] != direction or old["fields"].get("input_sha") != input_sha:
                raise HTTPException(409, "erp.formal_document_locked")
            return public(old)
        cur.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            ("erp-stock:" + tid + ":" + str(workspace_id),),
        )
        from services.erp.item_identity import resolve_items

        resolve_items(cur, tenant_id=tid, workspace_id=workspace_id, items=clean["items"])
        if direction == "out":
            apply_issue_costs(cur, clean, tenant_id=tid, workspace_client_id=workspace_id)
        clean["input_sha"] = input_sha
        number = allocate(cur, tenant_id=tid, direction=direction, business_date=clean["date"])
        clean["document_number"] = number
        if attachment:
            from services.ocr import pdf_storage

            path, _ = pdf_storage.save_bytes(str(user["id"]), attachment[1], ".bin")
            if not path:
                raise HTTPException(503, "erp.attachment_failed")
            paths.append(path)
            clean["attachment_path"] = path
        cur.execute(
            "INSERT INTO erp_stock_documents(id,tenant_id,workspace_client_id,direction,doc_no,doc_date,fields,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING *",
            (
                document_id,
                tid,
                workspace_id,
                direction,
                number,
                business_dates.standard(clean["date"]),
                json.dumps(clean, ensure_ascii=False),
                str(user["id"]),
            ),
        )
        return public(cur.fetchone())


def public(row):
    return {
        "id": str(row["id"]),
        "direction": row["direction"],
        "doc_no": row["doc_no"],
        "fields": {
            k: v for k, v in row["fields"].items() if k not in {"attachment_path", "input_sha"}
        },
    }


def list_documents(user, request, *, workspace_id, direction):
    authorize(user, workspace_id, direction)
    tid = str(user["tenant_id"])
    creator = record_creator_scope(request, user)
    with db.get_cursor_rls(tid, user_id=str(user["id"])) as cur:
        internal_records.workspace(cur, user, workspace_id)
        sql = "SELECT * FROM erp_stock_documents WHERE tenant_id=%s AND workspace_client_id=%s AND direction=%s"
        args = [tid, workspace_id, direction]
        if creator:
            sql += " AND created_by=%s"
            args.append(creator)
        cur.execute(sql + " ORDER BY doc_date DESC,created_at DESC,id DESC", tuple(args))
        docs = [public(r) for r in cur.fetchall()]
        if direction == "out" and docs:
            refresh_issue_values(
                cur, docs, tenant_id=tid, workspace_id=workspace_id, created_by=creator
            )
        return docs


def add_movements(cur, out, *, tenant_id, workspace_client_id, date_to, created_by=None):
    from services.stockcard import grouping
    from services.stockcard.rolling import Movement

    sql = "SELECT * FROM erp_stock_documents WHERE tenant_id=%s AND workspace_client_id=%s AND doc_date<=%s"
    args = [tenant_id, workspace_client_id, date_to]
    if created_by:
        sql += " AND created_by=%s"
        args.append(created_by)
    cur.execute(sql, tuple(args))
    for doc in cur.fetchall():
        for i, item in enumerate(doc["fields"]["items"]):
            key = grouping.group_key(product_id=item.get("product_id"), description=item["name"])
            out.add_movement(
                key,
                Movement(
                    doc["doc_date"],
                    doc["doc_no"],
                    item["name"],
                    doc["direction"],
                    Decimal(item["qty"]),
                    Decimal(item["price"]) if doc["direction"] == "in" else None,
                    (doc["doc_date"], doc["created_at"], i),
                    Decimal(item["subtotal"]) if doc["direction"] == "in" else None,
                ),
            )


def attachment_bytes(user, request, *, workspace_id, direction, document_id):
    authorize(user, workspace_id, direction)
    from services.ocr import pdf_storage

    tid = str(user["tenant_id"])
    creator = record_creator_scope(request, user)
    with db.get_cursor_rls(tid, user_id=str(user["id"])) as cur:
        internal_records.workspace(cur, user, workspace_id)
        cur.execute(
            "SELECT * FROM erp_stock_documents WHERE id=%s AND tenant_id=%s AND workspace_client_id=%s AND direction=%s",
            (str(document_id), tid, workspace_id, direction),
        )
        row = cur.fetchone()
        if not row or (creator and str(row["created_by"]) != str(creator)):
            raise HTTPException(404, "erp.not_found")
        content = pdf_storage.read_bytes(row["fields"].get("attachment_path", ""))
        if content is None:
            raise HTTPException(404, "erp.attachment_not_found")
        return content


def apply_issue_costs(cur, fields, *, tenant_id, workspace_client_id):
    from datetime import date
    from services.stockcard import grouping, report, rolling

    day = date.fromisoformat(business_dates.standard(fields["date"]))
    data, openings = report.load_context(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        date_to=day,
        include_stock_documents=True,
    )
    balances = {}
    for key in set(data.by_key) | set(openings):
        _, bal, _ = report._roll_key(
            data.by_key.get(key, []), openings.get(key), day, day, erp_costs=True
        )
        balances[key] = bal
    values = []
    for item in fields["items"]:
        key = grouping.group_key(product_id=item.get("product_id"), description=item["name"])
        bal = balances.get(key, rolling.ZERO_BALANCE)
        bal, row = rolling.apply_erp(
            bal, rolling.Movement(day, "", "", "out", Decimal(item["qty"]), None, (day,))
        )
        balances[key] = bal
        item["price"] = None if row["unit_price"] is None else str(row["unit_price"])
        item["subtotal"] = None if row["amount"] is None else str(row["amount"])
        values.append(row["amount"])
    fields["total_amount"] = (
        None if any(v is None for v in values) else str(sum(values, Decimal("0")))
    )


def save(user, *, workspace_id, direction, document_id, fields, attachment=None):
    from services.ocr import pdf_storage

    paths = []
    try:
        return _save(
            user,
            workspace_id=workspace_id,
            direction=direction,
            document_id=document_id,
            fields=fields,
            attachment=attachment,
            paths=paths,
        )
    except Exception:
        for path in paths:
            pdf_storage.delete_pdf(path)
        raise


def refresh_issue_values(cur, docs, *, tenant_id, workspace_id, created_by=None):
    """Use the same replay as the report, including later backdated receipts."""
    from datetime import date
    from collections import defaultdict
    from services.stockcard import report, grouping

    groups = report.groups(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_id,
        date_from=date.min,
        date_to=date.max,
        created_by=created_by,
        erp_costs=True,
    )
    values = defaultdict(list)
    for group in groups:
        for row in group["rows"]:
            if row["kind"] == "out":
                values[(row["doc_no"], group["product"]["key"])].append(row)
    for doc in docs:
        amounts = []
        for item in doc["fields"]["items"]:
            key = grouping.group_key(product_id=item.get("product_id"), description=item["name"])
            rows = values[(doc["doc_no"], key)]
            if rows:
                row = rows.pop(0)
                item["price"] = row["unit_price"]
                item["subtotal"] = row["amount"]
            amounts.append(None if item["subtotal"] is None else Decimal(item["subtotal"]))
        doc["fields"]["total_amount"] = (
            None if any(v is None for v in amounts) else str(sum(amounts, Decimal("0")))
        )
