# -*- coding: utf-8 -*-
"""建单落库:每行 → 账本草稿(采购/销项)+ ocr_history(ERP 推送读源)。

两张表本就独立无 FK(账本用于对账/复核,ocr_history 是 MR.ERP/Express 推送唯一读源)。本模块
逐行两边都写,用 ocr_history.source_ref 反指账本单据 id 做可追溯。逐行独立事务——某行失败只该行
落 failed,不连坐其它行(Zihao:真实失败要看得见,不是全部成功的假象)。

账本建单复用既有手工入口,零重造:采购走 intake.build_draft_from_invoice → docs.create_doc;
销项走 sales.document.create_draft(只落草稿,不抢发号/不过账)。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core import db
from services.purchase import docs as docs_svc
from services.purchase import intake as intake_svc
from services.sales import document as sales_svc

_SUMMARY_SOURCE = "summary_table_batch"


def _clean_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """剥内部下划线字段(_direction/_walkin/_product_code)→ ERP mapper / ocr_history 读的干净 fields。"""
    return {k: v for k, v in fields.items() if not k.startswith("_")}


def _sales_lines(fields: Dict[str, Any]) -> List[Dict[str, Any]]:
    """items → 销项明细行(qty×unit_price;vat 由 create_draft 按 vat_rate 统一算)。"""
    lines: List[Dict[str, Any]] = []
    for it in fields.get("items") or []:
        lines.append(
            {
                "description": (it.get("name") or "").strip() or "-",
                "qty": it.get("qty") or "1",
                "unit_price": it.get("price") or it.get("subtotal") or "0",
                "vat_applicable": True,
            }
        )
    if not lines:
        lines = [
            {
                "description": "-",
                "qty": "1",
                "unit_price": fields.get("subtotal") or fields.get("total_amount") or "0",
                "vat_applicable": True,
            }
        ]
    return lines


def _buyer_block(fields: Dict[str, Any]) -> Dict[str, Any]:
    """销项买方块。有 13 位税号 → 公司;散客/无税号 → 匿名(anonymous · normalize_buyer 会清税号)。"""
    from services.purchase.field_clean import clean_tax_id

    tax = clean_tax_id(fields.get("buyer_tax"))
    if tax:
        btype = "company"
    else:
        btype = "anonymous"
    return {
        "type": btype,
        "name": (fields.get("buyer_name") or "").strip(),
        "address": (fields.get("buyer_addr") or "").strip(),
        "tax_id": tax,
    }


def _payment_block(fields: Dict[str, Any]) -> Dict[str, Any]:
    from services.erp.express_push.common import payment_is_paid

    paid = payment_is_paid(fields)
    status = "paid" if paid is True else "unpaid"
    return {
        "status": status,
        "payment_method": (fields.get("payment_method") or "").strip() or None,
    }


def _create_purchase(cur, *, tenant_id, ws_id, created_by, fields) -> str:
    """采购/费用草稿。kind 由 intake.judge_direction 定(税票+VAT+买方身份=进项票,否则费用)。"""
    kind, _ = intake_svc.judge_direction(fields)
    draft = intake_svc.build_draft_from_invoice(fields, kind=kind, categories=None)
    draft["source"] = _SUMMARY_SOURCE
    created = docs_svc.create_doc(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=ws_id,
        created_by=created_by,
        data=draft,
        settings={},
        status="draft",
    )
    return created["doc"]["id"]


def _create_sales(cur, *, tenant_id, ws_id, created_by, fields, has_vat) -> str:
    """销项草稿(不发号、不过账)。买方=对方(散客则匿名),行取自 items。"""
    doc = sales_svc.create_draft(
        cur,
        tenant_id=tenant_id,
        created_by=created_by,
        doc_type="tax_invoice" if has_vat else "receipt",
        client_id=None,
        seller_workspace_client_id=ws_id,
        currency="THB",
        vat_rate=7 if has_vat else 0,
        wht_rate=0,
        lines=_sales_lines(fields),
        buyer=_buyer_block(fields),
        payment=_payment_block(fields),
    )
    return doc["id"]


def _write_ocr_history(
    *, created_by, tenant_id, ws_id, fields, doc_id, batch_ref, index
) -> Optional[str]:
    """写推送读源。source_ref 反指账本单据 id;workspace_client_id 让推送时能解析账套税号判方向。"""
    return db.insert_ocr_history(
        user_id=created_by,
        filename=f"summary-{batch_ref}-{index + 1}",
        page_count=1,
        pages=[{"fields": fields, "is_copy": False, "is_duplicate": False}],
        confidence="manual",
        elapsed_ms=0,
        source=_SUMMARY_SOURCE,
        source_ref=str(doc_id),
        tenant_id=tenant_id,
        workspace_client_id=ws_id,
    )


def commit_rows(
    *,
    tenant_id: str,
    workspace_client_id: int,
    created_by: Optional[str],
    rows: List[Dict[str, Any]],
    batch_ref: str = "batch",
) -> List[Dict[str, Any]]:
    """整批建单。rows = [{row_index, fields}](已过 mapping;judge 的硬阻断行不应传进来)。

    每行独立事务:账本草稿 + ocr_history 同一游标内建,任一异常整行回滚落 failed。返回逐行结果
    [{row_index, status, doc_id?, ocr_history_id?, direction, error?}]。
    """
    results: List[Dict[str, Any]] = []
    for i, r in enumerate(rows):
        raw = r.get("fields") or {}
        direction = str(raw.get("_direction") or "sales")
        has_vat = raw.get("document_type") != "receipt"
        fields = _clean_fields(raw)
        try:
            with db.get_cursor_rls(
                tenant_id, workspace_client_id=workspace_client_id, commit=True
            ) as cur:
                if direction == "purchase":
                    doc_id = _create_purchase(
                        cur,
                        tenant_id=tenant_id,
                        ws_id=workspace_client_id,
                        created_by=created_by,
                        fields=fields,
                    )
                else:
                    doc_id = _create_sales(
                        cur,
                        tenant_id=tenant_id,
                        ws_id=workspace_client_id,
                        created_by=created_by,
                        fields=fields,
                        has_vat=has_vat,
                    )
            # ocr_history 走独立连接(insert_ocr_history 自管事务);账本已提交后再写,失败不回滚账本。
            ocr_id = _write_ocr_history(
                created_by=created_by,
                tenant_id=tenant_id,
                ws_id=workspace_client_id,
                fields=fields,
                doc_id=doc_id,
                batch_ref=batch_ref,
                index=r.get("row_index", i),
            )
            results.append(
                {
                    "row_index": r.get("row_index", i),
                    "status": "created" if ocr_id else "booked_no_push",
                    "doc_id": str(doc_id),
                    "ocr_history_id": ocr_id,
                    "direction": direction,
                }
            )
        except Exception as e:  # noqa: BLE001 — 逐行兜底:该行失败不连坐,错误如实回传
            results.append(
                {
                    "row_index": r.get("row_index", i),
                    "status": "failed",
                    "direction": direction,
                    "error": str(getattr(e, "code", None) or e)[:200],
                }
            )
    return results
