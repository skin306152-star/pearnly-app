from __future__ import annotations

from core.pos_api import PosError
from services.inventory import store as inv_store
from services.pos import sales_store, stock


def _shift_is_open(
    cur, *, tenant_id: str, workspace_client_id: int, shift_id: str, for_update: bool = False
) -> bool:
    cur.execute(
        "SELECT status FROM pos_shifts "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s"
        + (" FOR UPDATE" if for_update else ""),
        (tenant_id, workspace_client_id, shift_id),
    )
    row = cur.fetchone()
    return bool(row and row["status"] == "open")


def void_sale(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    sale_id: str,
    created_by=None,
    operator=None,
) -> dict:
    snapshot = sales_store.get_sale(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, sale_id=sale_id
    )
    if not snapshot or snapshot["sale_type"] != "sale":
        raise PosError("pos.void_not_allowed", 409)
    if snapshot.get("shift_id") and not _shift_is_open(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        shift_id=str(snapshot["shift_id"]),
        for_update=True,
    ):
        raise PosError("pos.void_not_allowed", 409)
    sale = sales_store.get_sale(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        sale_id=sale_id,
        for_update=True,
    )
    if not sale or sale["status"] != "completed" or sale["sale_type"] != "sale":
        raise PosError("pos.void_not_allowed", 409)
    locked_lines = sales_store.list_lines(
        cur, tenant_id=tenant_id, sale_id=sale_id, for_update=True
    )
    if sales_store.has_refunds(cur, tenant_id=tenant_id, sale_id=sale_id):
        raise PosError("pos.void_not_allowed", 409)
    warehouse = inv_store.get_or_create_default_warehouse(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    restore_stock = stock.sale_deducted_stock(cur, tenant_id=tenant_id, sale_id=sale_id)
    if restore_stock:
        for line in locked_lines:
            stock.restock(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                warehouse_id=warehouse["id"],
                product_id=str(line["product_id"]),
                batch_id=str(line["batch_id"]) if line["batch_id"] else None,
                qty_base=line["qty_base"],
                ref_type="pos_void",
                ref_id=sale_id,
                txn_type="adjust",
                created_by=created_by,
            )
    if not sales_store.set_status(
        cur,
        tenant_id=tenant_id,
        sale_id=sale_id,
        status="void",
        expected_status="completed",
    ):
        raise PosError("pos.void_not_allowed", 409)
    if operator is not None:
        from services.pos import approval

        approval.log_void_operator(tenant_id=tenant_id, sale_id=sale_id, operator=operator)
    return {"sale_id": sale_id, "status": "void", "stock_returned": restore_stock}
