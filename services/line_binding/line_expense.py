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
    """文本含金额 → ExpenseDraft + 落草稿 + 回确认卡(doc 10/14 · 绝不静默入账)。

    返回 True = 已处理(回了确认卡);False = 不是记账(回落功能提示)。
    事务所(firm)/ 未开 expense / 无默认套账 / 无金额 / 异常 → False(主路径 + 事务所底线不破坏)。
    """
    try:
        tid = bound_user.get("tenant_id")
        if not tid:
            return False
        from core.workspace_context import default_workspace_id
        from services.expense import expense_draft as draft_store
        from services.expense import line_quick_entry as lqe
        from services.line_binding import line_flex
        from services.purchase import categories as cat_svc
        from services.purchase import intake as intake_svc

        # 门控先行(读):事务所/未开 expense → 直接退,绝不为它跑付费 L2。
        with db.get_cursor_rls(str(tid)) as cur:
            if not intake_svc.line_expense_gate_open(cur, tenant_id=str(tid)):
                return False
            ws = default_workspace_id(cur, str(tid))
        if ws is None:
            return False

        # L1 确定性解析;兜不住(口语/长句·无金额)→ L2 LLM(有 key + 余额才调,扣 1 单位 OCR 费)。
        draft = lqe.parse_expense(text)
        used_l2 = False
        if not draft.has_amount():
            from services.expense import line_l2

            api_key = line_l2.resolve_api_key(bound_user)
            if not api_key or not _ocr_balance_ok(bound_user):
                return False
            data = line_l2.extract(text, api_key)
            if not data or line_l2.intent_of(data) != "expense":
                return False  # query/question/other → 批4 处理;此处回落功能提示
            draft = line_l2.to_draft(data, text)
            if not draft.has_amount():
                return False
            used_l2 = True

        with db.get_cursor_rls(str(tid), commit=True) as cur:
            # 归类:用本套账真实科目树(图/文共用·不分叉)。取业务主体名。
            tree = cat_svc.get_tree(cur, tenant_id=str(tid), workspace_client_id=ws)
            _fill_category(draft, text, tree)
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
        line_client.reply_messages(reply_token, [card])
        return True
    except Exception:
        logger.exception("[line] expense draft failed; fall back to hint")
        return False


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


def _fill_category(draft, text, tree) -> None:
    """据真实科目树把 draft 的 category/subcategory(名+id)填上(图/文共用 intake 匹配器)。"""
    from services.purchase import intake as intake_svc

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
