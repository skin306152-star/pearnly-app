# -*- coding: utf-8 -*-
"""LINE 一句话记账对话处理(文本路 · 统一智能通道)。

handle_expense_text:文本 → 智能解析(L1 规则 + L2 LLM)→ 记账直接落采购进项草稿单;
缺金额反问、查账、问答、越界挡回。护栏(doc 10 §1):用户可见文案全走 line_i18n 模板。
"""

from __future__ import annotations

import logging
import os

from core import db
from services.line_binding import line_client, line_expense_qa

logger = logging.getLogger(__name__)


_WEB_PURCHASE_URL = "https://pearnly.com/home"


def handle_expense_text(
    bound_user, reply_token, line_user_id, text, lang, quote_token=None
) -> bool:
    """文本 → LINE 大脑(LLM tool-calling)→ 工具执行(docs/smart-intake/15)。

    L1 快路:清晰记账(有金额+非问句)零 LLM 直接记。其余 → 大脑一次 LLM 听意图+抽槽+组织回复,
    确定性代码执行工具(记账/查账/查明细/撤销/编辑→网页/闲聊)。金额与过账永不信 LLM;问句/否定/
    假设永不写账。无 key/LLM 失败 → 回落确定性 L1。返回 True=已处理;未开 expense/无套账/异常 → False。
    """
    try:
        tid = bound_user.get("tenant_id")
        if not tid:
            return False
        from services.expense import line_quick_entry as lqe
        from services.expense import replies
        from services.line_binding import line_chat_memory

        # 对话记忆(PO-15):先取历史(不含本条)供大脑多轮连贯,再记本条用户消息。
        history = line_chat_memory.recent(line_user_id=line_user_id, tenant_id=str(tid))
        line_chat_memory.note(
            line_user_id=line_user_id, tenant_id=str(tid), role="user", content=text
        )

        # 0. 闲聊(零成本 L1)→ 智能问候/感谢(治复读)。
        small = replies.detect_smalltalk(text)
        if small:
            _reply_pool(reply_token, small, text, lang)
            return True

        from core.workspace_context import default_workspace_id
        from services.purchase import intake as intake_svc

        with db.get_cursor_rls(str(tid)) as cur:
            if not intake_svc.line_expense_gate_open(cur, tenant_id=str(tid)):
                return False
            ws = default_workspace_id(cur, str(tid))
        if ws is None:
            return False

        # 0. 待确认的更正(上句"改成X吗")→ 这句 是/否 → 执行/取消(优先于记账/大脑/兜底·PO-13)
        from services.expense import line_correct

        if line_correct.try_confirm(
            bound_user, reply_token, line_user_id, text, str(tid), ws, lang
        ):
            return True

        si = lqe.l1_intent(text)
        isq = lqe.is_question(text)

        # #7 收入识别:明确「收款/卖出」且无购买动词 → 不误记为支出。LINE 暂无收入流 →
        #    只识别 + 不入账 + 引导(保守:问句/已有 L1 意图不拦,宁漏勿误挡正常买东西)。
        if lqe.detect_income(text) and not isq and si is None:
            line_client.reply_text(reply_token, line_client.t_line(lang, "exp_income_guide"))
            line_chat_memory.note(
                line_user_id=line_user_id,
                tenant_id=str(tid),
                role="bot",
                content="[收入·未记账·引导网页]",
            )
            return True

        # 1a. 多项一句话(电费50 买菜40 电费10 吃饭50)→ 拆多笔·逐项智能归类·合计入账·卡显逐条
        #     (对标 Paypers)。问句/有其它 L1 意图不走(防误记)。
        multi = lqe.parse_multi(text)
        if multi and not isq and si is None:
            from services.line_binding import line_expense_multi

            return line_expense_multi.do_record_multi(
                bound_user, reply_token, text, str(tid), ws, multi, quote_token, lang
            )

        # 1. L1 快路:清晰记账(有金额 + 非问句 + 无其他 L1 意图)→ 直接记,零 LLM、零成本。
        parsed = lqe.parse_expense(text)
        if parsed.has_amount() and not isq and si is None:
            from services.expense import conversation

            with db.get_cursor_rls(str(tid), commit=True) as cur:
                pend = conversation.pop_pending(cur, line_user_id=line_user_id)
            # 续接补金额(更正待确认 pending 不在此并:已在第 0 步处理)
            if pend and not str(pend.get("missing") or "").startswith("correct:"):
                merged = pend["draft"]
                merged.amount = parsed.amount
                parsed = merged
            return _do_record(
                bound_user, reply_token, text, str(tid), ws, parsed, False, quote_token, lang
            )

        # 2. 大脑(一次 LLM):听意图 + 抽槽 + 自然回复 → 工具分发。
        from services.expense import line_agent, line_l2

        api_key = line_l2.resolve_api_key(bound_user)
        u = (
            line_agent.understand(text, api_key=api_key, history=history)
            if (api_key and _ocr_balance_ok(bound_user))
            else None
        )
        if u:
            _charge_line_l2(bound_user, str(tid))
            return _dispatch_agent(
                bound_user, reply_token, line_user_id, text, lang, str(tid), ws, u, quote_token
            )

        # 3. 兜底(无 LLM):L1 查账/求助/问答(知识库),否则礼貌带回(复用上面已算的 si/isq)。
        if si == "query":
            line_expense_qa.reply_summary(reply_token, lang, str(tid), ws)
        elif si == "support":
            _reply_pool(reply_token, "support", text, lang)
        elif isq:
            line_expense_qa.reply_question(reply_token, lang, str(tid), text)
        else:
            _reply_pool(reply_token, "scope", text, lang)
        return True
    except Exception:
        logger.exception("[line] expense handle failed; fall back")
        return False


def _dispatch_agent(
    bound_user, reply_token, line_user_id, text, lang, tid, ws, u, quote_token
) -> bool:
    """大脑决策 → 确定性工具执行。写账闸由 may_write 裁决(问句/否定/假设不写)。"""
    from services.expense import line_agent

    intent = u.get("intent")
    if intent == "query_summary":
        line_expense_qa.reply_summary(reply_token, lang, tid, ws)
        return True
    if intent == "query_detail":
        line_expense_qa.reply_detail(reply_token, lang, tid, ws)
        return True
    if intent == "undo":
        line_expense_qa.reply_undo(bound_user, reply_token, lang, tid, ws)
        return True
    if intent == "edit":
        amt = u.get("amount")
        if amt not in (None, "", 0):
            # 「上一笔改成 X」→ 更正:冲销原单 + 按新值重建草稿(请确认·绝不静默覆盖·PO-13)
            from services.expense import line_correct

            return line_correct.request_correct(
                bound_user, reply_token, line_user_id, amt, lang, tid, ws
            )
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_edit_web"))
        return True
    if line_agent.may_write(intent, u.get("speech_act")):
        from services.expense import line_l2

        draft = line_l2.to_draft(u, text)
        if draft.has_amount():
            return _do_record(
                bound_user, reply_token, text, tid, ws, draft, True, quote_token, lang
            )
        from services.expense import conversation

        with db.get_cursor_rls(tid, commit=True) as cur:
            conversation.save_pending(
                cur,
                line_user_id=line_user_id,
                tenant_id=tid,
                workspace_client_id=ws,
                draft=draft,
                missing="amount",
            )
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_need_amount"))
        return True
    # chat / out_of_scope / 含数字的问句否定假设 → 自然回复(无则礼貌带回)
    reply = (u.get("reply") or "").strip()
    if reply:
        line_client.reply_text(reply_token, reply)
        from services.line_binding import line_chat_memory

        line_chat_memory.note(line_user_id=line_user_id, tenant_id=tid, role="bot", content=reply)
    else:
        _reply_pool(reply_token, "scope", text, lang)
    return True


def _do_record(bound_user, reply_token, text, tid, ws, draft, used_l2, quote_token, lang) -> bool:
    """置信驱动入账(图/文同口径):建草稿 → 高置信 post_doc;回数据卡。计费由调用方管。"""
    from services.expense import confidence
    from services.line_binding import line_booker
    from services.purchase import categories as cat_svc
    from services.purchase import intake as intake_svc
    from services.purchase import settings as settings_svc

    created_by = str(bound_user["id"]) if bound_user.get("id") else None
    from services.expense import line_l2

    api_key = line_l2.resolve_api_key(bound_user)
    with db.get_cursor_rls(tid, commit=True) as cur:
        tree = cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws)
        _fill_category(cur, draft, text, tree, tid, ws, api_key)
        cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
        ws_name = intake_svc.workspace_name(cur, tenant_id=tid, workspace_client_id=ws)
        is_dup = _dup_warn(bound_user, draft, ws)
        verdict = confidence.grade(
            amount=draft.amount,
            vendor_name=draft.vendor_name,
            invoice_number=draft.invoice_number,
            document_type=draft.document_type or "",
            direction="expense",
            confidence_band="high" if not used_l2 else "needs_review",
            has_category=bool(draft.category_id),
            is_duplicate=is_dup,
            require_category=False,
        )
        # 文/图/多项共用入账编排(#10 line_booker):建草稿→按置信过账→铸 nonce。
        doc_id, state, token = line_booker.book_and_mint(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            data=_to_purchase_data(draft.model_dump()),
            settings=cfg,
            verdict=verdict,
            created_by=created_by,
        )
    _reply_card(reply_token, state, draft, doc_id, lang, quote_token, ws_name, token, str(ws or ""))
    return True


def _card_fields_from_draft(draft) -> dict:
    """ExpenseDraft → 数据卡归一字段。

    详情结构化(#10b):单笔也出逐条 `物品 ×数量 ฿金额`(对齐多笔),不再回显整句原文。
    物品名 = 清出的干净名(draft.note);数量>1 缀「×N」;金额=行总额。
    """
    item = (draft.note or "").strip()
    items = []
    if item and draft.amount is not None:
        from decimal import Decimal

        try:
            q = Decimal(str(draft.qty)) if draft.qty not in (None, "", 0) else Decimal("1")
        except Exception:
            q = Decimal("1")
        label = f"{item} ×{format(q.normalize(), 'f')}" if q > 1 else item
        items = [{"name": label, "amount": f"{draft.amount:,.2f}"}]
    return {
        "document_type": draft.document_type or "",
        "expense_type": draft.expense_type or "",
        "date": draft.doc_date or "",
        "category": draft.category or "",
        "subcategory": draft.subcategory or "",
        "vendor": draft.vendor_name or "",
        "seller_tax": getattr(draft, "vendor_tax_id", "") or "",
        "invoice_number": draft.invoice_number or "",
        "items": items,
        "detail": item,
    }


def _reply_card(
    reply_token, state, draft, doc_id, lang, quote_token, workspace_name="", token="", ws=""
) -> None:
    """回执 = 【引用原句的一行回执】+【Flex 数据卡】(Flex 不能被引用,故拆两条)。"""
    from services.line_binding import line_booker, line_card

    ack = {
        "type": "text",
        "text": line_client.t_line(lang, line_booker.ack_key(state), amount=draft.amount),
    }
    if quote_token:
        ack["quoteToken"] = quote_token
    card = line_card.result_card(
        state=state,
        amount=draft.amount,
        fields=_card_fields_from_draft(draft),
        field_confidence={},
        doc_id=doc_id,
        lang=lang,
        web_url=_WEB_PURCHASE_URL,
        source="text",
        workspace_name=workspace_name,
        token=token,
        liff_id=os.getenv("LINE_LIFF_ID", "").strip(),
        workspace_client_id=ws,
    )
    line_client.reply_messages(reply_token, [ack, card])


def _reply_pool(reply_token, kind, text, lang) -> None:
    """问候/感谢/跑题 → 轮选回复 + Quick Reply 引导(不复读)。"""
    from services.expense import replies

    items = [
        _qr_item(line_client.t_line(lang, "qr_record"), "ค่าน้ำ 50"),
        _qr_item(line_client.t_line(lang, "qr_query"), line_client.t_line(lang, "qr_query_text")),
    ]
    msg = {
        "type": "text",
        "text": replies.pick(kind, text, lang),
        "quickReply": {"items": items},
    }
    line_client.reply_messages(reply_token, [msg])


def _to_purchase_data(d: dict) -> dict:
    """expense_draft → 采购进项建单 data(doc_kind=expense·带卖家/分类·source=line)。

    数量(#8):「买2杯咖啡共120」→ 行 qty=2、单价=60(split_qty_price·总额不漂);无数量 → qty=1。
    """
    from services.expense.line_quick_entry import split_qty_price

    _qty, _unit_price = split_qty_price(d.get("amount"), d.get("qty"), d.get("unit_price"))
    line = {
        "item_type": "service" if (d.get("expense_type") == "service") else "goods",
        "description": (
            d.get("note") or d.get("subcategory") or d.get("category") or "LINE บันทึก"
        ).strip(),
        "qty": _qty,
        "unit_price": _unit_price,
        "vat_rate": 0,
        "wht_rate": 0,
        "category_id": d.get("category_id"),
        "subcategory_id": d.get("subcategory_id"),
    }
    from services.purchase import intake as _intake

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
        "payment_status": _intake.default_payment_status(d.get("document_type"), "expense"),
        "lines": [line],
    }


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


def _qr_item(label: str, text: str) -> dict:
    return {"type": "action", "action": {"type": "message", "label": label[:20], "text": text}}


def _fill_category(cur, draft, text, tree, tid, ws, api_key=None) -> None:
    """填 category/subcategory(名+id)。学习词典(越用越省)→ 关键词 → LLM 智能兜底。

    关键词对中文/泰文混输或品名(「水费」「ทุเรียน」)常命不中 → 有 key 时让 LLM 在真实树里挑
    (懂跨语言+品名),治文字路分类恒空。无 key 才止于关键词。
    """
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
    if not cat_id and api_key:
        from services.expense import category_ai

        cat_id, sub_id = category_ai.suggest_category(
            draft.vendor_name or "", text, tree, api_key=api_key
        )
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
