"""Shared automatic product codes for ERP forms, OCR and product maintenance."""


def allocate(cur, tenant_id):
    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("erp-items:" + str(tenant_id),)
    )
    cur.execute(
        "SELECT COALESCE(MAX(substring(code from 3)::bigint),0) AS n FROM products WHERE tenant_id=%s AND code ~ '^P-[0-9]+$'",
        (tenant_id,),
    )
    return "P-" + str(int(cur.fetchone()["n"]) + 1).zfill(6)


def prepare(cur, tenant_id, fields):
    result = dict(fields)
    if not str(result.get("code") or "").strip():
        result["code"] = allocate(cur, tenant_id)
    if result.get("unit") and not result.get("base_unit"):
        result["base_unit"] = result["unit"]
    return result


def guard_change(cur, tenant_id, workspace_id, product_id, fields):
    """Changing a used base unit would reinterpret every historical quantity."""
    from fastapi import HTTPException
    from services.erp.inventory import balances

    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
        ("erp-stock:" + str(tenant_id) + ":" + str(workspace_id),),
    )
    bal = balances(cur, tenant_id, workspace_id).get(str(product_id))
    if bal is None:
        return
    if fields.get("is_active") is False and bal.qty != 0:
        raise HTTPException(409, "sales.product_has_stock")
    if "unit" in fields or "base_unit" in fields:
        cur.execute(
            "SELECT unit,base_unit FROM products WHERE id=%s AND tenant_id=%s AND workspace_client_id=%s",
            (product_id, tenant_id, workspace_id),
        )
        old = cur.fetchone()
        if old and any(
            key in fields and (fields[key] or "") != (old[key] or "")
            for key in ("unit", "base_unit")
        ):
            raise HTTPException(409, "sales.product_unit_locked")
