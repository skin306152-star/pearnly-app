# -*- coding: utf-8 -*-
"""LINE 记账结果卡渲染(从 line_expense 抽出·纯展示层)。

草稿/文本记账入账后的「卡上方一行话 + Flex 数据卡」组装。数字全来自 draft(零编造),
ack_text 传入=大脑暖话显示在卡上方,空=回落 line_booker 的模板句(图/文旧路不变)。
"""

from __future__ import annotations


def card_fields_from_draft(draft) -> dict:
    """ExpenseDraft → 数据卡归一字段(#10b 详情结构化:逐条 `物品 ×数量 ฿金额`·物品名=draft.note 清出名)。"""
    from services.expense.line_quick_entry import qty_label

    item = (draft.note or "").strip()
    items = []
    if item and draft.amount is not None:
        items = [{"name": qty_label(item, draft.qty), "amount": f"{draft.amount:,.2f}"}]
    return {
        "document_type": draft.document_type or "",
        "expense_type": draft.expense_type or "",
        "date": draft.doc_date or "",
        "category": draft.category or "",
        "subcategory": draft.subcategory or "",
        "vendor": draft.vendor_name or "",
        "seller_tax": getattr(draft, "vendor_tax_id", "") or "",
        "invoice_number": draft.invoice_number or "",
        "payment_method": getattr(draft, "payment_method", "") or "",
        "items": items,
        "detail": item,
    }


def reply_card(
    reply_token,
    state,
    draft,
    doc_id,
    lang,
    quote_token,
    workspace_name="",
    token="",
    ws="",
    tenant_id=None,
    line_user_id="",
    ack_text="",
) -> None:
    """回执 = 卡上方一行话(ack_text 传入=大脑暖话·否则回落模板)+ Flex 数据卡(三路共用)。"""
    from services.line_binding import line_booker

    line_booker.emit_result_card(
        reply_token,
        state=state,
        amount=draft.amount,
        fields=card_fields_from_draft(draft),
        doc_id=doc_id,
        lang=lang,
        quote_token=quote_token,
        workspace_name=workspace_name,
        token=token,
        workspace_client_id=ws,
        tenant_id=tenant_id,
        line_user_id=line_user_id,
        ack_text=ack_text,
    )
