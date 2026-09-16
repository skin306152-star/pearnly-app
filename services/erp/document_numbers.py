"""Internal business numbers, allocated transactionally per tenant and date."""

from datetime import date

from services.erp.business_dates import standard


def allocate(cur, *, tenant_id, direction, business_date):
    prefix = {"purchase": "PE", "sales": "SI", "in": "IR", "out": "IS"}[direction]
    day = date.fromisoformat(standard(business_date))
    stem = f"{prefix}-{day.year + 543:04d}{day.month:02d}{day.day:02d}-"
    # Native sales numbers are unique per tenant, so numbering must not restart per workspace.
    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (f"erp-number:{tenant_id}:{stem}",)
    )
    table, column = (
        ("purchase_docs", "doc_no")
        if direction == "purchase"
        else ("sales_documents", "doc_number")
    )
    if direction in {"in", "out"}:
        table, column = "erp_stock_documents", "doc_no"
    cur.execute(
        f"SELECT COALESCE(MAX(substring({column} from %s)::bigint), 0) AS serial "
        f"FROM {table} WHERE tenant_id=%s AND {column} ~ %s",
        (len(stem) + 1, tenant_id, "^" + stem + "[0-9]+$"),
    )
    return stem + str(int(cur.fetchone()["serial"]) + 1).zfill(4)
