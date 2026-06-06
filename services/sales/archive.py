# -*- coding: utf-8 -*-
"""开票留底存档哈希(E3 · docs/16 §E3)。

开出时确定性渲染规范存档件(A4/正本)取 sha256 写回 sales_documents.pdf_sha256,任何时候
可复算核验已开票未被篡改。审计增强、非合规闸:渲染失败只记日志、留 NULL,绝不回滚已开出的
票。供 document.finalize_issue 与 credit_note 共用。
"""

from __future__ import annotations

import logging


def store_archival_hash(cur, tenant_id: str, doc_id, doc: dict, snapshot: dict) -> None:
    """渲染存档件取 sha256 写回 pdf_sha256(失败兜底,不抛)。"""
    try:
        from services.sales import pdf as pdf_svc

        digest = pdf_svc.archival_sha256(doc, snapshot.get("seller"), snapshot.get("buyer"))
    except Exception:
        logging.getLogger("mr-pilot").exception("sales archival hash failed doc=%s", doc_id)
        return
    cur.execute(
        "UPDATE sales_documents SET pdf_sha256=%s WHERE tenant_id=%s AND id=%s",
        (digest, tenant_id, doc_id),
    )
    doc["pdf_sha256"] = digest
