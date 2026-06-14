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
    """文本 → 记账确认卡(doc 10/14 · 绝不静默入账)。支持多轮澄清(缺金额会反问)。

    返回 True = 已处理(回了卡或澄清);False = 不是记账(回落功能提示)。
    事务所(firm)/ 未开 expense / 无默认套账 / 异常 → False(主路径 + 事务所底线不破坏)。
    """
    try:
        tid = bound_user.get("tenant_id")
        if not tid:
            return False
        from core.workspace_context import default_workspace_id
        from services.expense import expense_draft as draft_store
        from services.line_binding import line_flex
        from services.purchase import categories as cat_svc

        # 门控先行(读):事务所/未开 expense → 直接退,绝不为它跑付费 L2。
        from services.purchase import intake as intake_svc

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

        with db.get_cursor_rls(str(tid), commit=True) as cur:
            tree = cat_svc.get_tree(cur, tenant_id=str(tid), workspace_client_id=ws)
            _fill_category(cur, draft, text, tree, str(tid), ws)
            business_name = _business_name(cur, tenant_id=str(tid), ws=ws)
            created_by = str(bound_user["id"]) if bound_user.get("id") else None
            draft_id = draft_store.insert_draft(
                cur,
                tenant_id=str(tid),
                workspace_client_id=ws,
                draft=draft,
                line_user_id=line_user_id,
                created_by=created_by,
            )
        if used_l2:
            _charge_line_l2(bound_user, str(tid))
        # 查重(图/文共用 check_duplicate_invoice·按套账隔离):命中 → 卡前提示,不阻断由用户定夺。
        dup = _dup_warn(bound_user, draft, ws)
        labels = {k: line_client.t_line(lang, f"exp_card_{k}") for k in _CARD_LABEL_KEYS}
        card = line_flex.expense_confirm_flex(
            draft={
                "amount": str(draft.amount),
                "currency": draft.currency,
                "document_type": draft.document_type,
                "invoice_number": draft.invoice_number,
                "expense_type": draft.expense_type,
                "doc_date": draft.doc_date,
                "category": draft.category,
                "subcategory": draft.subcategory,
                "business_name": business_name,
                "note": draft.note,
                "vendor_name": draft.vendor_name,
            },
            draft_id=draft_id,
            labels=labels,
            edit_url=f"{_EXPENSE_DRAFT_URL}{draft_id}",
        )
        msgs = [card]
        if dup:
            msgs = [{"type": "text", "text": line_client.t_line(lang, "exp_dup_warn")}, card]
        line_client.reply_messages(reply_token, msgs)
        return True
    except Exception:
        logger.exception("[line] expense draft failed; fall back to hint")
        return False


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
            status = (
                "confirmed"
                if parsed.get("action") == line_postback.ACTION_EXP_CONFIRM
                else "discarded"
            )
            draft_store.set_status(
                cur, tenant_id=tid, workspace_client_id=ws, draft_id=draft_id, status=status
            )
            key = "exp_confirmed" if status == "confirmed" else "exp_discarded"
            line_client.reply_text(reply_token, line_client.t_line(lang, key, amount=d["amount"]))
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
