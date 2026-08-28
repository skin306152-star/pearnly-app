# -*- coding: utf-8 -*-
"""进项腿:OCR history → purchase_docs(posted)。

货/费判定走 services/purchase/item_verdict(仓库单一事实源,尊重人工裁决);复用
services/purchase/intake.build_draft_from_invoice 的既有映射(明细兜底、票面合计尊重)
+ docs.create_doc / posting.post_doc 既有建单-过账链路,不重写一遍。

置信度门控(resolve_image_intake 的 auto_book 判据)在这里**不重跑**:用户已经在录入工作台
点了「确认」,人闸已经过了,不该再拿机器置信度去二次拦一个人已经看过的东西。
"""

from __future__ import annotations

from core.pos_api import PosError
from services.intake_bridge.errors import SkipConversion
from services.purchase import docs as docs_svc
from services.purchase import intake as intake_svc
from services.purchase import item_verdict as item_verdict_svc
from services.purchase import posting as posting_svc
from services.purchase import settings as settings_svc


def book_from_history(
    cur, *, tenant_id, workspace_client_id, created_by, fields: dict, source: str = ""
) -> tuple:
    """建进项单据(draft)并立即过账(posted)。返回 (doc_id, doc_no)。

    doc_kind(purchase_invoice/expense)判定改走 item_verdict.item_verdict —— 仓库货/费判据
    单一事实源,尊重复核屏人工裁决(posting_item_type_manual),不另立一套"确认转换专用"
    判据造口径分裂。费用票即便没有 items 也能建单:build_draft_from_invoice 无明细时按
    票面总额/税前小计收敛成单行兜底。
    """
    is_expense, _src = item_verdict_svc.item_verdict(fields)
    kind = "expense" if is_expense else "purchase_invoice"
    draft = intake_svc.build_draft_from_invoice(fields, kind=kind)
    draft["source"] = {"line_erp": "line", "erp_web": "upload"}.get(source, "manual")
    settings = settings_svc.get_settings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    try:
        created = docs_svc.create_doc(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            created_by=created_by,
            data=draft,
            settings=settings,
            status="draft",
        )
    except PosError as e:
        if e.code == "purchase.dup_invoice":
            raise SkipConversion("duplicate") from e
        raise
    doc_id = created["doc"]["id"]
    posted = posting_svc.post_doc(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        doc_id=doc_id,
        auto_stock_in=bool(settings.get("auto_stock_in")),
        created_by=created_by,
    )
    return doc_id, posted["doc"].get("doc_no")
