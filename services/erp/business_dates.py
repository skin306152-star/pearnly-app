"""ERP business dates are Buddhist text; native DATE columns remain calculation dates."""

import re
from datetime import date

from fastapi import HTTPException

KEYS = ("date", "due_date", "delivery_date", "bill_date")


def standard(value):
    text = str(value or "").strip()
    match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:$|[ T])", text)
    if match:
        year, month, day = map(int, match.groups())
    else:
        match = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})(?:$|[ T])", text)
        if not match:
            raise HTTPException(422, detail="history.date_unreadable")
        day, month, year = map(int, match.groups())
    if year >= 2400:
        year -= 543
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        raise HTTPException(422, detail="history.date_unreadable") from None


def buddhist(value):
    year, month, day = standard(value).split("-")
    return f"{day}/{month}/{int(year) + 543}"


def business_fields(fields):
    result = dict(fields)
    for key in KEYS:
        if result.get(key) or key == "date":
            result[key] = buddhist(result.get(key))
    result["date_raw"] = result["date"]
    result["date_calendar"] = "buddhist"
    return result


def calculation_fields(fields):
    result = dict(fields)
    for key in KEYS:
        if result.get(key):
            result[key] = standard(result[key])
    return result


def internal_history(cur, tenant_id, history_id):
    if not history_id:
        return False
    cur.execute(
        "SELECT source FROM ocr_history WHERE id=%s AND tenant_id=%s", (history_id, tenant_id)
    )
    row = cur.fetchone()
    return bool(row and row.get("source") in {"erp_web", "line_erp"})


def export_date(value):
    day, month, year = buddhist(value).split("/")
    return f"{year}-{month}-{day}"
