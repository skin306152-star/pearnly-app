"""Cowork LINE ERP selection and full, paged draft review cards."""

from __future__ import annotations

import math
from urllib.parse import urlencode

_COPY = {
    "th": {
        "pick_erp": "เลือก ERP",
        "pick_account": "เลือกชุดบัญชี",
        "pick_direction": "เอกสารประเภทใด",
        "pick_mode": "เลือกวิธีลงบัญชี",
        "purchase": "ซื้อ",
        "sales": "ขาย",
        "stock": "สินค้า / สต๊อก",
        "service": "บริการ / ไม่ลงสต๊อก",
        "cash": "เงินสด",
        "credit": "เครดิต",
        "offline": "ออฟไลน์",
        "blocked": "ยังไม่พร้อม",
        "review": "ตรวจสอบเอกสาร",
        "target": "ERP / ชุดบัญชี",
        "direction": "ทิศทาง",
        "mode": "วิธีลงบัญชี",
        "items": "รายการ",
        "page": "หน้า",
        "prev": "ก่อนหน้า",
        "next": "ถัดไป",
        "confirm": "ยืนยันลงบัญชี",
        "edit": "แก้ไข",
        "discard": "ทิ้ง",
        "preflight": "ตรวจสอบก่อนส่ง",
        "ready": "พร้อมส่ง",
        "not_ready": "ยังส่งไม่ได้",
        "more": "เพิ่มเติม",
        "in_flight": "มีงานกำลังส่ง",
        "account_locked": "Express กำลังใช้งานชุดบัญชี",
    },
    "zh": {
        "pick_erp": "选择 ERP",
        "pick_account": "选择账套",
        "pick_direction": "选择单据方向",
        "pick_mode": "选择过账方式",
        "purchase": "采购",
        "sales": "销售",
        "stock": "库存商品",
        "service": "服务 / 非库存",
        "cash": "现金",
        "credit": "赊购 / 赊销",
        "offline": "小助手离线",
        "blocked": "暂不可推送",
        "review": "复核单据",
        "target": "ERP / 账套",
        "direction": "方向",
        "mode": "过账方式",
        "items": "商品明细",
        "page": "页",
        "prev": "上一页",
        "next": "下一页",
        "confirm": "确定入账",
        "edit": "编辑",
        "discard": "丢弃",
        "preflight": "推送预检",
        "ready": "可以推送",
        "not_ready": "暂不可推送",
        "more": "更多",
        "in_flight": "已有任务处理中",
        "account_locked": "Express 正在占用该账套",
    },
    "en": {
        "pick_erp": "Choose ERP",
        "pick_account": "Choose account set",
        "pick_direction": "Choose document direction",
        "pick_mode": "Choose posting mode",
        "purchase": "Purchase",
        "sales": "Sales",
        "stock": "Inventory",
        "service": "Service / non-stock",
        "cash": "Cash",
        "credit": "Credit",
        "offline": "Companion offline",
        "blocked": "Not ready",
        "review": "Review document",
        "target": "ERP / account set",
        "direction": "Direction",
        "mode": "Posting mode",
        "items": "Items",
        "page": "Page",
        "prev": "Previous",
        "next": "Next",
        "confirm": "Confirm and post",
        "edit": "Edit",
        "discard": "Discard",
        "preflight": "Push preflight",
        "ready": "Ready",
        "not_ready": "Not ready",
        "more": "More",
        "in_flight": "A task is in progress",
        "account_locked": "Express is using this account set",
    },
    "ja": {
        "pick_erp": "ERP を選択",
        "pick_account": "帳簿を選択",
        "pick_direction": "書類方向を選択",
        "pick_mode": "計上方法を選択",
        "purchase": "仕入",
        "sales": "売上",
        "stock": "在庫商品",
        "service": "サービス / 非在庫",
        "cash": "現金",
        "credit": "掛け",
        "offline": "コンパニオンがオフライン",
        "blocked": "利用不可",
        "review": "書類を確認",
        "target": "ERP / 帳簿",
        "direction": "方向",
        "mode": "計上方法",
        "items": "明細",
        "page": "ページ",
        "prev": "前へ",
        "next": "次へ",
        "confirm": "確認して計上",
        "edit": "編集",
        "discard": "破棄",
        "preflight": "送信前チェック",
        "ready": "送信可能",
        "not_ready": "送信不可",
        "more": "さらに表示",
        "in_flight": "処理中のタスクがあります",
        "account_locked": "Express が帳簿を使用中です",
    },
}

_HEADER_KEYS = (
    "invoice_number",
    "date",
    "document_type",
    "seller_name",
    "seller_tax",
    "seller_branch",
    "seller_address",
    "buyer_name",
    "buyer_tax",
    "buyer_branch",
    "buyer_address",
    "subtotal",
    "discount",
    "vat",
    "wht_amount",
    "total_amount",
    "currency",
    "payment_method",
    "notes",
)
_HEADER_LABELS = {
    "th": (
        "เลขที่เอกสาร",
        "วันที่",
        "ประเภทเอกสาร",
        "ผู้ขาย",
        "เลขภาษีผู้ขาย",
        "สาขาผู้ขาย",
        "ที่อยู่ผู้ขาย",
        "ผู้ซื้อ",
        "เลขภาษีผู้ซื้อ",
        "สาขาผู้ซื้อ",
        "ที่อยู่ผู้ซื้อ",
        "ก่อนภาษี",
        "ส่วนลด",
        "VAT",
        "หัก ณ ที่จ่าย",
        "ยอดรวม",
        "สกุลเงิน",
        "การชำระเงิน",
        "หมายเหตุ",
    ),
    "zh": (
        "单据号码",
        "日期",
        "单据类型",
        "卖方",
        "卖方税号",
        "卖方分店",
        "卖方地址",
        "买方",
        "买方税号",
        "买方分店",
        "买方地址",
        "未税金额",
        "折扣",
        "增值税",
        "预扣税",
        "总金额",
        "币种",
        "付款方式",
        "备注",
    ),
    "en": (
        "Invoice no.",
        "Date",
        "Document type",
        "Seller",
        "Seller tax ID",
        "Seller branch",
        "Seller address",
        "Buyer",
        "Buyer tax ID",
        "Buyer branch",
        "Buyer address",
        "Subtotal",
        "Discount",
        "VAT",
        "WHT",
        "Total",
        "Currency",
        "Payment",
        "Notes",
    ),
    "ja": (
        "書類番号",
        "日付",
        "書類種別",
        "売り手",
        "売り手税番号",
        "売り手支店",
        "売り手住所",
        "買い手",
        "買い手税番号",
        "買い手支店",
        "買い手住所",
        "小計",
        "割引",
        "VAT",
        "源泉税",
        "合計",
        "通貨",
        "支払方法",
        "備考",
    ),
}


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


def _bubble(title: str, rows: list[dict], alt_text: str | None = None) -> dict:
    return {
        "type": "flex",
        "altText": alt_text or title,
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "contents": [
                    {"type": "text", "text": title, "size": "lg", "weight": "bold", "wrap": True},
                    {"type": "separator", "margin": "md", "color": "#EEEAF7"},
                    *rows,
                ],
            },
        },
    }


def erp_picker_card(targets: list[dict], lang: str) -> dict:
    adapters = {str(item.get("adapter") or "").lower() for item in targets}
    rows = []
    for adapter, label in (("mrerp", "MR.ERP"), ("express", "Express")):
        count = sum(1 for item in targets if str(item.get("adapter") or "").lower() == adapter)
        available = adapter in adapters
        action = _postback(label, "cowork_erp_type", erp=adapter) if available else None
        rows.append(
            _row(
                label,
                f"{count} account set(s)" if available else _t(lang, "blocked"),
                action,
                muted=not available,
            )
        )
    return _bubble(_t(lang, "pick_erp"), rows)


def account_picker_card(targets: list[dict], adapter: str, lang: str, *, page: int = 0) -> dict:
    page_size = 8
    page_count = max(1, math.ceil(len(targets) / page_size))
    page = max(0, min(int(page), page_count - 1))
    rows = []
    for item in targets[page * page_size : (page + 1) * page_size]:
        selectable = bool(item.get("selectable"))
        state = str(item.get("connection_state") or "")
        detail = state
        if item.get("missing"):
            detail = " · ".join(str(value) for value in item["missing"][:3])
        checks = item.get("ready_checks") or {}
        if checks.get("local_account_lock") == "waiting_lock":
            detail = _t(lang, "account_locked")
        elif checks.get("cloud_in_flight"):
            detail = f"{detail} · {_t(lang, 'in_flight')}"
        action = None
        if selectable:
            action = _postback(
                str(item.get("label") or item.get("name") or adapter),
                "cowork_erp_target",
                endpoint=item.get("endpoint_id") or item.get("id"),
                workspace=item.get("workspace_client_id"),
            )
        rows.append(
            _row(
                str(item.get("label") or item.get("name") or adapter),
                detail or ("online" if selectable else _t(lang, "blocked")),
                action,
                muted=not selectable,
            )
        )
    navigation = []
    if page > 0:
        navigation.append(
            _button(
                _t(lang, "prev"),
                "cowork_erp_type",
                erp=adapter,
                page=page - 1,
            )
        )
    if page + 1 < page_count:
        navigation.append(
            _button(
                _t(lang, "more"),
                "cowork_erp_type",
                erp=adapter,
                page=page + 1,
            )
        )
    if navigation:
        rows.append(
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "margin": "md",
                "contents": navigation,
            }
        )
    return _bubble(_t(lang, "pick_account"), rows)


def direction_card(lang: str) -> dict:
    rows = [
        _row(
            _t(lang, "purchase"),
            "Purchase / ซื้อ",
            _postback(_t(lang, "purchase"), "cowork_direction", direction="purchase"),
        ),
        _row(
            _t(lang, "sales"),
            "Sales / ขาย",
            _postback(_t(lang, "sales"), "cowork_direction", direction="sales"),
        ),
    ]
    return _bubble(_t(lang, "pick_direction"), rows)


def mode_card(adapter: str, direction: str, lang: str) -> dict:
    if adapter == "express":
        options = ("stock", "service")
    else:
        options = ("credit",) if direction == "purchase" else ("cash", "credit")
    rows = [
        _row(
            _t(lang, value),
            f"{adapter.upper()} · {_t(lang, direction)}",
            _postback(_t(lang, value), "cowork_posting_mode", mode=value),
        )
        for value in options
    ]
    return _bubble(_t(lang, "pick_mode"), rows)


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
    from services.cowork_line.review_cards import preview_card as build

    return build(
        draft_id=draft_id,
        fields=fields,
        target=target,
        direction=direction,
        mode=mode,
        lang=lang,
        page=page,
        record_index=record_index,
        record_count=record_count,
        preflight=preflight,
    )
