"""Cowork LINE ERP selection and full, paged draft review cards."""

from __future__ import annotations

import math
from urllib.parse import urlencode

from services.cowork_line.card_fields import HEADER_KEYS, HEADER_LABELS
from services.cowork_line.card_reasons import reason_text
from services.line_dms.menu_cards import (
    THEME_BLUE,
    THEME_GREEN,
    THEME_PINK,
    THEME_PURPLE,
    menu_icon_disc,
    menu_item,
)

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
        "offline": "ออฟไลน์",
        "blocked": "ยังไม่พร้อม",
        "review": "ตรวจสอบเอกสาร",
        "review_hint": "ตรวจสอบข้อมูล เป้าหมาย ERP และชุดบัญชีก่อนยืนยัน",
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
        "account_count": "พร้อมใช้ {count} ชุดบัญชี",
        "configure_first": "กรุณาตั้งค่าบนเว็บไซต์ก่อนใช้งาน",
        "connection_ready": "เชื่อมต่อแล้ว พร้อมส่ง",
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
        "offline": "小助手离线",
        "blocked": "暂不可推送",
        "review": "复核单据",
        "review_hint": "确认字段、目标 ERP 和账套后再入账",
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
        "account_count": "{count} 个账套可用",
        "configure_first": "请先在网页端完成配置",
        "connection_ready": "连接正常，可以推送",
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
        "offline": "Companion offline",
        "blocked": "Not ready",
        "review": "Review document",
        "review_hint": "Check all fields, the ERP target, and account set before posting",
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
        "account_count": "{count} account set(s) ready",
        "configure_first": "Configure this integration on the website first",
        "connection_ready": "Connected and ready to send",
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
        "offline": "コンパニオンがオフライン",
        "blocked": "利用不可",
        "review": "書類を確認",
        "review_hint": "項目、ERP、帳簿を確認してから計上してください",
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
        "account_count": "{count} 個の帳簿を利用できます",
        "configure_first": "先にウェブ画面で設定してください",
        "connection_ready": "接続済み、送信できます",
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


_THEME_MUTED = {"accent": "#A39DAD", "soft": "#F2F1F5", "border": "#E1DFE7"}


def _choice(
    number: int,
    title: str,
    subtitle: str,
    action: dict | None,
    *,
    theme: dict[str, str],
    icon: str,
    muted: bool = False,
) -> dict:
    return menu_item(
        str(number),
        icon,
        _THEME_MUTED if muted else theme,
        title,
        subtitle,
        action,
    )


def _bubble(
    title: str,
    rows: list[dict],
    alt_text: str | None = None,
    *,
    subtitle: str = "",
) -> dict:
    head = {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "alignItems": "center",
        "contents": [
            menu_icon_disc("menu-head", "#EAF0FF", "40px", "22px"),
            {
                "type": "box",
                "layout": "vertical",
                "flex": 1,
                "contents": [
                    {"type": "text", "text": title, "size": "sm", "weight": "bold", "wrap": True},
                    {
                        "type": "text",
                        "text": subtitle or " ",
                        "size": "xxs",
                        "color": "#8A8A8A",
                        "wrap": True,
                        "margin": "xs",
                    },
                ],
            },
        ],
    }
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
                    head,
                    {"type": "separator", "margin": "lg", "color": "#EEEAF7"},
                    *rows,
                ],
            },
        },
    }


def erp_picker_card(targets: list[dict], lang: str) -> dict:
    rows = []
    adapters = (("mrerp", "MR.ERP", THEME_PURPLE), ("express", "Express", THEME_BLUE))
    for number, (adapter, label, theme) in enumerate(adapters, start=1):
        entries = [item for item in targets if str(item.get("adapter") or "").lower() == adapter]
        available = bool(entries)
        action = _postback(label, "cowork_erp_type", erp=adapter) if available else None
        rows.append(
            _choice(
                number,
                label,
                (
                    _t(lang, "account_count").format(count=len(entries))
                    if available
                    else _t(lang, "configure_first")
                ),
                action,
                theme=theme,
                icon="menu-3",
                muted=not available,
            )
        )
    return _bubble(
        _t(lang, "pick_erp"),
        rows,
        subtitle=_t(lang, "pick_erp_subtitle"),
    )


def account_picker_card(targets: list[dict], adapter: str, lang: str, *, page: int = 0) -> dict:
    page_size = 8
    page_count = max(1, math.ceil(len(targets) / page_size))
    page = max(0, min(int(page), page_count - 1))
    rows = []
    page_targets = targets[page * page_size : (page + 1) * page_size]
    for number, item in enumerate(page_targets, start=page * page_size + 1):
        selectable = bool(item.get("selectable"))
        missing = [str(value) for value in item.get("missing") or []]
        detail = _t(lang, "connection_ready") if selectable else _t(lang, "blocked")
        if missing:
            detail = reason_text(_lang(lang), missing[0]) or _t(lang, "blocked")
        checks = item.get("ready_checks") or {}
        if checks.get("local_account_lock") == "waiting_lock":
            detail = reason_text(_lang(lang), "account_set_locked")
        elif checks.get("cloud_in_flight"):
            detail = _t(lang, "in_flight")
        action = None
        if selectable:
            action = _postback(
                str(item.get("label") or item.get("name") or adapter),
                "cowork_erp_target",
                endpoint=item.get("endpoint_id") or item.get("id"),
                workspace=item.get("workspace_client_id"),
            )
        rows.append(
            _choice(
                number,
                str(item.get("label") or item.get("name") or adapter),
                detail,
                action,
                theme=THEME_BLUE if adapter == "express" else THEME_PURPLE,
                icon="menu-3",
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
    return _bubble(
        _t(lang, "pick_account"),
        rows,
        subtitle=_t(lang, "pick_account_subtitle"),
    )


def direction_card(lang: str) -> dict:
    rows = [
        _choice(
            1,
            _t(lang, "purchase"),
            _t(lang, "pick_direction_subtitle"),
            _postback(_t(lang, "purchase"), "cowork_direction", direction="purchase"),
            theme=THEME_GREEN,
            icon="menu-head",
        ),
        _choice(
            2,
            _t(lang, "sales"),
            _t(lang, "pick_direction_subtitle"),
            _postback(_t(lang, "sales"), "cowork_direction", direction="sales"),
            theme=THEME_PINK,
            icon="menu-head",
        ),
    ]
    return _bubble(
        _t(lang, "pick_direction"),
        rows,
        subtitle=_t(lang, "pick_direction_subtitle"),
    )


def mode_card(adapter: str, direction: str, lang: str) -> dict:
    if adapter == "express":
        options = ("stock", "service")
    else:
        options = ("credit",) if direction == "purchase" else ("cash", "credit")
    themes = (THEME_BLUE, THEME_PURPLE)
    rows = [
        _choice(
            index,
            _t(lang, value),
            f"{adapter.upper()} · {_t(lang, direction)}",
            _postback(_t(lang, value), "cowork_posting_mode", mode=value),
            theme=themes[(index - 1) % len(themes)],
            icon="menu-head",
        )
        for index, value in enumerate(options, start=1)
    ]
    return _bubble(
        _t(lang, "pick_mode"),
        rows,
        subtitle=_t(lang, "pick_mode_subtitle"),
    )


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
