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

from services.sales import numbering

STATUS_DRAFT = "draft"
STATUS_ISSUED = "issued"
STATUS_VOID = "void"

# doc_type → 默认号码前缀(可被开票请求覆盖)。
DEFAULT_PREFIX = {
    "tax_invoice": "INV",
    "tax_invoice_simple": "INV",
    "receipt": "RCP",
    "quotation": "QT",
}

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")

_DOC_COLS = (
    "id, tenant_id, doc_type, doc_number, client_id, issue_date, status, currency, "
    "subtotal, discount_total, vat_rate, vat_amount, wht_amount, grand_total, "
    "issued_at, created_by, created_at, updated_at"
)
_LINE_COLS = (
    "id, document_id, line_no, product_id, description, qty, unit_price, "
    "discount, vat_applicable, line_total"
)


def _d(v: Any) -> Decimal:
    return Decimal(str(v if v is not None else 0))


def compute_totals(lines: list, *, vat_rate, wht_rate=0) -> dict:
    """从明细行算金额。WHT 按 subtotal(不含 VAT)计,符合泰国惯例。"""
    vr, wr = _d(vat_rate), _d(wht_rate)
    subtotal = Decimal("0")
    vat_base = Decimal("0")
    disc_total = Decimal("0")
    norm_lines = []
    for i, ln in enumerate(lines, start=1):
        qty = _d(ln.get("qty", 1))
        price = _d(ln.get("unit_price", 0))
        disc = _d(ln.get("discount", 0))
        applicable = bool(ln.get("vat_applicable", True))
        line_total = (qty * price - disc).quantize(_CENT)
        subtotal += line_total
        disc_total += disc
        if applicable:
            vat_base += line_total
        norm_lines.append(
            {
                "line_no": i,
                "product_id": ln.get("product_id"),
                "description": (ln.get("description") or "").strip(),
                "qty": qty,
                "unit_price": price,
                "discount": disc,
                "vat_applicable": applicable,
                "line_total": line_total,
            }
        )
    vat_amount = (vat_base * vr / _HUNDRED).quantize(_CENT)
    wht_amount = (subtotal * wr / _HUNDRED).quantize(_CENT)
    grand = (subtotal + vat_amount - wht_amount).quantize(_CENT)
    return {
        "subtotal": subtotal.quantize(_CENT),
        "discount_total": disc_total.quantize(_CENT),
        "vat_rate": vr,
        "vat_amount": vat_amount,
        "wht_amount": wht_amount,
        "grand_total": grand,
        "lines": norm_lines,
    }


def _write_header_totals(cur, tenant_id: str, doc_id, t: dict) -> None:
    cur.execute(
        "UPDATE sales_documents SET subtotal=%s, discount_total=%s, vat_rate=%s, "
        "vat_amount=%s, wht_amount=%s, grand_total=%s, updated_at=now() "
        "WHERE tenant_id=%s AND id=%s",
        (
            t["subtotal"],
            t["discount_total"],
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
            "description, qty, unit_price, discount, vat_applicable, line_total) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                tenant_id,
                doc_id,
                ln["line_no"],
                ln["product_id"],
                ln["description"],
                ln["qty"],
                ln["unit_price"],
                ln["discount"],
                ln["vat_applicable"],
                ln["line_total"],
            ),
        )


def create_draft(
    cur,
    *,
    tenant_id: str,
    created_by: Optional[str],
    doc_type: str,
    client_id: Optional[int],
    currency: str,
    vat_rate,
    wht_rate,
    lines: list,
) -> dict:
    t = compute_totals(lines, vat_rate=vat_rate, wht_rate=wht_rate)
    cur.execute(
        "INSERT INTO sales_documents (tenant_id, doc_type, client_id, status, currency, "
        "subtotal, discount_total, vat_rate, vat_amount, wht_amount, grand_total, created_by) "
        "VALUES (%s,%s,%s,'draft',%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (
            tenant_id,
            doc_type,
            client_id,
            currency,
            t["subtotal"],
            t["discount_total"],
            t["vat_rate"],
            t["vat_amount"],
            t["wht_amount"],
            t["grand_total"],
            created_by,
        ),
    )
    doc_id = cur.fetchone()["id"]
    _replace_lines(cur, tenant_id, doc_id, t["lines"])
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
    currency=None,
    vat_rate,
    wht_rate,
    lines,
) -> Optional[str]:
    """改草稿。返回错误码('not_found' / 'not_draft')或 None(成功)。"""
    status = _status_of(cur, tenant_id, doc_id)
    if status is None:
        return "not_found"
    if status != STATUS_DRAFT:
        return "not_draft"
    sets, params = [], []
    for col, val in (("doc_type", doc_type), ("client_id", client_id), ("currency", currency)):
        if val is not None:
            sets.append(f"{col}=%s")
            params.append(val)
    if sets:
        cur.execute(
            f"UPDATE sales_documents SET {', '.join(sets)} WHERE tenant_id=%s AND id=%s",
            params + [tenant_id, doc_id],
        )
    t = compute_totals(lines, vat_rate=vat_rate, wht_rate=wht_rate)
    _write_header_totals(cur, tenant_id, doc_id, t)
    _replace_lines(cur, tenant_id, doc_id, t["lines"])
    return None


def issue_document(
    cur, *, tenant_id: str, doc_id, prefix: Optional[str], reset: str, on: date
) -> tuple[Optional[dict], Optional[str]]:
    """正式开出:草稿 → 事务取连号 → status=issued + 冻结。返回 (doc, error_code)。"""
    cur.execute(
        "SELECT status, doc_type FROM sales_documents WHERE tenant_id=%s AND id=%s FOR UPDATE",
        (tenant_id, doc_id),
    )
    row = cur.fetchone()
    if not row:
        return None, "not_found"
    if row["status"] != STATUS_DRAFT:
        return None, "not_draft"
    use_prefix = prefix or DEFAULT_PREFIX.get(row["doc_type"], "DOC")
    doc_number, _ = numbering.allocate(
        cur, tenant_id=tenant_id, doc_type=row["doc_type"], prefix=use_prefix, reset=reset, on=on
    )
    cur.execute(
        "UPDATE sales_documents SET status='issued', doc_number=%s, issue_date=%s, "
        "issued_at=now(), updated_at=now() WHERE tenant_id=%s AND id=%s",
        (doc_number, on, tenant_id, doc_id),
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
