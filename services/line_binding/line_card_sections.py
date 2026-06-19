# -*- coding: utf-8 -*-
"""LINE 数据卡的 Flex 原语与分区构建块(从 line_card 抽出 · 保 line_card <500)。

纯函数、无 IO、可单测。颜色令牌 + 文本原语 + 字段行/税额拆解/卖家行/明细行/分隔白卡。
line_card 负责编排(状态头/金额区/动作区/终态卡),本模块只产可复用的小块。
"""

from __future__ import annotations

from services.line_binding import line_postback
from services.purchase import item_name

# 颜色令牌(与定稿原型一致)。
BRAND = "#2563EB"
AMOUNT = "#111827"
AMOUNT_MISS = "#98A2B3"
LABEL = "#98A2B3"
DESC = "#475467"
VALUE = "#344054"
VALUE_STRONG = "#202939"
LOW = "#B45309"
META_STRONG = "#475467"
SEP = "#EEF0F3"
LINK = "#4D607C"
LINK_DANGER = "#8F4A4A"

REVIEW_BELOW = 0.85


def txt(text, *, size, color, **kw) -> dict:
    return {"type": "text", "text": str(text), "size": size, "color": color, **kw}


def field_row(label: str, value: str, t: dict, *, low: bool, strong: bool) -> dict:
    """两列字段行(左标签灰 · 右值)。低置信值缀「请核对」并转琥珀。"""
    val = (value or "").strip() or t["na"]
    if low and val != t["na"]:
        val = f"{val} {t['review']}"
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            txt(label, size="sm", color=LABEL, flex=4, wrap=True),
            txt(
                val,
                size="sm",
                color=LOW if low else (VALUE if not strong else "#202939"),
                flex=6,
                wrap=True,
                weight="bold" if strong else "regular",
            ),
        ],
    }


def breakdown_rows(fields: dict, t: dict) -> list:
    """税额拆解条:税前 ฿ · VAT ฿ · WHT ฿ · 舍入 ฿(各项有值才显·无 → 空不占位)。"""
    sub = str(fields.get("subtotal") or "").strip()
    vat = str(fields.get("vat") or "").strip()
    wht = str(fields.get("wht") or "").strip()
    discount = str(fields.get("discount") or "").strip()
    rounding = str(fields.get("rounding") or "").strip()
    parts = []
    if sub:
        parts.append(f"{t['subtotal']} ฿{sub}")
    if discount and discount.replace(".", "").replace("-", "").strip("0"):
        parts.append(f"{t['discount']} ฿{discount}")
    if vat:
        parts.append(f"VAT ฿{vat}")
    if wht and wht.replace(".", "").strip("0"):
        parts.append(f"WHT ฿{wht}")
    if rounding and rounding.replace(".", "").replace("-", "").strip("0"):
        parts.append(f"{t['rounding']} ฿{rounding}")
    if not parts:
        return []
    return [txt(" · ".join(parts), size="xxs", color=LABEL, margin="sm", wrap=True)]


def seller_rows(fields: dict, t: dict) -> list:
    """卖家税号/地址条件行(有值才显·空则不堆空行)。"""
    rows = []
    tax = str(fields.get("seller_tax") or "").strip()
    addr = str(fields.get("seller_addr") or "").strip()
    if tax:
        rows.append(field_row(t["tax_id"], tax, t, low=False, strong=False))
    if addr:
        rows.append(field_row(t["address"], addr, t, low=False, strong=False))
    return rows


def seclabel(text: str) -> dict:
    """分区小标题(灰·小号)。"""
    return txt(text, size="xs", color=LABEL, weight="bold")


def strip(text: str, bg: str, color: str) -> dict:
    """贴顶满宽细色条(融入卡·非浮动圆角块):总额不符 / 可能重复。"""
    return {
        "type": "box",
        "layout": "vertical",
        "paddingTop": "10px",
        "paddingBottom": "10px",
        "paddingStart": "18px",
        "paddingEnd": "18px",
        "backgroundColor": bg,
        "contents": [txt(text, size="xxs", color=color, wrap=True)],
    }


def missing_taxid(fields: dict) -> bool:
    """应有税号却没有(有 VAT 或税票类型)却无有效 seller_tax → 温和提示。普通小票不提示(避免堆警告)。
    seller_tax 已经 field_clean 清洗:invalid(短数字/日期片段)早成空 → 这里只看真有没有合法税号。"""
    if str(fields.get("seller_tax") or "").strip():
        return False
    vat_nonzero = bool(
        str(fields.get("vat") or "").replace(",", "").strip(" 0.")
    )  # 剥空白/0/小数点
    dt = str(fields.get("document_type") or "").lower()
    return vat_nonzero or "tax" in dt or "ภาษี" in dt or "กำกับ" in dt


_DIRTY_LABELS = {
    "seller": "vendor",
    "date": "date",
    "tax_id": "tax_id",
    "invoice": "inv_no",
    "address": "address",
}


def _review_strip(fields: dict, t: dict):
    """P2B:低置信字段汇总「请检查:卖家·日期·税号」(列出具体字段·琥珀)。无脏字段 → None。"""
    names = [t[_DIRTY_LABELS[d]] for d in (fields.get("dirty_fields") or []) if d in _DIRTY_LABELS]
    if not names:
        return None
    return strip(t["fields_review"].format(x=" · ".join(names)), "#FEF7EC", "#B45309")


def notices(fields: dict, warn_total: bool, t: dict) -> list:
    """卡顶提示细条(产品级·按重要性·最多 2 条·不堆满):
    低置信字段需检查(琥珀·列字段)> 金额可靠明细不符(琥珀)> 缺税号(琥珀)> 明细可能不全(灰)。"""
    out = []
    review = _review_strip(fields, t)
    if review:
        out.append(review)
    if warn_total:
        out.append(strip(t["warn_total"], "#FEF7EC", "#B45309"))
    if missing_taxid(fields):
        out.append(strip(t["no_taxid"], "#FEF7EC", "#B45309"))
    if fields.get("items_unread"):
        out.append(strip(t["items_partial"], "#F4F6F9", "#667085"))
    return out[:2]


def _display_item_name(raw, i: int, t: dict) -> str:
    """明细名展示兜底:POS 噪声/乱码清洗(item_name 收口·卡片与详情同一套);整名不可读 → 编号占位。"""
    return item_name.display(raw, i, t["item_n"])


def items_section(items: list, t: dict, *, cap: int = 5) -> list:
    """明细分区:小标题 + 逐条(编号 + 名称 + 右对齐价)。超 cap 行 → 截断 + 「还有N行,去详情页」。

    任一展示行的名称读不出(只能编号占位)→ 尾部温和提示「明细名称不清楚·请核对」(P2C·金额仍可确认)。
    免费/无价品项(amount 空)不渲染价格节点:LINE Flex 的 text 必须非空,空字符串会让整卡被拒(400)。
    """
    items = items or []
    rows = [seclabel(t["detail"])]
    any_unclear = False
    for i, it in enumerate(items[:cap], 1):
        name = _display_item_name(it.get("name"), i, t)
        any_unclear = any_unclear or item_name.is_unclear(it.get("name"))
        amt = str(it.get("amount") or "").strip()
        row = [txt(f"{i}. {name}", size="sm", color=VALUE, flex=5, wrap=True)]
        if amt:
            row.append(
                txt(
                    f"฿{amt}",
                    size="sm",
                    color=VALUE_STRONG,
                    weight="bold",
                    flex=2,
                    align="end",
                    wrap=True,
                )
            )
        rows.append({"type": "box", "layout": "horizontal", "contents": row})
    extra = len(items) - cap
    if extra > 0:
        rows.append(txt(t["items_more"].format(n=extra), size="xxs", color=LABEL, wrap=True))
    if any_unclear:
        rows.append(txt(t["items_name_unclear"], size="xxs", color=LOW, wrap=True))
    return rows


def prune_empty_text(node):
    """递归剔除空/纯空白的 Flex text 节点(及因此清空的 box):LINE 拒收空 text(400)。

    防整类「must be non-empty text」拒收(不只某一字段)。在卡片组装出口统一过一遍,任何漏网的
    空文本都不会让整张卡被拒。返回清洗后的节点;整节点应删 → None。
    """
    if isinstance(node, dict):
        if node.get("type") == "text" and not str(node.get("text") or "").strip():
            return None
        out = {k: prune_empty_text(v) for k, v in node.items()}
        contents = out.get("contents")
        if isinstance(contents, list):
            out["contents"] = [c for c in contents if c is not None]
            if out.get("type") == "box" and not out["contents"]:
                return None
        return out
    if isinstance(node, list):
        return [c for c in (prune_empty_text(i) for i in node) if c is not None]
    return node


def btn(label: str, *, primary: bool, postback: str = None, uri: str = None, danger=False) -> dict:
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
            "color": BRAND,
            "action": action,
        }
    return {
        "type": "button",
        "style": "link",
        "height": "sm",
        "color": LINK_DANGER if danger else LINK,
        "action": action,
    }


def liff_link(liff_id: str, web_url: str, ref: str, view: str = "", ws: str = "") -> str:
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


def stack(primary: dict, view: list, danger: list) -> list:
    """竖排装配:每个动作独占一行,行行之间画分隔线(对标 Paypers · 治同行挤压截断 + 视觉分隔)。"""
    buttons = ([primary] if primary else []) + view + danger
    out = []
    for i, b in enumerate(buttons):
        if i:
            out.append({"type": "separator", "margin": "xs", "color": SEP})
        out.append(b)
    return out


def footer(
    state: str,
    ref: str,
    web_url: str,
    t: dict,
    token: str = "",
    source: str = "doc",
    liff_id: str = "",
    ws: str = "",
    review_first: bool = False,
    block_confirm: bool = False,
) -> list:
    """动作区(按状态出合法动作 · 竖排满宽永不死路):
    confirm 确认入账(主)/编辑/丢弃;posted 查看详情(主)/修改/[替代收据]/撤销;
    dup 查看重复(主)/仍要入账/丢弃。
    block_confirm(金额不可靠)= 禁止入账:只给「打开核对」(去详情)+ 丢弃,**不出确认/继续按钮**。
    review_first(金额可靠但明细不符)= 降级:主按钮「打开核对」,确认入账降为次按钮「บันทึกต่อ」(仍可继续)。"""
    detail_uri = liff_link(liff_id, web_url, ref, ws=ws)
    pb = line_postback

    def link(label, uri, danger=False):
        return btn(label, primary=False, uri=uri, danger=danger)

    def kill(label, data):
        return btn(label, primary=False, postback=data, danger=True)

    primary, view, danger = None, [], []
    if state == "posted":
        primary = btn(t["btn_detail"], primary=True, uri=detail_uri)
        view.append(link(t["btn_edit"], liff_link(liff_id, web_url, ref, "edit", ws)))
        if source == "text" and ref:
            view.append(link(t["btn_receipt"], liff_link(liff_id, web_url, ref, "receipt", ws)))
        danger.append(kill(t["btn_undo"], pb.undo_data(ref, token)))
    elif state == "dup":
        primary = btn(t["btn_open"], primary=True, uri=detail_uri)
        view.append(btn(t["btn_post_anyway"], primary=False, postback=pb.confirm_data(ref, token)))
        danger.append(kill(t["btn_discard"], pb.discard_data(ref, token)))
    elif block_confirm or review_first:  # 主按钮「打开核对」去详情
        # block_confirm(金额不可靠)→ 禁确认/继续入账,只核对+丢弃;review_first(明细不符)→ 保留次按钮「继续保存」
        primary = btn(t["btn_review"], primary=True, uri=detail_uri)
        if review_first and not block_confirm:
            view.append(
                btn(t["btn_post_anyway"], primary=False, postback=pb.confirm_data(ref, token))
            )
        danger.append(kill(t["btn_discard"], pb.discard_data(ref, token)))
    else:  # confirm(草稿请确认)
        primary = btn(t["btn_confirm"], primary=True, postback=pb.confirm_data(ref, token))
        view.append(link(t["btn_edit"], detail_uri))
        danger.append(kill(t["btn_discard"], pb.discard_data(ref, token)))
    return stack(primary, view, danger)


def sheet(sections: list) -> list:
    """把各非空分区拼成一张连续白卡:区与区之间一条细横线(融入·按类分隔)。"""
    out = []
    for contents in sections:
        if not contents:
            continue
        if out:
            out.append({"type": "separator", "color": SEP})
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
