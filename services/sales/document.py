# -*- coding: utf-8 -*-
"""销项单据业务层(PO-4 · docs/sales-module/docs/13)。

建草稿 / 改草稿 / 取详情 / 列单 / 正式开出(事务取连号·冻结金额) / 作废。
金额服务端用 Decimal 精确算,不信前端。开出后(status != draft)禁改——update/issue
在此校验状态并返回错误码,路由层据此返 409。租户隔离靠 get_cursor_rls + 每条 WHERE
tenant_id。SQL 全参数化,列名只来自模块内常量。
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from psycopg2.extras import Json

from services.sales import buyer as buyer_mod
from services.sales import numbering
from services.sales import seller_profile

STATUS_DRAFT = "draft"
STATUS_ISSUED = "issued"
STATUS_VOID = "void"

# doc_type → 默认号码前缀(可被开票请求覆盖)。合并单(税票+收据)走自己的序列。
DEFAULT_PREFIX = {
    "tax_invoice": "INV",
    "tax_invoice_simple": "INV",
    "tax_invoice_receipt": "INV",
    "receipt": "RCP",
    "quotation": "QT",
}

# 收据 / 合并单开出前必须已收款(docs/16 §J3:收钱凭证无款不开)。
REQUIRE_PAYMENT = ("receipt", "tax_invoice_receipt")
PAYMENT_STATUSES = ("unpaid", "partial", "paid")

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")

_DOC_COLS = (
    "id, tenant_id, doc_type, doc_number, client_id, seller_workspace_client_id, issue_date, "
    "status, currency, subtotal, discount_total, vat_rate, vat_amount, wht_amount, grand_total, "
    "header_discount_amount, header_discount_pct, "
    "buyer_type, buyer_name, buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no, "
    "parties_snapshot, payment_status, paid_amount, payment_method, payment_date, "
    "due_date, payment_terms, "
    "issued_at, created_by, references_document_id, reference_reason, created_at, updated_at"
)
_LINE_COLS = (
    "id, document_id, line_no, product_id, description, qty, unit_price, "
    "discount, discount_pct, vat_applicable, line_total"
)


def _d(v: Any) -> Decimal:
    return Decimal(str(v if v is not None else 0))


def _has_value(v) -> bool:
    """折扣百分比是否真给了值(区分 0/None/空串 与有效百分比)。"""
    return v not in (None, "", 0, "0", "0.0", "0.00")


def _line_discount(gross: Decimal, ln: dict) -> tuple[Decimal, Optional[Decimal]]:
    """行折扣:给了 discount_pct 走百分比,否则用绝对 discount。折后净额不得为负(§D5)。"""
    pct = ln.get("discount_pct")
    if _has_value(pct):
        dp = _d(pct)
        disc = (gross * dp / _HUNDRED).quantize(_CENT)
    else:
        dp = None
        disc = _d(ln.get("discount", 0)).quantize(_CENT)
    if disc > gross:
        disc = gross
    return disc, dp


def _resolve_header_discount(base: Decimal, amount, pct) -> Decimal:
    """整单折扣:给了 pct 走百分比,否则绝对额。夹在 [0, subtotal]。"""
    h = (
        (base * _d(pct) / _HUNDRED).quantize(_CENT)
        if _has_value(pct)
        else _d(amount).quantize(_CENT)
    )
    if h < 0:
        return Decimal("0.00")
    return h if h <= base else base


def _taxable_vat_base(norm_lines: list, subtotal_pre: Decimal, header_disc: Decimal) -> Decimal:
    """整单折扣按 line_total 比例摊到应税净额上,保 VAT base 落在实际成交价(§D2)。"""
    taxable = sum((ln["line_total"] for ln in norm_lines if ln["vat_applicable"]), Decimal("0"))
    if header_disc == 0 or subtotal_pre == 0:
        return taxable.quantize(_CENT)
    taxable_share = (header_disc * taxable / subtotal_pre).quantize(_CENT)
    base = (taxable - taxable_share).quantize(_CENT)
    return base if base > 0 else Decimal("0.00")


def compute_totals(
    lines: list, *, vat_rate, wht_rate=0, header_discount_amount=0, header_discount_pct=0
) -> dict:
    """从明细行算金额。行级 + 整单折扣;VAT 落折后净额,WHT 按折后 subtotal。全程 Decimal。"""
    vr, wr = _d(vat_rate), _d(wht_rate)
    subtotal_pre = Decimal("0")
    disc_total = Decimal("0")
    norm_lines = []
    for i, ln in enumerate(lines, start=1):
        qty = _d(ln.get("qty", 1))
        price = _d(ln.get("unit_price", 0))
        gross = (qty * price).quantize(_CENT)
        disc, dp = _line_discount(gross, ln)
        line_total = (gross - disc).quantize(_CENT)
        subtotal_pre += line_total
        disc_total += disc
        norm_lines.append(
            {
                "line_no": i,
                "product_id": ln.get("product_id"),
                "description": (ln.get("description") or "").strip(),
                "qty": qty,
                "unit_price": price,
                "discount": disc,
                "discount_pct": dp,
                "vat_applicable": bool(ln.get("vat_applicable", True)),
                "line_total": line_total,
            }
        )

    header_disc = _resolve_header_discount(
        subtotal_pre, header_discount_amount, header_discount_pct
    )
    vat_base = _taxable_vat_base(norm_lines, subtotal_pre, header_disc)
    subtotal_after = (subtotal_pre - header_disc).quantize(_CENT)
    vat_amount = (vat_base * vr / _HUNDRED).quantize(_CENT)
    wht_amount = (subtotal_after * wr / _HUNDRED).quantize(_CENT)
    grand = (subtotal_after + vat_amount - wht_amount).quantize(_CENT)
    return {
        "subtotal": subtotal_pre.quantize(_CENT),
        "discount_total": disc_total.quantize(_CENT),
        "header_discount_amount": header_disc,
        "header_discount_pct": (
            _d(header_discount_pct) if _has_value(header_discount_pct) else None
        ),
        "vat_rate": vr,
        "vat_amount": vat_amount,
        "wht_amount": wht_amount,
        "grand_total": grand,
        "lines": norm_lines,
    }


def _write_header_totals(cur, tenant_id: str, doc_id, t: dict) -> None:
    cur.execute(
        "UPDATE sales_documents SET subtotal=%s, discount_total=%s, header_discount_amount=%s, "
        "header_discount_pct=%s, vat_rate=%s, vat_amount=%s, wht_amount=%s, grand_total=%s, "
        "updated_at=now() WHERE tenant_id=%s AND id=%s",
        (
            t["subtotal"],
            t["discount_total"],
            t["header_discount_amount"],
            t["header_discount_pct"],
            t["vat_rate"],
            t["vat_amount"],
            t["wht_amount"],
            t["grand_total"],
            tenant_id,
            doc_id,
        ),
    )


def _replace_lines(cur, tenant_id: str, doc_id, lines: list) -> None:
    cur.execute(
        "DELETE FROM sales_document_lines WHERE tenant_id=%s AND document_id=%s",
        (tenant_id, doc_id),
    )
    for ln in lines:
        cur.execute(
            "INSERT INTO sales_document_lines (tenant_id, document_id, line_no, product_id, "
            "description, qty, unit_price, discount, discount_pct, vat_applicable, line_total) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                tenant_id,
                doc_id,
                ln["line_no"],
                ln["product_id"],
                ln["description"],
                ln["qty"],
                ln["unit_price"],
                ln["discount"],
                ln["discount_pct"],
                ln["vat_applicable"],
                ln["line_total"],
            ),
        )


def _normalize_payment(payment: Optional[dict]) -> dict:
    """请求收款块 → 列值(docs/16 §J2)。状态非法回落 unpaid;金额走 Decimal。"""
    p = payment or {}
    status = p.get("status") or p.get("payment_status") or "unpaid"
    if status not in PAYMENT_STATUSES:
        status = "unpaid"
    return {
        "payment_status": status,
        "paid_amount": _d(p.get("paid_amount", 0)).quantize(_CENT),
        "payment_method": (p.get("method") or p.get("payment_method")) or None,
        "payment_date": p.get("date") or p.get("payment_date"),
    }


def _write_buyer_payment(cur, tenant_id, doc_id, buyer, payment) -> None:
    """写买方块 + 收款列(草稿可改)。buyer/payment 为 None 时跳过该部分(不动既有值)。"""
    sets, params = [], []
    if buyer is not None:
        for col, val in buyer_mod.to_columns(buyer_mod.normalize_buyer(buyer)).items():
            sets.append(f"{col}=%s")
            params.append(val)
    if payment is not None:
        for col, val in _normalize_payment(payment).items():
            sets.append(f"{col}=%s")
            params.append(val)
    if not sets:
        return
    sets.append("updated_at=now()")
    cur.execute(
        f"UPDATE sales_documents SET {', '.join(sets)} WHERE tenant_id=%s AND id=%s",
        params + [tenant_id, doc_id],
    )


def _write_terms(cur, tenant_id, doc_id, due_date, payment_terms) -> None:
    """账期字段(草稿可改)。任一非 None 才写,避免覆盖既有值(§G4)。"""
    sets, params = [], []
    for col, val in (("due_date", due_date), ("payment_terms", payment_terms)):
        if val is not None:
            sets.append(f"{col}=%s")
            params.append(val)
    if not sets:
        return
    cur.execute(
        f"UPDATE sales_documents SET {', '.join(sets)} WHERE tenant_id=%s AND id=%s",
        params + [tenant_id, doc_id],
    )


def _payment_gate(row: dict) -> Optional[str]:
    """§J3:收据/合并单开出时必须已收款(状态非 unpaid + 方式/日期齐)。"""
    if row["doc_type"] not in REQUIRE_PAYMENT:
        return None
    if (row.get("payment_status") or "unpaid") == "unpaid":
        return "payment_required"
    if not row.get("payment_method") or not row.get("payment_date"):
        return "payment_required"
    return None


def _seller_snapshot(s: Optional[dict]) -> dict:
    s = s or {}
    return {k: s.get(k) for k in ("name", "tax_id", "address", "branch", "phone")}


def _freeze_parties(cur, tenant_id: str, row: dict) -> dict:
    """开出时把卖方+买方冻结成快照(docs/16 §A)。已开出 PDF 从此渲染,不再实时 join。"""
    seller = None
    sid = row.get("seller_workspace_client_id")
    if sid:
        seller = seller_profile.get_seller(cur, tenant_id=tenant_id, workspace_client_id=sid)
    return {"seller": _seller_snapshot(seller), "buyer": buyer_mod.from_row(row)}


def create_draft(
    cur,
    *,
    tenant_id: str,
    created_by: Optional[str],
    doc_type: str,
    client_id: Optional[int],
    seller_workspace_client_id: Optional[int],
    currency: str,
    vat_rate,
    wht_rate,
    lines: list,
    buyer: Optional[dict] = None,
    payment: Optional[dict] = None,
    header_discount_amount=0,
    header_discount_pct=0,
    due_date=None,
    payment_terms=None,
) -> dict:
    t = compute_totals(
        lines,
        vat_rate=vat_rate,
        wht_rate=wht_rate,
        header_discount_amount=header_discount_amount,
        header_discount_pct=header_discount_pct,
    )
    cur.execute(
        "INSERT INTO sales_documents (tenant_id, doc_type, client_id, seller_workspace_client_id, "
        "status, currency, subtotal, discount_total, header_discount_amount, header_discount_pct, "
        "vat_rate, vat_amount, wht_amount, grand_total, created_by) "
        "VALUES (%s,%s,%s,%s,'draft',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (
            tenant_id,
            doc_type,
            client_id,
            seller_workspace_client_id,
            currency,
            t["subtotal"],
            t["discount_total"],
            t["header_discount_amount"],
            t["header_discount_pct"],
            t["vat_rate"],
            t["vat_amount"],
            t["wht_amount"],
            t["grand_total"],
            created_by,
        ),
    )
    doc_id = cur.fetchone()["id"]
    _replace_lines(cur, tenant_id, doc_id, t["lines"])
    _write_buyer_payment(cur, tenant_id, doc_id, buyer, payment)
    _write_terms(cur, tenant_id, doc_id, due_date, payment_terms)
    return get_document(cur, tenant_id=tenant_id, doc_id=doc_id)


def get_document(cur, *, tenant_id: str, doc_id) -> Optional[dict]:
    cur.execute(
        f"SELECT {_DOC_COLS} FROM sales_documents WHERE tenant_id=%s AND id=%s",
        (tenant_id, doc_id),
    )
    doc = cur.fetchone()
    if not doc:
        return None
    doc = dict(doc)
    cur.execute(
        f"SELECT {_LINE_COLS} FROM sales_document_lines "
        "WHERE tenant_id=%s AND document_id=%s ORDER BY line_no",
        (tenant_id, doc_id),
    )
    doc["lines"] = cur.fetchall()
    return doc


def list_documents(
    cur,
    *,
    tenant_id: str,
    status: Optional[str] = None,
    client_id: Optional[int] = None,
    limit: int = 100,
) -> list:
    sql = f"SELECT {_DOC_COLS} FROM sales_documents WHERE tenant_id=%s"
    params: list = [tenant_id]
    if status:
        sql += " AND status=%s"
        params.append(status)
    if client_id:
        sql += " AND client_id=%s"
        params.append(client_id)
    sql += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    cur.execute(sql, params)
    return cur.fetchall()


def _status_of(cur, tenant_id: str, doc_id, lock: bool = False) -> Optional[str]:
    cur.execute(
        "SELECT status FROM sales_documents WHERE tenant_id=%s AND id=%s"
        + (" FOR UPDATE" if lock else ""),
        (tenant_id, doc_id),
    )
    row = cur.fetchone()
    return row["status"] if row else None


def update_draft(
    cur,
    *,
    tenant_id: str,
    doc_id,
    doc_type=None,
    client_id=None,
    seller_workspace_client_id=None,
    currency=None,
    vat_rate,
    wht_rate,
    lines,
    buyer: Optional[dict] = None,
    payment: Optional[dict] = None,
    header_discount_amount=0,
    header_discount_pct=0,
    due_date=None,
    payment_terms=None,
) -> Optional[str]:
    """改草稿。返回错误码('not_found' / 'not_draft')或 None(成功)。"""
    status = _status_of(cur, tenant_id, doc_id)
    if status is None:
        return "not_found"
    if status != STATUS_DRAFT:
        return "not_draft"
    sets, params = [], []
    for col, val in (
        ("doc_type", doc_type),
        ("client_id", client_id),
        ("seller_workspace_client_id", seller_workspace_client_id),
        ("currency", currency),
    ):
        if val is not None:
            sets.append(f"{col}=%s")
            params.append(val)
    if sets:
        cur.execute(
            f"UPDATE sales_documents SET {', '.join(sets)} WHERE tenant_id=%s AND id=%s",
            params + [tenant_id, doc_id],
        )
    _write_buyer_payment(cur, tenant_id, doc_id, buyer, payment)
    _write_terms(cur, tenant_id, doc_id, due_date, payment_terms)
    t = compute_totals(
        lines,
        vat_rate=vat_rate,
        wht_rate=wht_rate,
        header_discount_amount=header_discount_amount,
        header_discount_pct=header_discount_pct,
    )
    _write_header_totals(cur, tenant_id, doc_id, t)
    _replace_lines(cur, tenant_id, doc_id, t["lines"])
    return None


def issue_document(
    cur, *, tenant_id: str, doc_id, prefix: Optional[str], reset: str, on: date
) -> tuple[Optional[dict], Optional[str]]:
    """正式开出:草稿 → 完整性/收款闸 → 事务取连号 → status=issued + 冻结双方快照。

    返回 (doc, error_code)。买方完整性(§B)与收款(§J)在取号前校验,不过则不占号。
    """
    cur.execute(
        "SELECT status, doc_type, seller_workspace_client_id, "
        "buyer_type, buyer_name, buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no, "
        "payment_status, payment_method, payment_date "
        "FROM sales_documents WHERE tenant_id=%s AND id=%s FOR UPDATE",
        (tenant_id, doc_id),
    )
    row = cur.fetchone()
    if not row:
        return None, "not_found"
    if row["status"] != STATUS_DRAFT:
        return None, "not_draft"
    berr = buyer_mod.validate_buyer(buyer_mod.from_row(row), row["doc_type"])
    if berr:
        return None, berr
    perr = _payment_gate(row)
    if perr:
        return None, perr
    use_prefix = prefix or DEFAULT_PREFIX.get(row["doc_type"], "DOC")
    doc_number, _ = numbering.allocate(
        cur, tenant_id=tenant_id, doc_type=row["doc_type"], prefix=use_prefix, reset=reset, on=on
    )
    snapshot = _freeze_parties(cur, tenant_id, row)
    cur.execute(
        "UPDATE sales_documents SET status='issued', doc_number=%s, issue_date=%s, "
        "issued_at=now(), parties_snapshot=%s, updated_at=now() WHERE tenant_id=%s AND id=%s",
        (doc_number, on, Json(snapshot), tenant_id, doc_id),
    )
    return get_document(cur, tenant_id=tenant_id, doc_id=doc_id), None


def void_document(cur, *, tenant_id: str, doc_id) -> Optional[str]:
    """作废:留记录、不回收号。返回错误码或 None。"""
    status = _status_of(cur, tenant_id, doc_id)
    if status is None:
        return "not_found"
    if status == STATUS_VOID:
        return "already_void"
    cur.execute(
        "UPDATE sales_documents SET status='void', updated_at=now() WHERE tenant_id=%s AND id=%s",
        (tenant_id, doc_id),
    )
    return None
