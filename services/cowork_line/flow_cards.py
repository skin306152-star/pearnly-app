"""Cowork LINE ERP selection and compact draft review cards."""

from __future__ import annotations

import math

from services.cowork_line.card_fields import HEADER_KEYS, HEADER_LABELS
from services.erp.line_target_choice import account_option_label, account_reference
from services.line_platform.quick_replies import (
    postback_action as _postback,
    question as _question,
    quick_reply_item as _quick_reply_item,
)

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

_REASON_COPY = {
    "th": {
        "endpoint_disabled": "ปิดใช้งาน",
        "endpoint_revoked": "ต้องเชื่อมต่อใหม่",
        "credentials_missing": "ยังไม่ได้ตั้งค่าบัญชี",
        "erp_connection_failed": "เชื่อมต่อไม่ได้",
        "companion_offline": "ผู้ช่วยออฟไลน์",
        "companion_not_ready": "ผู้ช่วยยังไม่พร้อม",
        "profile_unconfirmed": "ยังไม่ยืนยันชุดบัญชี",
        "profile_mismatch": "ชุดบัญชีไม่ตรงกัน",
        "workspace_unbound": "ยังไม่ได้ผูกบริษัท",
        "workspace_binding_conflict": "การผูกบริษัทขัดแย้ง",
    },
    "zh": {
        "endpoint_disabled": "已停用",
        "endpoint_revoked": "需要重新连接",
        "credentials_missing": "账号密码未配置",
        "erp_connection_failed": "连接失败",
        "companion_offline": "小助手离线",
        "companion_not_ready": "小助手未就绪",
        "profile_unconfirmed": "账套未确认",
        "profile_mismatch": "账套不一致",
        "workspace_unbound": "公司尚未绑定",
        "workspace_binding_conflict": "公司绑定冲突",
    },
    "en": {
        "endpoint_disabled": "disabled",
        "endpoint_revoked": "reconnect required",
        "credentials_missing": "credentials missing",
        "erp_connection_failed": "connection failed",
        "companion_offline": "companion offline",
        "companion_not_ready": "companion not ready",
        "profile_unconfirmed": "account set unconfirmed",
        "profile_mismatch": "account set mismatch",
        "workspace_unbound": "company not linked",
        "workspace_binding_conflict": "company link conflict",
    },
    "ja": {
        "endpoint_disabled": "無効",
        "endpoint_revoked": "再接続が必要",
        "credentials_missing": "認証情報未設定",
        "erp_connection_failed": "接続失敗",
        "companion_offline": "アシスタントはオフライン",
        "companion_not_ready": "アシスタント未準備",
        "profile_unconfirmed": "帳簿未確認",
        "profile_mismatch": "帳簿が一致しません",
        "workspace_unbound": "会社未連携",
        "workspace_binding_conflict": "会社連携の競合",
    },
}


def _lang(lang: str) -> str:
    return lang if lang in _COPY else "th"


def _t(lang: str, key: str) -> str:
    return _COPY[_lang(lang)][key]


def _reason(lang: str, target: dict) -> str:
    if target.get("selectable"):
        return _t(lang, "ready")
    code = str(target.get("block_reason") or (target.get("missing") or ["not_ready"])[0])
    return _REASON_COPY[_lang(lang)].get(code, _t(lang, "not_ready"))


def _status_lines(targets: list[dict], lang: str, *, limit: int = 8) -> str:
    lines = [
        f"{'✓' if target.get('selectable') else '•'} "
        f"{str(target.get('label') or target.get('adapter') or 'ERP')[:80]}: "
        f"{_reason(lang, target)}"
        for target in targets[:limit]
    ]
    if len(targets) > limit:
        lines.append(f"+{len(targets) - limit}")
    return "\n".join(lines)


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
        "\n".join(
            value
            for value in (_t(lang, "pick_erp_subtitle"), _status_lines(targets, lang))
            if value
        ),
        items,
    )


def account_picker_card(targets: list[dict], adapter: str, lang: str, *, page: int = 0) -> dict:
    ready_targets = [target for target in targets if target.get("selectable")]
    account_options = []
    for target in ready_targets:
        choices = [
            choice
            for choice in target.get("account_choices") or []
            if isinstance(choice, dict)
            and str(choice.get("key") or choice.get("account_set") or "").strip()
            and choice.get("writable") is not False
        ]
        account_options.extend((target, choice) for choice in choices)
        if not choices:
            account_options.append((target, None))
    page_count = max(1, math.ceil(len(account_options) / QR_PAGE_SIZE))
    page = max(0, min(int(page), page_count - 1))
    start = page * QR_PAGE_SIZE
    items = [
        _quick_reply_item(
            (
                account_option_label(target, account)
                if account
                else str(target.get("label") or target.get("name") or adapter)
            ),
            "cowork_erp_target",
            endpoint=target.get("endpoint_id") or target.get("id"),
            workspace=target.get("workspace_client_id"),
            account=(
                account_reference(account.get("key") or account.get("account_set"))
                if account
                else None
            ),
        )
        for target, account in account_options[start : start + QR_PAGE_SIZE]
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
        "\n".join(
            value
            for value in (_t(lang, "pick_account_subtitle"), _status_lines(targets, lang))
            if value
        ),
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
