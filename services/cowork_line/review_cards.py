"""Summary-only Cowork LINE document review card."""

from __future__ import annotations

import os

from services.cowork_line import flow_cards
from services.cowork_line.card_reasons import reason_text
from services.line_platform.summary_review_card import (
    build_summary_card,
    postback_action as build_postback_action,
)
from services.line_platform.system_i18n import field_value


def _field_value(fields: dict, key: str, lang: str, *, limit: int = 80) -> str:
    aliases = {
        "invoice_number": ("invoice_no",),
        "date": ("invoice_date",),
        "seller_tax": ("seller_tax_id",),
        "seller_address": ("seller_addr",),
        "buyer_tax": ("buyer_tax_id",),
        "buyer_address": ("buyer_addr",),
        "vat": ("vat_amount",),
    }
    for name in (key, *aliases.get(key, ())):
        value = fields.get(name)
        if value not in (None, "", [], {}):
            return field_value(lang, key, value)[:limit]
    return "-"


def _kv(label: str, value: str, *, accent: str | None = None) -> dict:
    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "sm",
        "contents": [
            {
                "type": "text",
                "text": label,
                "size": "xxs",
                "color": accent or "#777777",
                "weight": "bold" if accent else "regular",
                "flex": 2,
                "wrap": True,
            },
            {
                "type": "text",
                "text": value,
                "size": "sm" if accent else "xxs",
                "weight": "bold",
                "color": accent or "#1B1B2B",
                "align": "end",
                "flex": 3,
                "wrap": True,
            },
        ],
    }


def _items(fields: dict) -> list[dict]:
    return [item for item in fields.get("items") or [] if isinstance(item, dict)]


def _edit_uri(draft_id: str) -> str:
    liff_id = os.getenv("LINE_COWORK_LIFF_ID", "").strip() or os.getenv("LINE_LIFF_ID", "").strip()
    if liff_id:
        return f"https://liff.line.me/{liff_id}/?flow=cowork-intake&draft={draft_id}"
    return f"https://pearnly.com/liff/cowork-intake?flow=cowork-intake&draft={draft_id}"


def preview_card(
    *,
    draft_id: str,
    fields: dict,
    target: dict,
    direction: str,
    mode: str,
    lang: str,
    record_count: int = 1,
    item_count: int | None = None,
    preflight: dict | None = None,
    edit_uri: str | None = None,
    discard_action: dict | None = None,
) -> dict:
    accent = "#16873E" if direction == "purchase" else "#B11B50"
    adapter = str(target.get("adapter") or "").lower()
    erp_name = "MR.ERP" if adapter == "mrerp" else "Express" if adapter == "express" else "ERP"
    account_name = str(
        target.get("workspace_name") or target.get("label") or target.get("name") or "-"
    )
    target_name = erp_name if account_name == erp_name else f"{erp_name} · {account_name}"
    body = [
        _kv(flow_cards._t(lang, "target"), target_name),
        _kv(flow_cards._t(lang, "direction"), flow_cards._t(lang, direction)),
        _kv(flow_cards._t(lang, "mode"), flow_cards._t(lang, mode)),
        _kv(flow_cards._t(lang, "documents"), str(max(1, record_count))),
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
                    else reason_text(flow_cards._lang(lang), reason)
                    or flow_cards._t(lang, "not_ready")
                ),
            )
        )
    labels = flow_cards._HEADER_LABELS[flow_cards._lang(lang)]
    body.extend(
        _kv(
            label,
            _field_value(fields, key, lang),
            accent=accent if key == "total_amount" else None,
        )
        for key, label in zip(flow_cards._HEADER_KEYS, labels, strict=True)
    )
    title = f"{flow_cards._t(lang, 'review')} · {flow_cards._t(lang, direction)}"
    return build_summary_card(
        title=title,
        subtitle=flow_cards._t(lang, "review_hint"),
        alt_text=title,
        accent=accent,
        summary=body,
        detail_label=flow_cards._t(lang, "items"),
        detail_count=len(_items(fields)) if item_count is None else item_count,
        detail_hint=flow_cards._t(lang, "detail_hint"),
        edit_label=flow_cards._t(lang, "edit"),
        edit_uri=edit_uri or _edit_uri(draft_id),
        discard_action=discard_action
        or build_postback_action(flow_cards._t(lang, "discard"), "cowork_discard", draft_id),
    )


__all__ = ["preview_card"]
