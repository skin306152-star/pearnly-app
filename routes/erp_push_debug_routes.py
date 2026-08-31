"""Download the diagnostic workbook stored on an ERP push log."""

from __future__ import annotations

import base64
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _tid
from routes.erp_routes_access import _check_push_access
from services.auth.entrance import require_erp_portal
from services.erp import team_access

router = APIRouter()


@router.get("/api/erp/logs/{log_id}/debug-xlsx")
async def erp_log_debug_xlsx(log_id: str, request: Request):
    user = get_current_user_from_request(request)
    require_erp_portal(user)
    _check_push_access(user)
    creator = team_access.record_creator_scope(request, user)
    user_filter = "AND pl.user_id = %s" if creator else ""
    params = (log_id, creator) if creator else (log_id,)
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT pl.id, pl.user_id, pl.history_id, pl.request_body, pl.invoice_no,
                       u.tenant_id::text AS tid
                FROM push_logs pl
                LEFT JOIN users u ON u.id = pl.user_id
                WHERE pl.id = %s
                """ + user_filter + " LIMIT 1",
                params,
            )
            row = cur.fetchone()
    except Exception as exc:
        raise HTTPException(500, detail=f"db.error:{exc}") from exc
    if not row:
        raise HTTPException(404, detail="log.not_found")
    if str(row.get("tid") or "") != str(_tid(user) or ""):
        raise HTTPException(403, detail="log.cross_tenant")
    request_body = row.get("request_body") or {}
    if isinstance(request_body, str):
        try:
            request_body = json.loads(request_body)
        except (TypeError, ValueError):
            request_body = {}
    encoded = request_body.get("_debug_xlsx_b64") if isinstance(request_body, dict) else None
    if not encoded:
        raise HTTPException(404, detail="log.no_debug_xlsx")
    try:
        xlsx = base64.b64decode(encoded)
    except (TypeError, ValueError):
        raise HTTPException(500, detail="log.decode_failed") from None
    safe_invoice = (row.get("invoice_no") or "unknown").replace("/", "_").replace(" ", "_")[:40]
    filename = f"pearnly_debug_{safe_invoice}_{log_id[:8]}.xlsx"
    return Response(
        content=xlsx,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
