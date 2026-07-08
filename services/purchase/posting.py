# -*- coding: utf-8 -*-
"""进项单据状态机 · 入账/记付款/作废 + 库存联动(商户采购 · docs/purchasing/02 §1)。

post:draft→posted;进货入库开 → 按行 product_id 写 inventory(ref_type=purchase)。
pay:累计 paid_amount + 派生 payment_status(部分付款);超未付余额拦。
void:posted→void · 下游完整对冲(做账主凭证 + 付款凭证 + 库存逐笔回冲);已结账/已申报
     期间拒绝(acct.period_closed)→ 整事务回滚不留半作废(docs/purchasing/03)。
隔离=每句 WHERE tenant_id(+ workspace_client_id);钱 Decimal。调用方管事务。
"""

from __future__ import annotations

from decimal import Decimal

from core.pos_api import PosError
from services.accounting import hooks as acct_hooks
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
    acct_hooks.enqueue_posting(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type="purchase",
        source_id=doc_id,
        created_by=created_by,
    )
    # 建单即付(智能默认收据/用户手动设已付):购票过账后补记全额付款,账本应付↔现金对平
    # (pay_doc 同步记付款分录·做账关则 no-op)。get_doc 是嵌套结构,取字段走 doc["doc"]。
    payable = Decimal(str(doc["doc"].get("net_payable") or 0))
    if doc["doc"].get("payment_status") == "paid" and payable > 0:
        doc = pay_doc(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=doc_id,
            amount=payable,
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
    acct_hooks.enqueue_posting(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type="payment",
        source_id=str(acct_hooks.payment_event_id(doc_id, new_paid)),
        context={"amount": amt, "direction": "out", "ref": "进项付款"},
    )
    return docs_svc.get_doc(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )


def set_payment_status(cur, *, tenant_id, workspace_client_id, doc_id, status) -> dict:
    """一键改付款态(列表/卡 · PO-5):paid → 付清未付额;unpaid → 撤销付款。仅 posted。"""
    if status not in ("paid", "unpaid"):
        raise PosError("purchase.line_invalid", 422, detail="bad_status")
    if status == "unpaid":
        return unpay_doc(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
        )
    row = _load_status(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )
    if row is None:
        raise PosError("purchase.unexpected", 404)
    if row["status"] != "posted":
        raise PosError("purchase.not_draft", 409, detail="not_posted")
    remaining = Decimal(str(row["net_payable"] or 0)) - Decimal(str(row["paid_amount"] or 0))
    if remaining > 0:
        return pay_doc(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=doc_id,
            amount=remaining,
        )
    return docs_svc.get_doc(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )


def unpay_doc(cur, *, tenant_id, workspace_client_id, doc_id) -> dict:
    """撤销付款:清 paid_amount/payment_status + void 该单付款凭证(账本应付恢复)。仅 posted。"""
    row = _load_status(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )
    if row is None:
        raise PosError("purchase.unexpected", 404)
    if row["status"] != "posted":
        raise PosError("purchase.not_draft", 409, detail="not_posted")
    paid = Decimal(str(row["paid_amount"] or 0))
    if paid > 0:
        _void_payment_vouchers(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=doc_id,
            paid=paid,
        )
    cur.execute(
        "UPDATE purchase_docs SET paid_amount = 0, payment_status = 'unpaid', updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, doc_id),
    )
    return docs_svc.get_doc(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )


def _each_payment_voucher(cur, *, tenant_id, workspace_client_id, doc_id, paid):
    """沿累计链产出该单全部活跃付款凭证(新→旧)。

    付款凭证 source_id=event_id(单+累计已付)、total_debit=该笔金额:从当前累计找凭证 →
    yield → 调用方作废后 remaining -= 其单笔额 → 得上一笔累计 → 续找,直到清零或断链。
    """
    from services.accounting import vouchers as jv

    remaining = Decimal(str(paid or 0))
    guard = 0
    while remaining > 0 and guard < 200:
        guard += 1
        v = jv.find_active_by_source(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            source_type="payment",
            source_id=str(acct_hooks.payment_event_id(doc_id, remaining)),
        )
        if not v:
            return
        yield v
        remaining -= Decimal(str(v["total_debit"] or 0))


def _void_payment_vouchers(
    cur, *, tenant_id, workspace_client_id, doc_id, paid, strict=False, created_by=None
) -> None:
    """void 该单【全部】付款凭证(含多次部分付款 · 沿累计链回退)。做账关/无凭证则 no-op。

    strict=False(unpay 撤付款 · best-effort):SAVEPOINT 吞错不阻断 toggle,jv.set_status 直接置 void。
    strict=True(void_doc 整单作废):走 acct void_or_reverse(开放期 void / 已结期当期红冲),
    异常透传 → 整作废事务回滚(不留半作废 · docs/purchasing/04)。
    """
    if strict:
        for v in _each_payment_voucher(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=doc_id,
            paid=paid,
        ):
            acct_hooks.void_or_reverse(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                voucher_id=v["id"],
                created_by=created_by,
            )
        return

    from services.accounting import vouchers as jv

    try:
        cur.execute("SAVEPOINT unpay_void")
        for v in _each_payment_voucher(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=doc_id,
            paid=paid,
        ):
            jv.set_status(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                voucher_id=v["id"],
                status="void",
            )
        cur.execute("RELEASE SAVEPOINT unpay_void")
    except Exception:
        try:
            cur.execute("ROLLBACK TO SAVEPOINT unpay_void")
        except Exception:
            pass


def void_doc(cur, *, tenant_id, workspace_client_id, doc_id, created_by) -> dict:
    """作废:posted→void · 下游完整对冲(docs/purchasing/03+04)。draft 用 delete 而非 void。

    同一事务顺序:撤付款凭证 → 处理做账主凭证 → 库存逐笔回冲 → status=void。做账凭证按期间:
    开放期 void;已结/已申报期 **当期红冲**(反向凭证·原凭证不动·不篡改已报历史·04)。任一步抛错
    → 整事务回滚不留半作废。当前期也已结(无开放期)→ acct.no_open_period 透传。做账未开=只反库存。
    """
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

    if Decimal(str(row["paid_amount"] or 0)) > 0:
        _void_payment_vouchers(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=doc_id,
            paid=row["paid_amount"],
            strict=True,
            created_by=created_by,
        )
    acct_hooks.void_for_source(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type="purchase",
        source_id=doc_id,
        created_by=created_by,
    )
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
