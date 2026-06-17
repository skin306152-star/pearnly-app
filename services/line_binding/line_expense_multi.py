# -*- coding: utf-8 -*-
"""LINE 文字多项一句话 → 拆多笔、逐项归类、合计入账(从 line_expense 拆出·控行数)。

「电费50 买菜40 电费10 吃饭50」→ 每项独立行 + 智能批量归类 + 合计落采购,卡显逐条明细
(对标 Paypers รายการค่าใช้จ่าย)。解析在 line_quick_entry.parse_multi(确定性正则)。
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from core import db


def do_record_multi(bound_user, reply_token, text, tid, ws, items, quote_token, lang) -> bool:
    """每项独立行 + 智能归类(批量一次 LLM)·合计入账·卡显逐条明细。返回 True。"""
    from services.expense import category_ai, confidence, line_l2
    from services.expense.line_quick_entry import qty_label, split_qty_price
    from services.line_binding import line_booker
    from services.purchase import categories as cat_svc
    from services.purchase import intake as intake_svc
    from services.purchase import settings as settings_svc

    created_by = str(bound_user["id"]) if bound_user.get("id") else None
    api_key = line_l2.resolve_api_key(bound_user)
    today = date.today().isoformat()
    with db.get_cursor_rls(tid, commit=True) as cur:
        tree = cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws)
        # 优先 LLM 智能拆(口语「ฉันซื้อน้ำดื่ม 10 บาท ทุเรียน 300」→ 干净项目名+额+分类+日期+卖家·
        # 治正则乱拆);无 key/失败 → 退正则项 + 批量归类(清晰空格分隔仍可用)。
        parsed = category_ai.parse_and_categorize(text, tree, api_key=api_key)
        doc_date, vendor = today, ""
        if parsed:
            items = parsed["items"]
            cats = [(it["category_id"], it["subcategory_id"]) for it in items]
            doc_date = parsed.get("date") or today
            vendor = parsed.get("vendor") or ""
        else:
            cats = category_ai.categorize_items(items, tree, api_key=api_key)
        total = sum((it["amount"] for it in items), Decimal("0"))
        # 数量(#8):每项「2杯咖啡 120」→ 行 qty=2、单价=60(split_qty_price·总额不漂)。
        lines = []
        for it, (cid, sid) in zip(items, cats):
            _q, _up = split_qty_price(it["amount"], it.get("qty"))
            lines.append(
                {
                    "item_type": "goods",
                    "description": it["name"],
                    "qty": _q,
                    "unit_price": _up,
                    "vat_rate": 0,
                    "wht_rate": 0,
                    "category_id": cid,
                    "subcategory_id": sid,
                }
            )
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
        data = line_booker.to_purchase_data(
            lines=lines,
            doc_date=doc_date,
            category_id=doc_cat,
            supplier={"name": vendor},
        )
        verdict = confidence.grade(
            amount=str(total),
            vendor_name=vendor,
            invoice_number="",
            document_type="",
            direction="expense",
            confidence_band="high",
            has_category=bool(doc_cat),
            is_duplicate=False,
            require_category=False,
        )
        doc_id, state, token = line_booker.book_and_mint(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            data=data,
            settings=cfg,
            verdict=verdict,
            created_by=created_by,
        )
    names = [it["name"] for it in items]
    card_fields = {
        "document_type": "",
        "expense_type": "goods",
        "date": doc_date,
        "category": cat_name,
        "subcategory": sub_name,
        "vendor": vendor,
        "items": [
            {"name": qty_label(it["name"], it.get("qty")), "amount": f"{it['amount']:,.2f}"}
            for it in items
        ],
        "detail": " · ".join(names[:3]) + (f" 等{len(names)}项" if len(names) > 3 else ""),
    }
    line_booker.emit_result_card(
        reply_token,
        state=state,
        amount=str(total),
        fields=card_fields,
        doc_id=doc_id,
        lang=lang,
        quote_token=quote_token,
        workspace_name=ws_name,
        token=token,
        workspace_client_id=str(ws or ""),
    )
    return True
