# -*- coding: utf-8 -*-
"""销项单据业务层(PO-4 · docs/sales-module/docs/13)。

建/改/删草稿 · 取详情/列单 · 正式开出(事务取连号·冻结金额)·作废。金额服务端 Decimal 精确算;
开出后(status!=draft)禁改,update/issue 校验状态返错误码(路由层据此 409);租户隔离 get_cursor_rls
+ 每条 WHERE tenant_id;SQL 全参数化,列名只来自模块内常量。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from psycopg2.extras import Json

from services.sales import archive
from services.sales import buyer as buyer_mod
from services.sales import numbering
from services.sales import seller_profile
from services.sales.document_cols import _DOC_COLS, _LINE_COLS
from services.sales.document_writes import replace_lines as _replace_lines
from services.sales.document_writes import write_header_totals as _write_header_totals

# compute_totals 在此 re-export(沿用 doc_svc.compute_totals 约定);_CENT/_d 供收款归一化复用。
from services.sales.totals import _CENT, _d, compute_totals  # noqa: F401
from core import workspace_context as wc

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


def _ws_and(workspace_client_id: Optional[int]) -> tuple:
    """PO-7 主体隔离过滤(按 seller_workspace_client_id)。None→不过滤(向后兼容);
    给了→限本主体+NULL 未归属行(rollout-safe·PO-8 收口去 IS NULL)。"""
    if workspace_client_id is None:
        return "", ()
    return " AND (seller_workspace_client_id = %s OR seller_workspace_client_id IS NULL)", (
        int(workspace_client_id),
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


# 卖方快照字段:法定信息(§A 冻结)+ 品牌/模板(§L4 · 随单冻结,保证买方那联与存档一致)。
_SELLER_SNAPSHOT_FIELDS = (
    "name",
    "tax_id",
    "address",
    "branch",
    "phone",
    "email",
    "template_id",
    "brand_color",
    "logo_url",
    "seal_url",
    "signature_url",
    "footer_text",
)


def _seller_snapshot(s: Optional[dict]) -> dict:
    s = s or {}
    return {k: s.get(k) for k in _SELLER_SNAPSHOT_FIELDS}


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
    copies_layout="separate",
    paper_size="A4",
    doc_language="th_en",
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
        "price_includes_vat, vat_rate, vat_amount, wht_rate, wht_amount, grand_total, created_by, "
        "copies_layout, paper_size, doc_language) "
        "VALUES (%s,%s,%s,%s,'draft',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
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
            t["wht_rate"],
            t["wht_amount"],
            t["grand_total"],
            created_by,
            copies_layout,
            paper_size,
            doc_language,
        ),
    )
    doc_id = cur.fetchone()["id"]
    _replace_lines(cur, tenant_id, doc_id, t["lines"])
    _write_buyer_payment(cur, tenant_id, doc_id, buyer, payment)
    _write_terms(cur, tenant_id, doc_id, due_date, payment_terms)
    return get_document(cur, tenant_id=tenant_id, doc_id=doc_id)


def get_document(
    cur, *, tenant_id: str, doc_id, workspace_client_id: Optional[int] = None
) -> Optional[dict]:
    ws_sql, ws_params = _ws_and(workspace_client_id)
    cur.execute(
        f"SELECT {_DOC_COLS} FROM sales_documents WHERE tenant_id=%s AND id=%s{ws_sql}",
        (tenant_id, doc_id, *ws_params),
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
    q: Optional[str] = None,
    limit: int = 100,
    workspace_client_id: Optional[int] = None,
) -> list:
    ws_sql, ws_params = _ws_and(workspace_client_id)
    sql = f"SELECT {_DOC_COLS} FROM sales_documents WHERE tenant_id=%s{ws_sql}"
    params: list = [tenant_id, *ws_params]
    if status:
        sql += " AND status=%s"
        params.append(status)
    if client_id:
        sql += " AND client_id=%s"
        params.append(client_id)
    if q and q.strip():
        like = f"%{q.strip()}%"
        sql += " AND (doc_number ILIKE %s OR buyer_name ILIKE %s OR buyer_tax_id ILIKE %s)"
        params.extend([like, like, like])
    sql += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    cur.execute(sql, params)
    return cur.fetchall()


def _status_of(
    cur, tenant_id: str, doc_id, lock: bool = False, workspace_client_id: Optional[int] = None
) -> Optional[str]:
    ws_sql, ws_params = _ws_and(workspace_client_id)
    cur.execute(
        f"SELECT status FROM sales_documents WHERE tenant_id=%s AND id=%s{ws_sql}"
        + (" FOR UPDATE" if lock else ""),
        (tenant_id, doc_id, *ws_params),
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
    copies_layout=None,
    paper_size=None,
    doc_language=None,
    due_date=None,
    payment_terms=None,
    workspace_client_id: Optional[int] = None,
) -> Optional[str]:
    """改草稿(rejected 单可改 · 改后回草稿态并清驳回理由 §F)。错误码 not_found/not_draft 或 None。"""
    status = _status_of(cur, tenant_id, doc_id, workspace_client_id=workspace_client_id)
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
        ("copies_layout", copies_layout),
        ("paper_size", paper_size),
        ("doc_language", doc_language),
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


def lock_for_issue(
    cur, tenant_id: str, doc_id, workspace_client_id: Optional[int] = None
) -> Optional[dict]:
    """取号前锁行,读出闸校验所需字段(buyer/payment/seller)。供开出/审批通过共用。
    PO-7:按当前主体过滤(rollout-safe),不能跨主体开别套账的单。"""
    ws_sql, ws_params = _ws_and(workspace_client_id)
    cur.execute(
        "SELECT status, doc_type, seller_workspace_client_id, "
        "buyer_type, buyer_name, buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no, "
        "payment_status, payment_method, payment_date "
        f"FROM sales_documents WHERE tenant_id=%s AND id=%s{ws_sql} FOR UPDATE",
        (tenant_id, doc_id, *ws_params),
    )
    return cur.fetchone()


def finalize_issue(
    cur,
    *,
    tenant_id: str,
    doc_id,
    row: dict,
    prefix,
    reset: str,
    on: date,
    start: int = 1,
    approved_by=None,
) -> tuple[Optional[dict], Optional[str]]:
    """已锁行 → 完整性/收款闸 → 取连号 → status=issued + 冻结双方快照(不过闸不占号)。
    approved_by 非空记审批人/时间(§F)。issue_document 与 approval.approve 共用,保证两路径一致。
    """
    berr = buyer_mod.validate_buyer(buyer_mod.from_row(row), row["doc_type"])
    if berr:
        return None, berr
    perr = _payment_gate(row)
    if perr:
        return None, perr
    use_prefix = prefix or DEFAULT_PREFIX.get(row["doc_type"], "DOC")
    # PO-7b 连号按主体:用本单的卖方主体取号(NULL 单兜底到租户默认套账),每主体号段独立连续。
    ws = row.get("seller_workspace_client_id") or wc.default_workspace_id(cur, tenant_id)
    doc_number, _ = numbering.allocate(
        cur,
        tenant_id=tenant_id,
        doc_type=row["doc_type"],
        prefix=use_prefix,
        reset=reset,
        on=on,
        start=start,
        workspace_client_id=ws,
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
    doc = get_document(cur, tenant_id=tenant_id, doc_id=doc_id)
    archive.store_archival_hash(cur, tenant_id, doc_id, doc, snapshot)
    return doc, None


def issue_document(
    cur,
    *,
    tenant_id: str,
    doc_id,
    prefix: Optional[str],
    reset: str,
    on: date,
    start: int = 1,
    approval_mode: str = "none",
    workspace_client_id: Optional[int] = None,
) -> tuple[Optional[dict], Optional[str]]:
    """正式开出(直开路径 · approval_mode!=none 须走提交→审批 §F)。返回 (doc, error_code);
    买方完整性(§B)/收款(§J)在取号前校验,不过不占号。"""
    row = lock_for_issue(cur, tenant_id, doc_id, workspace_client_id=workspace_client_id)
    if not row:
        return None, "not_found"
    if row["status"] != STATUS_DRAFT:
        return None, "not_draft"
    if approval_mode and approval_mode != "none":
        return None, "approval_required"
    return finalize_issue(
        cur,
        tenant_id=tenant_id,
        doc_id=doc_id,
        row=row,
        prefix=prefix,
        reset=reset,
        on=on,
        start=start,
    )


def void_document(
    cur, *, tenant_id: str, doc_id, workspace_client_id: Optional[int] = None
) -> Optional[str]:
    """作废:留记录、不回收号。返回错误码或 None。"""
    status = _status_of(cur, tenant_id, doc_id, workspace_client_id=workspace_client_id)
    if status is None:
        return "not_found"
    if status == STATUS_VOID:
        return "already_void"
    ws_sql, ws_params = _ws_and(workspace_client_id)
    cur.execute(
        f"UPDATE sales_documents SET status='void', updated_at=now() "
        f"WHERE tenant_id=%s AND id=%s{ws_sql}",
        (tenant_id, doc_id, *ws_params),
    )
    return None


def delete_draft(
    cur, *, tenant_id: str, doc_id, workspace_client_id: Optional[int] = None
) -> Optional[str]:
    """删除草稿:仅草稿可删(未占连号);已开/已作废不可删。明细行随 FK ON DELETE CASCADE 自动删。"""
    status = _status_of(cur, tenant_id, doc_id, workspace_client_id=workspace_client_id)
    if status is None:
        return "not_found"
    if status != STATUS_DRAFT:
        return "not_draft"
    ws_sql, ws_params = _ws_and(workspace_client_id)
    cur.execute(
        f"DELETE FROM sales_documents WHERE tenant_id=%s AND id=%s{ws_sql}",
        (tenant_id, doc_id, *ws_params),
    )
    return None
