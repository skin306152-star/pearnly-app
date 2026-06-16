# -*- coding: utf-8 -*-
"""LINE 文字多项一句话 → 拆多笔、逐项归类、合计入账(从 line_expense 拆出·控行数)。

「电费50 买菜40 电费10 吃饭50」→ 每项独立行 + 智能批量归类 + 合计落采购,卡显逐条明细
(对标 Paypers รายการค่าใช้จ่าย)。解析在 line_quick_entry.parse_multi(确定性正则)。
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

from core import db
from services.line_binding import line_client

_WEB_PURCHASE_URL = "https://pearnly.com/home"


def do_record_multi(bound_user, reply_token, text, tid, ws, items, quote_token, lang) -> bool:
    """每项独立行 + 智能归类(批量一次 LLM)·合计入账·卡显逐条明细。返回 True。"""
    from services.expense import category_ai, confidence, line_l2
    from services.line_binding import line_action_nonce as nonce
    from services.line_binding import line_card
    from services.purchase import categories as cat_svc
    from services.purchase import confidence_post
    from services.purchase import intake as intake_svc
    from services.purchase import settings as settings_svc

    created_by = str(bound_user["id"]) if bound_user.get("id") else None
    api_key = line_l2.resolve_api_key(bound_user)
    total = sum((it["amount"] for it in items), Decimal("0"))
    today = date.today().isoformat()
    with db.get_cursor_rls(tid, commit=True) as cur:
        tree = cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws)
        cats = category_ai.categorize_items(items, tree, api_key=api_key)
        lines = [
            {
                "item_type": "goods",
                "description": it["name"],
                "qty": "1",
                "unit_price": str(it["amount"]),
                "vat_rate": 0,
                "wht_rate": 0,
                "category_id": cid,
                "subcategory_id": sid,
            }
            for it, (cid, sid) in zip(items, cats)
        ]
        doc_cat, doc_sub = next(((c, s) for c, s in cats if c), (None, None))
        cat_name = sub_name = ""
        for p in tree:
            if p["id"] == doc_cat:
                cat_name = p["name"]
                sub_name = next(
                    (c["name"] for c in (p.get("children") or []) if c["id"] == doc_sub), ""
                )
        cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
        ws_name = intake_svc.workspace_name(cur, tenant_id=tid, workspace_client_id=ws)
        data = {
            "doc_kind": "expense",
            "source": "line",
            "doc_date": today,
            "category_id": doc_cat,
            "supplier": {"name": ""},
            "currency": "THB",
            "payment_status": "paid",
            "lines": lines,
        }
        verdict = confidence.grade(
            amount=str(total),
            vendor_name="",
            invoice_number="",
            document_type="",
            direction="expense",
            confidence_band="high",
            has_category=bool(doc_cat),
            is_duplicate=False,
            require_category=False,
        )
        doc_id, state = confidence_post.book_by_confidence(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            data=data,
            settings=cfg,
            verdict=verdict,
            created_by=created_by,
        )
        token = nonce.mint(
            cur, tenant_id=tid, workspace_client_id=ws, action_ref=doc_id, user_id=created_by
        )
    names = [it["name"] for it in items]
    card_fields = {
        "document_type": "",
        "expense_type": "goods",
        "date": today,
        "category": cat_name,
        "subcategory": sub_name,
        "vendor": "",
        "items": [{"name": it["name"], "amount": f"{it['amount']:,.2f}"} for it in items],
        "detail": " · ".join(names[:3]) + (f" 等{len(names)}项" if len(names) > 3 else ""),
    }
    _ack_key = {"posted": "exp_ack_posted", "dup": "exp_ack_dup"}.get(state, "exp_ack_confirm")
    ack = {"type": "text", "text": line_client.t_line(lang, _ack_key, amount=str(total))}
    if quote_token:
        ack["quoteToken"] = quote_token
    card = line_card.result_card(
        state=state,
        amount=str(total),
        fields=card_fields,
        doc_id=doc_id,
        lang=lang,
        web_url=_WEB_PURCHASE_URL,
        source="text",
        workspace_name=ws_name,
        token=token,
        liff_id=os.getenv("LINE_LIFF_ID", "").strip(),
        workspace_client_id=str(ws or ""),
    )
    line_client.reply_messages(reply_token, [ack, card])
    return True
