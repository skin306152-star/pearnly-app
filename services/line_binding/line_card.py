# -*- coding: utf-8 -*-
"""LINE 识别结果数据卡(Flex · docs/smart-intake/15 §3)。

视觉照搬定稿原型(Downloads/pearnly-line-flex-card-prototype.html 的 flexJson):
状态条(浅底深字·非按钮)+ 金额&来源 meta + 字段表(低置信琥珀+「请核对」)+ 套账浅底条
+ 重复时红框显示原记录 + 动作区(唯一实心主按钮=提交,其余 link 文字链接)。四态四语。
chrome 文案内联(LINE 域,不进 home.js i18n);纯构建无 IO,可单测。
"""

from __future__ import annotations

from services.line_binding import line_postback

_REVIEW_BELOW = 0.85

# 四态:状态字色 / 浅底 / 图标。
_STATES = {
    "posted": {"color": "#16A34A", "bg": "#E7F6EC", "icon": "✓"},
    "confirm": {"color": "#D97706", "bg": "#FEF3E2", "icon": "◷"},
    "inbox": {"color": "#5B6470", "bg": "#F1F2F4", "icon": "↓"},
    "dup": {"color": "#DC2626", "bg": "#FDECEC", "icon": "!"},
}
_BRAND = "#2563EB"
_AMOUNT = "#111827"
_AMOUNT_MISS = "#98A2B3"
_LABEL = "#98A2B3"
_VALUE = "#344054"
_LOW = "#B45309"
_META_STRONG = "#475467"
_SEP = "#EEF0F3"
_WS_BG = "#F8FAFC"
_LINK = "#4D607C"
_LINK_DANGER = "#8F4A4A"

# chrome 4 语(状态/字段名/来源/按钮)。
_L = {
    "zh": {
        "posted": "已入账",
        "confirm": "请确认",
        "inbox": "需补全",
        "dup": "可能重复",
        "doc_type": "单据类型",
        "exp_type": "支出类型",
        "date": "日期",
        "category": "分类",
        "subcategory": "子分类",
        "vendor": "卖家",
        "inv_no": "发票号",
        "detail": "明细",
        "workspace": "套账",
        "meta_expense": "支出",
        "src_text": "来自文字",
        "src_doc": "来自单据",
        "src_bank": "付款证据",
        "goods": "🛍 商品",
        "service": "🧰 服务",
        "evidence": "💳 付款证据",
        "review": "(请核对)",
        "na": "—",
        "btn_confirm": "确认入账",
        "btn_post_anyway": "仍要入账",
        "btn_review": "复核 / 编辑",
        "btn_edit": "编辑",
        "btn_fill": "编辑补全",
        "btn_undo": "撤销",
        "btn_discard": "丢弃",
        "btn_open": "打开原记录",
        "dup_seen": "已存在记录",
    },
    "th": {
        "posted": "บันทึกแล้ว",
        "confirm": "โปรดยืนยัน",
        "inbox": "ต้องเพิ่มข้อมูล",
        "dup": "อาจซ้ำ",
        "doc_type": "ประเภทเอกสาร",
        "exp_type": "ประเภทค่าใช้จ่าย",
        "date": "วันที่",
        "category": "หมวดหมู่",
        "subcategory": "หมวดย่อย",
        "vendor": "ผู้ขาย",
        "inv_no": "เลขที่ใบกำกับ",
        "detail": "รายละเอียด",
        "workspace": "ชุดบัญชี",
        "meta_expense": "ค่าใช้จ่าย",
        "src_text": "จากข้อความ",
        "src_doc": "จากเอกสาร",
        "src_bank": "หลักฐานชำระเงิน",
        "goods": "🛍 สินค้า",
        "service": "🧰 บริการ",
        "evidence": "💳 หลักฐานชำระเงิน",
        "review": "(โปรดตรวจ)",
        "na": "—",
        "btn_confirm": "ยืนยันบันทึก",
        "btn_post_anyway": "บันทึกต่อ",
        "btn_review": "ตรวจสอบ / แก้ไข",
        "btn_edit": "แก้ไข",
        "btn_fill": "แก้ไข / เติมข้อมูล",
        "btn_undo": "ยกเลิก",
        "btn_discard": "ทิ้ง",
        "btn_open": "เปิดรายการเดิม",
        "dup_seen": "มีรายการอยู่แล้ว",
    },
    "en": {
        "posted": "Recorded",
        "confirm": "Confirm",
        "inbox": "Needs info",
        "dup": "Possible duplicate",
        "doc_type": "Document",
        "exp_type": "Type",
        "date": "Date",
        "category": "Category",
        "subcategory": "Subcategory",
        "vendor": "Vendor",
        "inv_no": "Invoice no.",
        "detail": "Detail",
        "workspace": "Ledger",
        "meta_expense": "Expense",
        "src_text": "From text",
        "src_doc": "From document",
        "src_bank": "Payment evidence",
        "goods": "🛍 Goods",
        "service": "🧰 Service",
        "evidence": "💳 Payment evidence",
        "review": "(review)",
        "na": "—",
        "btn_confirm": "Confirm",
        "btn_post_anyway": "Record anyway",
        "btn_review": "Review / Edit",
        "btn_edit": "Edit",
        "btn_fill": "Edit / Complete",
        "btn_undo": "Undo",
        "btn_discard": "Discard",
        "btn_open": "Open original",
        "dup_seen": "Existing record",
    },
    "ja": {
        "posted": "記帳済",
        "confirm": "確認",
        "inbox": "要入力",
        "dup": "重複の可能性",
        "doc_type": "書類種別",
        "exp_type": "費用種別",
        "date": "日付",
        "category": "分類",
        "subcategory": "サブ分類",
        "vendor": "取引先",
        "inv_no": "請求番号",
        "detail": "明細",
        "workspace": "帳簿",
        "meta_expense": "支出",
        "src_text": "テキストから",
        "src_doc": "書類から",
        "src_bank": "支払証憑",
        "goods": "🛍 商品",
        "service": "🧰 サービス",
        "evidence": "💳 支払証憑",
        "review": "(要確認)",
        "na": "—",
        "btn_confirm": "記帳する",
        "btn_post_anyway": "このまま記帳",
        "btn_review": "確認 / 編集",
        "btn_edit": "編集",
        "btn_fill": "編集 / 入力",
        "btn_undo": "取消",
        "btn_discard": "破棄",
        "btn_open": "元の記録を開く",
        "dup_seen": "既存の記録",
    },
}


def _lang(lang: str) -> dict:
    return _L.get((lang or "zh").lower(), _L["zh"])


# OCR document_type 原始码 → 4 语人话(避免卡上显 simplified_tax_invoice 等英文代号);
# 术语对齐网页 pur-dt-*。空 → 空;未知码 → 原值兜底(不编造)。
_DOC_TYPE_LABELS = {
    "tax_invoice": {"zh": "税务发票", "th": "ใบกำกับภาษี", "en": "Tax invoice", "ja": "税額票"},
    "simplified_tax_invoice": {
        "zh": "简式税票",
        "th": "ใบกำกับภาษีอย่างย่อ",
        "en": "Simplified tax invoice",
        "ja": "簡易税額票",
    },
    "receipt": {"zh": "收据", "th": "ใบเสร็จรับเงิน", "en": "Receipt", "ja": "領収書"},
    "credit_note": {
        "zh": "贷项通知单",
        "th": "ใบลดหนี้",
        "en": "Credit note",
        "ja": "クレジットノート",
    },
    "other": {"zh": "其他", "th": "อื่น ๆ", "en": "Other", "ja": "その他"},
}


def doc_type_label(code: str, lang: str) -> str:
    """document_type 原始码 → 当前语言人话。"""
    code = (code or "").strip()
    if not code:
        return ""
    m = _DOC_TYPE_LABELS.get(code)
    if not m:
        return code
    return m.get((lang or "zh").lower()) or m["en"]


def _txt(text, *, size, color, **kw) -> dict:
    return {"type": "text", "text": str(text), "size": size, "color": color, **kw}


def _field_row(label: str, value: str, t: dict, *, low: bool, strong: bool) -> dict:
    val = (value or "").strip() or t["na"]
    if low and val != t["na"]:
        val = f"{val} {t['review']}"
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            _txt(label, size="xxs", color=_LABEL, flex=2),
            _txt(
                val,
                size="xxs",
                color=_LOW if low else (_VALUE if not strong else "#202939"),
                flex=5,
                wrap=True,
                weight="bold" if strong else "regular",
            ),
        ],
    }


def _btn(label: str, *, primary: bool, postback: str = None, uri: str = None, danger=False) -> dict:
    action = (
        {"type": "postback", "label": label[:20], "data": postback, "displayText": label}
        if postback is not None
        else {"type": "uri", "label": label[:20], "uri": uri}
    )
    if primary:
        return {
            "type": "button",
            "style": "primary",
            "height": "sm",
            "color": _BRAND,
            "action": action,
        }
    return {
        "type": "button",
        "style": "link",
        "height": "sm",
        "color": _LINK_DANGER if danger else _LINK,
        "action": action,
    }


def _footer(state: str, ref: str, web_url: str, t: dict, can_post: bool) -> list:
    """唯一实心主按钮=提交动作;复核/编辑/撤销/丢弃=link 文字链接(非按钮)。永不死路。"""
    primary, links = None, []
    if state == "posted":
        links = [
            _btn(t["btn_review"], primary=False, uri=web_url),
            _btn(t["btn_undo"], primary=False, postback=line_postback.undo_data(ref), danger=True),
        ]
    elif state == "confirm":
        primary = _btn(t["btn_confirm"], primary=True, postback=line_postback.confirm_data(ref))
        links = [
            _btn(t["btn_edit"], primary=False, uri=web_url),
            _btn(
                t["btn_discard"],
                primary=False,
                postback=line_postback.discard_data(ref),
                danger=True,
            ),
        ]
    elif state == "dup":
        primary = _btn(t["btn_post_anyway"], primary=True, postback=line_postback.confirm_data(ref))
        links = [
            _btn(t["btn_open"], primary=False, uri=web_url),
            _btn(
                t["btn_discard"],
                primary=False,
                postback=line_postback.discard_data(ref),
                danger=True,
            ),
        ]
    else:  # inbox
        if can_post and ref:
            primary = _btn(
                t["btn_post_anyway"], primary=True, postback=line_postback.inbox_post_data(ref)
            )
        links = [_btn(t["btn_fill"], primary=False, uri=web_url)]
        if ref:
            links.append(
                _btn(
                    t["btn_discard"],
                    primary=False,
                    postback=line_postback.inbox_drop_data(ref),
                    danger=True,
                )
            )
    foot = []
    if primary:
        foot.append(primary)
    foot.append(
        {"type": "box", "layout": "horizontal", "justifyContent": "center", "contents": links}
    )
    return foot


def result_card(
    *,
    state: str,
    amount,
    fields: dict,
    field_confidence: dict = None,
    doc_id: str = "",
    lang: str = "zh",
    web_url: str = "https://pearnly.com/home",
    can_post: bool = True,
    source: str = "doc",
    workspace_name: str = "",
    dup_info: dict = None,
) -> dict:
    """识别结果 Flex 卡(照搬定稿原型)。

    state ∈ posted|confirm|inbox|dup;doc_id=动作目标 id(草稿/已入账=purchase_doc,inbox=intake_item)。
    source ∈ text|doc|bank(金额右侧来源标);workspace_name 非空则显套账条;dup_info 显原记录红框。
    can_post:inbox 有可用金额才给「仍要入账」(糊图 ฿0 只给编辑/丢弃)。
    """
    t = _lang(lang)
    st = _STATES.get(state, _STATES["confirm"])
    fc = field_confidence or {}

    def low(key):
        v = fc.get(key)
        return v is not None and float(v) < _REVIEW_BELOW

    et = (fields.get("expense_type") or "").lower()
    et_text = {"service": t["service"], "goods": t["goods"], "evidence": t["evidence"]}.get(
        et, t["na"]
    )
    src_text = {"text": t["src_text"], "bank": t["src_bank"]}.get(source, t["src_doc"])
    has_amt = amount not in (None, "")
    amt_text = f"฿{amount}" if has_amt else "Amount —"

    body = [
        {  # 状态条(浅底深字·非按钮)
            "type": "box",
            "layout": "vertical",
            "contents": [
                _txt(f"{st['icon']} {t[state]}", size="xs", color=st["color"], weight="bold")
            ],
            "backgroundColor": st["bg"],
            "cornerRadius": "xl",
            "paddingAll": "8px",
        },
        {  # 金额 + 右侧来源 meta
            "type": "box",
            "layout": "horizontal",
            "margin": "lg",
            "alignItems": "flex-end",
            "contents": [
                _txt(
                    amt_text,
                    size="xxl",
                    color=_AMOUNT if has_amt else _AMOUNT_MISS,
                    weight="bold",
                    flex=4,
                ),
                {
                    "type": "box",
                    "layout": "vertical",
                    "alignItems": "flex-end",
                    "flex": 3,
                    "contents": [
                        _txt(t["meta_expense"], size="xs", color=_META_STRONG, weight="bold"),
                        _txt(src_text, size="xxs", color=_LABEL, margin="xs"),
                    ],
                },
            ],
        },
        {"type": "separator", "margin": "lg", "color": _SEP},
        {  # 字段表
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "spacing": "sm",
            "contents": [
                _field_row(
                    t["doc_type"],
                    doc_type_label(fields.get("document_type"), lang),
                    t,
                    low=low("document_type"),
                    strong=True,
                ),
                _field_row(t["exp_type"], et_text, t, low=False, strong=False),
                _field_row(t["date"], fields.get("date"), t, low=low("date"), strong=False),
                _field_row(
                    t["category"], fields.get("category"), t, low=low("category"), strong=True
                ),
                _field_row(t["subcategory"], fields.get("subcategory"), t, low=False, strong=False),
                _field_row(t["vendor"], fields.get("vendor"), t, low=low("vendor"), strong=False),
                _field_row(
                    t["inv_no"],
                    fields.get("invoice_number"),
                    t,
                    low=low("invoice_number"),
                    strong=False,
                ),
                _field_row(t["detail"], fields.get("detail"), t, low=False, strong=False),
            ],
        },
    ]
    if state == "dup" and dup_info:
        body.append(
            {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "paddingAll": "8px",
                "backgroundColor": "#FFF7F7",
                "cornerRadius": "md",
                "contents": [
                    _txt(t["dup_seen"], size="xxs", color="#9F2830", weight="bold"),
                    _txt(
                        f"฿{dup_info.get('amount', '')} · {dup_info.get('vendor', '')} · {dup_info.get('date', '')}",
                        size="xxs",
                        color="#9F2830",
                        wrap=True,
                        margin="xs",
                    ),
                ],
            }
        )
    if workspace_name:
        body.append(
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "md",
                "paddingAll": "8px",
                "backgroundColor": _WS_BG,
                "cornerRadius": "md",
                "contents": [
                    _txt(t["workspace"], size="xxs", color="#667085", flex=2),
                    _txt(
                        workspace_name, size="xxs", color=_VALUE, weight="bold", align="end", flex=5
                    ),
                ],
            }
        )

    return {
        "type": "flex",
        "altText": f"{t[state]} · {amt_text}",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "body": {"type": "box", "layout": "vertical", "paddingAll": "16px", "contents": body},
            "footer": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "12px",
                "contents": _footer(state, doc_id, web_url, t, can_post),
            },
        },
    }
