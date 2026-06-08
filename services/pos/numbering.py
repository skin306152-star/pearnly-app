# -*- coding: utf-8 -*-
"""POS 小票连号 — 终端分段连号(POS 项目 · PO-B2 · docs/pos/08 ADR-3)。

每终端独立号段,前缀含终端码 → 离线生成即正式号,联网不重编。格式 <前缀>-T<终端>-<年>-<流水>
(如 RCP-T1-2026-00001)。底层复用销项 document_number_sequences(FOR UPDATE 防跳号),按
(tenant, doc_type, prefix, period) 计数;prefix 含终端码 ⇒ 每终端各自连续。

allocate 必须在已开启事务的 cursor 上调用(防并发跳号)。
"""

from __future__ import annotations

from datetime import date

from services.sales import numbering as sales_numbering

# 单据类型 → 号前缀(receipt 小票 / abbrev 简式税票 / refund 退货)。
_PREFIX = {
    "receipt": "RCP",
    "abbrev_tax_invoice": "ABB",
    "refund": "RFD",
}


def next_number(
    cur, *, tenant_id: str, terminal_id, kind: str, on: date, workspace_client_id=None
) -> tuple[str, int]:
    """取该终端下一个连号 → (展示号, 流水号)。kind ∈ receipt/abbrev_tax_invoice/refund。

    PO-7b:计号键含主体(每终端属一个门店/套账 → 单主体下号序不变,多主体跨店不撞)。
    """
    base = _PREFIX.get(kind, "RCP")
    prefix = f"{base}-T{terminal_id}-"
    return sales_numbering.allocate(
        cur,
        tenant_id=tenant_id,
        doc_type=f"pos_{kind}",
        prefix=prefix,
        reset=sales_numbering.RESET_YEARLY,
        on=on,
        workspace_client_id=workspace_client_id,
    )
