"""Paged Cowork LINE document review cards."""

from __future__ import annotations

import math
import os

from services.cowork_line import flow_cards


def _field_value(fields: dict, key: str, *, limit: int = 80) -> str:
    aliases = {
        "invoice_number": ("invoice_no",),
        "date": ("invoice_date",),
        "seller_tax": ("seller_tax_id",),
        "seller_address": ("seller_addr",),
        "buyer_tax": ("buyer_tax_id",),
        "buyer_address": ("buyer_addr",),
        "vat": ("vat_amount",),
        "name": ("description", "item_name", "product_name"),
        "qty": ("quantity",),
        "price": ("unit_price",),
        "subtotal": ("amount", "line_total"),
    }
    for name in (key, *aliases.get(key, ())):
        value = fields.get(name)
        if value not in (None, "", [], {}):
            return str(value)[:limit]
    return "-"


def _kv(label: str, value: str) -> dict:
    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "sm",
        "contents": [
            {
                "type": "text",
                "text": label,
                "size": "xxs",
                "color": "#777777",
                "flex": 2,
                "wrap": True,
            },
            {
                "type": "text",
                "text": value,
                "size": "xxs",
                "weight": "bold",
                "align": "end",
                "flex": 3,
                "wrap": True,
            },
        ],
    }


def _items(fields: dict) -> list[dict]:
    return [item for item in fields.get("items") or [] if isinstance(item, dict)]


def _review_pages(fields: dict) -> int:
    return 1 + math.ceil(len(_items(fields)) / 6)


def _edit_uri(draft_id: str) -> str:
    liff_id = os.getenv("LINE_COWORK_LIFF_ID", "").strip() or os.getenv("LINE_LIFF_ID", "").strip()
    if liff_id:
        return f"https://liff.line.me/{liff_id}?draft={draft_id}"
    return f"https://pearnly.com/liff/cowork-intake/{draft_id}"


def preview_card(
    *,
    draft_id: str,
    fields: dict,
    target: dict,
    direction: str,
    mode: str,
    lang: str,
    page: int = 0,
    record_index: int = 0,
    record_count: int = 1,
    preflight: dict | None = None,
) -> dict:
    total_pages = _review_pages(fields)
    page = max(0, min(int(page), total_pages - 1))
    body = [
        _kv(
            flow_cards._t(lang, "target"),
            str(target.get("label") or target.get("name") or "-"),
        ),
        _kv(flow_cards._t(lang, "direction"), flow_cards._t(lang, direction)),
        _kv(flow_cards._t(lang, "mode"), flow_cards._t(lang, mode)),
        {"type": "separator", "margin": "md", "color": "#EEEAF7"},
    ]
    if preflight is not None:
        reason = str(preflight.get("block_reason") or "")
        body.append(
            _kv(
                flow_cards._t(lang, "preflight"),
                (
                    flow_cards._t(lang, "ready")
                    if preflight.get("ok")
                    else f"{flow_cards._t(lang, 'not_ready')}: {reason}"
                ),
            )
        )
    if page == 0:
        labels = flow_cards._HEADER_LABELS[flow_cards._lang(lang)]
        body.extend(
            _kv(label, _field_value(fields, key))
            for key, label in zip(flow_cards._HEADER_KEYS, labels, strict=True)
        )
        body.append(_kv(flow_cards._t(lang, "items"), str(len(_items(fields)))))
    else:
        start = (page - 1) * 6
        for index, item in enumerate(_items(fields)[start : start + 6], start=start + 1):
            name = _field_value(item, "name")
            qty = _field_value(item, "qty")
            price = _field_value(item, "price")
            amount = _field_value(item, "subtotal")
            body.append(flow_cards._row(f"{index}. {name}", f"{qty} × {price} = {amount}"))
    nav = []
    if page > 0:
        nav.append(
            flow_cards._button(
                flow_cards._t(lang, "prev"),
                "cowork_preview_page",
                draft=draft_id,
                page=page - 1,
                record=record_index,
            )
        )
    if page + 1 < total_pages:
        nav.append(
            flow_cards._button(
                flow_cards._t(lang, "next"),
                "cowork_preview_page",
                draft=draft_id,
                page=page + 1,
                record=record_index,
            )
        )
    if nav:
        body.append(
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "md",
                "spacing": "sm",
                "contents": nav,
            }
        )
    body.append(_kv(flow_cards._t(lang, "page"), f"{page + 1}/{total_pages}"))
    if record_count > 1:
        record_nav = []
        if record_index > 0:
            record_nav.append(
                flow_cards._button(
                    flow_cards._t(lang, "prev"),
                    "cowork_preview_record",
                    draft=draft_id,
                    record=record_index - 1,
                )
            )
        if record_index + 1 < record_count:
            record_nav.append(
                flow_cards._button(
                    flow_cards._t(lang, "next"),
                    "cowork_preview_record",
                    draft=draft_id,
                    record=record_index + 1,
                )
            )
        body.append(_kv("Document", f"{record_index + 1}/{record_count}"))
        body.append(
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "sm",
                "spacing": "sm",
                "contents": record_nav,
            }
        )
    footer_contents = []
    if preflight is None or preflight.get("ok"):
        footer_contents.append(
            flow_cards._button(
                flow_cards._t(lang, "confirm"),
                "cowork_confirm",
                style="primary",
                draft=draft_id,
            )
        )
    footer_contents.extend(
        [
            {
                "type": "button",
                "style": "secondary",
                "height": "sm",
                "action": {
                    "type": "uri",
                    "label": flow_cards._t(lang, "edit")[:20],
                    "uri": _edit_uri(draft_id),
                },
            },
            flow_cards._button(
                flow_cards._t(lang, "discard"),
                "cowork_discard",
                draft=draft_id,
            ),
        ]
    )
    return {
        "type": "flex",
        "altText": flow_cards._t(lang, "review"),
        "contents": {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "contents": [
                    {
                        "type": "text",
                        "text": flow_cards._t(lang, "review"),
                        "size": "lg",
                        "weight": "bold",
                        "wrap": True,
                    },
                    *body,
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "paddingAll": "14px",
                "contents": footer_contents,
            },
        },
    }


__all__ = ["preview_card"]
