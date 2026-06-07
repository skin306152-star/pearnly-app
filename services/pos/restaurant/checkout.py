# -*- coding: utf-8 -*-
"""餐厅 POS 编排 · 埋单结账(POS 项目 · PO-R3 · docs/pos/restaurant/02 §5)。

session 行结成一张零售 pos_sale(复用连号/收款/报表/升级税票)+ 服务费 10% + VAT。整桌/按项分单/AA:
- whole/aa = 结本 session 全部未结行;by_item = 只结 line_ids ∩ 未结行(余行留台,可再开一张)。
- 服务费 = round(菜品折后净额 × rate);VAT 在(菜品+服务费)上**单次取整**(对齐 UI 484/31.66)。
菜品=成品,**埋单不扣库存**(BOM 后做),故不走零售 sale.create_sale。结清→session closed→桌转空闲。
钱全程 Decimal;client_uuid 幂等;每条 SQL WHERE tenant_id。在已开事务的 cursor 上调用(commit=True)。
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from core.pos_api import PosError
from services.pos import numbering, sales_store
from services.pos.restaurant import order_store, store
from services.sales.totals import compute_totals

VAT_RATE = Decimal("7")
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.2f}"


def _round(v: Decimal) -> Decimal:
    return v.quantize(_CENT, rounding=ROUND_HALF_UP)


def _parse_sold_at(raw) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _header_discount(hd) -> tuple:
    hd = hd or {}
    t, val = hd.get("type"), hd.get("value", 0)
    return (0, val) if t == "pct" else (val, 0) if t == "amount" else (0, 0)


def request_bill(cur, *, tenant_id: str, session_id: str) -> dict:
    session = store.get_session(cur, tenant_id=tenant_id, session_id=session_id)
    if not session:
        raise PosError("pos.product_not_found", 404)
    if session["status"] == "open":
        store.set_session_status(cur, tenant_id=tenant_id, session_id=session_id, status="billing")
    return {
        "session": {
            "id": session_id,
            "status": "billing" if session["status"] != "closed" else "closed",
        }
    }


def _compute(billable: list, *, service_rate, price_includes_vat: bool, header_discount) -> dict:
    """菜品 → totals + 服务费 + 合并 VAT。返回算价 + 每行规范(供落库/预览复用)。"""
    totals_lines = [
        {
            "product_id": str(r["product_id"]),
            "qty": Decimal(str(r["qty"])),
            "unit_price": Decimal(str(r["unit_price"])),
            "discount": Decimal(str(r["line_discount"])),
            "vat_applicable": bool(r["vat_applicable"]),
        }
        for r in billable
    ]
    hd_amount, hd_pct = _header_discount(header_discount)
    t = compute_totals(
        totals_lines,
        vat_rate=VAT_RATE,
        price_includes_vat=price_includes_vat,
        header_discount_amount=hd_amount,
        header_discount_pct=hd_pct,
    )
    food_net = t["subtotal"] - t["header_discount_amount"]  # 折后菜品净额(服务费基数)
    rate = Decimal(str(service_rate or 0))
    service = _round(food_net * rate / _HUNDRED) if rate > 0 else Decimal("0.00")
    billed_base = food_net + service
    if price_includes_vat:
        vat = _round(billed_base * VAT_RATE / (_HUNDRED + VAT_RATE))
        grand = _round(billed_base)
    else:
        vat = _round(billed_base * VAT_RATE / _HUNDRED)
        grand = _round(billed_base + vat)
    return {
        "totals": t,
        "subtotal": t["subtotal"],
        "discount_total": t["discount_total"] + t["header_discount_amount"],
        "service_charge": service,
        "service_rate": rate,
        "vat_amount": vat,
        "grand_total": grand,
        "price_includes_vat": price_includes_vat,
    }


def _split(grand: Decimal, ways: Optional[int]) -> Optional[dict]:
    if not ways or int(ways) <= 1:
        return None
    ways = int(ways)
    return {"ways": ways, "per_share": _money(_round(grand / Decimal(ways)))}


def _billable_for(cur, *, tenant_id: str, session_id: str, mode: str, line_ids) -> list:
    ids = line_ids if mode == "by_item" else None
    rows = order_store.list_billable_lines(
        cur, tenant_id=tenant_id, session_id=session_id, line_ids=ids
    )
    if not rows:
        raise PosError("pos.line_invalid", 422, detail="no_billable_lines")
    return rows


def bill_preview(
    cur,
    *,
    tenant_id: str,
    session_id: str,
    mode: str = "whole",
    line_ids=None,
    ways=None,
    price_includes_vat: bool = True,
    service_rate="10",
    header_discount=None,
) -> dict:
    if not store.get_session(cur, tenant_id=tenant_id, session_id=session_id):
        raise PosError("pos.product_not_found", 404)
    billable = _billable_for(
        cur, tenant_id=tenant_id, session_id=session_id, mode=mode, line_ids=line_ids
    )
    c = _compute(
        billable,
        service_rate=service_rate,
        price_includes_vat=price_includes_vat,
        header_discount=header_discount,
    )
    out = {
        "mode": mode,
        "lines": [_bill_line(r) for r in billable],
        "subtotal": _money(c["subtotal"]),
        "service_charge": _money(c["service_charge"]),
        "service_rate": (
            str(int(c["service_rate"]))
            if c["service_rate"] == c["service_rate"].to_integral()
            else str(c["service_rate"])
        ),
        "vat_amount": _money(c["vat_amount"]),
        "price_includes_vat": c["price_includes_vat"],
        "grand_total": _money(c["grand_total"]),
    }
    split = _split(c["grand_total"], ways) if mode == "aa" else None
    if split:
        out["split"] = split
    return out


def checkout(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    session_id: str,
    payload: dict,
    cashier_id=None,
    created_by=None,
) -> dict:
    cu = payload.get("client_uuid")
    if cu:
        existing = sales_store.find_sale_by_client_uuid(cur, tenant_id=tenant_id, client_uuid=cu)
        if existing:
            return _checkout_result(
                cur,
                tenant_id=tenant_id,
                sale=existing,
                session_id=session_id,
                split=None,
                deduped=True,
            )

    session = store.get_session(cur, tenant_id=tenant_id, session_id=session_id)
    if not session:
        raise PosError("pos.product_not_found", 404)
    mode = payload.get("mode", "whole")
    billable = _billable_for(
        cur, tenant_id=tenant_id, session_id=session_id, mode=mode, line_ids=payload.get("line_ids")
    )
    incl = bool(payload.get("price_includes_vat", True))
    c = _compute(
        billable,
        service_rate=payload.get("service_rate", "10"),
        price_includes_vat=incl,
        header_discount=payload.get("header_discount"),
    )

    sold_at = _parse_sold_at(payload.get("sold_at"))
    shift_id = payload.get("shift_id")
    _assert_shift_open(cur, tenant_id=tenant_id, shift_id=shift_id)
    terminal_id = _resolve_terminal(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        terminal_id=payload.get("terminal_id"),
    )
    receipt_no, _n = numbering.next_number(
        cur, tenant_id=tenant_id, terminal_id=terminal_id, kind="receipt", on=sold_at.date()
    )

    payments = payload.get("payments") or []
    paid_total = sum((Decimal(str(p.get("amount", 0))) for p in payments), Decimal("0"))
    grand = c["grand_total"]
    change = (paid_total - grand) if paid_total > grand else Decimal("0.00")

    sale = sales_store.insert_sale(
        cur,
        tenant_id=tenant_id,
        fields={
            "workspace_client_id": workspace_client_id,
            "client_uuid": cu,
            "shift_id": shift_id,
            "terminal_id": terminal_id,
            "cashier_id": cashier_id,
            "receipt_no": receipt_no,
            "doc_kind": "receipt",
            "sale_type": "sale",
            "refund_of_sale_id": None,
            "member_client_id": payload.get("member_client_id"),
            "subtotal": c["subtotal"],
            "discount_total": c["discount_total"],
            "vat_amount": c["vat_amount"],
            "grand_total": grand,
            "price_includes_vat": incl,
            "paid_total": paid_total,
            "change_amount": change,
            "status": "completed",
            "sold_at": sold_at,
            "created_by": created_by,
        },
    )
    sale_id = str(sale["id"])
    order_store.set_sale_service_charge(
        cur, tenant_id=tenant_id, sale_id=sale_id, service_charge=c["service_charge"]
    )

    for src, nl in zip(billable, c["totals"]["lines"]):
        factor = Decimal(str(src["unit_factor"]))
        qty = Decimal(str(src["qty"]))
        sales_store.insert_line(
            cur,
            tenant_id=tenant_id,
            sale_id=sale_id,
            fields={
                "product_id": str(src["product_id"]),
                "sell_unit": src["sell_unit"],
                "unit_factor": factor,
                "qty": qty,
                "qty_base": qty * factor,
                "unit_price": Decimal(str(src["unit_price"])),
                "line_discount": nl["discount"],
                "vat_applicable": bool(src["vat_applicable"]),
                "batch_id": None,
                "refund_of_line_id": None,
                "line_total": nl["line_total"],
            },
        )
    for p in payments:
        sales_store.insert_payment(
            cur,
            tenant_id=tenant_id,
            sale_id=sale_id,
            method=p.get("method", "cash"),
            amount=p.get("amount", 0),
            ref=p.get("ref"),
        )

    order_store.settle_lines(
        cur, tenant_id=tenant_id, line_ids=[str(r["id"]) for r in billable], sale_id=sale_id
    )
    if order_store.count_unsettled(cur, tenant_id=tenant_id, session_id=session_id) == 0:
        store.set_session_status(
            cur, tenant_id=tenant_id, session_id=session_id, status="closed", closed=True
        )
    split = _split(grand, payload.get("ways")) if mode == "aa" else None
    full = sales_store.get_sale(cur, tenant_id=tenant_id, sale_id=sale_id)
    return _checkout_result(
        cur, tenant_id=tenant_id, sale=full, session_id=session_id, split=split, deduped=False
    )


# ── 内部 ──────────────────────────────────────────────────────────────
def _assert_shift_open(cur, *, tenant_id: str, shift_id) -> None:
    if not shift_id:
        return
    cur.execute(
        "SELECT status FROM pos_shifts WHERE tenant_id = %s AND id = %s",
        (tenant_id, shift_id),
    )
    row = cur.fetchone()
    if not row or row["status"] != "open":
        raise PosError("pos.shift_closed", 409)


def _resolve_terminal(cur, *, tenant_id: str, workspace_client_id: int, terminal_id) -> int:
    if terminal_id:
        return int(terminal_id)
    from services.pos import cashier as cashier_dal

    term = cashier_dal.get_or_create_default_terminal(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    return int(term["id"])


def _bill_line(r: dict) -> dict:
    return {
        "line_id": str(r["id"]),
        "product_id": str(r["product_id"]),
        "name": {"th": r.get("name_th"), "en": r.get("name_en"), "zh": r.get("name_zh")},
        "qty": f"{Decimal(str(r['qty'])):.3f}",
        "unit_price": _money(r["unit_price"]),
        "line_total": _money(r["line_total"]),
    }


def _checkout_result(
    cur, *, tenant_id: str, sale: dict, session_id: str, split, deduped: bool
) -> dict:
    session = store.get_session(cur, tenant_id=tenant_id, session_id=session_id)
    out = {
        "sale": {
            "id": str(sale["id"]),
            "receipt_no": sale["receipt_no"],
            "subtotal": _money(sale["subtotal"]),
            "service_charge": _money(
                _sale_service_charge(cur, tenant_id=tenant_id, sale_id=str(sale["id"]))
            ),
            "vat_amount": _money(sale["vat_amount"]),
            "grand_total": _money(sale["grand_total"]),
            "paid_total": _money(sale["paid_total"]),
            "change_amount": _money(sale["change_amount"]),
            "status": sale["status"],
        },
        "session": {"id": session_id, "status": session["status"] if session else "closed"},
        "deduped": deduped,
    }
    if split:
        out["split"] = split
    return out


def _sale_service_charge(cur, *, tenant_id: str, sale_id: str) -> Decimal:
    cur.execute(
        "SELECT service_charge FROM pos_sales WHERE tenant_id = %s AND id = %s",
        (tenant_id, sale_id),
    )
    row = cur.fetchone()
    return (
        Decimal(str(row["service_charge"]))
        if row and row["service_charge"] is not None
        else Decimal("0")
    )
