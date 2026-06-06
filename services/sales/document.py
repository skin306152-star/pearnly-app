# -*- coding: utf-8 -*-
"""销项单据业务层(PO-4 · docs/sales-module/docs/13)。

建草稿 / 改草稿 / 取详情 / 列单 / 正式开出(事务取连号·冻结金额) / 作废。
金额服务端用 Decimal 精确算,不信前端。开出后(status != draft)禁改——update/issue
在此校验状态并返回错误码,路由层据此返 409。租户隔离靠 get_cursor_rls + 每条 WHERE
tenant_id。SQL 全参数化,列名只来自模块内常量。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from psycopg2.extras import Json

from services.sales import buyer as buyer_mod
from services.sales import numbering
from services.sales import seller_profile

# 金额计算抽到 totals.py(纯函数叶子);compute_totals 在此 re-export,沿用
# doc_svc.compute_totals 调用约定。_CENT/_d 供本模块收款归一化复用。
from services.sales.totals import _CENT, _d, compute_totals  # noqa: F401

STATUS_DRAFT = "draft"
STATUS_ISSUED = "issued"
STATUS_VOID = "void"
# 审批工作流态(docs/16 §F):approval_mode!=none 时草稿先提交审批,owner 批准才取号开出。
STATUS_PENDING = "pending_approval"
STATUS_REJECTED = "rejected"
# 草稿可编辑/可提交审批的态:草稿本身 + 被驳回(改后回到草稿)。
EDITABLE_STATUSES = (STATUS_DRAFT, STATUS_REJECTED)

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

_DOC_COLS = (
    "id, tenant_id, doc_type, doc_number, client_id, seller_workspace_client_id, issue_date, "
    "status, currency, subtotal, discount_total, vat_rate, vat_amount, wht_amount, grand_total, "
    "header_discount_amount, header_discount_pct, price_includes_vat, "
    "buyer_type, buyer_name, buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no, "
    "parties_snapshot, payment_status, paid_amount, payment_method, payment_date, "
    "due_date, payment_terms, approved_by, approved_at, rejected_reason, "
    "issued_at, created_by, references_document_id, reference_reason, created_at, updated_at"
)
_LINE_COLS = (
    "id, document_id, line_no, product_id, description, qty, unit_price, "
    "discount, discount_pct, vat_applicable, line_total"
)


def _write_header_totals(cur, tenant_id: str, doc_id, t: dict) -> None:
    cur.execute(
        "UPDATE sales_documents SET subtotal=%s, discount_total=%s, header_discount_amount=%s, "
        "header_discount_pct=%s, price_includes_vat=%s, vat_rate=%s, vat_amount=%s, "
        "wht_amount=%s, grand_total=%s, updated_at=now() WHERE tenant_id=%s AND id=%s",
        (
            t["subtotal"],
            t["discount_total"],
            t["header_discount_amount"],
            t["header_discount_pct"],
            t["price_includes_vat"],
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
    price_includes_vat=False,
    due_date=None,
    payment_terms=None,
) -> dict:
    t = compute_totals(
        lines,
        vat_rate=vat_rate,
        wht_rate=wht_rate,
        header_discount_amount=header_discount_amount,
        header_discount_pct=header_discount_pct,
        price_includes_vat=price_includes_vat,
    )
    cur.execute(
        "INSERT INTO sales_documents (tenant_id, doc_type, client_id, seller_workspace_client_id, "
        "status, currency, subtotal, discount_total, header_discount_amount, header_discount_pct, "
        "price_includes_vat, vat_rate, vat_amount, wht_amount, grand_total, created_by) "
        "VALUES (%s,%s,%s,%s,'draft',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
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
            t["price_includes_vat"],
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
    price_includes_vat=False,
    due_date=None,
    payment_terms=None,
) -> Optional[str]:
    """改草稿。返回错误码('not_found' / 'not_draft')或 None(成功)。

    被驳回(rejected)的单可继续改,改动即回到草稿态并清掉驳回理由(§F:rejected→改→draft)。
    """
    status = _status_of(cur, tenant_id, doc_id)
    if status is None:
        return "not_found"
    if status not in EDITABLE_STATUSES:
        return "not_draft"
    # 改动总把状态归位草稿、清驳回理由(草稿态为幂等无害,驳回态则回到草稿)。
    sets, params = ["status='draft'", "rejected_reason=NULL"], []
    for col, val in (
        ("doc_type", doc_type),
        ("client_id", client_id),
        ("seller_workspace_client_id", seller_workspace_client_id),
        ("currency", currency),
    ):
        if val is not None:
            sets.append(f"{col}=%s")
            params.append(val)
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
        price_includes_vat=price_includes_vat,
    )
    _write_header_totals(cur, tenant_id, doc_id, t)
    _replace_lines(cur, tenant_id, doc_id, t["lines"])
    return None


def lock_for_issue(cur, tenant_id: str, doc_id) -> Optional[dict]:
    """取号前锁行,读出闸校验所需字段(buyer/payment/seller)。供开出/审批通过共用。"""
    cur.execute(
        "SELECT status, doc_type, seller_workspace_client_id, "
        "buyer_type, buyer_name, buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no, "
        "payment_status, payment_method, payment_date "
        "FROM sales_documents WHERE tenant_id=%s AND id=%s FOR UPDATE",
        (tenant_id, doc_id),
    )
    return cur.fetchone()


def finalize_issue(
    cur, *, tenant_id: str, doc_id, row: dict, prefix, reset: str, on: date, approved_by=None
) -> tuple[Optional[dict], Optional[str]]:
    """已锁行 → 完整性/收款闸 → 取连号 → status=issued + 冻结双方快照。不过闸不占号。

    approved_by 非空时同时记审批人/时间(经审批通过开出 · §F)。供 issue_document 与
    approval.approve 共用,保证两条路径取号/冻结/校验完全一致。
    """
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
    sets = [
        "status='issued'",
        "doc_number=%s",
        "issue_date=%s",
        "issued_at=now()",
        "parties_snapshot=%s",
    ]
    params: list = [doc_number, on, Json(snapshot)]
    if approved_by is not None:
        sets += ["approved_by=%s", "approved_at=now()", "rejected_reason=NULL"]
        params.append(approved_by)
    sets.append("updated_at=now()")
    cur.execute(
        f"UPDATE sales_documents SET {', '.join(sets)} WHERE tenant_id=%s AND id=%s",
        params + [tenant_id, doc_id],
    )
    return get_document(cur, tenant_id=tenant_id, doc_id=doc_id), None


def issue_document(
    cur,
    *,
    tenant_id: str,
    doc_id,
    prefix: Optional[str],
    reset: str,
    on: date,
    approval_mode: str = "none",
) -> tuple[Optional[dict], Optional[str]]:
    """正式开出(直开路径)。approval_mode!=none 时草稿不能直开,须走提交审批→审批通过(§F)。

    返回 (doc, error_code)。买方完整性(§B)与收款(§J)在取号前校验,不过则不占号。
    """
    row = lock_for_issue(cur, tenant_id, doc_id)
    if not row:
        return None, "not_found"
    if row["status"] != STATUS_DRAFT:
        return None, "not_draft"
    if approval_mode and approval_mode != "none":
        return None, "approval_required"
    return finalize_issue(
        cur, tenant_id=tenant_id, doc_id=doc_id, row=row, prefix=prefix, reset=reset, on=on
    )


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
