# -*- coding: utf-8 -*-
"""POS 退货(POS 项目 · PO-B2 · docs/pos/04 §6)。

生成一张 sale_type=refund 的负额小票(独立 RFD 连号),按行回补原批次库存,行指回原行
(refund_of_line_id)以累计已退量。超退 → pos.over_refund。金额按原行比例 + 复用 totals.py
的 VAT 规则(价内外与原单一致),再取负。幂等 client_uuid。一个事务(调用方 commit)。
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from core.pos_api import PosError
from services.inventory import store as inv_store
from services.pos import cashier as cashier_dal
from services.pos import numbering, sale as sale_svc, sale_binding, sales_store, stock
from services.sales.totals import compute_totals


def refund(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    original_sale_id: str,
    lines: list,
    refund_method: str = "cash",
    refund_payments: list | None = None,
    client_uuid=None,
    terminal_id=None,
    shift_id=None,
    cashier_id=None,
    created_by=None,
) -> dict:
    if client_uuid:
        existing = sales_store.find_sale_by_client_uuid(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            client_uuid=client_uuid,
        )
        if existing:
            # 重放也如实报库存侧结果(餐饮单本就没回补过)。
            return _refund_result(
                existing,
                deduped=True,
                stock_returned=stock.sale_deducted_stock(
                    cur, tenant_id=tenant_id, sale_id=original_sale_id
                ),
            )

    orig = sales_store.get_sale(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, sale_id=original_sale_id
    )
    if not orig:
        raise PosError("pos.product_not_found", 404)
    if orig["status"] != "completed" or orig["sale_type"] != "sale":
        raise PosError("pos.void_not_allowed", 409)
    binding = _current_refund_binding(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        cashier_id=cashier_id,
    )

    orig_lines = {
        str(ln["id"]): ln
        for ln in sales_store.list_lines(cur, tenant_id=tenant_id, sale_id=original_sale_id)
    }

    refund_items = []
    totals_lines = []
    for rl in lines:
        oline = orig_lines.get(str(rl.get("sale_line_id")))
        if not oline:
            raise PosError("pos.line_invalid", 422, detail=str(rl.get("sale_line_id")))
        rqty = Decimal(str(rl.get("qty", 0)))
        oqty = Decimal(str(oline["qty"]))
        if rqty <= 0 or oqty <= 0:
            raise PosError("pos.line_invalid", 422)
        already = sales_store.refunded_qty_for_line(
            cur, tenant_id=tenant_id, line_id=str(oline["id"])
        )
        if already + rqty > oqty:
            raise PosError("pos.over_refund", 409, detail=str(oline["product_id"]))
        fraction = rqty / oqty
        disc = (Decimal(str(oline["line_discount"])) * fraction).quantize(Decimal("0.01"))
        totals_lines.append(
            {
                "qty": rqty,
                "unit_price": Decimal(str(oline["unit_price"])),
                "discount": disc,
                "vat_applicable": bool(oline["vat_applicable"]),
            }
        )
        refund_items.append(
            {
                "oline": oline,
                "qty": rqty,
                "qty_base": rqty * Decimal(str(oline["unit_factor"])),
            }
        )

    totals = compute_totals(
        totals_lines,
        vat_rate=sale_svc.VAT_RATE,
        price_includes_vat=bool(orig["price_includes_vat"]),
    )

    receipt_no, _n = numbering.next_number(
        cur,
        tenant_id=tenant_id,
        terminal_id=binding["terminal_id"],
        kind="refund",
        on=date.today(),
        workspace_client_id=workspace_client_id,
    )
    grand = -totals["grand_total"]
    # 混合支付原路拆退:调用方按原单各方式给退款拆分;Σ 必须等于退款总额(防拆错钱)。
    # 存前先校验,不等直接 422,绝不落一张各方式加不平的退货单。
    _validate_refund_payments(refund_payments, totals["grand_total"])

    refund_sale = sales_store.insert_sale(
        cur,
        tenant_id=tenant_id,
        fields={
            "workspace_client_id": workspace_client_id,
            "client_uuid": client_uuid,
            "shift_id": binding["shift_id"],
            "terminal_id": binding["terminal_id"],
            "cashier_id": binding["cashier_id"],
            "receipt_no": receipt_no,
            "doc_kind": orig["doc_kind"],
            "sale_type": "refund",
            "refund_of_sale_id": original_sale_id,
            "member_client_id": orig.get("member_client_id"),
            "subtotal": -totals["subtotal"],
            "discount_total": -(totals["discount_total"] + totals["header_discount_amount"]),
            "vat_amount": -totals["vat_amount"],
            "grand_total": grand,
            "price_includes_vat": bool(orig["price_includes_vat"]),
            "paid_total": grand,
            "change_amount": Decimal("0.00"),
            "status": "completed",
            "sold_at": datetime.now(timezone.utc),
            "created_by": created_by,
        },
    )
    refund_sale_id = str(refund_sale["id"])

    wh = inv_store.get_or_create_default_warehouse(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    # 原单没扣过库存(餐饮成品单)就不回补——回补要照镜像扣减,不是照有单就补。
    restore_stock = stock.sale_deducted_stock(cur, tenant_id=tenant_id, sale_id=original_sale_id)
    for item, nl in zip(refund_items, totals["lines"]):
        oline = item["oline"]
        sales_store.insert_line(
            cur,
            tenant_id=tenant_id,
            sale_id=refund_sale_id,
            fields={
                "product_id": str(oline["product_id"]),
                "sell_unit": oline["sell_unit"],
                "unit_factor": oline["unit_factor"],
                "qty": item["qty"],
                "qty_base": item["qty_base"],
                "unit_price": oline["unit_price"],
                "line_discount": nl["discount"],
                "vat_applicable": bool(oline["vat_applicable"]),
                "batch_id": str(oline["batch_id"]) if oline["batch_id"] else None,
                "refund_of_line_id": str(oline["id"]),
                "line_total": -nl["line_total"],
                "cost_total": _refund_line_cost(oline, item["qty"]),
            },
        )
        if restore_stock:
            stock.restock(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                warehouse_id=wh["id"],
                product_id=str(oline["product_id"]),
                batch_id=str(oline["batch_id"]) if oline["batch_id"] else None,
                qty_base=item["qty_base"],
                ref_type="pos_refund",
                ref_id=refund_sale_id,
                txn_type="return_in",
                created_by=created_by,
            )

    # 原路拆退:逐笔按原方式记一行负额(现金退现金/刷卡退刷卡),对账各方式各归各。
    # 单笔兼容(老前台只给 refund_method)= 整额退该方式的退化拆退,归一走同一条负额写入路径。
    payments = refund_payments or [{"method": refund_method, "amount": grand}]
    for p in payments:
        sales_store.insert_payment(
            cur,
            tenant_id=tenant_id,
            sale_id=refund_sale_id,
            method=p.get("method", "cash"),
            amount=-abs(Decimal(str(p.get("amount", 0)))),
        )
    return _refund_result(refund_sale, deduped=False, stock_returned=restore_stock)


def _current_refund_binding(
    cur, *, tenant_id: str, workspace_client_id: int, cashier_id: str | None
) -> dict:
    if not cashier_id:
        raise PosError("pos.forbidden", 403)
    shift = cashier_dal.get_open_shift_for_cashier(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        cashier_id=cashier_id,
        for_update=True,
    )
    if not shift:
        raise PosError("pos.shift_closed", 409)
    bound = sale_binding.resolve(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        shift_id=str(shift["id"]),
        terminal_id=shift["terminal_id"],
        cashier_id=cashier_id,
    )
    return {**bound, "shift_id": str(shift["id"])}


def _validate_refund_payments(refund_payments: list | None, refund_grand_total: Decimal) -> None:
    """拆退各方式金额之和必须等于退货总额,否则 422。

    调用方按原单方式给正额拆分(现金 6 / 刷卡 4),存库时统一取负(见 insert 处)。此处按绝对值
    合计对账,容忍调用方传正/负号,但总额加不平就拒——钱路不允许"退了但各方式加不平"。
    """
    if not refund_payments:
        return
    total = sum((abs(Decimal(str(p.get("amount", 0)))) for p in refund_payments), Decimal("0"))
    if total.quantize(Decimal("0.01")) != refund_grand_total.quantize(Decimal("0.01")):
        raise PosError("pos.refund_amount_mismatch", 422)


def _refund_line_cost(oline: dict, rqty: Decimal) -> Decimal | None:
    """退货行成本快照 = 原行成本 × 退货比例,取负(镜像 line_total 负号 · 报表毛利回冲用)。

    原行无成本(老单据/无进价 · cost_total 为 None)→ 退货行也 None,不造 0:报表据此如实标
    "成本不全"而非拿假 0 冲出虚高毛利。
    """
    ocost = oline.get("cost_total")
    if ocost is None:
        return None
    fraction = rqty / Decimal(str(oline["qty"]))
    return -(Decimal(str(ocost)) * fraction).quantize(Decimal("0.01"))


def _refund_result(sale: dict, *, deduped: bool, stock_returned: bool) -> dict:
    return {
        "refund_sale": {
            "id": str(sale["id"]),
            "receipt_no": sale["receipt_no"],
            "grand_total": sale_svc._money(sale["grand_total"]),
        },
        "stock_returned": stock_returned,
        "deduped": deduped,
    }
