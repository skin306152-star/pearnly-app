# -*- coding: utf-8 -*-
"""POS 小票升级正式税票(POS 项目 · PO-B4 · docs/pos/04 §6 / 03 §9)。

简式小票(pos_sales)→ 全式 ใบกำกับภาษี(落 sales_documents,复用销项合规机制:连号
FOR UPDATE 不跳号、开出冻结买卖双方快照、status=issued 不可改、存档 sha256)。升级后回填
pos_sales.full_invoice_id 作「被全式取代」标记——VAT 申报时全式票计、被取代的简式票不再计,
不重复计 VAT(消费侧按 full_invoice_id 过滤)。

金额不重算:全式票逐字搬运小票已冻结的行 + totals(同一笔交易,票面必与小票一致),只经
compute_totals 复算校验一致性以复用销项写入路径。同一笔重复升级 → pos.already_upgraded。
买方税号/完整性不合规 → pos.tax_id_invalid(契约 04 §6 仅此两错误码)。
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from core.pos_api import PosError
from services.pos import sale as sale_svc, sales_store
from services.sales import document as doc_svc
from services.sales import settings as settings_svc

# 全式税票固定走 tax_invoice 序列(与销项手开税票同一连号池,保证连号真连续)。
_DOC_TYPE = "tax_invoice"
# 契约请求 branch_type 用 head/branch;买方模块用 hq/branch。
_BRANCH_MAP = {"head": "hq", "branch": "branch"}


def _to_buyer(raw: Optional[dict]) -> dict:
    """升级请求买方块 → 买方模块 canonical 入参(party_type→type · head→hq)。"""
    raw = raw or {}
    return {
        "type": raw.get("party_type") or raw.get("type") or "company",
        "name": raw.get("name"),
        "address": raw.get("address"),
        "tax_id": raw.get("tax_id"),
        "branch_type": _BRANCH_MAP.get(raw.get("branch_type"), raw.get("branch_type")),
        "branch_no": raw.get("branch_no"),
    }


def _sale_lines_as_doc_lines(cur, *, tenant_id: str, sale_id: str) -> tuple[list, Decimal]:
    """小票行 → 单据行入参(qty/unit_price/line_discount/vat 逐字搬),并返回行折扣合计。"""
    cur.execute(
        "SELECT l.qty, l.unit_price, l.line_discount, l.vat_applicable, l.product_id, "
        "p.name_th, p.name_en, p.name_zh "
        "FROM pos_sale_lines l JOIN products p ON p.id = l.product_id "
        "WHERE l.tenant_id = %s AND l.sale_id = %s ORDER BY l.id",
        (tenant_id, sale_id),
    )
    lines, line_disc_total = [], Decimal("0")
    for r in cur.fetchall():
        disc = Decimal(str(r["line_discount"] or 0))
        line_disc_total += disc
        lines.append(
            {
                "product_id": str(r["product_id"]),
                "description": r["name_th"] or r["name_en"] or r["name_zh"] or "",
                "qty": Decimal(str(r["qty"])),
                "unit_price": Decimal(str(r["unit_price"])),
                "discount": disc,
                "vat_applicable": bool(r["vat_applicable"]),
            }
        )
    return lines, line_disc_total


def _resolve_issue_date(sold_at) -> date:
    if isinstance(sold_at, datetime):
        return sold_at.astimezone(timezone.utc).date()
    return datetime.now(timezone.utc).date()


def upgrade_to_full_tax_invoice(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    sale_id: str,
    buyer: Optional[dict],
    created_by: Optional[str] = None,
) -> dict:
    """小票 → 全式税票。单事务(调用方 commit):校验 → 建草稿 → 取连号开出冻结 → 回填标记。"""
    sale = sales_store.get_sale(cur, tenant_id=tenant_id, sale_id=sale_id)
    if not sale or sale["sale_type"] != "sale" or sale["status"] != "completed":
        raise PosError("pos.product_not_found", 404)
    if sale.get("full_invoice_id"):
        raise PosError("pos.already_upgraded", 409)

    nb = _to_buyer(buyer)
    lines, line_disc_total = _sale_lines_as_doc_lines(cur, tenant_id=tenant_id, sale_id=sale_id)
    if not lines:
        raise PosError("pos.line_invalid", 422, detail="empty_sale")
    # 整单折扣 = 小票总折扣 - 行折扣合计(小票只存 discount_total 合计,此处反解以无损复算)。
    header_discount = Decimal(str(sale["discount_total"] or 0)) - line_disc_total
    if header_discount < 0:
        header_discount = Decimal("0")

    draft = doc_svc.create_draft(
        cur,
        tenant_id=tenant_id,
        created_by=created_by,
        doc_type=_DOC_TYPE,
        client_id=None,
        seller_workspace_client_id=int(workspace_client_id),
        currency="THB",
        vat_rate=sale_svc.VAT_RATE,
        wht_rate=0,
        lines=lines,
        buyer=nb,
        header_discount_amount=header_discount,
        price_includes_vat=bool(sale["price_includes_vat"]),
    )
    doc_id = draft["id"]

    st = settings_svc.get_settings(cur, tenant_id=tenant_id)
    # 升级在收银台直开,不走销项审批工作流(approval_mode 固定 none)。
    doc, err = doc_svc.issue_document(
        cur,
        tenant_id=tenant_id,
        doc_id=doc_id,
        prefix=st["number_prefix"],
        reset=st["number_reset"],
        on=_resolve_issue_date(sale.get("sold_at")),
        start=st["number_start"],
        approval_mode="none",
    )
    if err:
        # 契约 04 §6:升级仅暴露 tax_id_invalid(买方税号/完整性)与 already_upgraded。
        raise PosError("pos.tax_id_invalid", 422, detail=err)

    sales_store.set_full_invoice_id(cur, tenant_id=tenant_id, sale_id=sale_id, doc_id=doc_id)
    return {
        "document": {
            "id": str(doc["id"]),
            "doc_number": doc["doc_number"],
            "doc_type": doc["doc_type"],
        }
    }
