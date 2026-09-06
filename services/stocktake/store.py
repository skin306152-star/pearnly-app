"""Scoped stocktake snapshots and serialized count/close transactions."""

from uuid import uuid4

from fastapi import HTTPException
from psycopg2.extras import execute_values

from core import db
from core.workspace_context import assert_scope
from services.stocktake.excel import FIELDS


def cursor(scope, *, commit=False):
    return db.get_cursor_rls(
        tenant_id=scope.tenant_id,
        workspace_client_id=scope.workspace_client_id,
        user_id=scope.user_id,
        commit=commit,
    )


def _task(cur, scope, task_id, *, lock=False):
    assert_scope(cur, scope)
    cur.execute(
        "SELECT * FROM cowork_stocktakes WHERE id=%s AND tenant_id=%s "
        "AND workspace_client_id=%s" + (" FOR UPDATE" if lock else ""),
        (str(task_id), scope.tenant_id, scope.workspace_client_id),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, detail="stocktake.not_found")
    return dict(row)


def create(scope, name, items, request_id, source_digest):
    task_id = str(request_id)
    with cursor(scope, commit=True) as cur:
        assert_scope(cur, scope)
        cur.execute(
            "INSERT INTO cowork_stocktakes "
            "(id, tenant_id, workspace_client_id, name, created_by, source_digest) "
            "VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING RETURNING id",
            (
                task_id,
                scope.tenant_id,
                scope.workspace_client_id,
                name,
                scope.user_id,
                source_digest,
            ),
        )
        if not cur.fetchone():
            existing = _task(cur, scope, task_id)
            if existing["name"] != name or existing["source_digest"] != source_digest:
                raise HTTPException(409, detail="stocktake.import_conflict")
            return {"id": task_id}
        execute_values(
            cur,
            "INSERT INTO cowork_stocktake_items "
            "(id,stocktake_id,tenant_id,workspace_client_id," + ",".join(FIELDS) + ") VALUES %s",
            [
                (
                    str(uuid4()),
                    task_id,
                    scope.tenant_id,
                    scope.workspace_client_id,
                    *(item[k] for k in FIELDS),
                )
                for item in items
            ],
        )
    return {"id": task_id}


def listing(scope):
    with cursor(scope) as cur:
        assert_scope(cur, scope)
        cur.execute(
            """SELECT s.*, COUNT(i.id) AS total,
            COUNT(i.actual_qty) AS counted,
            COUNT(*) FILTER (WHERE i.actual_qty <> i.book_qty) AS differences
            FROM cowork_stocktakes s LEFT JOIN cowork_stocktake_items i ON i.stocktake_id=s.id
            WHERE s.tenant_id=%s AND s.workspace_client_id=%s
            GROUP BY s.id ORDER BY s.created_at DESC""",
            (scope.tenant_id, scope.workspace_client_id),
        )
        return {"tasks": [dict(row) for row in cur.fetchall()]}


def detail(scope, task_id):
    with cursor(scope) as cur:
        task = _task(cur, scope, task_id)
        cur.execute(
            "SELECT *, actual_qty - book_qty AS difference FROM cowork_stocktake_items "
            "WHERE stocktake_id=%s AND tenant_id=%s AND workspace_client_id=%s "
            "ORDER BY product_code, warehouse, location",
            (str(task_id), scope.tenant_id, scope.workspace_client_id),
        )
        task["items"] = [dict(row) for row in cur.fetchall()]
        return task


def count(scope, task_id, item_id, qty, version):
    with cursor(scope, commit=True) as cur:
        task = _task(cur, scope, task_id, lock=True)
        if task["status"] != "active":
            raise HTTPException(409, detail="stocktake.closed")
        cur.execute(
            "SELECT * FROM cowork_stocktake_items WHERE id=%s AND stocktake_id=%s "
            "AND tenant_id=%s AND workspace_client_id=%s FOR UPDATE",
            (str(item_id), str(task_id), scope.tenant_id, scope.workspace_client_id),
        )
        old = cur.fetchone()
        if not old:
            raise HTTPException(404, detail="stocktake.not_found")
        if old["version"] != version:
            if (
                old["version"] == version + 1
                and old["actual_qty"] == qty
                and str(old["counted_by"]) == scope.user_id
            ):
                return {"ok": True, "version": old["version"]}
            raise HTTPException(409, detail="stocktake.conflict")
        cur.execute(
            "UPDATE cowork_stocktake_items SET actual_qty=%s, version=version+1, "
            "counted_by=%s, counted_at=NOW() WHERE id=%s",
            (qty, scope.user_id, str(item_id)),
        )
        cur.execute(
            "INSERT INTO cowork_stocktake_counts "
            "(tenant_id,workspace_client_id,item_id,previous_qty,actual_qty,version,counted_by) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                scope.tenant_id,
                scope.workspace_client_id,
                str(item_id),
                old["actual_qty"],
                qty,
                version + 1,
                scope.user_id,
            ),
        )
        return {"ok": True, "version": version + 1}


def close(scope, task_id):
    with cursor(scope, commit=True) as cur:
        task = _task(cur, scope, task_id, lock=True)
        if task["status"] == "active":
            cur.execute(
                "UPDATE cowork_stocktakes SET status='closed', closed_at=NOW(), "
                "closed_by=%s WHERE id=%s",
                (scope.user_id, str(task_id)),
            )
        return {"ok": True}
