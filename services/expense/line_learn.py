# -*- coding: utf-8 -*-
"""分类学习按钮(LINE 06 · Phase B-1)— 让 Pearnly 沉淀用户的分类习惯。

用户改了某笔分类后,追发一条 3 档按钮问要不要把这次修正沉淀成规则:
  [仅这次]                 不存规则(这条已改·已是现状)。
  [以后「{卖家}」都记{分类}]  存「卖家 → 科目」:文字路写卖家名关键词(lookup_learned 子串),
                            图片路复用 learn_category 写 seller:/tax: 键。
  [这个套账都这样]          存「品名 → 科目」(本套账内该品名跨卖家都套用)。

学习一律走现有引擎(conversation.learn / line_correct_data.learn_category · expense_learned 表),
本模块只加「按钮 surface」。三档共享一个一次性令牌(nonce)→ 重复点幂等;payload(科目/卖家/品名)
存于令牌 action_ref(JSON),不信客户端。学习写入 try/except 吞掉,绝不拖垮改分类主流程。

文字路分类(line_expense._fill_category)只查 lookup_learned 子串 → 故卖家/品名都写成裸关键词;
不改 lookup_learned 的查询优先级,只新增可被它命中的键。
"""

from __future__ import annotations

import json
import logging

from core import db
from services.expense import conversation
from services.expense import line_correct_i18n as ci
from services.line_binding import line_postback

logger = logging.getLogger(__name__)


def offer(tid, ws, line_user_id, lang, *, doc_id) -> None:
    """改分类成功后追发学习按钮(push·best-effort)。没分类不问;拿不到卖家则不显「这家」按钮。

    payload(科目 id/名 + 卖家 + 品名 + 税号)存进一次性令牌;3 档按钮共享它(幂等)。任何异常只记日志,
    绝不拖垮主流程(用户已看到改完的状态卡)。"""
    try:
        from services.line_binding import line_action_nonce as nonce
        from services.line_binding import line_client
        from services.purchase import docs as docs_svc

        with db.get_cursor_rls(tid, commit=True) as cur:
            detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
            doc = (detail or {}).get("doc") or {}
            cid = doc.get("category_id")
            if not cid:  # 没分类 → 没什么可记,不打扰
                return
            cat = doc.get("category_name") or doc.get("category") or ""
            sup = (detail or {}).get("supplier") or {}
            vendor = (sup.get("name") or "").strip()
            tax = str(sup.get("tax_id") or "").strip()
            lines = detail.get("lines") or []
            sid = next(
                (ln.get("subcategory_id") for ln in lines if ln.get("category_id") == cid), None
            )
            sub = _sub_name(cur, tid, ws, cid, sid) if sid else ""
            item = _item_keyword(lines, vendor)
            payload = json.dumps(
                {
                    "cid": str(cid),
                    "sid": str(sid) if sid else None,
                    "cat": cat,
                    "sub": sub,
                    "vendor": vendor,
                    "item": item,
                    "tax": tax,
                },
                ensure_ascii=False,
            )
            token = nonce.mint(
                cur, tenant_id=tid, workspace_client_id=ws, action_ref=payload, user_id=line_user_id
            )
        line_client.push_messages(line_user_id, [_card(vendor, cat, token, lang)])
    except Exception:  # noqa: BLE001 — 学习是附带收益,绝不拖垮改分类主流程
        logger.warning("[line learn] offer failed", exc_info=True)


def handle_postback(bound_user, reply_token, scope, token, lang) -> None:
    """学习按钮 postback:消费令牌(幂等)→ 按 scope 写规则 → 诚实回执。任何异常都回执不抛。"""
    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    luid = bound_user.get("line_user_id") or ""
    if not tid:
        return
    from services.line_binding import line_reply

    def _say(body):
        line_reply.reply_text_context(reply_token, body, line_user_id=luid, tenant_id=tid)

    try:
        from services.line_binding import line_action_nonce as nonce

        with db.get_cursor_rls(tid, commit=True) as cur:
            res = nonce.consume(cur, tenant_id=tid, token=token)
            if res["status"] != "ok":  # used/expired/missing → 幂等友好提示,不重复写
                _say(ci.t(ci.LEARN_STALE, lang))
                return
            payload = json.loads(res["action_ref"])
            body = _apply_scope(cur, scope, tid, res["workspace_client_id"], payload, lang)
        _say(body)
    except Exception:  # noqa: BLE001
        logger.warning("[line learn] postback failed", exc_info=True)
        _say(ci.t(ci.LEARN_STALE, lang))


def _apply_scope(cur, scope, tid, ws, payload, lang) -> str:
    """按 scope 写 expense_learned(复用现有引擎)→ 回执文案。once 不写规则。"""
    cid = payload.get("cid")
    sid = payload.get("sid")
    cat = payload.get("cat", "")
    sub = payload.get("sub", "")
    vendor = (payload.get("vendor") or "").strip()
    item = (payload.get("item") or "").strip()
    tax = payload.get("tax") or ""

    if scope == "vendor":
        from services.expense.line_correct_data import learn_category

        # 图片路:seller:/tax: 键(_smart_category find_exact 精确命中)。
        learn_category(
            cur, tid=tid, ws=ws, supplier={"name": vendor, "tax_id": tax or None}, cid=cid, sid=sid
        )
        # 文字路:卖家名裸关键词(lookup_learned 子串·治真机「tops 水」文字记账)。
        if vendor:
            conversation.learn(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                keyword=vendor.lower(),
                category_id=cid,
                subcategory_id=sid,
                category_name=cat,
                subcategory_name=sub,
            )
        return ci.t(ci.LEARN_VENDOR, lang, vendor=vendor, cat=cat)

    if scope == "ws":
        if item:  # 品名裸关键词 → 本套账内该品名跨卖家都套用(治「水」老被记成水费)
            conversation.learn(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                keyword=item.lower(),
                category_id=cid,
                subcategory_id=sid,
                category_name=cat,
                subcategory_name=sub,
            )
        return ci.t(ci.LEARN_WS, lang, item=item, cat=cat)

    return ci.t(ci.LEARN_ONCE, lang)  # once:不写规则


def _card(vendor, cat, token, lang) -> dict:
    """3 档(无卖家则 2 档)学习按钮卡。按钮 label 截 20 字(displayText 留全文)。"""
    from services.line_binding import line_card_sections as s

    btns = [
        s.btn(
            ci.t(ci.LEARN_BTN_ONCE, lang),
            primary=False,
            postback=line_postback.learn_data("once", token),
        )
    ]
    if vendor:
        btns.append(
            s.btn(
                ci.t(ci.LEARN_BTN_VENDOR, lang, vendor=vendor, cat=cat),
                primary=True,
                postback=line_postback.learn_data("vendor", token),
            )
        )
    btns.append(
        s.btn(
            ci.t(ci.LEARN_BTN_WS, lang),
            primary=False,
            postback=line_postback.learn_data("ws", token),
        )
    )
    ask = ci.t(ci.LEARN_ASK, lang)
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "16px",
            "spacing": "sm",
            "contents": [s.txt(ask, size="sm", color="#111827", weight="bold", wrap=True)],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "12px",
            "contents": btns,
        },
    }
    return s.prune_empty_text({"type": "flex", "altText": ask, "contents": bubble})


def _sub_name(cur, tid, ws, cid, sid) -> str:
    """子科目 id → 名(回执/学习记名用)。查不到 → ''。"""
    from services.purchase import categories as cat_svc

    for p in cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws):
        if str(p.get("id")) == str(cid):
            for c in p.get("children") or []:
                if str(c.get("id")) == str(sid):
                    return c.get("name") or ""
    return ""


def _item_keyword(lines, vendor) -> str:
    """首个非空行品名,去掉卖家名 → 品名关键词(「tops 水」→「水」)。无 → ''。"""
    import re

    desc = next(
        (str(ln.get("description") or "").strip() for ln in lines if ln.get("description")), ""
    )
    if not desc:
        return ""
    if vendor:
        desc = re.sub(re.escape(vendor), "", desc, flags=re.IGNORECASE).strip(" -·:、,/")
    return desc
