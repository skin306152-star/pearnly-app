# -*- coding: utf-8 -*-
"""LINE 入账编排共享口(/simplify #10)。

文本单笔(line_expense._do_record)、文本多项(line_expense_multi)、图片(line_ingest)三路
此前各写一份「book_by_confidence → nonce.mint」和一份 ack-key 表。收成一处:行为不变,
只去重复(改后复验归类/总额不变)。
"""

from __future__ import annotations

# 回执文案 key:状态 → line_i18n 键(原散在 3 处,完全相同)。
_ACK_KEYS = {"posted": "exp_ack_posted", "dup": "exp_ack_dup"}

_WEB_PURCHASE_URL = "https://pearnly.com/home"


def ack_key(state: str) -> str:
    """入账状态 → 引用回执的 i18n 文案 key(posted/dup/其余=confirm)。"""
    return _ACK_KEYS.get(state, "exp_ack_confirm")


def _amount_le_zero(amount) -> bool:
    """金额 ≤ 0 或读不出(None/「—」/非数)→ True(不能当成功草稿)。"""
    from decimal import Decimal, InvalidOperation

    try:
        return Decimal(str(amount or "0").replace(",", "").strip() or "0") <= 0
    except (InvalidOperation, ValueError, TypeError):
        return True


def ack_message(lang: str, state: str, amount, fields: dict = None) -> str:
    """引用回执文案:草稿态遇金额读不出/不可靠 → 警示口径(不显 ✅·不说「已保存草稿」),
    否则照常(高置信 confirm 绿勾 / posted 已入账 / dup 可能重复)。

    total≤0 → 「ยังอ่านยอดเงินไม่ได้ · 请核对」(不带金额);amount_unreliable 但 >0 → 「⚠️ {金额} · 请核对」。
    文案放 line_card_i18n(line_i18n 已满 500)·与卡片 review 态同源同口径。
    """
    from services.line_binding import line_client

    le_zero = _amount_le_zero(amount)
    if state == "confirm" and ((fields or {}).get("amount_unreliable") or le_zero):
        from services.line_binding.line_card_i18n import chrome

        t = chrome(lang)
        return t["ack_amount_unread"] if le_zero else t["ack_review"].format(amount=amount)
    return line_client.t_line(lang, ack_key(state), amount=amount)


def _find_dup_doc(cur, tenant_id, workspace_client_id, data):
    """撞 dup_invoice 后取已有单(与 create_doc 同口径算 dedupe_key)。LINE 路无 amount_override,
    故 grand_total 直接 compute_purchase_totals(lines) 即等于 create_doc 的 _effective_calc。"""
    from services.purchase import docs as docs_svc
    from services.purchase import totals as totals_svc

    calc = totals_svc.compute_purchase_totals(data.get("lines") or [])
    supplier = data.get("supplier")
    supplier_tax = supplier.get("tax_id") if isinstance(supplier, dict) else None
    dkey = totals_svc.dedupe_key(
        supplier_tax=supplier_tax, doc_no=data.get("doc_no"), grand_total=calc["grand_total"]
    )
    if not dkey:
        return None
    return docs_svc.find_by_dedupe(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, dedupe_key=dkey
    )


def book_and_mint(
    cur, *, tenant_id, workspace_client_id, data, settings, verdict, created_by
) -> tuple[str, str, str]:
    """建草稿 → 按置信过账(book_by_confidence)→ 为卡片动作铸 nonce token。

    返回 (doc_id, state, token)。三路共用同一编排(消除各写一份)。行为与原逐路实现等价。
    重复票:create_doc 撞 dedupe_block 抛 dup_invoice → 不重复入账,指向已有单 → state='dup'
    出「可能重复」卡(治原图片路回落纯文字/静默丢 · spec §1 dup 卡此前不可达)。
    """
    from core.pos_api import PosError
    from services.line_binding import line_action_nonce as nonce
    from services.purchase import confidence_post

    try:
        doc_id, state = confidence_post.book_by_confidence(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            data=data,
            settings=settings,
            verdict=verdict,
            created_by=created_by,
        )
    except PosError as e:
        if (e.code or "") != "purchase.dup_invoice":
            raise
        existing = _find_dup_doc(cur, tenant_id, workspace_client_id, data)
        doc_id, state = (str(existing["id"]) if existing else ""), "dup"
    token = (
        nonce.mint(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            action_ref=doc_id,
            user_id=created_by,
        )
        if doc_id
        else ""
    )
    return doc_id, state, token


def to_purchase_data(
    *, lines, doc_date, supplier, category_id=None, document_type="", doc_no=None, currency="THB"
) -> dict:
    """费用建单 data 组装(单笔/多项路共用)。付款态走 intake.default_payment_status:无单据类型的
    费用单 → 已付(消除多项路硬编码 'paid' 漂移,二者本就等值)。doc_kind=expense·source=line。"""
    from services.purchase import intake as _intake

    return {
        "doc_kind": "expense",
        "source": "line",
        "doc_date": doc_date,
        "category_id": category_id,
        "supplier": supplier,
        "doc_no": doc_no,
        "currency": currency,
        "payment_status": _intake.default_payment_status(document_type, "expense"),
        "lines": lines,
    }


def emit_result_card(
    reply_token,
    *,
    state,
    amount,
    fields,
    doc_id,
    lang,
    quote_token="",
    workspace_name="",
    token="",
    workspace_client_id="",
    field_confidence=None,
    source="text",
    tenant_id=None,
    line_user_id="",
) -> None:
    """三路共用发卡口:引用回执(text·可被引用)+ Flex 数据卡(不可引用 → 拆两条发)。

    发完把两条消息 id 绑到该 doc(line_message_refs)→ 用户长按任一条 reply「删除/改成X」可
    精确定位这张单(引用底座 P1A)。记映射 best-effort,失败不阻塞回执。
    """
    import logging
    import os

    from services.line_binding import line_client

    try:
        # line_card import 放 try 内:模块未部署/渲染失败都在此兜底,不冒泡成上层兜底误判。
        from services.line_binding import line_card

        ack = {"type": "text", "text": ack_message(lang, state, amount, fields)}
        if quote_token:
            ack["quoteToken"] = quote_token
        card = line_card.result_card(
            state=state,
            amount=amount,
            fields=fields,
            field_confidence=field_confidence or {},
            doc_id=doc_id,
            lang=lang,
            web_url=_WEB_PURCHASE_URL,
            source=source,
            workspace_name=workspace_name,
            token=token,
            liff_id=os.getenv("LINE_LIFF_ID", "").strip(),
            workspace_client_id=workspace_client_id,
        )
        sent = line_client.reply_messages_with_meta(reply_token, [ack, card])
        _bind_refs(tenant_id, workspace_client_id, line_user_id, sent, doc_id, state)
    except Exception as e:  # noqa: BLE001
        # 记录已建好 · 仅卡片发送失败 → 明确告知卡片问题,不让上层当成未处理。
        logging.getLogger(__name__).warning(f"[line] 数据卡发送失败: {e}")
        line_client.reply_messages(
            reply_token,
            [{"type": "text", "text": line_client.t_ocr(lang, "card_render_failed")}],
        )


def _bind_refs(tenant_id, workspace_client_id, line_user_id, sent, doc_id, state) -> None:
    """把已发消息 id 绑到 doc(供 quote-reply 精确定位)。无 tenant/doc/消息 → 跳过。"""
    if not (tenant_id and doc_id and sent):
        return
    from services.line_binding import line_message_refs

    line_message_refs.record_safe(
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        line_user_id=line_user_id,
        message_ids=[m.get("id") for m in sent if m.get("id")],
        ref_id=doc_id,
        state=state,
    )
    # 发卡即重置改错上下文:用户开了新一笔 → 上次编辑/恢复留的续接/提问态已死,清掉(别让残留的
    # correctactive/correctval 截走后续「取消」误当「取消编辑」)。草稿(confirm)/已入账(posted)
    # 再把本单设为「当前可改」目标(active 续接·TTL 15min):无需长按引用直接说「ร้านเป็น 7-11」即改;
    # dup/终态只清不设。best-effort,失败不阻塞回执。
    if not line_user_id:
        return
    import logging

    try:
        from services.expense import line_correct

        if state in ("confirm", "posted"):
            line_correct._set_active(tenant_id, workspace_client_id, doc_id, line_user_id)
        else:
            line_correct._clear(tenant_id, line_user_id)
    except Exception:  # noqa: BLE001
        logging.getLogger(__name__).warning("[line refs] reset active 失败;不阻塞回执")


def push_result_card(
    line_user_id, lang, ingest, quote_token=None, ws_client_id="", tenant_id=None
) -> None:
    """图片路识别结果数据卡 push(异步·无 replyToken):引用照片回执 + Flex 卡。失败回落纯文字。

    发完绑消息 id → doc(同 emit_result_card · 引用底座 P1A)。与 emit_result_card 同处共用发卡口。
    """
    import logging
    import os

    from services.line_binding import line_client

    state = ingest.get("state", "confirm")
    doc_id = ingest.get("ref") or ingest.get("doc_id") or ""
    try:
        # line_card import 放 try 内:即便拆分模块未部署(ImportError)也在此兜底,绝不冒泡成「读取失败」。
        from services.line_binding import line_card

        ack = {
            "type": "text",
            "text": ack_message(
                lang, state, ingest.get("amount") or "—", ingest.get("card_fields") or {}
            ),
        }
        if quote_token:
            ack["quoteToken"] = quote_token
        card = line_card.result_card(
            state=state,
            amount=ingest.get("amount"),
            fields=ingest.get("card_fields") or {},
            field_confidence=ingest.get("field_confidence") or {},
            doc_id=doc_id,
            lang=lang,
            web_url=_WEB_PURCHASE_URL,
            source=ingest.get("source") or "image",
            workspace_name=ingest.get("workspace_name") or "",
            token=ingest.get("token") or "",
            warn_total=bool(ingest.get("warn_total")),
            liff_id=os.getenv("LINE_LIFF_ID", "").strip(),
            workspace_client_id=str(ws_client_id or ""),
        )
        sent = line_client.push_messages_with_meta(line_user_id, [ack, card])
        if not sent and not line_client.push_messages(line_user_id, [ack, card]):
            # 卡被 LINE 拒(如 Flex 校验失败)且非异常 → 明确告知,不让卡片静默消失。
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "card_render_failed"))
            return
        _bind_refs(tenant_id, ws_client_id, line_user_id, sent, doc_id, state)
    except Exception as e:  # noqa: BLE001
        # OCR 已成功 · 仅卡片渲染/发送失败(含模块未部署)→ 明确告知卡片问题,绝不谎报「读取失败」。
        logging.getLogger(__name__).warning(f"[line_ocr] 数据卡 push 失败: {e}")
        line_client.push_text(line_user_id, line_client.t_ocr(lang, "card_render_failed"))
