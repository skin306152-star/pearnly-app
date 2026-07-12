# -*- coding: utf-8 -*-
"""POS 小票编排(POS 项目 · PO-B2 · docs/pos/04 §6)。

建小票 = 一个事务:幂等(client_uuid 命中返原结果)→ 校班次 → 算价(复用销项 totals.py · 价内外)
→ 发终端连号 → FEFO 扣库存 → 落 pos_sales/lines/payments。取单/作废同此层。钱 Decimal、量
numeric(14,3)、应用层 WHERE tenant_id。
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from core.pos_api import PosError
from services.accounting import hooks as acct_hooks
from services.inventory import store as inv_store
from services.pos import numbering, payment_settlement, sale_caps, sales_store, stock, void
from services.pos.sale_binding import resolve as _resolve_sale_binding
from services.sales.totals import compute_totals

VAT_RATE = Decimal("7")  # 泰国标准 VAT(价内外均按此 · 复用 totals.py)


def _money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.2f}"


def _parse_sold_at(raw) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _to_decimal(v) -> Optional[Decimal]:
    return Decimal(str(v)) if v is not None else None


def _resolve_unit(
    cur, *, tenant_id: str, workspace_client_id: int, prod: dict, sell_unit: Optional[str]
) -> tuple:
    """(换算系数, 该售卖单位的挂牌价)。base 单位价取 products.unit_price;命名单位取 product_units.price。

    挂牌价供 caps 改价判定用(手工价低于挂牌 = 改价);未设价 → None(无从判定改价,不拦)。
    """
    if not sell_unit or sell_unit == prod["base_unit"]:
        return Decimal("1"), _to_decimal(prod.get("unit_price"))
    r = sales_store.get_unit_factor(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_id=str(prod["id"]),
        unit_name=sell_unit,
    )
    if not r:
        raise PosError("pos.line_invalid", 422, detail=sell_unit)
    return Decimal(str(r["factor_to_base"])), _to_decimal(r.get("price"))


def _assert_shift_open(cur, *, tenant_id: str, shift_id: Optional[str]) -> None:
    # 卖货必须挂一个 open 班次:缺 shift_id 一律拒(否则现金责任链断 · 见 POS-RO-002)。
    if not shift_id:
        raise PosError("pos.shift_closed", 409, detail="shift_required")
    cur.execute(
        "SELECT status FROM pos_shifts WHERE tenant_id = %s AND id = %s",
        (tenant_id, shift_id),
    )
    row = cur.fetchone()
    if not row or row["status"] != "open":
        raise PosError("pos.shift_closed", 409)


def _header_discount(hd: dict) -> tuple:
    hd = hd or {}
    t, val = hd.get("type"), hd.get("value", 0)
    return (0, val) if t == "pct" else (val, 0) if t == "amount" else (0, 0)


def _validated_payments(payments: list, grand_total: Decimal) -> tuple[list, Decimal, Decimal]:
    return payment_settlement.validate(payments, grand_total)


def _settle_payments(payments: list, grand_total: Decimal) -> tuple[Decimal, Decimal]:
    _, paid_total, change = payment_settlement.validate(payments, grand_total)
    return paid_total, change


def create_sale(
    cur, *, tenant_id: str, workspace_client_id: int, payload: dict, created_by=None, operator=None
) -> dict:
    cu = payload.get("client_uuid")
    if cu:
        existing = sales_store.find_sale_by_client_uuid(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, client_uuid=cu
        )
        if existing:
            return _sale_result(existing, deduped=True)

    binding = _resolve_sale_binding(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        shift_id=payload.get("shift_id"),
        terminal_id=payload.get("terminal_id"),
        cashier_id=operator.get("cashier_id") if operator else None,
    )
    wh = inv_store.get_or_create_default_warehouse(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    warehouse_id = wh["id"]
    sold_at = _parse_sold_at(payload.get("sold_at"))

    resolved = []
    totals_lines = []
    for ln in payload.get("lines", []):
        prod = sales_store.get_product_for_sale(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            product_id=ln.get("product_id"),
        )
        if not prod:
            raise PosError("pos.line_invalid", 422, detail=str(ln.get("product_id")))
        qty = Decimal(str(ln.get("qty", 0)))
        if qty <= 0:
            raise PosError("pos.line_invalid", 422)
        factor, list_price = _resolve_unit(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            prod=prod,
            sell_unit=ln.get("sell_unit"),
        )
        unit_price = Decimal(str(ln.get("unit_price", 0)))
        line_discount = Decimal(str(ln.get("line_discount") or 0))
        vat_app = bool(prod["vat_applicable"])
        totals_lines.append(
            {
                "qty": qty,
                "unit_price": unit_price,
                "discount": line_discount,
                "vat_applicable": vat_app,
            }
        )
        resolved.append(
            {
                "product_id": str(prod["id"]),
                "sell_unit": ln.get("sell_unit") or prod["base_unit"],
                "factor": factor,
                "qty": qty,
                "qty_base": qty * factor,
                "unit_price": unit_price,
                "list_price": list_price,
                "vat_applicable": vat_app,
                "track_batch": bool(prod["track_batch"]),
                "explicit_batch_id": ln.get("batch_id"),
            }
        )

    hd_amount, hd_pct = _header_discount(payload.get("header_discount"))
    totals = compute_totals(
        totals_lines,
        vat_rate=VAT_RATE,
        price_includes_vat=bool(payload.get("price_includes_vat")),
        header_discount_amount=hd_amount,
        header_discount_pct=hd_pct,
    )
    payments, paid_total, change = payment_settlement.validate(
        payload.get("payments") or [], totals["grand_total"]
    )

    # 折扣/改价授权闸(flag 关时返 []·完全跳过):无权且未授权在此抛,一件库存都不动。
    caps_events = sale_caps.enforce(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        operator=operator,
        approval=payload.get("approval"),
        totals=totals,
        resolved=resolved,
    )

    terminal_id = binding["terminal_id"]
    doc_kind = payload.get("doc_kind", "receipt")
    num_kind = doc_kind if doc_kind in ("receipt", "abbrev_tax_invoice") else "receipt"
    receipt_no, _n = numbering.next_number(
        cur,
        tenant_id=tenant_id,
        terminal_id=terminal_id,
        kind=num_kind,
        on=sold_at.date(),
        workspace_client_id=workspace_client_id,
    )

    grand = totals["grand_total"]

    sale = sales_store.insert_sale(
        cur,
        tenant_id=tenant_id,
        fields={
            "workspace_client_id": workspace_client_id,
            "client_uuid": cu,
            "shift_id": payload.get("shift_id"),
            "terminal_id": terminal_id,
            "cashier_id": binding["cashier_id"],
            "receipt_no": receipt_no,
            "doc_kind": doc_kind,
            "sale_type": "sale",
            "refund_of_sale_id": None,
            "member_client_id": payload.get("member_client_id"),
            "subtotal": totals["subtotal"],
            "discount_total": totals["discount_total"] + totals["header_discount_amount"],
            "vat_amount": totals["vat_amount"],
            "grand_total": grand,
            "price_includes_vat": bool(payload.get("price_includes_vat")),
            "paid_total": paid_total,
            "change_amount": change,
            "status": "completed",
            "sold_at": sold_at,
            "created_by": created_by,
        },
    )
    sale_id = str(sale["id"])

    for item, nl in zip(resolved, totals["lines"]):
        deducted = stock.deduct_for_sale(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            warehouse_id=warehouse_id,
            product_id=item["product_id"],
            qty_base=item["qty_base"],
            track_batch=item["track_batch"],
            explicit_batch_id=item["explicit_batch_id"],
            sale_id=sale_id,
            created_by=created_by,
        )
        # 成本快照落在建单这一刻(不等报表期现算):按实际扣减的批次/散装段算 COGS,
        # 事后批次成本被改也不影响历史单据的毛利(见 stock.cost_for_moves)。
        cost_total = stock.cost_for_moves(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            warehouse_id=warehouse_id,
            product_id=item["product_id"],
            moves=deducted["moves"],
        )
        sales_store.insert_line(
            cur,
            tenant_id=tenant_id,
            sale_id=sale_id,
            fields={
                "product_id": item["product_id"],
                "sell_unit": item["sell_unit"],
                "unit_factor": item["factor"],
                "qty": item["qty"],
                "qty_base": item["qty_base"],
                "unit_price": item["unit_price"],
                "line_discount": nl["discount"],
                "vat_applicable": item["vat_applicable"],
                "batch_id": deducted["batch_id"],
                "refund_of_line_id": None,
                "line_total": nl["line_total"],
                "cost_total": cost_total,
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
    acct_hooks.enqueue_posting(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type="pos",
        source_id=sale_id,
        created_by=created_by,
    )
    sale_caps.audit(tenant_id, sale_id, operator, caps_events)
    return _sale_result(sale, deduped=False)


def sync_sales(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    items: list,
    cashier_id=None,
    created_by=None,
    operator=None,
) -> dict:
    """离线批量补传(PO-B5 · docs/pos/04 §6 sync)。逐张幂等处理,部分失败不卡其余。

    每张包在 SAVEPOINT 里:成功 RELEASE、失败 ROLLBACK TO(清掉该张引发的 aborted 状态,
    不污染同批其余)。client_uuid 命中=返原结果 deduped=true(防补传双扣)。cashier_id 取自
    token(不信 body · 与单建一致),shift_id/terminal_id 等保留离线会话原值。失败项带错误码
    返回供端上保留重试。
    """
    results = []
    for raw in items:
        cu = raw.get("client_uuid") if isinstance(raw, dict) else None
        cur.execute("SAVEPOINT pos_sync_item")
        try:
            payload = {**raw, "cashier_id": cashier_id}
            res = create_sale(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                payload=payload,
                created_by=created_by,
                operator=operator,
            )
            cur.execute("RELEASE SAVEPOINT pos_sync_item")
            results.append(
                {
                    "client_uuid": cu,
                    "ok": True,
                    "sale_id": res["sale"]["id"],
                    "receipt_no": res["sale"]["receipt_no"],
                    "deduped": res["deduped"],
                }
            )
        except PosError as e:
            cur.execute("ROLLBACK TO SAVEPOINT pos_sync_item")
            results.append(
                {
                    "client_uuid": cu,
                    "ok": False,
                    "status": e.http_status,
                    "error": _err_body(e.code, e.detail),
                }
            )
        except Exception:
            # 结构性坏张(类型/缺字段)也不许卡批:回退到 savepoint,标 line_invalid 让端上重试。
            cur.execute("ROLLBACK TO SAVEPOINT pos_sync_item")
            results.append(
                {"client_uuid": cu, "ok": False, "error": _err_body("pos.line_invalid", None)}
            )
    return {"results": results}


def _err_body(code: str, detail) -> dict:
    body = {"code": code, "message_key": code}
    if detail:
        body["detail"] = detail
    return body


def _sale_result(sale: dict, *, deduped: bool) -> dict:
    return {
        "sale": {
            "id": str(sale["id"]),
            "receipt_no": sale["receipt_no"],
            "grand_total": _money(sale["grand_total"]),
            "vat_amount": _money(sale["vat_amount"]),
            "paid_total": _money(sale["paid_total"]),
            "change_amount": _money(sale["change_amount"]),
            "status": sale["status"],
        },
        "stock_applied": True,
        "deduped": deduped,
    }


def get_sale_detail(cur, *, tenant_id: str, workspace_client_id: int, sale_id: str) -> dict:
    sale = sales_store.get_sale(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, sale_id=sale_id
    )
    if not sale:
        raise PosError("pos.product_not_found", 404)
    return _detail_view(cur, tenant_id=tenant_id, sale=sale)


def get_sale_by_receipt(cur, *, tenant_id: str, workspace_client_id: int, receipt_no: str) -> dict:
    sale = sales_store.get_sale_by_receipt(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, receipt_no=receipt_no
    )
    if not sale:
        raise PosError("pos.product_not_found", 404)
    return _detail_view(cur, tenant_id=tenant_id, sale=sale)


def _detail_view(cur, *, tenant_id: str, sale: dict) -> dict:
    lines = sales_store.list_lines(cur, tenant_id=tenant_id, sale_id=str(sale["id"]))
    payments = sales_store.list_payments(cur, tenant_id=tenant_id, sale_id=str(sale["id"]))
    return {
        "sale": _header_view(sale),
        "lines": [
            {
                "id": str(ln["id"]),
                "product_id": str(ln["product_id"]),
                "sell_unit": ln["sell_unit"],
                "qty": float(ln["qty"]),
                "qty_base": float(ln["qty_base"]),
                "unit_price": _money(ln["unit_price"]),
                "line_discount": _money(ln["line_discount"]),
                "vat_applicable": ln["vat_applicable"],
                "batch_id": str(ln["batch_id"]) if ln["batch_id"] else None,
                "line_total": _money(ln["line_total"]),
            }
            for ln in lines
        ],
        "payments": [
            {"method": p["method"], "amount": _money(p["amount"]), "ref": p["ref"]}
            for p in payments
        ],
    }


def _header_view(sale: dict) -> dict:
    return {
        "id": str(sale["id"]),
        "receipt_no": sale["receipt_no"],
        "doc_kind": sale["doc_kind"],
        "sale_type": sale["sale_type"],
        "subtotal": _money(sale["subtotal"]),
        "discount_total": _money(sale["discount_total"]),
        "vat_amount": _money(sale["vat_amount"]),
        "grand_total": _money(sale["grand_total"]),
        "price_includes_vat": sale["price_includes_vat"],
        "paid_total": _money(sale["paid_total"]),
        "change_amount": _money(sale["change_amount"]),
        "status": sale["status"],
        "sold_at": sale["sold_at"].isoformat() if sale.get("sold_at") else None,
    }


def void_sale(
    cur, *, tenant_id: str, workspace_client_id: int, sale_id: str, created_by=None, operator=None
) -> dict:
    return void.void_sale(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        sale_id=sale_id,
        created_by=created_by,
        operator=operator,
    )
