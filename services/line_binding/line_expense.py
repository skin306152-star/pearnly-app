# -*- coding: utf-8 -*-
"""LINE 一句话记账对话处理(文本路 · 统一智能通道)。

handle_expense_text:文本 → 智能解析(L1 规则 + L2 LLM)→ 记账直接落采购进项草稿单;
缺金额反问、查账、问答、越界挡回。护栏(doc 10 §1):用户可见文案全走 line_i18n 模板。
"""

from __future__ import annotations

import logging

from core import db
from services.line_binding import line_client, line_expense_qa, line_reply

logger = logging.getLogger(__name__)


def handle_expense_text(
    bound_user, reply_token, line_user_id, text, lang, quote_token=None, quoted_message_id=None
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
        stid = str(tid)
        # 统一回复出口(P1C):闭包捕获本轮上下文,所有回复带 quoteToken + 记 bot 记忆。
        ctx = dict(quote_token=quote_token, line_user_id=line_user_id, tenant_id=stid)

        def _say(body):
            line_reply.reply_text_context(reply_token, body, **ctx)

        def _pool(kind):
            line_expense_qa.reply_pool(reply_token, kind, text, lang, **ctx)

        from services.expense import line_classify
        from services.expense import line_quick_entry as lqe
        from services.expense import replies
        from services.line_binding import line_chat_memory

        text = line_classify.normalize_user_text(text)  # 全角标点归一(治全角冒号解析失败·#8)
        # 对话记忆(PO-15):先取历史(不含本条)供大脑多轮连贯,再记本条用户消息。
        history = line_chat_memory.recent(line_user_id=line_user_id, tenant_id=stid)
        line_chat_memory.note(line_user_id=line_user_id, tenant_id=stid, role="user", content=text)

        # 0. 闲聊/引导(零成本 L1)→ 问候/感谢/能力说明/开始/上传(治复读)。引用用户当前消息。
        small = replies.detect_smalltalk(text)
        if small:
            _pool(small)
            return True

        from core.workspace_context import default_workspace_id
        from services.purchase import intake as intake_svc

        with db.get_cursor_rls(stid) as cur:
            if not intake_svc.line_expense_gate_open(cur, tenant_id=stid):
                return False
            ws = default_workspace_id(cur, stid)
        if ws is None:
            return False

        # 0. 改错会话态(最高优先·#6):待选字段/待新值/待 是否确认 → 续接多轮(先于引用提醒/记账/大脑)。
        from services.expense import line_correct, line_correct_flow

        if line_correct_flow.try_correction_state(
            bound_user, reply_token, line_user_id, text, stid, ws, lang, quote_token=quote_token
        ):
            return True

        # 引用某记录说「识别错了/不对」(无具体改动)→ 澄清改哪里(不当 OCR 失败让重拍·守卫见 line_correct)。
        if line_correct.maybe_clarify_feedback(reply_token, text, lang, ws, quoted_message_id, ctx):
            return True

        si = lqe.l1_intent(text)
        isq = lqe.is_question(text)
        # 改错分流(P2):「上一笔改成X / 第1张改成Y」是改错 → 跳过 L1 记账,交大脑判 edit 抽字段。
        is_edit = lqe.is_edit_request(text)

        # #7 收入识别:明确「收款/卖出」且无购买动词 → 不误记支出(保守·问句/已有 L1 意图不拦)。
        if lqe.detect_income(text) and not isq and si is None:
            _say(line_client.t_line(lang, "exp_income_guide"))
            return True

        # 1a. 多项一句话(电费50 买菜40 电费10 吃饭50)→ 拆多笔·逐项智能归类·合计入账·卡显逐条
        #     (对标 Paypers)。问句/有其它 L1 意图不走(防误记)。
        multi = lqe.parse_multi(text)
        if multi and not isq and si is None:
            from services.line_binding import line_expense_multi

            return line_expense_multi.do_record_multi(
                bound_user, reply_token, text, stid, ws, multi, quote_token, lang, line_user_id
            )

        # 1. L1 快路:清晰记账(有金额 + 非问句 + 无其他 L1 意图 + 非改错)→ 直接记,零 LLM、零成本。
        parsed = lqe.parse_expense(text)
        if parsed.has_amount() and not isq and si is None and not is_edit:
            from services.expense import conversation

            with db.get_cursor_rls(stid, commit=True) as cur:
                pend = conversation.pop_pending(cur, line_user_id=line_user_id)
            # 续接补金额:仅「缺金额」会话态合并(correct/detail 等其它 pending 不当补金额用)。
            if pend and str(pend.get("missing") or "") == "amount":
                merged = pend["draft"]
                merged.amount = parsed.amount
                parsed = merged
            return _do_record(
                bound_user,
                reply_token,
                text,
                stid,
                ws,
                parsed,
                False,
                quote_token,
                lang,
                line_user_id,
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
            _charge_line_l2(bound_user, stid)
            return _dispatch_agent(
                bound_user,
                reply_token,
                line_user_id,
                text,
                lang,
                stid,
                ws,
                u,
                quote_token,
                quoted_message_id,
            )

        # 3. 兜底(无 LLM):L1 查账/求助/问答(知识库),否则礼貌带回(复用上面已算的 si/isq)。
        #    全部引用用户当前消息(quoteToken),让用户知道在回应哪句。
        if si == "query":
            line_expense_qa.reply_summary(
                reply_token, lang, stid, ws, quote_token=quote_token, line_user_id=line_user_id
            )
        elif si == "support":
            _pool("support")
        elif isq:
            line_expense_qa.reply_question(
                reply_token, lang, stid, text, quote_token=quote_token, line_user_id=line_user_id
            )
        elif is_edit:
            # 改错但无 LLM 抽不出改什么字段 → 教 LINE 内回复语法,不瞎猜也不甩去网页。
            _say(line_client.t_line(lang, "line_need_reply_record"))
        else:
            _pool("unknown")
        return True
    except Exception:
        logger.exception("[line] expense handle failed; fall back")
        return False


def _dispatch_agent(
    bound_user,
    reply_token,
    line_user_id,
    text,
    lang,
    tid,
    ws,
    u,
    quote_token,
    quoted_message_id=None,
) -> bool:
    """大脑决策 → 确定性工具执行。写账闸由 may_write 裁决(问句/否定/假设不写)。"""
    from services.expense import line_agent

    ctx = dict(quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid)

    def _say(body):
        line_reply.reply_text_context(reply_token, body, **ctx)

    intent = u.get("intent")
    if intent == "query_summary":
        line_expense_qa.reply_summary(
            reply_token, lang, tid, ws, quote_token=quote_token, line_user_id=line_user_id
        )
        return True
    if intent == "query_detail":
        line_expense_qa.reply_detail(
            reply_token, lang, tid, ws, line_user_id, quote_token=quote_token
        )
        return True
    if intent == "undo":
        # 撤销:引用某条回执→撤那张;明确「上一笔」→撤最近;对象不明确→提示 reply(不默认撤最近)。
        line_expense_qa.reply_undo(
            bound_user,
            reply_token,
            lang,
            tid,
            ws,
            line_user_id,
            quoted_message_id,
            text,
            quote_token=quote_token,
        )
        return True
    if intent == "edit":
        # 改错:定位目标(引用>第N笔>明确上一笔·不明确则提示 reply)→ 冲销原单 + 忠实克隆草稿 +
        # 应用改动(金额/卖家/日期/科目)→ 请确认(绝不静默覆盖·PO-13)。单/多行规则在 line_correct。
        from services.expense import line_correct

        return line_correct.request_correct(
            bound_user,
            reply_token,
            line_user_id,
            text,
            u,
            quoted_message_id,
            lang,
            tid,
            ws,
            quote_token=quote_token,
        )
    if line_agent.may_write(intent, u.get("speech_act")):
        from services.expense import line_l2

        draft = line_l2.to_draft(u, text)
        if draft.has_amount():
            return _do_record(
                bound_user,
                reply_token,
                text,
                tid,
                ws,
                draft,
                True,
                quote_token,
                lang,
                line_user_id,
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
        _say(line_client.t_line(lang, "exp_need_amount"))
        return True
    # chat / out_of_scope(含数字的问句/否定/假设也落这里):Brain OS — LLM 只给 chat_kind 枚举,
    # 确定性映射到统一 i18n 文案(LLM 绝不直接对用户说话,杜绝旧 demo/同义文案漂移)。
    # 引用某记录说「识别错了」的已在文本入口前置拦截澄清(不到这里)。
    line_expense_qa.reply_pool(reply_token, u.get("chat_kind") or "unknown", text, lang, **ctx)
    return True


def _do_record(
    bound_user, reply_token, text, tid, ws, draft, used_l2, quote_token, lang, line_user_id=""
) -> bool:
    """置信驱动入账(图/文同口径):建草稿 → 高置信 post_doc;回数据卡。计费由调用方管。"""
    from services.expense import confidence
    from services.line_binding import line_booker
    from services.purchase import categories as cat_svc
    from services.purchase import intake as intake_svc
    from services.purchase import settings as settings_svc

    created_by = str(bound_user["id"]) if bound_user.get("id") else None
    from services.expense import line_l2
    from services.expense.line_classify import detect_payment_method

    # 付款方式:仅采纳一句话里真识别到的(转账/现金/刷卡)→ 卡显「付款方式」。未提 → 不猜不显。
    draft.payment_method = draft.payment_method or detect_payment_method(text)
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
    _reply_card(
        reply_token,
        state,
        draft,
        doc_id,
        lang,
        quote_token,
        ws_name,
        token,
        str(ws or ""),
        tenant_id=tid,
        line_user_id=line_user_id,
    )
    return True


def _card_fields_from_draft(draft) -> dict:
    """ExpenseDraft → 数据卡归一字段。

    详情结构化(#10b):单笔也出逐条 `物品 ×数量 ฿金额`(对齐多笔),不再回显整句原文。
    物品名 = 清出的干净名(draft.note);数量>1 缀「×N」;金额=行总额。
    """
    from services.expense.line_quick_entry import qty_label

    item = (draft.note or "").strip()
    items = []
    if item and draft.amount is not None:
        items = [{"name": qty_label(item, draft.qty), "amount": f"{draft.amount:,.2f}"}]
    return {
        "document_type": draft.document_type or "",
        "expense_type": draft.expense_type or "",
        "date": draft.doc_date or "",
        "category": draft.category or "",
        "subcategory": draft.subcategory or "",
        "vendor": draft.vendor_name or "",
        "seller_tax": getattr(draft, "vendor_tax_id", "") or "",
        "invoice_number": draft.invoice_number or "",
        "payment_method": getattr(draft, "payment_method", "") or "",
        "items": items,
        "detail": item,
    }


def _reply_card(
    reply_token,
    state,
    draft,
    doc_id,
    lang,
    quote_token,
    workspace_name="",
    token="",
    ws="",
    tenant_id=None,
    line_user_id="",
) -> None:
    """回执 = 引用原句一行 + Flex 数据卡(三路共用 line_booker.emit_result_card)。"""
    from services.line_binding import line_booker

    line_booker.emit_result_card(
        reply_token,
        state=state,
        amount=draft.amount,
        fields=_card_fields_from_draft(draft),
        doc_id=doc_id,
        lang=lang,
        quote_token=quote_token,
        workspace_name=workspace_name,
        token=token,
        workspace_client_id=ws,
        tenant_id=tenant_id,
        line_user_id=line_user_id,
    )


def _to_purchase_data(d: dict) -> dict:
    """expense_draft → 采购进项建单 data(单笔路 · 单行)。

    数量(#8):「买2杯咖啡共120」→ 行 qty=2、单价=60(split_qty_price·总额不漂);无数量 → qty=1。
    doc-level 组装走共享 line_booker.to_purchase_data(与多项路同口径)。
    """
    from services.expense.line_quick_entry import split_qty_price
    from services.line_binding import line_booker

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
    return line_booker.to_purchase_data(
        lines=[line],
        doc_date=d.get("doc_date"),
        category_id=d.get("category_id"),
        supplier={
            "name": (d.get("vendor_name") or "").strip(),
            "tax_id": (d.get("vendor_tax_id") or "").strip() or None,
        },
        document_type=d.get("document_type"),
        doc_no=(d.get("invoice_number") or "").strip() or None,
        currency=d.get("currency") or "THB",
    )


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
