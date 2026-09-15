"""Idempotent count entries, correction audit, and per-product totals."""

from fastapi import HTTPException
from psycopg2.extras import Json

from services.stocktake import store, photos
from services.stocktake.excel import quantity as validate_quantity


def fetch(cur, scope, task_id, limit=100, offset=0):
    cur.execute(
        """SELECT e.*, i.product_code, i.product_name, i.barcode, i.unit,
        (SELECT COUNT(*) FROM cowork_stocktake_photos p WHERE p.entry_id=e.id
         AND p.tenant_id=e.tenant_id AND p.workspace_client_id=e.workspace_client_id) AS photo_count,
        COALESCE(NULLIF(u.full_name,''), u.username, u.id::text) AS counted_by_name,
        COALESCE(NULLIF(m.full_name,''), m.username, m.id::text) AS updated_by_name
        FROM cowork_stocktake_entries e JOIN cowork_stocktake_items i ON i.id=e.item_id
        JOIN users u ON u.id=e.counted_by JOIN users m ON m.id=e.updated_by
        WHERE e.stocktake_id=%s AND e.tenant_id=%s AND e.workspace_client_id=%s
        ORDER BY e.counted_at DESC, e.id""" + (" LIMIT %s OFFSET %s" if limit else ""),
        (
            str(task_id),
            scope.tenant_id,
            scope.workspace_client_id,
            *([limit, offset] if limit else []),
        ),
    )
    return [dict(row) for row in cur.fetchall()]


def total(cur, scope, task_id):
    cur.execute(
        "SELECT COUNT(*) AS total FROM cowork_stocktake_entries WHERE stocktake_id=%s "
        "AND tenant_id=%s AND workspace_client_id=%s",
        (str(task_id), scope.tenant_id, scope.workspace_client_id),
    )
    return cur.fetchone()["total"]


def listing(scope, task_id, limit, offset):
    with store.cursor(scope) as cur:
        store._task(cur, scope, task_id, lock=True)
        return {
            "entries": fetch(cur, scope, task_id, limit, offset),
            "total": total(cur, scope, task_id),
        }


def _state(row):
    return {
        key: str(row[key]) if key == "quantity" else row[key]
        for key in ("warehouse", "location", "quantity", "voided")
    }


def _replay(cur, scope, request_id, request):
    cur.execute(
        "SELECT * FROM cowork_stocktake_entry_events WHERE operation_id=%s "
        "AND tenant_id=%s AND workspace_client_id=%s",
        (str(request_id), scope.tenant_id, scope.workspace_client_id),
    )
    event = cur.fetchone()
    if not event:
        return None
    if event["request"] != request:
        raise HTTPException(409, detail="stocktake.operation_conflict")
    return {"ok": True, "entry_id": str(event["entry_id"]), "version": event["version"]}


def _audit(cur, scope, request_id, entry_id, version, request, previous, current):
    cur.execute(
        "INSERT INTO cowork_stocktake_entry_events "
        "(operation_id,entry_id,tenant_id,workspace_client_id,version,request,previous,current,actor_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (operation_id) DO NOTHING RETURNING operation_id",
        (
            str(request_id),
            str(entry_id),
            scope.tenant_id,
            scope.workspace_client_id,
            version,
            Json(request),
            Json(previous) if previous else None,
            Json(current),
            scope.user_id,
        ),
    )
    if not cur.fetchone():
        raise HTTPException(409, detail="stocktake.operation_conflict")


def _total(cur, scope, item_id):
    cur.execute(
        "SELECT SUM(quantity) AS total FROM cowork_stocktake_entries "
        "WHERE item_id=%s AND tenant_id=%s AND workspace_client_id=%s AND NOT voided",
        (str(item_id), scope.tenant_id, scope.workspace_client_id),
    )
    total = cur.fetchone()["total"]
    if total is not None:
        validate_quantity(total, nonnegative=True)
    cur.execute(
        "UPDATE cowork_stocktake_items SET actual_qty=%s, version=version+1, "
        "counted_by=%s, counted_at=NOW() WHERE id=%s AND tenant_id=%s AND workspace_client_id=%s",
        (total, scope.user_id, str(item_id), scope.tenant_id, scope.workspace_client_id),
    )


def write(
    scope,
    task_id,
    target_id,
    request_id,
    qty,
    warehouse,
    location,
    *,
    version=None,
    voided=False,
    photo_values=(),
):
    warehouse, location = warehouse.strip(), location.strip()
    if not warehouse or len(warehouse) > 300 or len(location) > 300:
        raise HTTPException(422, detail="stocktake.warehouse_required")
    qty = validate_quantity(qty, nonnegative=True)
    images = photos.prepare(photo_values)
    request = {
        "task_id": str(task_id),
        "target_id": str(target_id),
        "version": version,
        "quantity": format(qty, ".6f"),
        "warehouse": warehouse,
        "location": location,
        "voided": voided,
        "actor_id": scope.user_id,
    }
    if images:
        request["photos"] = [digest for _, digest in images]
    with store.cursor(scope, commit=True) as cur:
        task = store._task(cur, scope, task_id, lock=True)
        if task["count_mode"] != "scan":
            raise HTTPException(409, detail="stocktake.legacy_task")
        receipt = _replay(cur, scope, request_id, request)
        if receipt:
            return receipt
        if task["status"] != "active":
            raise HTTPException(409, detail="stocktake.closed")
        current = {
            "warehouse": warehouse,
            "location": location,
            "quantity": str(qty),
            "voided": voided,
        }
        previous = None
        if version is None:
            entry_id, item_id, next_version = request_id, target_id, 0
            cur.execute(
                "SELECT id FROM cowork_stocktake_items WHERE id=%s AND stocktake_id=%s "
                "AND tenant_id=%s AND workspace_client_id=%s",
                (str(item_id), str(task_id), scope.tenant_id, scope.workspace_client_id),
            )
            if not cur.fetchone():
                raise HTTPException(404, detail="stocktake.not_found")
            cur.execute(
                "INSERT INTO cowork_stocktake_entries "
                "(id,stocktake_id,item_id,tenant_id,workspace_client_id,warehouse,location,quantity,counted_by,updated_by) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING RETURNING id",
                (
                    str(entry_id),
                    str(task_id),
                    str(item_id),
                    scope.tenant_id,
                    scope.workspace_client_id,
                    warehouse,
                    location,
                    qty,
                    scope.user_id,
                    scope.user_id,
                ),
            )
            if not cur.fetchone():
                raise HTTPException(409, detail="stocktake.operation_conflict")
        else:
            entry_id = target_id
            cur.execute(
                "SELECT * FROM cowork_stocktake_entries WHERE id=%s AND stocktake_id=%s "
                "AND tenant_id=%s AND workspace_client_id=%s FOR UPDATE",
                (str(entry_id), str(task_id), scope.tenant_id, scope.workspace_client_id),
            )
            old = cur.fetchone()
            if not old:
                raise HTTPException(404, detail="stocktake.not_found")
            if old["version"] != version:
                raise HTTPException(409, detail="stocktake.conflict")
            previous, item_id, next_version = _state(old), old["item_id"], version + 1
            cur.execute(
                "UPDATE cowork_stocktake_entries SET warehouse=%s, location=%s, quantity=%s, "
                "voided=%s, version=version+1, updated_by=%s, updated_at=NOW() WHERE id=%s",
                (warehouse, location, qty, voided, scope.user_id, str(entry_id)),
            )
        photos.save(cur, scope, entry_id, images)
        _audit(cur, scope, request_id, entry_id, next_version, request, previous, current)
        _total(cur, scope, item_id)
        return {"ok": True, "entry_id": str(entry_id), "version": next_version}
