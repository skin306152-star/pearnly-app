# -*- coding: utf-8 -*-
"""LINE 图片置信驱动入账(STP+HITL · docs/smart-intake/15 §1)。

从 intake.py 拆出(单一职责 + 控行数)。复用 intake 的判方向/建草稿/查重/落 inbox,叠加置信
分级 → create_doc(post 再 post_doc)。门控由调用方(line_image_ocr)先判 expense 开关。
"""

from __future__ import annotations

from services.purchase import intake as ik


def ingest_line_image(
    cur,
    *,
    tenant_id,
    workspace_client_id,
    fields,
    confidence,
    created_by,
    field_confidence=None,
    image_ref=None,
    api_key=None,
) -> dict:
    """LINE 图片 OCR → 置信驱动入账。

    resolve_image_intake(判方向/建草稿/查重/低置信落 inbox)→ grade 决定:
      post 高置信齐全 → create_doc + post_doc(正式入账)
      confirm/dup     → create_doc 草稿(等卡片确认)
      inbox           → 已由 resolve_image_intake 落待归类(sales/recon 兜底再 stash)
    返回 {state, doc_id, amount, card_fields, field_confidence},调用方据此发数据卡。
    """
    from services.expense import confidence as conf
    from services.line_binding import line_action_nonce as nonce
    from services.purchase import categories as cat_svc
    from services.purchase import confidence_post
    from services.purchase import settings as settings_svc

    settings = settings_svc.get_settings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    ws_name = ik.workspace_name(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    res = ik.resolve_image_intake(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        fields=fields,
        confidence=confidence,
        settings=settings,
        source="line",
        image_url=image_ref,
        field_confidence=field_confidence,
    )
    # 明细从 OCR 逐条抽取填(需补全卡也显·不只 draft 卡):顶 3 + 「等N项」。draft 卡下方再以真行覆盖。
    _item_names = [
        str(it.get("name") or "").strip()
        for it in (fields.get("items") or [])
        if (it.get("name") or "").strip()
    ]
    card_fields = {
        "document_type": fields.get("document_type") or "",
        "expense_type": "goods",
        "date": fields.get("date") or "",
        "category": "",
        "subcategory": "",
        "vendor": fields.get("seller_name") or "",
        "seller_tax": fields.get("seller_tax") or "",
        "seller_addr": fields.get("seller_addr") or "",
        "subtotal": fields.get("subtotal") or "",
        "vat": fields.get("vat") or "",
        "wht": fields.get("wht_amount") or "",
        "invoice_number": fields.get("invoice_number") or "",
        "detail": (
            " · ".join(_item_names[:3])
            + (f" 等{len(_item_names)}项" if len(_item_names) > 3 else "")
            if _item_names
            else ""
        ),
    }
    fc = res.get("field_confidence") or {}
    draft = res.get("draft")

    # 低置信/糊图(resolve 已落 inbox)或 sales/recon(LINE 不建单)→ 待归类安全网(不丢)。
    if draft is None:
        item_id = res.get("inbox_item_id")
        if res["route"] not in ("inbox",):
            item_id = ik._stash_inbox(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                source="line",
                raw=fields,
                image_url=image_ref,
                ai_guess={"route": res["route"], "confidence": confidence},
            )
        # 待归类展示金额(供卡片 + 决定是否给「仍要入账」):有可用总额才让一键入账,糊图 ฿0 只给编辑/丢弃。
        disp_amount = (fields.get("total_amount") or "").strip() or None
        return {
            "state": "inbox",
            "doc_id": "",
            "ref": item_id or "",
            "can_post": bool(disp_amount),
            "amount": disp_amount,
            "card_fields": card_fields,
            "field_confidence": fc,
            "workspace_name": ws_name,
            "token": nonce.mint(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                action_ref=item_id or "",
                user_id=created_by,
            ),
        }

    amount = draft.get("grand_total") or "0"
    # 逐条明细填进卡(对标竞品「รายการค่าใช้จ่าย」):取真实商品行(跳过卖家兜底单行),顶 3 条 + 「等N项」。
    descs = [
        (ln.get("description") or "").strip()
        for ln in (draft.get("lines") or [])
        if (ln.get("description") or "").strip() not in ("", "—")
    ]
    if descs:
        card_fields["detail"] = " · ".join(descs[:3]) + (
            f" 等{len(descs)}项" if len(descs) > 3 else ""
        )
    # 自动归类:先关键词命中(零成本),落空再 LLM 在真实科目里兜底(PO-9 · 仅图片路,省成本)。
    cats = cat_svc.get_tree(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    vendor_name = draft["supplier"].get("name") or ""
    first_desc = draft["lines"][0]["description"] if draft.get("lines") else ""
    cat_id, sub_id = ik._match_category(f"{vendor_name} {first_desc}", cats)
    if not cat_id and api_key:
        from services.expense import category_ai

        cat_id, sub_id = category_ai.suggest_category(
            vendor_name, " / ".join(descs[:5]), cats, api_key=api_key
        )
    if cat_id:
        draft["category_id"] = cat_id
        for p in cats:
            if p["id"] == cat_id:
                card_fields["category"] = p["name"]
                for c in p.get("children") or []:
                    if c["id"] == sub_id:
                        card_fields["subcategory"] = c["name"]

    verdict = conf.grade(
        amount=amount,
        vendor_name=draft["supplier"].get("name") or "",
        invoice_number=draft.get("doc_no") or "",
        document_type=fields.get("document_type") or "",
        direction=res["route"],
        confidence_band=confidence,
        has_category=bool(cat_id),
        is_duplicate=bool(res.get("dedupe_hit")),
        require_category=False,
    )
    # 文/图共用置信入账编排(PO-11):auto_book 开(默认)则高置信齐全直接过账,关则确认优先。
    doc_id, state = confidence_post.book_by_confidence(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        data=draft,
        settings=settings,
        verdict=verdict,
        created_by=created_by,
    )
    return {
        "state": state,
        "doc_id": doc_id,
        "ref": doc_id,
        "can_post": True,
        "amount": amount,
        "card_fields": card_fields,
        "field_confidence": fc,
        "workspace_name": ws_name,
        "token": nonce.mint(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            action_ref=doc_id,
            user_id=created_by,
        ),
    }
