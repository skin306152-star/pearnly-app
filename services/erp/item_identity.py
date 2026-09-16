"""Exact internal item identity. Fuzzy search never merges stock identities."""

from fastapi import HTTPException


def resolve_items(cur, *, tenant_id, workspace_id, items):
    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("erp-items:" + str(tenant_id),)
    )
    for item in items:
        name = str(item.get("name") or "").strip()
        code = str(item.get("code") or "").strip()
        unit = str(item.get("unit") or "").strip()
        base = "SELECT id,code,unit FROM products WHERE tenant_id=%s AND workspace_client_id=%s AND is_active=TRUE "
        if code:
            cur.execute(base + "AND code=%s", (tenant_id, workspace_id, code))
        else:
            cur.execute(
                base + "AND (name_th=%s OR name_en=%s OR name_zh=%s) AND COALESCE(unit,'')=%s",
                (tenant_id, workspace_id, name, name, name, unit),
            )
        rows = cur.fetchall()
        if len(rows) > 1:
            raise HTTPException(409, "erp.product_ambiguous")
        if rows:
            product = rows[0]
            if code and unit and (product.get("unit") or "") != unit:
                raise HTTPException(409, "erp.product_unit_mismatch")
        else:
            if not code:
                cur.execute(
                    "SELECT COALESCE(MAX(substring(code from 3)::bigint),0) AS n FROM products WHERE tenant_id=%s AND code ~ '^P-[0-9]+$'",
                    (tenant_id,),
                )
                code = "P-" + str(int(cur.fetchone()["n"]) + 1).zfill(6)
            cur.execute(
                "INSERT INTO products(tenant_id,workspace_client_id,code,name_th,unit,base_unit) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id,code,unit",
                (tenant_id, workspace_id, code, name, unit, unit),
            )
            product = cur.fetchone()
        item["product_id"] = str(product["id"])
        item["code"] = product["code"]
        item["unit"] = product.get("unit") or ""


def search(user, workspace_id, query):
    """Scoped suggestions only; selecting a candidate supplies its exact code."""
    from core import db
    from services.erp.internal_records import authorize, workspace
    from services.authz.deps import actor_has_perm

    direction = "purchase" if actor_has_perm(None, user, "purchase.doc.create") else "sales"
    authorize(user, workspace_id, direction)
    query = str(query or "").strip()[:100]
    if not query:
        return []
    with db.get_cursor_rls(
        tenant_id=str(user["tenant_id"]), user_id=str(user["id"]), workspace_client_id=workspace_id
    ) as cur:
        workspace(cur, user, workspace_id)
        cur.execute(
            "SELECT id::text AS product_id,code,name_th,name_en,name_zh,unit FROM products "
            "WHERE tenant_id=%s AND workspace_client_id=%s AND is_active=TRUE "
            "AND (strpos(lower(COALESCE(code,'')),lower(%s))>0 "
            "OR strpos(lower(COALESCE(name_th,'')),lower(%s))>0 "
            "OR strpos(lower(COALESCE(name_en,'')),lower(%s))>0 "
            "OR strpos(lower(COALESCE(name_zh,'')),lower(%s))>0) ORDER BY code LIMIT 20",
            (str(user["tenant_id"]), workspace_id, query, query, query, query),
        )
        return [dict(row) for row in cur.fetchall()]
