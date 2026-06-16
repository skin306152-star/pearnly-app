# -*- coding: utf-8 -*-
"""置信驱动入账编排(文/图共用 · PO-11 · docs/smart-intake/15)。

把「建草稿 → 按置信 + auto_book 决定是否直接过账」这套从文本路(line_expense._do_record)和
图片路(line_ingest.ingest_line_image)各写一份的逻辑收成一处,行为一致(决策1):
auto_book 开(默认)→ 高置信齐全直接入正式账(可一键撤销);auto_book 关 → 先草稿发确认卡。
调用方管事务/分类/数据卡;本函数只做 create_doc → (条件) post_doc → 返回 (doc_id, state)。
"""

from __future__ import annotations

from services.purchase import docs as docs_svc
from services.purchase import posting as posting_svc


def book_by_confidence(
    cur, *, tenant_id, workspace_client_id, data, settings, verdict, created_by
) -> tuple[str, str]:
    """建草稿 → 高置信且 auto_book 开则过账。返回 (doc_id, state)。state ∈ posted|confirm|dup。"""
    created = docs_svc.create_doc(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        created_by=created_by,
        data=data,
        settings=settings,
        status="draft",
    )
    doc_id = str(created["doc"]["id"])
    if verdict.action == "post" and bool(settings.get("auto_book")):
        posting_svc.post_doc(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=doc_id,
            auto_stock_in=bool(settings.get("auto_stock_in")),
            created_by=created_by,
        )
        return doc_id, "posted"
    return doc_id, ("dup" if verdict.dup else "confirm")
