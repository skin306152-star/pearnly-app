"""Replay-safe internal ERP metadata upgrade, run only by the serial schema job.

Original rows are retained in a tenant-isolated backup table. Native quantities,
amounts and calculation dates are never rewritten. Cowork histories are excluded.
"""

import json
import re
from core import db
from core.rls import apply_tenant_rls
from services.erp.business_dates import business_fields
from services.erp.document_numbers import allocate
from services.erp.item_identity import resolve_items


def backup(cur, tenant, kind, key, value):
    cur.execute(
        "INSERT INTO erp_history_upgrade_backups(tenant_id,kind,row_id,payload) "
        "VALUES(%s,%s,%s,%s::jsonb) ON CONFLICT DO NOTHING",
        (tenant, kind, str(key), json.dumps(value, default=str, ensure_ascii=False)),
    )


def upgrade(cur, tenant_id=None):
    cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('erp-history-upgrade-v1',0))")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS erp_history_upgrade_backups ("
        "tenant_id uuid NOT NULL,kind text NOT NULL,row_id text NOT NULL,payload jsonb NOT NULL,"
        "created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(tenant_id,kind,row_id))"
    )
    apply_tenant_rls(cur, "erp_history_upgrade_backups")
    cur.execute(
        "SELECT * FROM ocr_history WHERE source IN ('erp_web','line_erp') "
        "AND (%s::uuid IS NULL OR tenant_id=%s::uuid) ORDER BY created_at,id FOR UPDATE",
        (tenant_id, tenant_id),
    )
    histories = cur.fetchall()
    identities = {}
    for history in histories:
        tid, wid = history["tenant_id"], history["workspace_client_id"]
        if not wid:
            continue
        backup(cur, tid, "ocr_history", history["id"], history)
        pages = history.get("pages") or []
        if not pages:
            continue
        for page in pages:
            fields = page.get("fields") or {}
            if fields.get("date"):
                page["fields"] = business_fields(fields)
        fields = pages[0].get("fields") or {}
        fields.setdefault("bill_number", fields.get("invoice_number") or "")
        for table, number, direction, line_table, fk in (
            ("purchase_docs", "doc_no", "purchase", "purchase_lines", "purchase_doc_id"),
            ("sales_documents", "doc_number", "sales", "sales_document_lines", "document_id"),
        ):
            cur.execute(
                f"SELECT * FROM {table} WHERE tenant_id=%s AND ocr_history_id=%s FOR UPDATE",
                (tid, history["id"]),
            )
            for doc in cur.fetchall():
                backup(cur, tid, table, doc["id"], doc)
                business_number = doc[number] or ""
                if not re.fullmatch(r"(?:PE|SI)-\d{8}-\d{4,}", business_number):
                    business_number = allocate(
                        cur,
                        tenant_id=tid,
                        direction=direction,
                        business_date=doc.get("doc_date") or doc.get("issue_date"),
                    )
                    cur.execute(
                        f"UPDATE {table} SET {number}=%s WHERE id=%s AND tenant_id=%s",
                        (business_number, doc["id"], tid),
                    )
                fields["document_number"] = business_number
                items = fields.get("items") or []
                cur.execute(
                    f"SELECT * FROM {line_table} WHERE tenant_id=%s AND {fk}=%s ORDER BY line_no FOR UPDATE",
                    (tid, doc["id"]),
                )
                lines = cur.fetchall()
                if len(lines) != len(items):
                    raise RuntimeError("ERP history upgrade: native line count mismatch")
                for line, item in zip(lines, items):
                    backup(cur, tid, line_table, line["id"], line)
                    if line.get("product_id"):
                        cur.execute(
                            "SELECT id,code,unit FROM products WHERE id=%s AND tenant_id=%s AND workspace_client_id=%s",
                            (line["product_id"], tid, wid),
                        )
                        product = cur.fetchone()
                        if not product:
                            raise RuntimeError("ERP history upgrade: product scope mismatch")
                        item.update(
                            product_id=str(product["id"]),
                            code=product["code"],
                            unit=product["unit"] or "",
                        )
                    else:
                        resolve_items(cur, tenant_id=tid, workspace_id=wid, items=[item])
                        cur.execute(
                            f"UPDATE {line_table} SET product_id=%s WHERE id=%s AND tenant_id=%s",
                            (item["product_id"], line["id"], tid),
                        )
                    identities.setdefault(
                        (str(tid), wid, str(item.get("name") or "").strip()), set()
                    ).add(item["product_id"])
        cur.execute(
            "UPDATE ocr_history SET pages=%s::jsonb WHERE tenant_id=%s AND id=%s",
            (json.dumps(pages, default=str, ensure_ascii=False), tid, history["id"]),
        )
    for (tid, wid, name), products in identities.items():
        cur.execute(
            "SELECT * FROM stock_card_openings WHERE tenant_id=%s AND workspace_client_id=%s AND name_key=%s FOR UPDATE",
            (tid, wid, name),
        )
        opening = cur.fetchone()
        if not opening:
            continue
        if len(products) != 1:
            raise RuntimeError("ERP history upgrade: ambiguous opening identity")
        product_id = next(iter(products))
        cur.execute(
            "SELECT 1 FROM stock_card_openings WHERE tenant_id=%s AND workspace_client_id=%s AND product_id=%s",
            (tid, wid, product_id),
        )
        if cur.fetchone():
            raise RuntimeError("ERP history upgrade: conflicting opening identities")
        backup(cur, tid, "stock_card_openings", opening["id"], opening)
        cur.execute(
            "UPDATE stock_card_openings SET product_id=%s,name_key=NULL WHERE tenant_id=%s AND id=%s",
            (product_id, tid, opening["id"]),
        )
    return len(histories)


def migrate():
    with db.get_cursor_rls(bypass=True, commit=True) as cur:
        return upgrade(cur)
