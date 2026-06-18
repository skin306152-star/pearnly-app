# -*- coding: utf-8 -*-
"""LINE 识别结果数据卡(Flex · docs/smart-intake/15 §3 · P1D 成品化)。

一张卡让用户一眼看懂:状态徽章 + 整句说明(header)/ 金额 + 税额拆解 + 来源 + 记录号 /
字段区(空字段不堆空行·低置信「请核对」)/ 明细(顶 5 行 + 「还有N行」)/ 套账 / 动作区
(按状态出合法按钮·竖排满宽永不死路)/ 底部 reply 操作引导。终态(已撤销/已丢弃)走 terminal_card。

Flex 原语与分区构建块在 line_card_sections;chrome 文案在 line_card_i18n。纯构建无 IO,可单测。
"""

from __future__ import annotations

from services.line_binding import line_card_sections as s
from services.line_binding import line_postback
from services.line_binding.line_card_doctype import doc_type_label
from services.line_binding.line_card_i18n import chrome as _lang

# 三态:状态字色 / 浅底 / 图标(待归类已下线)。
_STATES = {
    "posted": {"color": "#16A34A", "bg": "#E7F6EC", "icon": "✓"},
    "confirm": {"color": "#D97706", "bg": "#FEF3E2", "icon": "◷"},
    "dup": {"color": "#DC2626", "bg": "#FDECEC", "icon": "!"},
}
# 终态:中性灰(已撤销/已丢弃 · 非告警非成功,只是收尾)。
_TERMINAL = {
    "voided": {"color": "#667085", "bg": "#F2F4F7", "icon": "↩"},
    "discarded": {"color": "#667085", "bg": "#F2F4F7", "icon": "🗑"},
}


def _amount_text(amount, t: dict) -> tuple[bool, str]:
    if amount in (None, ""):
        return False, f"— {t['currency']}"
    return True, f"{amount} {t['currency']}"


def _state_meta(state: str, t: dict) -> str:
    return {
        "posted": t["state_saved"],
        "confirm": t["state_pending"],
        "dup": t["state_review"],
    }.get(state, t["state_pending"])


def _short_id(doc_id) -> str:
    """长 uuid → 短可读记录号(末 6 位大写)。无 → 空。"""
    d = str(doc_id or "").strip().replace("-", "")
    return d[-6:].upper() if d else ""


# 来源标:文字/图片/文件/缓存/付款证据(银行)。未知 → 票据兜底。
_SRC_KEYS = {
    "text": "src_text",
    "image": "src_image",
    "file": "src_file",
    "cache": "src_cache",
    "bank": "src_bank",
}

# 付款方式规范码 → chrome key(真识别到方式时显「付款方式」)。
_PAY_METHODS = {
    "cash": "pay_cash",
    "transfer": "pay_transfer",
    "bank_transfer": "pay_transfer",
    "promptpay": "pay_promptpay",
    "card": "pay_card",
    "credit_card": "pay_card",
    "debit_card": "pay_card",
    "other": "pay_other",
}


def _method_label(code: str, t: dict) -> str:
    """付款方式码 → 人话。已知码取译;非空非已知码(真识别的自由文本)原样显(不丢真信息)。"""
    key = _PAY_METHODS.get((code or "").strip().lower())
    return t[key] if key else str(code or "").strip()


def _payment_row(fields: dict, t: dict):
    """付款行(条件):真识别到方式 → 「付款方式: X」;否则仅明确未付/部分付 → 「付款状态: …」;
    系统默认 paid 或无法判断 → 不显示(绝不显「未说明」,不把默认 paid 当真实付款)。"""
    method = str(fields.get("payment_method") or "").strip()
    if method:
        return s.field_row(t["pay_method"], _method_label(method, t), t, low=False, strong=False)
    status = str(fields.get("payment_status") or "").strip().lower()
    if status == "unpaid":
        return s.field_row(t["pay_status"], t["pay_unpaid"], t, low=False, strong=False)
    if status in ("partial", "partially_paid"):
        return s.field_row(t["pay_status"], t["pay_partial"], t, low=False, strong=False)
    return None


def _expense_type_text(fields: dict, t: dict) -> str:
    """费用类型人话。空/未知 → 空(由调用方略过整行,绝不粗暴显「商品」)。"""
    et = (fields.get("expense_type") or "").strip().lower()
    return {
        "service": t["service"],
        "goods": t["goods"],
        "evidence": t["evidence"],
        "expense": t["expense"],
    }.get(et, "")


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
            "color": s.BRAND,
            "action": action,
        }
    return {
        "type": "button",
        "style": "link",
        "height": "sm",
        "color": s.LINK_DANGER if danger else s.LINK,
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
            out.append({"type": "separator", "margin": "xs", "color": s.SEP})
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
    review_first: bool = False,
) -> list:
    """动作区(按状态出合法动作 · 竖排满宽永不死路):
    confirm 确认入账(主)/编辑/丢弃;posted 查看详情(主)/修改/[替代收据]/撤销;
    dup 查看重复(主)/仍要入账/丢弃。review_first(明细与总额不符)= confirm 卡降级:
    主按钮改「打开核对」(去详情),确认入账降为次按钮「บันทึกต่อ」——不假装明细完整、不默认继续入账。"""
    detail_uri = _liff_link(liff_id, web_url, ref, ws=ws)
    pb = line_postback

    def link(label, uri, danger=False):
        return _btn(label, primary=False, uri=uri, danger=danger)

    def kill(label, data):
        return _btn(label, primary=False, postback=data, danger=True)

    primary, view, danger = None, [], []
    if state == "posted":
        primary = _btn(t["btn_detail"], primary=True, uri=detail_uri)
        view.append(link(t["btn_edit"], _liff_link(liff_id, web_url, ref, "edit", ws)))
        if source == "text" and ref:
            view.append(link(t["btn_receipt"], _liff_link(liff_id, web_url, ref, "receipt", ws)))
        danger.append(kill(t["btn_undo"], pb.undo_data(ref, token)))
    elif state == "dup":
        primary = _btn(t["btn_open"], primary=True, uri=detail_uri)
        view.append(_btn(t["btn_post_anyway"], primary=False, postback=pb.confirm_data(ref, token)))
        danger.append(kill(t["btn_discard"], pb.discard_data(ref, token)))
    elif review_first:  # confirm 但明细与总额不符 → 引导核对优先,入账降次按钮(仍可继续)
        primary = _btn(t["btn_review"], primary=True, uri=detail_uri)
        view.append(_btn(t["btn_post_anyway"], primary=False, postback=pb.confirm_data(ref, token)))
        danger.append(kill(t["btn_discard"], pb.discard_data(ref, token)))
    else:  # confirm(草稿请确认)
        primary = _btn(t["btn_confirm"], primary=True, postback=pb.confirm_data(ref, token))
        view.append(link(t["btn_edit"], detail_uri))
        danger.append(kill(t["btn_discard"], pb.discard_data(ref, token)))
    return _stack(primary, view, danger)


def _status_header(state: str, t: dict) -> dict:
    """状态条 = bubble header:满宽贴边、跟随卡片顶部圆角。短徽章(彩色加粗)上,整句说明(深灰)下。"""
    st = _STATES.get(state, _STATES["confirm"])
    desc_key = {"posted": "card_state_posted_desc", "dup": "card_state_dup_desc"}.get(
        state, "card_state_confirm_desc"
    )
    return {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "14px",
        "paddingStart": "20px",
        "backgroundColor": st["bg"],
        "contents": [
            s.txt(
                f"{st['icon']} {t[state]}", size="sm", color=st["color"], weight="bold", wrap=True
            ),
            s.txt(t[desc_key], size="xxs", color=s.DESC, margin="xs", wrap=True),
        ],
    }


def _amount_section(amount, state: str, source: str, doc_id: str, fields: dict, t: dict) -> list:
    """金额区:大号总额 + 右栏 meta(支出 / 状态 / 来源 / 记录号)+ 税额拆解(税前/VAT/WHT/舍入)。"""
    has_amt, amt_text = _amount_text(amount, t)
    src_text = t[_SRC_KEYS.get(source, "src_doc")]
    meta = [
        s.txt(t["meta_expense"], size="xs", color=s.META_STRONG, weight="bold"),
        s.txt(_state_meta(state, t), size="xxs", color=s.VALUE, margin="xs", weight="bold"),
        s.txt(src_text, size="xxs", color=s.LABEL, margin="xs"),
    ]
    short = _short_id(doc_id)
    if short:
        meta.append(s.txt(f"{t['record']} #{short}", size="xxs", color=s.LABEL, margin="xs"))
    return [
        {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "flex-end",
            "contents": [
                s.txt(
                    amt_text,
                    size="xl",
                    color=s.AMOUNT if has_amt else s.AMOUNT_MISS,
                    weight="bold",
                    flex=5,
                    wrap=True,
                ),
                {
                    "type": "box",
                    "layout": "vertical",
                    "alignItems": "flex-end",
                    "flex": 3,
                    "contents": meta,
                },
            ],
        },
        *s.breakdown_rows(fields, t),
    ]


def _core_section(fields: dict, lang: str, t: dict, low) -> list:
    """基本信息区:单据类型/费用类型/日期/分类/子分类/付款 —— 空字段不堆空行(逐行条件加入)。"""
    rows = []
    dt = doc_type_label(fields.get("document_type"), lang)
    if dt:
        rows.append(s.field_row(t["doc_type"], dt, t, low=low("document_type"), strong=True))
    et = _expense_type_text(fields, t)
    if et:
        rows.append(s.field_row(t["exp_type"], et, t, low=False, strong=False))
    if str(fields.get("date") or "").strip():
        rows.append(s.field_row(t["date"], fields.get("date"), t, low=low("date"), strong=False))
    if str(fields.get("category") or "").strip():
        rows.append(
            s.field_row(t["category"], fields.get("category"), t, low=low("category"), strong=True)
        )
    if str(fields.get("subcategory") or "").strip():
        rows.append(
            s.field_row(t["subcategory"], fields.get("subcategory"), t, low=False, strong=False)
        )
    pay = _payment_row(fields, t)
    if pay:
        rows.append(pay)
    return rows


def _seller_section(fields: dict, t: dict, low) -> list:
    """卖家区(有值才显):卖家 + 税号 + 地址 + 单据号。"""
    if not ((str(fields.get("vendor") or "").strip()) or s.seller_rows(fields, t)):
        return []
    rows = [s.field_row(t["vendor"], fields.get("vendor"), t, low=low("vendor"), strong=False)]
    rows += s.seller_rows(fields, t)
    if str(fields.get("invoice_number") or "").strip():
        rows.append(
            s.field_row(
                t["inv_no"],
                fields.get("invoice_number"),
                t,
                low=low("invoice_number"),
                strong=False,
            )
        )
    return rows


def _items_section(fields: dict, t: dict) -> list:
    """明细区:逐条带价(顶 5 行 + 「还有N行」)。无 items:OCR 未能逐项识别时给诚实提示(去详情页),
    否则退回 detail 单行;都没有 → 不显该区。"""
    items = fields.get("items") or []
    if items:
        rows = s.items_section(items, t, cap=5)
        mods = str(fields.get("modifiers") or "").strip()
        if mods:  # 0 元 modifier/赠品作备注(不占主明细)
            rows.append(
                s.txt(t["note_free_items"].format(x=mods), size="xxs", color=s.LABEL, wrap=True)
            )
        return rows
    if fields.get("items_unread"):
        return [
            s.seclabel(t["detail"]),
            s.txt(t["items_unread"], size="xxs", color=s.LABEL, wrap=True),
        ]
    detail = str(fields.get("detail") or "").strip()
    if detail:
        return [s.seclabel(t["detail"]), s.txt(detail, size="xxs", color=s.VALUE, wrap=True)]
    return []


def _full_bleed_bar(label: str, value: str) -> dict:
    """满宽填色条(贴边·非浮动胶囊):套账等 meta。"""
    return {
        "type": "box",
        "layout": "horizontal",
        "paddingTop": "12px",
        "paddingBottom": "12px",
        "paddingStart": "18px",
        "paddingEnd": "18px",
        "backgroundColor": "#F4F6F9",
        "contents": [
            s.txt(label, size="xxs", color="#667085", flex=2),
            s.txt(value, size="xxs", color=s.VALUE, weight="bold", align="end", flex=5),
        ],
    }


def _reply_guide_bar(t: dict) -> dict:
    """卡底 reply 操作引导(亲切·非错误提示):回复这条记录即可改/删/撤。"""
    return {
        "type": "box",
        "layout": "vertical",
        "paddingTop": "10px",
        "paddingBottom": "12px",
        "paddingStart": "18px",
        "paddingEnd": "18px",
        "contents": [s.txt(t["reply_guide"], size="xxs", color=s.LABEL, wrap=True)],
    }


def _bubble(*, alt: str, header: dict, body: list, footer: list = None) -> dict:
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": header,
        "body": {"type": "box", "layout": "vertical", "paddingAll": "0px", "contents": body},
    }
    if footer:
        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "paddingTop": "2px",
            "paddingBottom": "4px",
            "paddingStart": "12px",
            "paddingEnd": "12px",
            "contents": footer,
        }
    # 出口统一剔空 text 节点:防任何漏网空文本让整张卡被 LINE 拒收(400 must be non-empty text)。
    return s.prune_empty_text({"type": "flex", "altText": alt, "contents": bubble})


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
    """识别结果 Flex 卡(P1D)。

    state ∈ posted|confirm|dup;doc_id=动作目标 purchase_doc id。source ∈ text|image|file|cache|
    bank|doc。workspace_name 非空显套账条;dup_info 显原记录红框;warn_total 显「请核对」琥珀条。
    token:postback 一次性防重放令牌(空=旧卡兼容链路)。
    """
    t = _lang(lang)
    fc = field_confidence or {}

    def low(key):
        v = fc.get(key)
        return v is not None and float(v) < s.REVIEW_BELOW

    # 顶部融入式提示细条:异常提示(总额不符/缺税号/明细不全·按重要性 ≤2 条)+ 可能重复(红·状态级)。
    strips = s.notices(fields, warn_total, t)
    if state == "dup" and dup_info:
        dl = (
            f"{t['dup_seen']} · ฿{dup_info.get('amount', '')} · "
            f"{dup_info.get('vendor', '')} · {dup_info.get('date', '')}"
        )
        strips.append(s.strip(dl, "#FDECEC", "#9F2830"))

    body = strips + s.sheet(
        [
            _amount_section(amount, state, source, doc_id, fields, t),
            _core_section(fields, lang, t, low),
            _seller_section(fields, t, low),
            _items_section(fields, t),
        ]
    )
    if workspace_name:
        body.append(_full_bleed_bar(t["workspace"], workspace_name))
    body.append(_reply_guide_bar(t))

    _, amt_text = _amount_text(amount, t)
    return _bubble(
        alt=f"{t[state]} · {amt_text}",
        header=_status_header(state, t),
        body=body,
        footer=_footer(
            state,
            doc_id,
            web_url,
            t,
            token,
            source,
            liff_id,
            str(workspace_client_id or ""),
            review_first=bool(warn_total),
        ),
    )


def terminal_card(
    *,
    state: str,
    amount=None,
    doc_id: str = "",
    lang: str = "zh",
    web_url: str = "https://pearnly.com/home",
    workspace_name: str = "",
    liff_id: str = "",
    workspace_client_id="",
) -> dict:
    """终态卡(已撤销/已丢弃):徽章 + 整句说明 + 金额/记录号 + 仅「查看记录」(丢弃无记录可看 →
    不出按钮)。不显示任何不可执行动作(验收 6)。state ∈ voided|discarded。"""
    t = _lang(lang)
    st = _TERMINAL.get(state, _TERMINAL["voided"])
    desc = t["void_desc"] if state == "voided" else t["discard_desc"]
    header = {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "14px",
        "paddingStart": "20px",
        "backgroundColor": st["bg"],
        "contents": [
            s.txt(
                f"{st['icon']} {t[state]}", size="sm", color=st["color"], weight="bold", wrap=True
            ),
            s.txt(desc, size="xxs", color=s.DESC, margin="xs", wrap=True),
        ],
    }
    body_rows = []
    has_amt, amt_text = _amount_text(amount, t)
    if has_amt:
        body_rows.append(s.txt(amt_text, size="lg", color=s.VALUE, weight="bold", wrap=True))
    short = _short_id(doc_id)
    if short:
        body_rows.append(s.txt(f"{t['record']} #{short}", size="xxs", color=s.LABEL, margin="xs"))
    body = s.sheet([body_rows]) if body_rows else []
    if workspace_name:
        body.append(_full_bleed_bar(t["workspace"], workspace_name))

    footer = None
    if state == "voided" and doc_id:
        uri = _liff_link(liff_id, web_url, doc_id, ws=str(workspace_client_id or ""))
        footer = [_btn(t["btn_view_record"], primary=True, uri=uri)]
    return _bubble(
        alt=f"{t[state]} · {amt_text if has_amt else ''}".strip(" ·"),
        header=header,
        body=body,
        footer=footer,
    )
