# -*- coding: utf-8 -*-
"""LINE 识别结果数据卡(Flex · docs/smart-intake/15 §3)。

视觉照搬定稿原型(Downloads/pearnly-line-flex-card-prototype.html 的 flexJson):
状态条(浅底深字·非按钮)+ 金额&来源 meta + 字段表(低置信琥珀+「请核对」)+ 套账浅底条
+ 重复时红框显示原记录 + 动作区(唯一实心主按钮=提交,其余 link 文字链接)。三态四语。
chrome 文案内联(LINE 域,不进 home.js i18n);纯构建无 IO,可单测。
"""

from __future__ import annotations

from services.line_binding import line_postback
from services.line_binding.line_card_doctype import doc_type_label
from services.line_binding.line_card_i18n import chrome as _lang

_REVIEW_BELOW = 0.85

# 三态:状态字色 / 浅底 / 图标(待归类已下线)。
_STATES = {
    "posted": {"color": "#16A34A", "bg": "#E7F6EC", "icon": "✓"},
    "confirm": {"color": "#D97706", "bg": "#FEF3E2", "icon": "◷"},
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
_LINK = "#4D607C"
_LINK_DANGER = "#8F4A4A"


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
            _txt(label, size="sm", color=_LABEL, flex=4, wrap=True),
            _txt(
                val,
                size="sm",
                color=_LOW if low else (_VALUE if not strong else "#202939"),
                flex=6,
                wrap=True,
                weight="bold" if strong else "regular",
            ),
        ],
    }


def _breakdown_rows(fields: dict, t: dict) -> list:
    """税额拆解条(完整税票有税前/VAT/WHT 时):税前 ฿ · VAT ฿ · WHT ฿。无 → 空(不占位)。"""
    sub = str(fields.get("subtotal") or "").strip()
    vat = str(fields.get("vat") or "").strip()
    wht = str(fields.get("wht") or "").strip()
    parts = []
    if sub:
        parts.append(f"{t['subtotal']} ฿{sub}")
    if vat:
        parts.append(f"VAT ฿{vat}")
    if wht and wht.replace(".", "").strip("0"):
        parts.append(f"WHT ฿{wht}")
    if not parts:
        return []
    return [_txt(" · ".join(parts), size="xxs", color=_LABEL, margin="sm", wrap=True)]


def _seller_rows(fields: dict, t: dict) -> list:
    """卖家税号/地址条件行(完整税票有值才显·空则不堆叠空行)。"""
    rows = []
    tax = str(fields.get("seller_tax") or "").strip()
    addr = str(fields.get("seller_addr") or "").strip()
    if tax:
        rows.append(_field_row(t["tax_id"], tax, t, low=False, strong=False))
    if addr:
        rows.append(_field_row(t["address"], addr, t, low=False, strong=False))
    return rows


def _seclabel(text: str) -> dict:
    """分区小标题(灰·小号)。"""
    return _txt(text, size="xs", color=_LABEL, weight="bold")


def _strip(text: str, bg: str, color: str) -> dict:
    """贴顶满宽细色条(融入卡·非浮动圆角块):总额不符 / 可能重复。"""
    return {
        "type": "box",
        "layout": "vertical",
        "paddingTop": "10px",
        "paddingBottom": "10px",
        "paddingStart": "18px",
        "paddingEnd": "18px",
        "backgroundColor": bg,
        "contents": [_txt(text, size="xxs", color=color, wrap=True)],
    }


def _items_rows(items: list, t: dict) -> list:
    """逐条明细(编号 + 名称 + 右对齐价 · 全部按票据显示 · 对标 Paypers รายการค่าใช้จ่าย)。"""
    rows = []
    for i, it in enumerate(items or [], 1):
        name = (str(it.get("name") or "").strip()) or t["na"]
        amt = str(it.get("amount") or "").strip()
        rows.append(
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    _txt(f"{i}. {name}", size="sm", color=_VALUE, flex=5, wrap=True),
                    _txt(
                        f"฿{amt}" if amt else "",
                        size="sm",
                        color="#202939",
                        weight="bold",
                        flex=2,
                        align="end",
                        wrap=True,
                    ),
                ],
            }
        )
    return rows


def _sheet(sections: list) -> list:
    """把各非空分区拼成一张连续白卡:区与区之间一条细横线(融入·按类分隔)。"""
    out = []
    for contents in sections:
        if not contents:
            continue
        if out:
            out.append({"type": "separator", "color": _SEP})
        out.append(
            {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "spacing": "sm",
                "contents": contents,
            }
        )
    return out


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


def _liff_link(liff_id: str, web_url: str, ref: str, view: str = "", ws: str = "") -> str:
    """深链到该记录复核屏。配了 LIFF ID → liff.line.me/{id}?...(LINE 用 LIFF webview 打开·自动
    用 LINE 身份登录);未配 → 回退站内 /liff 路由(至少能打开)。无 ref → 通用页(不死链)。

    ws=该单所属套账 id:带上 → 复核屏自动切到该套账并跳过套账门(记录只在它自己的套账可见)。
    """
    if not ref:
        return web_url
    extra = (f"&view={view}" if view else "") + (f"&ws={ws}" if ws else "")
    if liff_id:
        return f"https://liff.line.me/{liff_id}?liff=purchase&doc={ref}{extra}"
    base = web_url.split("/home")[0].rstrip("/") or "https://pearnly.com"
    qs = extra.lstrip("&")
    return f"{base}/liff/purchase/{ref}" + (f"?{qs}" if qs else "")


def _stack(primary: dict, view: list, danger: list) -> list:
    """竖排装配:每个动作独占一行,行行之间画分隔线(对标 Paypers · 治同行挤压截断 + 视觉分隔)。"""
    buttons = ([primary] if primary else []) + view + danger
    out = []
    for i, btn in enumerate(buttons):
        if i:
            out.append({"type": "separator", "margin": "xs", "color": _SEP})
        out.append(btn)
    return out


def _footer(
    state: str,
    ref: str,
    web_url: str,
    t: dict,
    token: str = "",
    source: str = "doc",
    liff_id: str = "",
    ws: str = "",
) -> list:
    """动作区:主按钮=提交;复核/编辑/替代收据=查看组;撤销/丢弃=危险组。竖排满宽永不死路。"""
    edit_uri = _liff_link(liff_id, web_url, ref, ws=ws)
    pb = line_postback

    def link(label, uri):
        return _btn(label, primary=False, uri=uri)

    def kill(label, data):
        return _btn(label, primary=False, postback=data, danger=True)

    def main(label, data):
        return _btn(label, primary=True, postback=data)

    primary, view, danger = None, [], []
    if state == "posted":
        view.append(link(t["btn_review"], edit_uri))
        if source == "text" and ref:
            view.append(link(t["btn_receipt"], _liff_link(liff_id, web_url, ref, "receipt", ws)))
        danger.append(kill(t["btn_undo"], pb.undo_data(ref, token)))
    elif state == "dup":
        primary = main(t["btn_post_anyway"], pb.confirm_data(ref, token))
        view.append(link(t["btn_open"], edit_uri))
        danger.append(kill(t["btn_discard"], pb.discard_data(ref, token)))
    else:  # confirm(草稿请确认)
        primary = main(t["btn_confirm"], pb.confirm_data(ref, token))
        view.append(link(t["btn_edit"], edit_uri))
        danger.append(kill(t["btn_discard"], pb.discard_data(ref, token)))
    return _stack(primary, view, danger)


def result_card(
    *,
    state: str,
    amount,
    fields: dict,
    field_confidence: dict = None,
    doc_id: str = "",
    lang: str = "zh",
    web_url: str = "https://pearnly.com/home",
    source: str = "doc",
    workspace_name: str = "",
    dup_info: dict = None,
    token: str = "",
    warn_total: bool = False,
    liff_id: str = "",
    workspace_client_id="",
) -> dict:
    """识别结果 Flex 卡(照搬定稿原型)。

    state ∈ posted|confirm|dup;doc_id=动作目标 purchase_doc id(待归类已下线·糊图/฿0 也建草稿)。
    source ∈ text|doc|bank(金额右侧来源标);workspace_name 非空则显套账条;dup_info 显原记录红框。
    token:postback 动作的一次性防重放令牌(PO-12),空则按钮不带令牌(旧卡兼容链路)。
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

    # 状态条 = bubble header:满宽贴边、跟随卡片顶部圆角(对标 Paypers·非浮动胶囊)。
    status_header = {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "14px",
        "paddingStart": "20px",
        "backgroundColor": st["bg"],
        "contents": [_txt(f"{st['icon']} {t[state]}", size="sm", color=st["color"], weight="bold")],
    }

    # 顶部融入式提示细条(非浮动圆角块):总额不符(琥珀)/ 可能重复(红)。
    strips = []
    if warn_total:
        strips.append(_strip(t["warn_total"], "#FEF7EC", "#B45309"))
    if state == "dup" and dup_info:
        dl = (
            f"{t['dup_seen']} · ฿{dup_info.get('amount', '')} · "
            f"{dup_info.get('vendor', '')} · {dup_info.get('date', '')}"
        )
        strips.append(_strip(dl, "#FDECEC", "#9F2830"))

    # 金额区
    amount_sec = [
        {
            "type": "box",
            "layout": "horizontal",
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
        *_breakdown_rows(fields, t),
    ]

    # 基本信息区
    core_sec = [
        _field_row(
            t["doc_type"],
            doc_type_label(fields.get("document_type"), lang),
            t,
            low=low("document_type"),
            strong=True,
        ),
        _field_row(t["exp_type"], et_text, t, low=False, strong=False),
        _field_row(t["date"], fields.get("date"), t, low=low("date"), strong=False),
        _field_row(t["category"], fields.get("category"), t, low=low("category"), strong=True),
        _field_row(t["subcategory"], fields.get("subcategory"), t, low=False, strong=False),
    ]

    # 卖家区(有值才显·各行自带标签·靠分隔线与基本信息分开,不另加冗余小标题)
    seller_sec = []
    if (str(fields.get("vendor") or "").strip()) or _seller_rows(fields, t):
        seller_sec.append(
            _field_row(t["vendor"], fields.get("vendor"), t, low=low("vendor"), strong=False)
        )
        seller_sec += _seller_rows(fields, t)
        if str(fields.get("invoice_number") or "").strip():
            seller_sec.append(
                _field_row(
                    t["inv_no"],
                    fields.get("invoice_number"),
                    t,
                    low=low("invoice_number"),
                    strong=False,
                )
            )

    # 明细区:逐条带价全部显示(无 items 退回 detail 单行)
    items = fields.get("items") or []
    items_sec = []
    if items:
        items_sec = [_seclabel(t["detail"]), *_items_rows(items, t)]
    elif str(fields.get("detail") or "").strip():
        items_sec = [
            _seclabel(t["detail"]),
            _txt(fields["detail"], size="xxs", color=_VALUE, wrap=True),
        ]

    body = strips + _sheet([amount_sec, core_sec, seller_sec, items_sec])
    # 套账:满宽填色条(贴边·非浮动胶囊),置于字段区与动作区之间。
    if workspace_name:
        body.append(
            {
                "type": "box",
                "layout": "horizontal",
                "paddingTop": "12px",
                "paddingBottom": "12px",
                "paddingStart": "18px",
                "paddingEnd": "18px",
                "backgroundColor": "#F4F6F9",
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
            "header": status_header,
            "body": {"type": "box", "layout": "vertical", "paddingAll": "0px", "contents": body},
            "footer": {
                "type": "box",
                "layout": "vertical",
                "paddingTop": "2px",
                "paddingBottom": "4px",
                "paddingStart": "12px",
                "paddingEnd": "12px",
                "contents": _footer(
                    state,
                    doc_id,
                    web_url,
                    t,
                    token,
                    source,
                    liff_id,
                    str(workspace_client_id or ""),
                ),
            },
        },
    }
