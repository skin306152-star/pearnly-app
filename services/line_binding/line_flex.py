# -*- coding: utf-8 -*-
"""LINE OCR 结果 Flex 卡(纯构建 · 替纯文字 · 阶段三)。

字段 + 置信"请核"标 + [确认入采购][记为费用][修改] 按钮(前两个 postback 接 intake 分流,
修改走 LIFF 在 LINE 内开网页复核屏)。labels 由调用方按语言注入(保持本模块纯/可测,不耦合
i18n)。低置信字段(field_confidence < 0.85)着琥珀 + 追"请核"标,喂 §5.4 需复核高亮。
"""

from __future__ import annotations

from services.line_binding import line_postback

ESCALATE_CONF = 0.85
_AMBER = "#D97706"
_INK = "#262626"
_MUTE = "#8C8C8C"


def _is_low(field_confidence: dict, key: str) -> bool:
    c = (field_confidence or {}).get(key)
    return c is not None and c < ESCALATE_CONF


def _field_row(label: str, value, low: bool, review_mark: str):
    val = str(value) if (value not in (None, "")) else "-"
    if low and review_mark:
        val = f"{val} {review_mark}"
    return {
        "type": "box",
        "layout": "baseline",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": _MUTE, "flex": 2},
            {
                "type": "text",
                "text": val,
                "size": "sm",
                "color": _AMBER if low else _INK,
                "flex": 4,
                "wrap": True,
            },
        ],
    }


def _btn(label: str, *, data: str = "", uri: str = "", style: str = "primary"):
    action = (
        {"type": "uri", "label": label, "uri": uri}
        if uri
        else {"type": "postback", "label": label, "data": data, "displayText": label}
    )
    return {"type": "button", "style": style, "height": "sm", "action": action}


def ocr_result_flex(
    *, fields: dict, field_confidence: dict, doc_id: str, labels: dict, liff_url: str = ""
) -> dict:
    """OCR 字段 → Flex message dict。labels 键:head/vendor/no/date/amount/confirm/expense/
    edit/review_mark(调用方按语言填)。返回可直接 push 的 {type:flex,...}。"""
    f = fields or {}
    fc = field_confidence or {}
    mark = labels.get("review_mark", "")
    vendor = f.get("seller_name") or f.get("vendor") or ""
    inv_no = f.get("invoice_number") or f.get("invoice_no") or ""
    date = f.get("date") or ""
    amount = f.get("total_amount") or f.get("total") or ""

    body = [
        {"type": "text", "text": labels.get("head", ""), "weight": "bold", "size": "md"},
        {"type": "separator", "margin": "md"},
        _field_row(labels.get("vendor", ""), vendor, _is_low(fc, "seller_tax"), mark),
        _field_row(labels.get("no", ""), inv_no, _is_low(fc, "invoice_number"), mark),
        _field_row(labels.get("date", ""), date, _is_low(fc, "date"), mark),
        _field_row(labels.get("amount", ""), amount, _is_low(fc, "total_amount"), mark),
    ]

    footer = [
        _btn(labels.get("confirm", ""), data=line_postback.confirm_data(doc_id), style="primary"),
        _btn(
            labels.get("expense", ""),
            data=line_postback.redirect_data(doc_id, "expense"),
            style="secondary",
        ),
    ]
    if liff_url:
        footer.append(_btn(labels.get("edit", ""), uri=liff_url, style="secondary"))

    return {
        "type": "flex",
        "altText": labels.get("head", "OCR"),
        "contents": {
            "type": "bubble",
            "body": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": body},
            "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": footer},
        },
    }


_EXPENSE_TYPE_LABEL = {"goods": "🛍 สินค้า", "service": "🔧 บริการ"}


def expense_confirm_flex(*, draft: dict, draft_id: str, labels: dict, edit_url: str = "") -> dict:
    """文本/图片路记账确认卡(doc 10 §5:提议确认,不静默)。字段对齐 Paypers(全字段)。

    labels 键:head/amount/doc_type/inv_no/exp_type/date/category/subcategory/business/detail/
    vendor/confirm/discard/edit(调用方按语言填)。金额永远显示算出的总额供一眼核对(doc 10 §3)。
    空字段显示"-"。按钮走 postback(确认/丢弃),绝不自动入账。
    """
    d = draft or {}
    amount = d.get("amount")
    amount_str = f"{amount} {d.get('currency') or 'THB'}" if amount not in (None, "") else "-"
    exp_type = _EXPENSE_TYPE_LABEL.get(d.get("expense_type") or "", d.get("expense_type") or "")

    body = [
        {"type": "text", "text": labels.get("head", ""), "weight": "bold", "size": "md"},
        {"type": "text", "text": amount_str, "weight": "bold", "size": "xl", "color": _INK},
        {"type": "separator", "margin": "md"},
        _field_row(labels.get("doc_type", ""), d.get("document_type"), False, ""),
        _field_row(labels.get("inv_no", ""), d.get("invoice_number"), False, ""),
        _field_row(labels.get("exp_type", ""), exp_type, False, ""),
        _field_row(labels.get("date", ""), d.get("doc_date"), False, ""),
        _field_row(labels.get("category", ""), d.get("category"), False, ""),
        _field_row(labels.get("subcategory", ""), d.get("subcategory"), False, ""),
        _field_row(labels.get("business", ""), d.get("business_name"), False, ""),
        _field_row(labels.get("detail", ""), d.get("note"), False, ""),
        _field_row(labels.get("vendor", ""), d.get("vendor_name"), False, ""),
    ]
    footer = [
        _btn(
            labels.get("confirm", ""),
            data=line_postback.expense_confirm_data(draft_id),
            style="primary",
        ),
        _btn(
            labels.get("discard", ""),
            data=line_postback.expense_discard_data(draft_id),
            style="secondary",
        ),
    ]
    if edit_url:
        footer.append(_btn(labels.get("edit", ""), uri=edit_url, style="secondary"))

    return {
        "type": "flex",
        "altText": labels.get("head", "expense"),
        "contents": {
            "type": "bubble",
            "body": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": body},
            "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": footer},
        },
    }
