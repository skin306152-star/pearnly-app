# -*- coding: utf-8 -*-
"""LINE 识别结果数据卡(Flex · docs/smart-intake/15 §3)。

四态外壳:已入账(绿)/ 请确认(琥珀)/ 需补全(灰)/ 可能重复(红)。字段表逐行,低置信值标琥珀
+「请核对」。按状态出动作钮(撤销/确认=postback,复核/补全=深链网页)。卡 chrome 标签 4 语内联
(LINE 域,不进 home.js i18n);纯构建无 IO,可单测。
"""

from __future__ import annotations

from services.line_binding import line_postback

# 低于此置信的字段值标琥珀 +「请核对」。
_REVIEW_BELOW = 0.85

_AMBER = "#D97706"
_INK = "#1F2937"
_MUTE = "#8C8C8C"

# 四态:pill 文案 key + 主色。
_STATES = {
    "posted": {"color": "#16A34A"},
    "confirm": {"color": "#D97706"},
    "inbox": {"color": "#6B7280"},
    "dup": {"color": "#DC2626"},
}

# 卡 chrome 4 语(状态头 / 字段名 / 按钮 / 支出类型)。
_L = {
    "zh": {
        "posted": "✅ 已入账",
        "confirm": "⏳ 请确认",
        "inbox": "📥 需补全",
        "dup": "⚠️ 可能重复",
        "doc_type": "单据类型",
        "exp_type": "支出类型",
        "date": "日期",
        "category": "分类",
        "subcategory": "子分类",
        "vendor": "卖家",
        "inv_no": "发票号",
        "detail": "明细",
        "goods": "🛍 商品",
        "service": "🧰 服务",
        "review": "(请核对)",
        "na": "—",
        "btn_undo": "↩️ 撤销",
        "btn_confirm": "✅ 确认入账",
        "btn_edit": "✏️ 复核",
        "btn_fill": "✏️ 去补全",
    },
    "th": {
        "posted": "✅ บันทึกแล้ว",
        "confirm": "⏳ โปรดยืนยัน",
        "inbox": "📥 ต้องเติมข้อมูล",
        "dup": "⚠️ อาจซ้ำ",
        "doc_type": "ประเภทเอกสาร",
        "exp_type": "ประเภทค่าใช้จ่าย",
        "date": "วันที่",
        "category": "หมวดหมู่",
        "subcategory": "หมวดย่อย",
        "vendor": "ผู้ขาย",
        "inv_no": "เลขที่ใบกำกับ",
        "detail": "รายละเอียด",
        "goods": "🛍 สินค้า",
        "service": "🧰 บริการ",
        "review": "(โปรดตรวจ)",
        "na": "—",
        "btn_undo": "↩️ ยกเลิก",
        "btn_confirm": "✅ ยืนยันบันทึก",
        "btn_edit": "✏️ ตรวจสอบ",
        "btn_fill": "✏️ เติมข้อมูล",
    },
    "en": {
        "posted": "✅ Recorded",
        "confirm": "⏳ Confirm",
        "inbox": "📥 Needs info",
        "dup": "⚠️ Possible duplicate",
        "doc_type": "Document",
        "exp_type": "Type",
        "date": "Date",
        "category": "Category",
        "subcategory": "Subcategory",
        "vendor": "Vendor",
        "inv_no": "Invoice no.",
        "detail": "Detail",
        "goods": "🛍 Goods",
        "service": "🧰 Service",
        "review": "(review)",
        "na": "—",
        "btn_undo": "↩️ Undo",
        "btn_confirm": "✅ Confirm",
        "btn_edit": "✏️ Review",
        "btn_fill": "✏️ Complete",
    },
    "ja": {
        "posted": "✅ 記帳済",
        "confirm": "⏳ 確認",
        "inbox": "📥 要入力",
        "dup": "⚠️ 重複の可能性",
        "doc_type": "書類種別",
        "exp_type": "費用種別",
        "date": "日付",
        "category": "分類",
        "subcategory": "サブ分類",
        "vendor": "取引先",
        "inv_no": "請求番号",
        "detail": "明細",
        "goods": "🛍 商品",
        "service": "🧰 サービス",
        "review": "(要確認)",
        "na": "—",
        "btn_undo": "↩️ 取消",
        "btn_confirm": "✅ 記帳する",
        "btn_edit": "✏️ 確認",
        "btn_fill": "✏️ 入力する",
    },
}


def _lang(lang: str) -> dict:
    return _L.get((lang or "zh").lower(), _L["zh"])


def _row(label: str, value: str, *, review: bool, review_word: str) -> dict:
    val = (value or "").strip()
    text = (val or "—") + ((" " + review_word) if (review and val) else "")
    return {
        "type": "box",
        "layout": "baseline",
        "spacing": "sm",
        "contents": [
            {"type": "text", "text": label, "color": _MUTE, "size": "sm", "flex": 4},
            {
                "type": "text",
                "text": text,
                "color": _AMBER if review else _INK,
                "size": "sm",
                "flex": 7,
                "wrap": True,
            },
        ],
    }


def _btn_postback(label: str, data: str, *, primary: bool) -> dict:
    return {
        "type": "button",
        "style": "primary" if primary else "secondary",
        "height": "sm",
        "action": {"type": "postback", "label": label[:20], "data": data, "displayText": label},
    }


def _btn_uri(label: str, uri: str, *, primary: bool) -> dict:
    return {
        "type": "button",
        "style": "primary" if primary else "secondary",
        "height": "sm",
        "action": {"type": "uri", "label": label[:20], "uri": uri},
    }


def _footer(state: str, doc_id: str, web_url: str, t: dict) -> list:
    if state == "posted":
        return [
            _btn_uri(t["btn_edit"], web_url, primary=True),
            _btn_postback(t["btn_undo"], line_postback.undo_data(doc_id), primary=False),
        ]
    if state in ("confirm", "dup"):
        return [
            _btn_postback(t["btn_confirm"], line_postback.confirm_data(doc_id), primary=True),
            _btn_uri(t["btn_edit"], web_url, primary=False),
        ]
    return [_btn_uri(t["btn_fill"], web_url, primary=True)]  # inbox


def result_card(
    *,
    state: str,
    amount,
    fields: dict,
    field_confidence: dict = None,
    doc_id: str = "",
    lang: str = "zh",
    web_url: str = "https://pearnly.com/home",
    currency: str = "THB",
) -> dict:
    """识别结果 Flex 卡。state ∈ posted|confirm|inbox|dup;fields 为归一字段 dict。"""
    t = _lang(lang)
    fc = field_confidence or {}
    color = _STATES.get(state, _STATES["confirm"])["color"]

    def review(key: str) -> bool:
        v = fc.get(key)
        return v is not None and float(v) < _REVIEW_BELOW

    et = (fields.get("expense_type") or "").lower()
    et_text = t["service"] if et == "service" else (t["goods"] if et == "goods" else t["na"])
    amt_text = f"{amount} {currency}" if amount not in (None, "") else t["na"]

    rows = [
        _row(
            t["doc_type"],
            fields.get("document_type") or t["na"],
            review=review("document_type"),
            review_word=t["review"],
        ),
        _row(t["exp_type"], et_text, review=False, review_word=t["review"]),
        _row(
            t["date"], fields.get("date") or t["na"], review=review("date"), review_word=t["review"]
        ),
        _row(
            t["category"],
            fields.get("category") or t["na"],
            review=review("category"),
            review_word=t["review"],
        ),
        _row(
            t["subcategory"],
            fields.get("subcategory") or t["na"],
            review=False,
            review_word=t["review"],
        ),
        _row(
            t["vendor"],
            fields.get("vendor") or t["na"],
            review=review("vendor"),
            review_word=t["review"],
        ),
        _row(
            t["inv_no"],
            fields.get("invoice_number") or t["na"],
            review=review("invoice_number"),
            review_word=t["review"],
        ),
        _row(t["detail"], fields.get("detail") or t["na"], review=False, review_word=t["review"]),
    ]

    body = {
        "type": "box",
        "layout": "vertical",
        "spacing": "md",
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": t.get(state, t["confirm"]),
                        "color": "#FFFFFF",
                        "size": "sm",
                        "weight": "bold",
                        "align": "center",
                    }
                ],
                "backgroundColor": color,
                "cornerRadius": "md",
                "paddingAll": "8px",
            },
            {"type": "text", "text": amt_text, "size": "xxl", "weight": "bold", "color": _INK},
            {"type": "separator"},
            {"type": "box", "layout": "vertical", "spacing": "sm", "contents": rows},
        ],
    }
    footer = _footer(state, doc_id, web_url, t)
    return {
        "type": "flex",
        "altText": f"{t.get(state, '')} · {amt_text}",
        "contents": {
            "type": "bubble",
            "body": body,
            "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": footer},
        },
    }
