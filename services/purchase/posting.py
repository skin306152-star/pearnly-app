# -*- coding: utf-8 -*-
"""进项单据状态机 · 入账/记付款/作废 + 库存联动(商户采购 · docs/purchasing/02 §1)。

post:draft→posted;进货入库开 → 按行 product_id 写 inventory(ref_type=purchase)。
pay:累计 paid_amount + 派生 payment_status(部分付款);超未付余额拦。
void:posted→void;已入库则逐笔取负回冲(精确反转 receive 写入的 base 量,含批次)。
隔离=每句 WHERE tenant_id(+ workspace_client_id);钱 Decimal。调用方管事务。
"""

from __future__ import annotations

from decimal import Decimal

from core.pos_api import PosError
from services.inventory import ledger, store as inv_store
from services.purchase import docs as docs_svc

_STOCK_KINDS = ("purchase_invoice", "purchase_order")


def _load_status(cur, *, tenant_id, workspace_client_id, doc_id):
    cur.execute(
        "SELECT status, doc_kind, net_payable, paid_amount FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, doc_id),
    )
    return cur.fetchone()


def post_doc(cur, *, tenant_id, workspace_client_id, doc_id, auto_stock_in, created_by) -> dict:
    """入账:draft→posted。进货入库开 → 写库存(未配 SKU 的行跳过,不阻断)。"""
    row = _load_status(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )
    if row is None:
        raise PosError("purchase.unexpected", 404)
    if row["status"] != "draft":
        raise PosError("purchase.not_draft", 409, detail="not_draft")

    cur.execute(
        "UPDATE purchase_docs SET status = 'posted', updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, doc_id),
    )

    stock_applied = 0
    if auto_stock_in and row["doc_kind"] in _STOCK_KINDS:
        stock_applied = _apply_stock(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=doc_id,
            created_by=created_by,
        )
    doc = docs_svc.get_doc(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )
    return {**doc, "stock_applied": stock_applied}


def _apply_stock(cur, *, tenant_id, workspace_client_id, doc_id, created_by) -> int:
    """按已配 SKU 的进货行写入库;未配行跳过(屏8 匹配后再 post 或手工入库)。"""
    cur.execute(
        "SELECT product_id, qty, unit, batch_no, expiry_date, unit_price FROM purchase_lines "
        "WHERE tenant_id = %s AND purchase_doc_id = %s "
        "AND product_id IS NOT NULL AND item_type = 'goods'",
        (tenant_id, doc_id),
    )
    rows = cur.fetchall()
    lines = [
        {
            "product_id": r["product_id"],
            "qty": r["qty"],
            "unit_name": r["unit"],
            "batch_no": r["batch_no"],
            "expiry_date": r["expiry_date"],
            "unit_cost": r["unit_price"],
        }
        for r in rows
        if Decimal(str(r["qty"] or 0)) > 0
    ]
    if not lines:
        return 0
    wh = inv_store.get_or_create_default_warehouse(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    res = ledger.receive(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        warehouse_id=wh["id"],
        lines=lines,
        ref_type="purchase",
        ref_id=doc_id,
        client_uuid=f"purchase_post_{doc_id}",
        created_by=created_by,
    )
    return len(res.get("txn_ids", []))


def pay_doc(cur, *, tenant_id, workspace_client_id, doc_id, amount) -> dict:
    """记付款(支持部分)。超未付余额 / 非正额 → amount_mismatch。仅 posted 可付。"""
    row = _load_status(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )
    if row is None:
        raise PosError("purchase.unexpected", 404)
    if row["status"] != "posted":
        raise PosError("purchase.not_draft", 409, detail="not_posted")

    amt = Decimal(str(amount or 0))
    payable = Decimal(str(row["net_payable"] or 0))
    paid = Decimal(str(row["paid_amount"] or 0))
    remaining = payable - paid
    if amt <= 0 or amt > remaining:
        raise PosError("purchase.amount_mismatch", 422, detail="over_or_zero")

    new_paid = paid + amt
    status = "paid" if new_paid >= payable else "partial"
    cur.execute(
        "UPDATE purchase_docs SET paid_amount = %s, payment_status = %s, updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (new_paid, status, tenant_id, workspace_client_id, doc_id),
    )
    return docs_svc.get_doc(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )


def void_doc(cur, *, tenant_id, workspace_client_id, doc_id, created_by) -> dict:
    """作废:posted→void。已入库逐笔取负回冲。draft 用 delete 而非 void。"""
    row = _load_status(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )
    if row is None:
        raise PosError("purchase.unexpected", 404)
    if row["status"] == "void":
        return docs_svc.get_doc(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
        )
    if row["status"] != "posted":
        raise PosError("purchase.not_draft", 409, detail="only_posted_voidable")

    _reverse_stock(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        doc_id=doc_id,
        created_by=created_by,
    )
    cur.execute(
        "UPDATE purchase_docs SET status = 'void', updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, doc_id),
    )
    return docs_svc.get_doc(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )


def _reverse_stock(cur, *, tenant_id, workspace_client_id, doc_id, created_by) -> None:
    """逐笔取负回冲本单已写的入库流水(精确反转 base 量 + 批次/仓)。"""
    cur.execute(
        "SELECT product_id, warehouse_id, batch_id, qty_delta FROM inventory_transactions "
        "WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND ref_type = 'purchase' AND ref_id = %s AND txn_type = 'purchase_in'",
        (tenant_id, workspace_client_id, doc_id),
    )
    for r in cur.fetchall():
        ledger.apply_movement(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            warehouse_id=r["warehouse_id"],
            product_id=r["product_id"],
            batch_id=r["batch_id"],
            txn_type="purchase_void",
            qty_delta=-Decimal(str(r["qty_delta"])),
            ref_type="purchase_void",
            ref_id=doc_id,
            created_by=created_by,
        )
