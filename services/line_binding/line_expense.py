# -*- coding: utf-8 -*-
"""LINE 一句话记账对话处理(文本路 · 统一智能通道)。

handle_expense_text:文本 → 智能解析(L1 规则 + L2 LLM)→ 记账直接落采购进项草稿单;
缺金额反问、查账、问答、越界挡回。护栏(doc 10 §1):用户可见文案全走 line_i18n 模板。
"""

from __future__ import annotations

import logging

from core import db
from services.line_binding import line_client

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

        # 1. L1 快路:清晰记账(有金额 + 非问句 + 无其他 L1 意图)→ 直接记,零 LLM、零成本。
        parsed = lqe.parse_expense(text)
        si = lqe.l1_intent(text)
        isq = lqe.is_question(text)
        if parsed.has_amount() and not isq and si is None:
            from services.expense import conversation

            with db.get_cursor_rls(str(tid), commit=True) as cur:
                pend = conversation.pop_pending(cur, line_user_id=line_user_id)
            if pend:  # 续接:上句缺金额存了半成品,这句补金额 → 合并
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
            line_agent.understand(text, api_key=api_key)
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
            _reply_summary(reply_token, lang, str(tid), ws)
        elif si == "support":
            _reply_pool(reply_token, "support", text, lang)
        elif isq:
            _reply_question(reply_token, lang, str(tid), text)
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
        _reply_summary(reply_token, lang, tid, ws)
        return True
    if intent == "query_detail":
        _reply_detail(reply_token, lang, tid, ws)
        return True
    if intent == "undo":
        _reply_undo(bound_user, reply_token, lang, tid, ws)
        return True
    if intent == "edit":
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
    else:
        _reply_pool(reply_token, "scope", text, lang)
    return True


def _do_record(bound_user, reply_token, text, tid, ws, draft, used_l2, quote_token, lang) -> bool:
    """置信驱动入账(图/文同口径):建草稿 → 高置信 post_doc;回数据卡。计费由调用方管。"""
    from services.expense import confidence
    from services.purchase import categories as cat_svc
    from services.purchase import docs as docs_svc
    from services.purchase import intake as intake_svc
    from services.purchase import posting as posting_svc
    from services.purchase import settings as settings_svc

    created_by = str(bound_user["id"]) if bound_user.get("id") else None
    with db.get_cursor_rls(tid, commit=True) as cur:
        tree = cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws)
        _fill_category(cur, draft, text, tree, tid, ws)
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
        created = docs_svc.create_doc(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            created_by=created_by,
            data=_to_purchase_data(draft.model_dump()),
            settings=cfg,
            status="draft",
        )
        doc_id = str(created["doc"]["id"])
        if verdict.action == "post":
            posting_svc.post_doc(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                doc_id=doc_id,
                auto_stock_in=False,
                created_by=created_by,
            )
            state = "posted"
        else:
            state = "dup" if verdict.dup else "confirm"
    _reply_card(reply_token, state, draft, doc_id, lang, quote_token, ws_name)
    return True


def _card_fields_from_draft(draft) -> dict:
    """ExpenseDraft → 数据卡归一字段。"""
    return {
        "document_type": draft.document_type or "",
        "expense_type": draft.expense_type or "",
        "date": draft.doc_date or "",
        "category": draft.category or "",
        "subcategory": draft.subcategory or "",
        "vendor": draft.vendor_name or "",
        "seller_tax": getattr(draft, "vendor_tax_id", "") or "",
        "invoice_number": draft.invoice_number or "",
        "detail": (draft.note or "").strip(),
    }


def _reply_card(reply_token, state, draft, doc_id, lang, quote_token, workspace_name="") -> None:
    """回执 = 【引用原句的一行回执】+【Flex 数据卡】(Flex 不能被引用,故拆两条)。"""
    from services.line_binding import line_card

    ack_key = {"posted": "exp_ack_posted", "dup": "exp_ack_dup"}.get(state, "exp_ack_confirm")
    ack = {"type": "text", "text": line_client.t_line(lang, ack_key, amount=draft.amount)}
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


def _reply_summary(reply_token, lang, tid, ws) -> None:
    """查账汇总(本月已入账 + 按分类拆解)· DB 真查,绝不让模型编数字。"""
    from services.expense import line_qa

    try:
        with db.get_cursor_rls(tid) as cur:
            s = line_qa.month_summary(cur, tenant_id=tid, workspace_client_id=ws)
    except Exception:
        logger.exception("[line] summary failed")
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_q_not_found"))
        return
    if s["count"] == 0:
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_sum_empty"))
        return
    uncat = line_client.t_line(lang, "exp_uncat")
    lines = [line_client.t_line(lang, "exp_sum_head", amount=s["total"], n=s["count"])]
    for c in s["by_category"][:6]:
        lines.append(f"• {c['name'] or uncat}: ฿{c['amount']} ({c['count']})")
    line_client.reply_text(reply_token, "\n".join(lines))


def _reply_detail(reply_token, lang, tid, ws) -> None:
    """查明细(本月逐笔)· DB 真查 → 列表。"""
    from services.expense import line_qa

    try:
        with db.get_cursor_rls(tid) as cur:
            rows = line_qa.month_detail(cur, tenant_id=tid, workspace_client_id=ws, limit=10)
    except Exception:
        logger.exception("[line] detail failed")
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_q_not_found"))
        return
    if not rows:
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_sum_empty"))
        return
    uncat = line_client.t_line(lang, "exp_uncat")
    lines = [line_client.t_line(lang, "exp_detail_head", n=len(rows))]
    for r in rows:
        tail = f" · {r['vendor']}" if r["vendor"] else ""
        lines.append(f"• {r['date']} {r['category'] or uncat} ฿{r['amount']}{tail}")
    line_client.reply_text(reply_token, "\n".join(lines))


def _reply_undo(bound_user, reply_token, lang, tid, ws) -> None:
    """撤销上一笔(LINE 记的、已入账正式单)· void_doc 冲销,不物理删。无 → 诚实告知。"""
    uid = str(bound_user["id"]) if bound_user.get("id") else None
    try:
        from services.purchase import posting as posting_svc

        with db.get_cursor_rls(tid, commit=True) as cur:
            cur.execute(
                "SELECT id, grand_total FROM purchase_docs "
                "WHERE tenant_id = %s AND workspace_client_id = %s AND source = 'line' "
                "AND status = 'posted' ORDER BY created_at DESC LIMIT 1",
                (tid, ws),
            )
            row = cur.fetchone()
            if not row:
                line_client.reply_text(reply_token, line_client.t_line(lang, "exp_undo_none"))
                return
            res = posting_svc.void_doc(
                cur, tenant_id=tid, workspace_client_id=ws, doc_id=str(row["id"]), created_by=uid
            )
            amt = (res.get("doc") or {}).get("grand_total") or row["grand_total"]
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_undo_done", amount=amt))
    except Exception:
        logger.exception("[line] undo failed")
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_undo_none"))


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
