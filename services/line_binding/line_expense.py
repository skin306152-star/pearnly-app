# -*- coding: utf-8 -*-
"""LINE 一句话记账对话处理(文本路 · doc 10/14)。

从 line_webhook_routes 抽出,保 webhook 薄(只路由)。两个入口:
  handle_expense_text     文本含金额 → L1/L2 解析 → 落草稿 → 回确认卡(绝不静默入账)
  handle_expense_postback 确认卡按钮 → 草稿置 confirmed/discarded(留痕)
护栏(doc 10 §1):用户可见文案全走 line_i18n 模板;L2 只产结构化数据。
"""

from __future__ import annotations

import logging

from core import db
from services.line_binding import line_client, line_postback

logger = logging.getLogger(__name__)

# 费用草稿网页编辑深链(doc 14 §6 · 前端复核屏接此 draft id · 泰语先行)。
_EXPENSE_DRAFT_URL = "https://pearnly.com/home#expense-draft="

_CARD_LABEL_KEYS = (
    "head",
    "doc_type",
    "inv_no",
    "exp_type",
    "date",
    "category",
    "subcategory",
    "business",
    "detail",
    "vendor",
    "confirm",
    "discard",
    "edit",
)


def handle_expense_text(bound_user, reply_token, line_user_id, text, lang) -> bool:
    """文本 → 智能解析 → 直接落采购进项草稿单(统一智能通道 · Zihao 2026-06-15 拍板)。

    所有账号(不分业态)统一走;有金额 → 直接入采购(不回确认卡);缺金额 → 反问;
    查账/问答/越界 → 对应智能回复。返回 True=已处理;False=非记账(回落功能提示)。
    未开 expense 模块 / 无默认套账 / 异常 → False。
    """
    try:
        tid = bound_user.get("tenant_id")
        if not tid:
            return False
        from core.workspace_context import default_workspace_id
        from services.purchase import categories as cat_svc
        from services.purchase import docs as docs_svc
        from services.purchase import intake as intake_svc
        from services.purchase import settings as settings_svc

        # 门控先行(读):未开 expense 模块 → 退(不按业态分·统一智能通道)。
        with db.get_cursor_rls(str(tid)) as cur:
            if not intake_svc.line_expense_gate_open(cur, tenant_id=str(tid)):
                return False
            ws = default_workspace_id(cur, str(tid))
        if ws is None:
            return False

        draft, used_l2, action = _resolve_draft(bound_user, line_user_id, text, str(tid), ws)
        if action == "clarify":
            # 确是记账但缺金额 → 反问一句(已存会话态),不静默丢(doc 10 §1.6)。
            line_client.reply_text(reply_token, line_client.t_line(lang, "exp_need_amount"))
            return True
        if action == "query":  # 查账(本月花多少)→ DB 真查(doc 10 §1.4)
            _reply_query(reply_token, lang, str(tid), ws)
            return True
        if action == "question":  # 问答 → 知识中心带出处,查不到诚实兜底(doc 10 §1.3)
            _reply_question(reply_token, lang, str(tid), text)
            return True
        if action == "other":  # 越界/闲聊 → 礼貌挡回 + Quick Reply 引导(doc 10 §1.5)
            _reply_scope_block(reply_token, lang)
            return True
        if draft is None:
            return False

        # 有金额 → 直接落采购进项草稿单(统一智能通道 · 不回确认卡 · Zihao 2026-06-15 拍板)。
        # 草稿状态:用户在「采购 · 待归类/进项」里复核/补全/推 ERP。
        with db.get_cursor_rls(str(tid), commit=True) as cur:
            tree = cat_svc.get_tree(cur, tenant_id=str(tid), workspace_client_id=ws)
            _fill_category(cur, draft, text, tree, str(tid), ws)
            cfg = settings_svc.get_settings(cur, tenant_id=str(tid), workspace_client_id=ws)
            created_by = str(bound_user["id"]) if bound_user.get("id") else None
            docs_svc.create_doc(
                cur,
                tenant_id=str(tid),
                workspace_client_id=ws,
                created_by=created_by,
                data=_to_purchase_data(draft.model_dump()),
                settings=cfg,
                status="draft",
            )
        if used_l2:
            _charge_line_l2(bound_user, str(tid))
        body = line_client.t_line(lang, "exp_recorded_purchase", amount=draft.amount)
        if _dup_warn(bound_user, draft, ws):
            body = line_client.t_line(lang, "exp_dup_warn") + "\n\n" + body
        line_client.reply_text(reply_token, body)
        return True
    except Exception:
        logger.exception("[line] expense record failed; fall back to hint")
        return False


def _to_purchase_data(d: dict) -> dict:
    """expense_draft → 采购进项建单 data(doc_kind=expense·单行=总额·带卖家/分类·source=line)。"""
    line = {
        "item_type": "service" if (d.get("expense_type") == "service") else "goods",
        "description": (
            d.get("note") or d.get("subcategory") or d.get("category") or "LINE บันทึก"
        ).strip(),
        "qty": "1",
        "unit_price": str(d.get("amount") or "0"),
        "vat_rate": 0,
        "wht_rate": 0,
        "category_id": d.get("category_id"),
        "subcategory_id": d.get("subcategory_id"),
    }
    return {
        "doc_kind": "expense",
        "source": "line",
        "doc_date": d.get("doc_date"),
        "category_id": d.get("category_id"),
        "supplier": {
            "name": (d.get("vendor_name") or "").strip(),
            "tax_id": (d.get("vendor_tax_id") or "").strip() or None,
        },
        "doc_no": (d.get("invoice_number") or "").strip() or None,
        "currency": d.get("currency") or "THB",
        "lines": [line],
    }


def _post_to_purchase(cur, tid: str, ws: int, d: dict, bound_user) -> None:
    """LINE 确认入账 → 落一张采购进项草稿单(图/文同下游 · 用户可在进项采购看到/补全/推 ERP)。"""
    from services.purchase import docs as docs_svc
    from services.purchase import settings as settings_svc

    cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
    created_by = str(bound_user["id"]) if bound_user.get("id") else None
    docs_svc.create_doc(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        created_by=created_by,
        data=_to_purchase_data(d),
        settings=cfg,
        status="draft",
    )


def _receipt_url(draft_id: str, tid: str, ws: int) -> str:
    """替代收据 PDF 链接(签名 token · 外部浏览器可开)。"""
    import time

    from services.expense import receipt_token

    tok = receipt_token.sign(draft_id=draft_id, tenant_id=tid, ws=ws, now_ts=int(time.time()))
    return f"https://pearnly.com/api/expense/receipt/{draft_id}?t={tok}"


def _dup_warn(bound_user, draft, ws) -> bool:
    """查重(图/文共用 check_duplicate_invoice)。命中已识别历史 → True(卡前提示)。任何异常 → False。"""
    try:
        if not (draft.invoice_number or (draft.vendor_name and draft.amount)):
            return False
        from services.ocr_history.queries import check_duplicate_invoice

        dup = check_duplicate_invoice(
            str(bound_user["id"]),
            draft.invoice_number or None,
            draft.doc_date,
            draft.vendor_name or None,
            float(draft.amount) if draft.amount is not None else None,
            workspace_client_id=ws,
        )
        return bool(dup)
    except Exception:
        logger.warning("[line] dup check failed; skip warning")
        return False


def _resolve_draft(bound_user, line_user_id, text, tid, ws):
    """→ (draft, used_l2, action)。action: '' 正常出卡 / 'clarify' 已反问缺金额 / None 非记账。

    顺序:① 有金额 → 若有待补会话态则合并(续接澄清),否则 L1 直接出 ② 无金额 → L2 兜底;
    L2 判记账但仍缺金额 → 存会话态 + 反问;L2 判非记账 → None。
    """
    from services.expense import conversation
    from services.expense import line_quick_entry as lqe

    parsed = lqe.parse_expense(text)
    if parsed.has_amount():
        with db.get_cursor_rls(tid, commit=True) as cur:
            pend = conversation.pop_pending(cur, line_user_id=line_user_id)
        if pend:  # 续接:上一句缺金额存了半成品,这句补上金额 → 合并
            merged = pend["draft"]
            merged.amount = parsed.amount
            return merged, False, ""
        return parsed, False, ""

    # 无金额 → L2(有 key + 余额才调)
    from services.expense import line_l2

    api_key = line_l2.resolve_api_key(bound_user)
    if not api_key or not _ocr_balance_ok(bound_user):
        return None, False, None
    data = line_l2.extract(text, api_key)
    if not data:
        return None, False, None
    intent = line_l2.intent_of(data)
    if intent != "expense":
        return None, False, intent  # query / question / other → 下方分发(批4)
    draft = line_l2.to_draft(data, text)
    if draft.has_amount():
        return draft, True, ""
    # 确是记账但 LLM 也没抽到金额 → 存会话态 + 反问(不静默丢)
    with db.get_cursor_rls(tid, commit=True) as cur:
        conversation.save_pending(
            cur,
            line_user_id=line_user_id,
            tenant_id=tid,
            workspace_client_id=ws,
            draft=draft,
            missing="amount",
        )
    return None, False, "clarify"


def handle_expense_postback(bound_user, reply_token, parsed, lang) -> None:
    """费用草稿确认/丢弃(doc 10 §5)。确认 → status=confirmed + 回执;丢弃 → discarded(留痕不删)。"""
    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    draft_id = parsed.get("draft_id")
    if not tid or not draft_id:
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_not_found"))
        return
    try:
        from core.workspace_context import default_workspace_id
        from services.expense import expense_draft as draft_store

        with db.get_cursor_rls(tid, commit=True) as cur:
            ws = default_workspace_id(cur, tid)
            d = (
                draft_store.get_draft(cur, tenant_id=tid, workspace_client_id=ws, draft_id=draft_id)
                if ws is not None
                else None
            )
            if not d:
                line_client.reply_text(reply_token, line_client.t_line(lang, "exp_not_found"))
                return
            if parsed.get("action") == line_postback.ACTION_EXP_CONFIRM:
                # 确认入账 = 落一张采购进项草稿单(LINE 记账的归宿 · 图/文同下游)。
                _post_to_purchase(cur, tid, ws, d, bound_user)
                draft_store.set_status(
                    cur,
                    tenant_id=tid,
                    workspace_client_id=ws,
                    draft_id=draft_id,
                    status="confirmed",
                )
                status = "confirmed"
            else:
                draft_store.set_status(
                    cur,
                    tenant_id=tid,
                    workspace_client_id=ws,
                    draft_id=draft_id,
                    status="discarded",
                )
                status = "discarded"
        if status == "confirmed":
            # 确认后给替代收据 PDF 链接(签名 token · 外部浏览器可开 · doc 14 §7)。
            body = line_client.t_line(lang, "exp_confirmed", amount=d["amount"])
            body += "\n📄 " + _receipt_url(draft_id, tid, ws)
            line_client.reply_text(reply_token, body)
        else:
            line_client.reply_text(reply_token, line_client.t_line(lang, "exp_discarded"))
    except Exception:
        logger.exception("[line postback] expense draft confirm failed")
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_not_found"))


def _reply_query(reply_token, lang, tid, ws) -> None:
    """查账(本月花多少)· DB 真查 → 模板填数。"""
    from services.expense import line_qa

    try:
        with db.get_cursor_rls(tid) as cur:
            total = line_qa.month_spending(cur, tenant_id=tid, workspace_client_id=ws)
        line_client.reply_text(
            reply_token, line_client.t_line(lang, "exp_query_month", amount=total)
        )
    except Exception:
        logger.exception("[line] query failed")
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_q_not_found"))


def _reply_question(reply_token, lang, tid, question) -> None:
    """问答 · 知识中心带出处;查不到诚实兜底 + 指路(绝不编造)。"""
    from services.expense import line_qa

    try:
        with db.get_cursor_rls(tid) as cur:
            res = line_qa.knowledge_answer(cur, tenant_id=tid, question=question)
    except Exception:
        logger.exception("[line] question failed")
        res = None
    if not res:
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_q_not_found"))
        return
    src = ", ".join(res["citations"]) if res.get("citations") else ""
    body = res["answer"]
    if src:
        body += "\n\n" + line_client.t_line(lang, "exp_q_source", src=src)
    line_client.reply_text(reply_token, body)


def _reply_scope_block(reply_token, lang) -> None:
    """越界/闲聊 → 礼貌挡回 + Quick Reply 引导(不硬答)。"""
    items = [
        _qr_item(line_client.t_line(lang, "qr_record"), "ค่าน้ำ 50"),
        _qr_item(line_client.t_line(lang, "qr_query"), line_client.t_line(lang, "qr_query_text")),
    ]
    msg = {
        "type": "text",
        "text": line_client.t_line(lang, "exp_scope_block"),
        "quickReply": {"items": items},
    }
    line_client.reply_messages(reply_token, [msg])


def _qr_item(label: str, text: str) -> dict:
    return {"type": "action", "action": {"type": "message", "label": label[:20], "text": text}}


def _fill_category(cur, draft, text, tree, tid, ws) -> None:
    """填 category/subcategory(名+id)。先查已学习词典(越用越省),再内置关键词匹配真实树。"""
    from services.expense import conversation
    from services.purchase import intake as intake_svc

    learned = conversation.lookup_learned(cur, tenant_id=tid, workspace_client_id=ws, text=text)
    if learned and learned["category_id"]:
        draft.category = learned["category_name"]
        draft.category_id = learned["category_id"]
        draft.subcategory = learned["subcategory_name"]
        draft.subcategory_id = learned["subcategory_id"]
        return

    cat_id, sub_id = intake_svc._match_category(text, tree)
    if not cat_id:
        return
    for parent in tree:
        if parent["id"] == cat_id:
            draft.category = parent["name"]
            draft.category_id = str(cat_id)
            for child in parent.get("children") or []:
                if child["id"] == sub_id:
                    draft.subcategory = child["name"]
                    draft.subcategory_id = str(sub_id)
            return


def _business_name(cur, *, tenant_id, ws) -> str:
    """套账主体名(确认卡「业务主体」栏)。"""
    cur.execute(
        "SELECT name FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (ws, tenant_id),
    )
    row = cur.fetchone()
    return (row["name"] or "") if row else ""


def _ocr_balance_ok(bound_user) -> bool:
    """L2 付费前余额闸:余额够 或 豁免 → True。任何异常 → False(不调付费 L2·不阻塞)。"""
    try:
        tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
        billing = db.get_billing_status_combined(str(bound_user["id"]), tid)
        return bool(billing.get("allowed") or billing.get("is_exempt"))
    except Exception:
        logger.warning("[line l2] balance check failed; skip paid L2")
        return False


def _charge_line_l2(bound_user, tenant_id: str) -> None:
    """L2 调用按 OCR credits 口径扣 1 单位(L1 命中零成本)。尽力而为,失败只记日志。"""
    try:
        db.charge_ocr_async(str(bound_user["id"]), tenant_id, "pdf", 1, None, "line_text_l2")
    except Exception:
        logger.warning("[line l2] charge failed (recorded draft still valid)")
