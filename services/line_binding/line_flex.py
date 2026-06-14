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
