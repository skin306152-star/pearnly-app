# -*- coding: utf-8 -*-
"""进项腿:OCR history → purchase_docs(posted)。

复用 services/purchase/intake.build_draft_from_invoice 的既有映射(费用/进项票判定、明细
兜底、票面合计尊重)+ docs.create_doc / posting.post_doc 既有建单-过账链路,不重写一遍。

置信度门控(resolve_image_intake 的 auto_book 判据)在这里**不重跑**:用户已经在录入工作台
点了「确认」,人闸已经过了,不该再拿机器置信度去二次拦一个人已经看过的东西。
"""

from __future__ import annotations

from core.pos_api import PosError
from services.intake_bridge.errors import SkipConversion
from services.purchase import docs as docs_svc
from services.purchase import intake as intake_svc
from services.purchase import posting as posting_svc
from services.purchase import settings as settings_svc


def book_from_history(cur, *, tenant_id, workspace_client_id, created_by, fields: dict) -> tuple:
    """建进项单据(draft)并立即过账(posted)。返回 (doc_id, doc_no)。

    doc_kind(purchase_invoice/expense)判定沿用 intake.judge_direction —— 与录入工作台
    自动分流同一套规则,不另立一套"确认转换专用"判据造口径分裂。费用票即便没有 items 也能
    建单:build_draft_from_invoice 无明细时按票面总额/税前小计收敛成单行兜底。
    """
    kind, _route = intake_svc.judge_direction(fields)
    draft = intake_svc.build_draft_from_invoice(fields, kind=kind)
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
