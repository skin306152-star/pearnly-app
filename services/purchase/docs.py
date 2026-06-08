# -*- coding: utf-8 -*-
"""进项单据 DAL · 建/列(含 KPI)/详/改草稿/删(商户采购 · docs/purchasing/01-02 §1)。

进项票/采购单/费用同表(doc_kind)。建单:totals 反算合计(权威)→ 解析/自动建供应商 →
dedupe 防重复抵扣 → 写头+行。posted 不可改(409)。删仅 draft。post/pay/void 见 posting.py。
隔离=每句 WHERE tenant_id + workspace_client_id;钱字段 Decimal;值全 %s 参数化。调用方管事务。
"""

from __future__ import annotations

import json
from typing import Optional

from core.pos_api import PosError
from services.purchase import suppliers as sup_svc
from services.purchase import totals as totals_svc

_DOC_COLS = (
    "id, workspace_client_id, doc_kind, supplier_id, doc_no, doc_date, has_vat, "
    "currency, fx_rate, subtotal, discount_total, vat_amount, wht_amount, rounding, "
    "grand_total, net_payable, category_id, requester, requester_user_id, "
    "approval_status, payment_status, paid_amount, due_date, source, dedupe_key, "
    "status, created_by, created_at, updated_at"
)
_LINE_COLS = (
    "id, line_no, item_type, product_id, description, qty, unit, unit_price, discount, "
    "line_total, vat_rate, vat_applicable, wht_rate, category_id, subcategory_id, "
    "batch_no, expiry_date"
)
_KINDS = ("purchase_invoice", "purchase_order", "expense")


def _resolve_supplier(cur, *, tenant_id, workspace_client_id, supplier) -> Optional[str]:
    """供应商解析:给 id 用 id;给 {name,tax_id,...} 则匹配/自动建(AI 拍票语义)。"""
    if not supplier:
        return None
    if isinstance(supplier, str):
        return supplier
    sid = supplier.get("id")
    if sid:
        return sid
    if not (supplier.get("name") or "").strip():
        return None
    row = sup_svc.create_supplier(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        name=supplier.get("name"),
        tax_id=supplier.get("tax_id"),
        branch_type=supplier.get("branch_type"),
        branch_no=supplier.get("branch_no"),
        address=supplier.get("address"),
        phone=supplier.get("phone"),
    )
    return row["id"]


def find_by_dedupe(cur, *, tenant_id, workspace_client_id, dedupe_key) -> Optional[dict]:
    """按指纹查已录单据(防重复抵扣)。dedupe_key 空 → None。"""
    if not dedupe_key:
        return None
    cur.execute(
        f"SELECT {_DOC_COLS} FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND dedupe_key = %s "
        "LIMIT 1",
        (tenant_id, workspace_client_id, dedupe_key),
    )
    return cur.fetchone()


def _validate_lines(norm_lines: list) -> None:
    """每行须有品名或商品 + 数量>0(否则 line_invalid)。"""
    if not norm_lines:
        raise PosError("purchase.line_invalid", 422, detail="no_lines")
    for ln in norm_lines:
        has_item = bool(ln["description"]) or bool(ln["product_id"])
        if not has_item or ln["qty"] <= 0:
            raise PosError("purchase.line_invalid", 422, detail=f"line_{ln['line_no']}")


def create_doc(
    cur, *, tenant_id, workspace_client_id, created_by, data, settings, status="draft"
) -> dict:
    """建进项单据(草稿/直接 posted 由调用方 status 决定;入库联动在 posting.post_doc)。"""
    doc_kind = data.get("doc_kind") or "expense"
    if doc_kind not in _KINDS:
        raise PosError("purchase.line_invalid", 422, detail="bad_doc_kind")

    calc = totals_svc.compute_purchase_totals(
        data.get("lines"),
        doc_discount=data.get("discount_total", 0),
        rounding=data.get("rounding", 0),
    )
    _validate_lines(calc["lines"])

    expected = data.get("grand_total")
    if expected is not None and totals_svc._q(totals_svc._d(expected)) != calc["grand_total"]:
        raise PosError("purchase.amount_mismatch", 422)

    supplier_id = _resolve_supplier(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        supplier=data.get("supplier"),
    )
    supplier_tax = (
        (data.get("supplier") or {}).get("tax_id")
        if isinstance(data.get("supplier"), dict)
        else None
    )
    dkey = totals_svc.dedupe_key(
        supplier_tax=supplier_tax,
        doc_no=data.get("doc_no"),
        grand_total=calc["grand_total"],
    )
    if dkey and settings.get("dedupe_block"):
        if find_by_dedupe(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, dedupe_key=dkey
        ):
            raise PosError("purchase.dup_invoice", 409)

    cur.execute(
        """
        INSERT INTO purchase_docs
            (tenant_id, workspace_client_id, doc_kind, supplier_id, doc_no, doc_date,
             has_vat, currency, fx_rate, subtotal, discount_total, vat_amount, wht_amount,
             rounding, grand_total, net_payable, category_id, requester, requester_user_id,
             approval_status, due_date, source, ocr_raw, dedupe_key, status, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s::jsonb, %s, %s, %s)
        RETURNING id
        """,
        (
            tenant_id,
            workspace_client_id,
            doc_kind,
            supplier_id,
            (data.get("doc_no") or None),
            (data.get("doc_date") or None),
            bool(data.get("has_vat", calc["vat_amount"] > 0)),
            (data.get("currency") or "THB"),
            totals_svc._d(data.get("fx_rate", 1)),
            calc["subtotal"],
            calc["discount_total"],
            calc["vat_amount"],
            calc["wht_amount"],
            calc["rounding"],
            calc["grand_total"],
            calc["net_payable"],
            (data.get("category_id") or None),
            (data.get("requester") or None),
            (data.get("requester_user_id") or None),
            (data.get("approval_status") or "none"),
            (data.get("due_date") or None),
            (data.get("source") or "manual"),
            json.dumps(data.get("ocr_raw")) if data.get("ocr_raw") is not None else None,
            dkey,
            status,
            created_by,
        ),
    )
    doc_id = cur.fetchone()["id"]
    _insert_lines(cur, tenant_id=tenant_id, doc_id=doc_id, lines=calc["lines"])
    return get_doc(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id)


def _insert_lines(cur, *, tenant_id, doc_id, lines) -> None:
    for ln in lines:
        cur.execute(
            """
            INSERT INTO purchase_lines
                (tenant_id, purchase_doc_id, line_no, item_type, product_id, description,
                 qty, unit, unit_price, discount, line_total, vat_rate, vat_applicable,
                 wht_rate, category_id, subcategory_id, batch_no, expiry_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                tenant_id,
                doc_id,
                ln["line_no"],
                ln["item_type"],
                ln["product_id"],
                ln["description"],
                ln["qty"],
                ln["unit"],
                ln["unit_price"],
                ln["discount"],
                ln["line_total"],
                ln["vat_rate"],
                ln["vat_applicable"],
                ln["wht_rate"],
                ln["category_id"],
                ln["subcategory_id"],
                ln["batch_no"],
                ln["expiry_date"],
            ),
        )


def get_doc(cur, *, tenant_id, workspace_client_id, doc_id) -> Optional[dict]:
    """详情:头(带 supplier_name/tax_id)+ 行 + 附件。不存在/跨套账 → None。"""
    sql = (
        f"SELECT d.{', d.'.join(_DOC_COLS.split(', '))}, "
        "s.name AS supplier_name, s.tax_id AS supplier_tax_id "
        "FROM purchase_docs d "
        "LEFT JOIN suppliers s ON s.id = d.supplier_id AND s.tenant_id = d.tenant_id "
        "WHERE d.tenant_id = %s AND d.workspace_client_id = %s AND d.id = %s"
    )
    cur.execute(sql, (tenant_id, workspace_client_id, doc_id))
    doc = cur.fetchone()
    if doc is None:
        return None
    cur.execute(
        f"SELECT {_LINE_COLS} FROM purchase_lines "
        "WHERE tenant_id = %s AND purchase_doc_id = %s ORDER BY line_no",
        (tenant_id, doc_id),
    )
    lines = cur.fetchall()
    cur.execute(
        "SELECT id, kind, url, generated, created_at FROM purchase_attachments "
        "WHERE tenant_id = %s AND purchase_doc_id = %s ORDER BY created_at",
        (tenant_id, doc_id),
    )
    attachments = cur.fetchall()
    return {"doc": doc, "lines": lines, "attachments": attachments}


def list_docs(
    cur, *, tenant_id, workspace_client_id, kind=None, status=None, unpaid=False, q=None
) -> dict:
    """列单据 + 本月 KPI(进货/费用/可抵进项税/未付)。"""
    sql = (
        f"SELECT d.{', d.'.join(_DOC_COLS.split(', '))}, s.name AS supplier_name "
        "FROM purchase_docs d "
        "LEFT JOIN suppliers s ON s.id = d.supplier_id AND s.tenant_id = d.tenant_id "
        "WHERE d.tenant_id = %s AND d.workspace_client_id = %s"
    )
    params: list = [tenant_id, workspace_client_id]
    if kind in _KINDS:
        sql += " AND d.doc_kind = %s"
        params.append(kind)
    if status in ("draft", "posted", "void"):
        sql += " AND d.status = %s"
        params.append(status)
    if unpaid:
        sql += " AND d.payment_status <> 'paid' AND d.status = 'posted'"
    if q:
        sql += " AND (s.name ILIKE %s OR d.doc_no ILIKE %s)"
        like = f"%{q.strip()}%"
        params += [like, like]
    sql += " ORDER BY d.created_at DESC LIMIT 500"
    cur.execute(sql, tuple(params))
    docs = cur.fetchall()
    return {"docs": docs, "summary": _summary(cur, tenant_id, workspace_client_id)}


def _summary(cur, tenant_id, workspace_client_id) -> dict:
    """本月聚合(单表 FILTER · 无 join 无笛卡尔)。未付=应付余额(不限本月)。"""
    cur.execute(
        """
        SELECT
          COALESCE(SUM(grand_total) FILTER (
            WHERE doc_kind IN ('purchase_invoice','purchase_order')
              AND doc_date >= date_trunc('month', CURRENT_DATE)), 0) AS goods_total,
          COALESCE(SUM(grand_total) FILTER (
            WHERE doc_kind = 'expense'
              AND doc_date >= date_trunc('month', CURRENT_DATE)), 0) AS expense_total,
          COALESCE(SUM(vat_amount) FILTER (
            WHERE doc_kind = 'purchase_invoice' AND has_vat
              AND doc_date >= date_trunc('month', CURRENT_DATE)), 0) AS vat_claimable,
          COALESCE(SUM(net_payable - paid_amount) FILTER (
            WHERE payment_status <> 'paid'), 0) AS unpaid_total
        FROM purchase_docs
        WHERE tenant_id = %s AND workspace_client_id = %s AND status = 'posted'
        """,
        (tenant_id, workspace_client_id),
    )
    r = cur.fetchone()
    return {
        "goods_total": r["goods_total"],
        "expense_total": r["expense_total"],
        "vat_claimable": r["vat_claimable"],
        "unpaid_total": r["unpaid_total"],
    }


def update_draft(
    cur, *, tenant_id, workspace_client_id, created_by, doc_id, data, settings
) -> dict:
    """改草稿:posted/void 不可改(not_draft 409)。整体重算 + 重写行(删旧插新)。"""
    cur.execute(
        "SELECT status FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, doc_id),
    )
    row = cur.fetchone()
    if row is None:
        raise PosError("purchase.unexpected", 404)
    if row["status"] != "draft":
        raise PosError("purchase.not_draft", 409)

    calc = totals_svc.compute_purchase_totals(
        data.get("lines"),
        doc_discount=data.get("discount_total", 0),
        rounding=data.get("rounding", 0),
    )
    _validate_lines(calc["lines"])
    supplier_id = _resolve_supplier(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        supplier=data.get("supplier"),
    )
    cur.execute(
        """
        UPDATE purchase_docs SET
            doc_kind = %s, supplier_id = %s, doc_no = %s, doc_date = %s, has_vat = %s,
            currency = %s, fx_rate = %s, subtotal = %s, discount_total = %s, vat_amount = %s,
            wht_amount = %s, rounding = %s, grand_total = %s, net_payable = %s,
            category_id = %s, requester = %s, due_date = %s, updated_at = now()
        WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s
        """,
        (
            (data.get("doc_kind") or "expense"),
            supplier_id,
            (data.get("doc_no") or None),
            (data.get("doc_date") or None),
            bool(data.get("has_vat", calc["vat_amount"] > 0)),
            (data.get("currency") or "THB"),
            totals_svc._d(data.get("fx_rate", 1)),
            calc["subtotal"],
            calc["discount_total"],
            calc["vat_amount"],
            calc["wht_amount"],
            calc["rounding"],
            calc["grand_total"],
            calc["net_payable"],
            (data.get("category_id") or None),
            (data.get("requester") or None),
            (data.get("due_date") or None),
            tenant_id,
            workspace_client_id,
            doc_id,
        ),
    )
    cur.execute(
        "DELETE FROM purchase_lines WHERE tenant_id = %s AND purchase_doc_id = %s",
        (tenant_id, doc_id),
    )
    _insert_lines(cur, tenant_id=tenant_id, doc_id=doc_id, lines=calc["lines"])
    return get_doc(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id)


def match_line_product(
    cur, *, tenant_id, workspace_client_id, line_id, product_id=None, create=None
) -> dict:
    """行↔商品库:匹配现有 SKU 或一键建新(seam 屏8)。行须属本套账内某单据。"""
    if create and not product_id:
        from services.sales import products as products_svc

        name = (create.get("name") or "").strip()
        if not name:
            raise PosError("purchase.line_invalid", 422, detail="product_name")
        prod = products_svc.create_product(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            fields={
                "name_th": name,
                "name_en": name,
                "name_zh": name,
                "barcode": create.get("barcode"),
            },
        )
        product_id = prod["id"]
    if not product_id:
        raise PosError("purchase.line_invalid", 422, detail="no_product")
    cur.execute(
        "UPDATE purchase_lines SET product_id = %s "
        "WHERE tenant_id = %s AND id = %s AND purchase_doc_id IN ("
        "  SELECT id FROM purchase_docs "
        "  WHERE tenant_id = %s AND workspace_client_id = %s) "
        "RETURNING id, product_id",
        (product_id, tenant_id, line_id, tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if row is None:
        raise PosError("purchase.unexpected", 404)
    return {"line_id": row["id"], "product_id": row["product_id"]}


def delete_doc(cur, *, tenant_id, workspace_client_id, doc_id) -> None:
    """删草稿(仅 draft · 级联删行/附件由 FK ON DELETE CASCADE)。"""
    cur.execute(
        "DELETE FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s AND status = 'draft'",
        (tenant_id, workspace_client_id, doc_id),
    )
    if cur.rowcount == 0:
        raise PosError("purchase.not_draft", 409)
