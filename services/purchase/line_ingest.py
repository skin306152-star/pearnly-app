# -*- coding: utf-8 -*-
"""LINE 图片置信驱动入账(STP+HITL · docs/smart-intake/15 §1)。

从 intake.py 拆出(单一职责 + 控行数)。复用 intake 的判方向/建草稿/查重/落 inbox,叠加置信
分级 → create_doc(post 再 post_doc)。门控由调用方(line_image_ocr)先判 expense 开关。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from services.purchase import intake as ik


def _dec(v) -> Decimal:
    try:
        return Decimal(str(v).replace(",", "").strip() or "0")
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _total_mismatch(fields: dict) -> bool:
    """抽到的逐条明细加总 + VAT 与票面总额对不上(超 1 baht 且 2%)→ 提示明细可能不全/有误。

    无明细 / 无总额 → 不判(不误报)。明细额取 subtotal,缺则 qty×price。这是软提示,不阻断。
    """
    items = fields.get("items") or []
    total = _dec(fields.get("total_amount"))
    if not items or total <= 0:
        return False
    items_sum = Decimal("0")
    for it in items:
        sub = _dec(it.get("subtotal"))
        items_sum += sub if sub > 0 else (_dec(it.get("qty") or 1) * _dec(it.get("price")))
    if items_sum <= 0:
        return False
    recon = items_sum + _dec(fields.get("vat"))
    tol = max(Decimal("1"), total * Decimal("0.02"))
    return abs(recon - total) > tol


def _card_items(fields: dict) -> list:
    """OCR items → 卡片逐条明细 [{name, amount}](按票据全部显示·带价)。

    amount 取行 subtotal,缺则 qty×price。无名称的行跳过。供数据卡 Paypers 式编号带价列表。
    """
    out = []
    for it in fields.get("items") or []:
        name = str(it.get("name") or "").strip()
        if not name:
            continue
        amt = _dec(it.get("subtotal"))
        if amt <= 0:
            amt = _dec(it.get("qty") or 1) * _dec(it.get("price"))
        out.append({"name": name, "amount": (f"{amt:,.2f}" if amt > 0 else "")})
    return out


def _smart_category(cur, *, tenant_id, workspace_client_id, vendor, descs, api_key):
    """智能归类(图片路 · LLM 优先 → 关键词兜底)。返回 (cat_id, sub_id, cat_name, sub_name)。

    很多泰文品名/供应商关键词命不中或误命中(分类不对/空)→ 有 key 时先让 LLM 在真实科目树里挑
    (懂「ไฮดีเซล=柴油→交通」),挑不出/无 key 再退关键词。全空 → (None, None, '', '')。
    """
    from services.purchase import categories as cat_svc

    cats = cat_svc.get_tree(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    joined = " / ".join(d for d in descs[:5] if d)
    from services.expense import category_ai

    # 1) 无歧义高频商户硬规则(瞬时·永远一致):加油站→燃油 / Grab→交通 / 水电→水电 / 电信→通讯。
    cat_id, sub_id = category_ai.rule_category(vendor, joined, cats)
    # 2) 没命中规则 → LLM(2.5-flash·temp=0·看品名+业态判,治便利店/餐厅这类有歧义的)。
    if not cat_id and api_key:
        cat_id, sub_id = category_ai.suggest_category(vendor, joined, cats, api_key=api_key)
    # 3) 还没有 → 关键词兜底。
    if not cat_id:
        cat_id, sub_id = ik._match_category(f"{vendor} {descs[0] if descs else ''}", cats)
    if not cat_id:
        return None, None, "", ""
    for p in cats:
        if p["id"] == cat_id:
            sub_name = next((c["name"] for c in (p.get("children") or []) if c["id"] == sub_id), "")
            return cat_id, sub_id, p["name"], sub_name
    return cat_id, sub_id, "", ""


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
    """LINE 图片 OCR → 置信驱动入账(待归类已下线:一律建草稿落列表)。

    resolve_image_intake(判方向/建草稿/查重)→ grade 决定:
      post 高置信齐全 → create_doc + post_doc(正式入账)
      confirm/dup     → create_doc 草稿(落列表·卡片可一键确认)
    返回 {state, doc_id, amount, card_fields, field_confidence},调用方据此发数据卡。
    """
    from services.expense import confidence as conf
    from services.line_binding import line_booker
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
        "items": _card_items(fields),
        "detail": (
            " · ".join(_item_names[:3])
            + (f" 等{len(_item_names)}项" if len(_item_names) > 3 else "")
            if _item_names
            else ""
        ),
    }
    fc = res.get("field_confidence") or {}
    warn_total = _total_mismatch(fields)
    draft = res["draft"]
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
    # 智能归类(LLM 优先 → 关键词兜底):懂泰文品名,治「分类不对/空」。
    vendor_name = draft["supplier"].get("name") or ""
    cat_id, sub_id, _cat_name, _sub_name = _smart_category(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        vendor=vendor_name,
        descs=descs,
        api_key=api_key,
    )
    if cat_id:
        draft["category_id"] = cat_id
        card_fields["category"] = _cat_name
        card_fields["subcategory"] = _sub_name

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
    # 文/图/多项共用入账编排(#10 line_booker):建草稿→按置信过账→铸 nonce token。
    doc_id, state, token = line_booker.book_and_mint(
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
        "amount": amount,
        "card_fields": card_fields,
        "field_confidence": fc,
        "workspace_name": ws_name,
        "warn_total": warn_total,
        "token": token,
    }
