"""Cowork LINE ERP selection and compact draft review cards."""

from __future__ import annotations

import math
from urllib.parse import urlencode

from services.cowork_line.card_fields import HEADER_KEYS, HEADER_LABELS

QR_LIMIT = 13
QR_PAGE_SIZE = 11

_COPY = {
    "th": {
        "pick_erp": "เลือก ERP",
        "pick_erp_subtitle": "เลือกปลายทางสำหรับเอกสารชุดนี้",
        "pick_account": "เลือกชุดบัญชี",
        "pick_account_subtitle": "ระบบตรวจสอบการเชื่อมต่อก่อนให้เลือก",
        "pick_direction": "เอกสารประเภทใด",
        "pick_direction_subtitle": "เลือกก่อนอัปโหลด เพื่อให้ลงบัญชีถูกทิศทาง",
        "pick_mode": "เลือกวิธีลงบัญชี",
        "pick_mode_subtitle": "เลือกวิธีบันทึกเอกสารชุดนี้",
        "purchase": "ซื้อ",
        "sales": "ขาย",
        "stock": "สินค้า / สต๊อก",
        "service": "บริการ / ไม่ลงสต๊อก",
        "cash": "เงินสด",
        "credit": "เครดิต",
        "review": "ตรวจสอบเอกสาร",
        "review_hint": "สรุปเอกสาร · เปิดหน้ารายละเอียดเพื่อตรวจสอบและลงบัญชี",
        "target": "ERP / ชุดบัญชี",
        "direction": "ทิศทาง",
        "mode": "วิธีลงบัญชี",
        "items": "รายการ",
        "prev": "ก่อนหน้า",
        "edit": "ดู / แก้ไขรายละเอียด",
        "detail_hint": "แตะเพื่อดูเอกสารต้นฉบับ ฟิลด์ OCR และรายการทั้งหมด",
        "documents": "เอกสาร",
        "discard": "ทิ้ง",
        "preflight": "ตรวจสอบก่อนส่ง",
        "ready": "พร้อมส่ง",
        "not_ready": "ยังส่งไม่ได้",
        "more": "เพิ่มเติม",
    },
    "zh": {
        "pick_erp": "选择 ERP",
        "pick_erp_subtitle": "选择本批单据的推送目标",
        "pick_account": "选择账套",
        "pick_account_subtitle": "系统已在选择前检查连接状态",
        "pick_direction": "选择单据方向",
        "pick_direction_subtitle": "上传前先选择，避免单据方向识别错误",
        "pick_mode": "选择过账方式",
        "pick_mode_subtitle": "选择本批单据的入账方式",
        "purchase": "采购",
        "sales": "销售",
        "stock": "库存商品",
        "service": "服务 / 非库存",
        "cash": "现金",
        "credit": "赊购 / 赊销",
        "review": "复核单据",
        "review_hint": "单据摘要 · 进入明细完成复核与入账",
        "target": "ERP / 账套",
        "direction": "方向",
        "mode": "过账方式",
        "items": "商品明细",
        "prev": "上一页",
        "edit": "查看 / 编辑全部明细",
        "detail_hint": "点击查看原始票据、OCR 全字段和全部商品明细",
        "documents": "发票数量",
        "discard": "丢弃",
        "preflight": "推送预检",
        "ready": "可以推送",
        "not_ready": "暂不可推送",
        "more": "更多",
    },
    "en": {
        "pick_erp": "Choose ERP",
        "pick_erp_subtitle": "Choose where this document batch should be sent",
        "pick_account": "Choose account set",
        "pick_account_subtitle": "Connection status is checked before selection",
        "pick_direction": "Choose document direction",
        "pick_direction_subtitle": "Choose before upload to keep posting direction correct",
        "pick_mode": "Choose posting mode",
        "pick_mode_subtitle": "Choose how this document batch should be posted",
        "purchase": "Purchase",
        "sales": "Sales",
        "stock": "Inventory",
        "service": "Service / non-stock",
        "cash": "Cash",
        "credit": "Credit",
        "review": "Review document",
        "review_hint": "Document summary · open details to review and post",
        "target": "ERP / account set",
        "direction": "Direction",
        "mode": "Posting mode",
        "items": "Items",
        "prev": "Previous",
        "edit": "View / edit details",
        "detail_hint": "Open the originals, all OCR fields, and every item",
        "documents": "Documents",
        "discard": "Discard",
        "preflight": "Push preflight",
        "ready": "Ready",
        "not_ready": "Not ready",
        "more": "More",
    },
    "ja": {
        "pick_erp": "ERP を選択",
        "pick_erp_subtitle": "この書類の送信先を選択してください",
        "pick_account": "帳簿を選択",
        "pick_account_subtitle": "選択前に接続状態を確認します",
        "pick_direction": "書類方向を選択",
        "pick_direction_subtitle": "アップロード前に仕入または売上を選択します",
        "pick_mode": "計上方法を選択",
        "pick_mode_subtitle": "この書類の計上方法を選択してください",
        "purchase": "仕入",
        "sales": "売上",
        "stock": "在庫商品",
        "service": "サービス / 非在庫",
        "cash": "現金",
        "credit": "掛け",
        "review": "書類を確認",
        "review_hint": "書類の概要 · 明細画面で確認して計上してください",
        "target": "ERP / 帳簿",
        "direction": "方向",
        "mode": "計上方法",
        "items": "明細",
        "prev": "前へ",
        "edit": "明細を表示・編集",
        "detail_hint": "原本、OCR 全項目、すべての明細を確認できます",
        "documents": "書類数",
        "discard": "破棄",
        "preflight": "送信前チェック",
        "ready": "送信可能",
        "not_ready": "送信不可",
        "more": "さらに表示",
    },
}

_HEADER_KEYS = HEADER_KEYS
_HEADER_LABELS = HEADER_LABELS


def _lang(lang: str) -> str:
    return lang if lang in _COPY else "th"


def _t(lang: str, key: str) -> str:
    return _COPY[_lang(lang)][key]


def _postback(label: str, action: str, **params) -> dict:
    data = {"a": action, **{key: value for key, value in params.items() if value is not None}}
    return {
        "type": "postback",
        "label": label[:20],
        "data": urlencode(data),
        "displayText": label[:300],
    }


def _button(label: str, action: str, *, style: str = "secondary", **params) -> dict:
    return {
        "type": "button",
        "style": style,
        "height": "sm",
        "action": _postback(label, action, **params),
    }


def _row(title: str, subtitle: str, action: dict | None = None, *, muted: bool = False) -> dict:
    row = {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "13px",
        "margin": "sm",
        "cornerRadius": "12px",
        "borderWidth": "1px",
        "borderColor": "#E7E2F5" if not muted else "#EEEEEE",
        "backgroundColor": "#FFFFFF" if not muted else "#F6F6F6",
        "contents": [
            {"type": "text", "text": title or "-", "weight": "bold", "size": "sm", "wrap": True},
            {
                "type": "text",
                "text": subtitle or " ",
                "size": "xxs",
                "color": "#777777",
                "wrap": True,
                "margin": "xs",
            },
        ],
    }
    if action:
        row["action"] = action
    return row


def _quick_reply_item(label: str, action: str, **params) -> dict:
    return {"type": "action", "action": _postback(label, action, **params)}


def _question(title: str, subtitle: str, items: list[dict]) -> dict:
    message = {"type": "text", "text": f"{title}\n{subtitle}"}
    if items:
        message["quickReply"] = {"items": items}
    return message


def erp_picker_card(targets: list[dict], lang: str) -> dict:
    items = []
    for adapter, label in (("mrerp", "MR.ERP"), ("express", "Express")):
        available = any(
            str(target.get("adapter") or "").lower() == adapter and target.get("selectable")
            for target in targets
        )
        if available:
            items.append(_quick_reply_item(label, "cowork_erp_type", erp=adapter))
    return _question(
        _t(lang, "pick_erp"),
        _t(lang, "pick_erp_subtitle"),
        items,
    )


def account_picker_card(targets: list[dict], adapter: str, lang: str, *, page: int = 0) -> dict:
    targets = [target for target in targets if target.get("selectable")]
    page_count = max(1, math.ceil(len(targets) / QR_PAGE_SIZE))
    page = max(0, min(int(page), page_count - 1))
    start = page * QR_PAGE_SIZE
    items = [
        _quick_reply_item(
            str(item.get("label") or item.get("name") or adapter),
            "cowork_erp_target",
            endpoint=item.get("endpoint_id") or item.get("id"),
            workspace=item.get("workspace_client_id"),
        )
        for item in targets[start : start + QR_PAGE_SIZE]
    ]
    if page > 0:
        items.insert(
            0,
            _quick_reply_item(_t(lang, "prev"), "cowork_erp_type", erp=adapter, page=page - 1),
        )
    if page + 1 < page_count:
        items.append(
            _quick_reply_item(_t(lang, "more"), "cowork_erp_type", erp=adapter, page=page + 1)
        )
    return _question(
        _t(lang, "pick_account"),
        _t(lang, "pick_account_subtitle"),
        items,
    )


def direction_card(lang: str) -> dict:
    return _question(
        _t(lang, "pick_direction"),
        _t(lang, "pick_direction_subtitle"),
        [
            _quick_reply_item(_t(lang, "purchase"), "cowork_direction", direction="purchase"),
            _quick_reply_item(_t(lang, "sales"), "cowork_direction", direction="sales"),
        ],
    )


def mode_card(adapter: str, direction: str, lang: str) -> dict:
    if adapter == "express":
        options = ("stock", "service")
    else:
        options = ("credit",) if direction == "purchase" else ("cash", "credit")
    return _question(
        _t(lang, "pick_mode"),
        _t(lang, "pick_mode_subtitle"),
        [
            _quick_reply_item(_t(lang, value), "cowork_posting_mode", mode=value)
            for value in options
        ],
    )


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
) -> dict:
    from services.cowork_line.review_cards import preview_card as build

    return build(
        draft_id=draft_id,
        fields=fields,
        target=target,
        direction=direction,
        mode=mode,
        lang=lang,
        record_count=record_count,
        item_count=item_count,
        preflight=preflight,
    )
