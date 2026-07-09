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
from services.pos import numbering, sales_store, stock
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


def _resolve_factor(
    cur, *, tenant_id: str, workspace_client_id: int, prod: dict, sell_unit: Optional[str]
) -> Decimal:
    if not sell_unit or sell_unit == prod["base_unit"]:
        return Decimal("1")
    r = sales_store.get_unit_factor(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_id=str(prod["id"]),
        unit_name=sell_unit,
    )
    if not r:
        raise PosError("pos.line_invalid", 422, detail=sell_unit)
    return Decimal(str(r["factor_to_base"]))


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


def _shift_is_open(cur, *, tenant_id: str, shift_id: str) -> bool:
    cur.execute(
        "SELECT status FROM pos_shifts WHERE tenant_id = %s AND id = %s",
        (tenant_id, shift_id),
    )
    row = cur.fetchone()
    return bool(row and row["status"] == "open")


def _header_discount(hd: dict) -> tuple:
    hd = hd or {}
    t, val = hd.get("type"), hd.get("value", 0)
    return (0, val) if t == "pct" else (val, 0) if t == "amount" else (0, 0)


def create_sale(
    cur, *, tenant_id: str, workspace_client_id: int, payload: dict, created_by=None
) -> dict:
    cu = payload.get("client_uuid")
    if cu:
        existing = sales_store.find_sale_by_client_uuid(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, client_uuid=cu
        )
        if existing:
            return _sale_result(existing, deduped=True)

    _assert_shift_open(cur, tenant_id=tenant_id, shift_id=payload.get("shift_id"))
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
        factor = _resolve_factor(
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

    terminal_id = payload.get("terminal_id")
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

    payments = payload.get("payments") or []
    paid_total = sum((Decimal(str(p.get("amount", 0))) for p in payments), Decimal("0"))
    grand = totals["grand_total"]
    change = (paid_total - grand) if paid_total > grand else Decimal("0.00")

    sale = sales_store.insert_sale(
        cur,
        tenant_id=tenant_id,
        fields={
            "workspace_client_id": workspace_client_id,
            "client_uuid": cu,
            "shift_id": payload.get("shift_id"),
            "terminal_id": terminal_id,
            "cashier_id": payload.get("cashier_id"),  # 必须是 pos_cashiers.id 或 NULL(FK)
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
        batch_used = stock.deduct_for_sale(
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
                "batch_id": batch_used,
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
    acct_hooks.enqueue_posting(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type="pos",
        source_id=sale_id,
        created_by=created_by,
    )
    return _sale_result(sale, deduped=False)


def sync_sales(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    items: list,
    cashier_id=None,
    created_by=None,
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
            results.append({"client_uuid": cu, "ok": False, "error": _err_body(e.code, e.detail)})
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


def build_receipt_pdf(
    cur, *, tenant_id: str, workspace_client_id: int, sale_id: str, width_mm: int = 80
) -> bytes:
    """热敏小票 PDF(复用销项 pdf_thermal · 58/80mm)。doc_type=receipt;合计按存额反推以票面自洽。"""
    from services.sales.pdf_thermal import render_thermal_pdf

    sale = sales_store.get_sale(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, sale_id=sale_id
    )
    if not sale:
        raise PosError("pos.product_not_found", 404)
    cur.execute(
        "SELECT l.qty, l.unit_price, l.line_total, p.name_th, p.name_en "
        "FROM pos_sale_lines l JOIN products p ON p.id = l.product_id "
        "WHERE l.tenant_id = %s AND l.sale_id = %s ORDER BY l.id",
        (tenant_id, sale_id),
    )
    doc_lines = [
        {
            "description": r["name_th"] or r["name_en"],
            "qty": r["qty"],
            "unit_price": r["unit_price"],
            "line_total": r["line_total"],
        }
        for r in cur.fetchall()
    ]
    payments = sales_store.list_payments(cur, tenant_id=tenant_id, sale_id=sale_id)
    grand = Decimal(str(sale["grand_total"]))
    vat = Decimal(str(sale["vat_amount"]))
    subtotal = grand if sale["price_includes_vat"] else (grand - vat)
    cur.execute(
        "SELECT name, address, tax_id, phone FROM workspace_clients WHERE tenant_id = %s AND id = %s",
        (tenant_id, sale["workspace_client_id"]),
    )
    seller = dict(cur.fetchone() or {})
    doc = {
        "doc_type": "receipt",
        "doc_number": sale["receipt_no"],
        "issue_date": sale["sold_at"],
        "lines": doc_lines,
        "subtotal": subtotal,
        "header_discount_amount": 0,
        "vat_rate": VAT_RATE,
        "vat_amount": vat,
        "wht_amount": 0,
        "grand_total": grand,
        "price_includes_vat": bool(sale["price_includes_vat"]),
        "currency": "THB",
        "payment_status": "paid",
        "payment_method": payments[0]["method"] if payments else None,
        "paid_amount": sale["paid_total"],
    }
    return render_thermal_pdf(doc, seller, {}, width_mm=width_mm)


def void_sale(
    cur, *, tenant_id: str, workspace_client_id: int, sale_id: str, created_by=None
) -> dict:
    """作废当班错单:回补库存 + 标 void。已交班/已退货/已作废 → void_not_allowed。"""
    sale = sales_store.get_sale(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, sale_id=sale_id
    )
    if not sale or sale["status"] != "completed" or sale["sale_type"] != "sale":
        raise PosError("pos.void_not_allowed", 409)
    if sale.get("shift_id") and not _shift_is_open(
        cur, tenant_id=tenant_id, shift_id=str(sale["shift_id"])
    ):
        raise PosError("pos.void_not_allowed", 409)  # 已交班不可作废
    if sales_store.has_refunds(cur, tenant_id=tenant_id, sale_id=sale_id):
        raise PosError("pos.void_not_allowed", 409)
    wh = inv_store.get_or_create_default_warehouse(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    # 原单没扣过库存(餐饮成品单)就不回补——回补要照镜像扣减,不是照有单就补。
    restore_stock = stock.sale_deducted_stock(cur, tenant_id=tenant_id, sale_id=sale_id)
    if restore_stock:
        for ln in sales_store.list_lines(cur, tenant_id=tenant_id, sale_id=sale_id):
            stock.restock(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                warehouse_id=wh["id"],
                product_id=str(ln["product_id"]),
                batch_id=str(ln["batch_id"]) if ln["batch_id"] else None,
                qty_base=ln["qty_base"],
                ref_type="pos_void",
                ref_id=sale_id,
                txn_type="adjust",
                created_by=created_by,
            )
    sales_store.set_status(cur, tenant_id=tenant_id, sale_id=sale_id, status="void")
    return {"sale_id": sale_id, "status": "void", "stock_returned": restore_stock}
