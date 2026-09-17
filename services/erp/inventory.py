"""POS inventory presentation backed by the ERP document journal.

No second stock balance is written: receipts, issues, purchases and sales are
replayed by the same stockcard engine used by the report and issue costing.
"""

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
from uuid import uuid4
import json

from fastapi import HTTPException
from services.erp import business_dates, document_numbers, internal_records
from services.stockcard import report, grouping, rolling


def balances(cur, tenant_id, workspace_id, *, created_by=None):
    data, openings = report.load_context(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_id,
        date_to=date.max,
        created_by=created_by,
        include_stock_documents=True,
    )
    return {
        grouping.key_product_id(key): report._roll_key(
            data.by_key.get(key, []), openings.get(key), date.min, date.max, erp_costs=True
        )[1]
        for key in set(data.by_key) | set(openings)
        if grouping.is_product_key(key)
    }


def overview(cur, *, tenant_id, workspace_id, query="", mask_cost=False, created_by=None):
    stock = balances(cur, tenant_id, workspace_id, created_by=created_by)
    cur.execute(
        "SELECT * FROM products WHERE tenant_id=%s AND workspace_client_id=%s "
        "AND is_active=TRUE ORDER BY code,name_th,id",
        (tenant_id, workspace_id),
    )
    items, values = [], []
    needle = (query or "").strip().casefold()
    for p in cur.fetchall():
        if needle and not any(
            needle in str(p.get(k) or "").casefold()
            for k in ("code", "barcode", "name_th", "name_en", "name_zh")
        ):
            continue
        bal = stock.get(str(p["id"]), rolling.ZERO_BALANCE)
        status = (
            "out"
            if bal.qty <= 0
            else "low" if p["min_stock"] is not None and bal.qty < p["min_stock"] else "ok"
        )
        values.append(bal.value if bal.qty else Decimal("0"))
        items.append(
            {
                "product_id": str(p["id"]),
                "code": p["code"],
                "name": {k: p.get("name_" + k) for k in ("th", "en", "zh")},
                "image_url": p["image_url"],
                "barcode": p["barcode"],
                "base_unit": p["unit"] or p["base_unit"],
                "qty_on_hand": str(bal.qty),
                "min_stock": None if p["min_stock"] is None else str(p["min_stock"]),
                "avg_cost": None if mask_cost or bal.unit is None else str(bal.unit),
                "status": status,
                "track_batch": bool(p["track_batch"]),
                "batches": [],
            }
        )
    return {
        "items": items,
        "cost_visible": not mask_cost,
        "summary": {
            "sku_count": sum(Decimal(i["qty_on_hand"]) != 0 for i in items),
            "stock_value": (
                None
                if mask_cost or any(v is None for v in values)
                else str(sum(values, Decimal("0")))
            ),
            "low_count": sum(i["status"] == "low" for i in items),
            "out_count": sum(i["status"] == "out" for i in items),
        },
    }


def count(cur, user, workspace_id, lines, *, request_id=None):
    """An absolute physical count posts only its variance, under the stock lock.

    Retrying the same target count without an intervening movement is a no-op.
    Original quantity and counted quantity remain in the saved document audit.
    """
    tid = str(user["tenant_id"])
    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
        ("erp-stock:" + tid + ":" + str(workspace_id),),
    )
    if request_id:
        cur.execute(
            "SELECT doc_no FROM erp_stock_documents WHERE tenant_id=%s AND workspace_client_id=%s AND fields->>'count_request_id'=%s",
            (tid, workspace_id, request_id),
        )
        existing = cur.fetchall()
        if existing:
            return {"documents": [row["doc_no"] for row in existing]}
    stock = balances(cur, tid, workspace_id)
    seen, docs = set(), []
    day = datetime.now(ZoneInfo("Asia/Bangkok")).date()
    for line in lines:
        pid = str(line["product_id"])
        if pid in seen or line.get("batch_id"):
            raise HTTPException(422, "erp.invalid_document")
        seen.add(pid)
        cur.execute(
            "SELECT * FROM products WHERE id::text=%s AND tenant_id=%s AND workspace_client_id=%s AND is_active=TRUE",
            (pid, tid, workspace_id),
        )
        p = cur.fetchone()
        if not p:
            raise HTTPException(404, "erp.product_not_found")
        target = internal_records._decimal(line["counted_qty"])
        bal = stock.get(pid, rolling.ZERO_BALANCE)
        delta = target - bal.qty
        if not delta:
            continue
        direction = "in" if delta > 0 else "out"
        qty = abs(delta)
        _, movement = rolling.apply_erp(
            bal, rolling.Movement(day, "", "", direction, qty, None, (day,))
        )
        number = document_numbers.allocate(
            cur, tenant_id=tid, direction=direction, business_date=day
        )
        item = {
            "product_id": pid,
            "code": p["code"],
            "name": p["name_th"],
            "unit": p["unit"] or p["base_unit"] or "",
            "qty": str(qty),
            "price": None if movement["unit_price"] is None else str(movement["unit_price"]),
            "subtotal": None if movement["amount"] is None else str(movement["amount"]),
        }
        fields = {
            "date": business_dates.buddhist(day),
            "document_number": number,
            "source": "inventory_count",
            "count_request_id": request_id,
            "before_qty": str(bal.qty),
            "counted_qty": str(target),
            "items": [item],
            "total_amount": item["subtotal"],
        }
        cur.execute(
            "INSERT INTO erp_stock_documents(id,tenant_id,workspace_client_id,direction,doc_no,doc_date,fields,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s)",
            (
                str(uuid4()),
                tid,
                workspace_id,
                direction,
                number,
                day,
                json.dumps(fields),
                str(user["id"]),
            ),
        )
        docs.append(number)
    return {"documents": docs}
