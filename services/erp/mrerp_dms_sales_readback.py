# -*- coding: utf-8 -*-
"""Fresh sales and booking readback from an operator's MR.ERP DMS session."""

from __future__ import annotations

import html
import json
import logging
import re
from datetime import date
from typing import Any, Dict, Iterable, List, Optional

from services.erp.erp_dms_intake import _run_logged_in
from services.erp.mrerp_dms_client_base import DMSClientError

logger = logging.getLogger(__name__)

LIST_PATH = "drfcbc/component/showdata.php"
TOP_SALES_PATH = "home/component/carmaxsellchart.php"

SEARCH_COLUMNS = {
    "booking_no": "1",
    "booking_date": "2",
    "delivery_date": "3",
    "advisor": "4",
    "customer": "5",
    "vehicle": "6",
    "color": "7",
    "finance_status": "8",
    "allocation_status": "9",
    "sales_doc_no": "10",
    "engine_no": "11",
}

STATUS_FILTERS = {
    "all": "1",
    "cancelled": "2",
    "active": "3",
    "draft": "4",
    "booking": "5",
    "cash": "6",
    "finance_pending": "7",
    "finance_approved": "8",
    "manager_pending": "9",
    "ready": "10",
    "unallocated": "11",
    "allocated_no_contract": "12",
    "contract_opened": "13",
    "contract_not_opened": "14",
    "delivery_overdue": "15",
}

TOP_GROUPS = {"model": "1", "type": "2", "subtype": "3"}
TOP_METRICS = {"quantity": "1", "amount": "2"}

_ROW_RE = re.compile(r'data-val="([^"]+)"', re.I)
_CELL_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.S | re.I)


def _text(raw: str) -> str:
    value = html.unescape(re.sub(r"<.*?>", "", raw or "")).strip()
    return "" if value == "-" else " ".join(value.split())


def parse_sales_rows(body: str) -> List[Dict[str, str]]:
    """Parse the native DMS booking/sales-progress list without changing status meaning."""
    source = body or ""
    marks = list(_ROW_RE.finditer(source))
    rows: List[Dict[str, str]] = []
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(source)
        cells = [_text(value) for value in _CELL_RE.findall(source[mark.end() : end])]
        if len(cells) < 13 or not cells[2]:
            continue
        rows.append(
            {
                "id": mark.group(1),
                "cancel_status": cells[0],
                "record_status": cells[1],
                "booking_no": cells[2],
                "booking_date": cells[3],
                "delivery_date": cells[4],
                "advisor": cells[5],
                "customer": cells[6],
                "vehicle": cells[7],
                "color": cells[8],
                "finance_status": cells[9],
                "allocation_status": cells[10],
                "sales_doc_no": cells[11],
                "engine_no": cells[12],
            }
        )
    return rows


def _enabled_endpoint(user_id: str) -> Optional[dict]:
    from core import db

    for endpoint in db.list_erp_endpoints(str(user_id)) or []:
        if (endpoint.get("adapter") or "").strip().lower() != "mrerp_dms":
            continue
        if endpoint.get("enabled") is False:
            continue
        return endpoint
    return None


def fetch_sales_records(
    user_id: str,
    *,
    field: str = "booking_no",
    query: str = "",
    status: str = "active",
    limit: int = 10,
    page: int = 1,
) -> Dict[str, Any]:
    """Log in and read one live page. No cookies or results are retained between calls."""
    try:
        endpoint = _enabled_endpoint(user_id)
    except Exception:
        logger.exception("DMS sales endpoint lookup failed")
        return {"ok": False, "error_code": "ERR_UNEXPECTED"}
    if not endpoint:
        return {"ok": False, "error_code": "ERR_NO_CREDS"}
    column = SEARCH_COLUMNS.get(field, SEARCH_COLUMNS["booking_no"])
    filter_code = STATUS_FILTERS.get(status, STATUS_FILTERS["active"])
    size = min(max(int(limit or 10), 1), 30)
    page_no = max(int(page or 1), 1)

    def _read(client, _adapter):
        body = client._post_text(
            LIST_PATH,
            {
                "sdtamt": str(size),
                "sdtpage": str(page_no),
                "sd": str(query or "").strip(),
                "ftd": filter_code,
                "selcolsort": column,
                "selcolsorttype": "2",
            },
        )
        if (body or "").lstrip().startswith("err::"):
            raise DMSClientError(body[:200], "ERR_DMS_TECHNICAL")
        rows = parse_sales_rows(body)
        return {
            "ok": True,
            "kind": "sales_records",
            "source": "mrerp_dms_live",
            "field": field,
            "query": str(query or "").strip(),
            "status": status,
            "page": page_no,
            "limit": size,
            "has_more": len(rows) == size,
            "rows": rows,
        }

    return _run_logged_in(endpoint, _read)


def _tag(source: str, tag: str, element_id: str) -> str:
    match = re.search(
        rf"<{tag}[^>]+id=[\"']{re.escape(element_id)}[\"'][^>]*>.*?</{tag}>",
        source,
        re.S | re.I,
    )
    return match.group(0) if match else ""


def _options(source: str, element_id: str) -> List[Dict[str, str]]:
    block = _tag(source, "select", element_id)
    rows = []
    for value, attrs, label in re.findall(
        r"<option[^>]*value=[\"']([^\"']*)[\"']([^>]*)>(.*?)</option>",
        block,
        re.S | re.I,
    ):
        rows.append(
            {
                "id": value.strip(),
                "name": _text(label),
                "selected": "selected" in attrs.lower(),
            }
        )
    return rows


def _input_value(source: str, element_id: str) -> str:
    match = re.search(rf"<input[^>]+id=[\"']{re.escape(element_id)}[\"'][^>]*>", source, re.I)
    if not match:
        return ""
    value = re.search(r"value=[\"']([^\"']*)[\"']", match.group(0), re.I)
    return html.unescape(value.group(1)).strip() if value else ""


def _concrete_ids(rows: Iterable[Dict[str, str]]) -> str:
    values = [row["id"] for row in rows if row.get("id") and row.get("id") != "0"]
    return ",".join(dict.fromkeys(values))


def _period_default() -> tuple[str, str]:
    today = date.today()
    year_be = today.year + 543
    return f"01/{today.month:02d}/{year_be}", f"{today.day:02d}/{today.month:02d}/{year_be}"


def fetch_top_sales(
    user_id: str,
    *,
    group: str = "model",
    metric: str = "quantity",
    date_from: str = "",
    date_to: str = "",
    limit: int = 10,
    page: int = 1,
) -> Dict[str, Any]:
    """Read the native highest-sales dashboard for all branches and teams visible to the login."""
    try:
        endpoint = _enabled_endpoint(user_id)
    except Exception:
        logger.exception("DMS highest-sales endpoint lookup failed")
        return {"ok": False, "error_code": "ERR_UNEXPECTED"}
    if not endpoint:
        return {"ok": False, "error_code": "ERR_NO_CREDS"}
    group_code = TOP_GROUPS.get(group, TOP_GROUPS["model"])
    metric_code = TOP_METRICS.get(metric, TOP_METRICS["quantity"])
    size = min(max(int(limit or 10), 1), 30)
    page_no = max(int(page or 1), 1)
    default_from, default_to = _period_default()

    def _read(client, adapter):
        home = adapter._transport().get(adapter.base_url + "home/home.php").text
        user_id_value = _input_value(home, "idusers")
        branches = _options(home, "carmaxsellbranch")
        teams = _options(home, "carmaxsellteam")
        branch_ids = _concrete_ids(branches)
        team_ids = _concrete_ids(teams)
        if not user_id_value or not branch_ids or not team_ids:
            raise DMSClientError("highest-sales dashboard filters unavailable")
        payload = {
            "idusers": user_id_value,
            "carmaxselltypedata": group_code,
            "carmaxsellbranch": branch_ids,
            "carmaxsellteam": team_ids,
            "txtcarmaxselldate_bg": date_from or default_from,
            "txtcarmaxselldate_to": date_to or default_to,
            "carmaxsellqnt": metric_code,
            "carmaxsellshow": str(size),
            "carmaxsellpage": str(page_no),
        }
        count_body = client._post_text(TOP_SALES_PATH, {**payload, "status": "all"})
        if (count_body or "").lstrip().startswith("err::"):
            raise DMSClientError(count_body[:200])
        page_body = client._post_text(TOP_SALES_PATH, {**payload, "status": "page"})
        try:
            labels, _ids, values = json.loads(page_body)
        except (TypeError, ValueError) as exc:
            raise DMSClientError("highest-sales response is not valid JSON") from exc
        total = int(str(count_body).strip() or 0)
        rows = [
            {"label": str(label), "value": value}
            for label, value in zip(labels or [], values or [])
        ]
        return {
            "ok": True,
            "kind": "top_sales",
            "source": "mrerp_dms_live",
            "group": group,
            "metric": metric,
            "date_from": payload["txtcarmaxselldate_bg"],
            "date_to": payload["txtcarmaxselldate_to"],
            "branches": [row["name"] for row in branches if row.get("id") != "0"],
            "teams": [row["name"] for row in teams if row.get("id") != "0"],
            "page": page_no,
            "limit": size,
            "total": total,
            "has_more": page_no * size < total,
            "rows": rows,
        }

    return _run_logged_in(endpoint, _read)


__all__ = [
    "SEARCH_COLUMNS",
    "STATUS_FILTERS",
    "fetch_sales_records",
    "fetch_top_sales",
    "parse_sales_rows",
]
