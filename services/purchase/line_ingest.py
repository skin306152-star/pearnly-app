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


def _same_money(a: Decimal, b: Decimal, *, total: Decimal = Decimal("0")) -> bool:
    tol = max(Decimal("1"), total * Decimal("0.02"))
    return abs(a - b) <= tol


def _items_sum(fields: dict) -> Decimal:
    items_sum = Decimal("0")
    for it in fields.get("items") or []:
        name = str(it.get("name") or "").strip()
        if name and ik._is_summary_item_name(name):
            continue
        sub = _dec(it.get("subtotal"))
        items_sum += sub if sub > 0 else (_dec(it.get("qty") or 1) * _dec(it.get("price")))
    return items_sum


def _items_reconcile_total(fields: dict) -> bool:
    total = _dec(fields.get("total_amount"))
    if total <= 0:
        return False
    items_sum = _items_sum(fields)
    if items_sum <= 0:
        return False
    if _same_money(items_sum, total, total=total):
        return True
    return _same_money(items_sum + _dec(fields.get("vat")), total, total=total)


def _total_mismatch(fields: dict) -> bool:
    """抽到的逐条明细加总 + VAT 与票面总额对不上(超 1 baht 且 2%)→ 提示明细可能不全/有误。

    无明细 / 无总额 → 不判(不误报)。明细额取 subtotal,缺则 qty×price。这是软提示,不阻断。
    """
    items = fields.get("items") or []
    total = _dec(fields.get("total_amount"))
    if not items or total <= 0:
        return False
    items_sum = _items_sum(fields)
    if items_sum <= 0:
        return False
    return not _items_reconcile_total(fields)


def _vat_breakdown(fields: dict) -> tuple[str, str]:
    """卡片税额拆解 (税前 ก่อนภาษี, VAT) —— 税额用确定性算,不信 OCR 误读的位数(铁律)。

    泰国 VAT 固定 7%。OCR 的 vat 若接近含税值 total×7/107(即 7% 含税票)→ 按 7% 确定性重算 vat 与税前
    (治 #21 把 9.16 读成 10 → 仍出 130.84/9.16)。非 7%/读偏太多 → 退回 total−vat(仍与总额自洽)。
    无 VAT/无总额 → 用票面 subtotal、VAT 留空。
    """
    vat = _dec(fields.get("vat"))
    total = _dec(fields.get("total_amount"))
    if vat > 0 and total > vat:
        seven = total * Decimal("7") / Decimal("107")
        if abs(vat - seven) <= max(Decimal("1"), seven * Decimal("0.12")):
            vat = seven.quantize(Decimal("0.01"))
        return f"{(total - vat):,.2f}", f"{vat:,.2f}"
    return str(fields.get("subtotal") or ""), str(fields.get("vat") or "")


def _clean_item_name(name) -> str:
    """明细名去前导项目符号/破折号(「- TW ไม่หวาน」→「TW ไม่หวาน」),让卡片明细干净。"""
    return str(name or "").strip().lstrip("-–•· ").strip()


def _card_items(fields: dict) -> list:
    """OCR items → 卡片逐条明细 [{name, amount}](按票据全部显示·带价)。

    amount 取行 subtotal,缺则 qty×price。无名称的行跳过。供数据卡 Paypers 式编号带价列表。
    """
    out = []
    for it in fields.get("items") or []:
        name = str(it.get("name") or "").strip()
        if ik._is_summary_item_name(name):
            continue
        amt = _dec(it.get("subtotal"))
        if amt <= 0:
            amt = _dec(it.get("qty") or 1) * _dec(it.get("price"))
        if amt <= 0:
            continue  # 0 元 modifier(ไม่หวาน 0%/แถมฟรี)不进主明细 → 走 _free_modifier_names 进备注
        out.append({"name": _clean_item_name(name), "amount": f"{amt:,.2f}"})
    return out


def _free_modifier_names(fields: dict) -> list:
    """0 元 modifier/赠品名(ไม่หวาน 0%/แถมฟรี):不占主金额明细,作卡片备注保留(信息不丢)。"""
    out = []
    for it in fields.get("items") or []:
        name = str(it.get("name") or "").strip()
        if not name or ik._is_summary_item_name(name):
            continue
        amt = _dec(it.get("subtotal"))
        if amt <= 0:
            amt = _dec(it.get("qty") or 1) * _dec(it.get("price"))
        if amt <= 0:
            out.append(_clean_item_name(name))
    return out


def _category_names(cats: list, cat_id, sub_id) -> tuple[str, str]:
    for p in cats:
        if p["id"] == cat_id:
            sub_name = next((c["name"] for c in (p.get("children") or []) if c["id"] == sub_id), "")
            return p["name"], sub_name
    return "", ""


def _dominant_item_category(cats: list, items: list, *, api_key):
    from services.expense import category_ai

    clean = [
        {"name": str(it.get("name") or "").strip(), "amount": _dec(it.get("amount"))}
        for it in (items or [])
        if str(it.get("name") or "").strip()
    ]
    if not clean:
        return None, None, Decimal("0")
    choices = category_ai.categorize_items(clean, cats, api_key=api_key)
    weights: dict[tuple, Decimal] = {}
    total_weight = Decimal("0")
    for it, pair in zip(clean, choices):
        cat_id, sub_id = pair
        weight = it["amount"] if it["amount"] > 0 else Decimal("1")
        total_weight += weight
        if not cat_id:
            continue
        weights[(cat_id, sub_id)] = weights.get((cat_id, sub_id), Decimal("0")) + weight
    if not weights:
        return None, None, Decimal("0")
    (cat_id, sub_id), weight = max(weights.items(), key=lambda kv: kv[1])
    share = (weight / total_weight) if total_weight > 0 else Decimal("0")
    return cat_id, sub_id, share


def _smart_category(cur, *, tenant_id, workspace_client_id, vendor, descs, items, api_key):
    """图片路分类:逐项规则/批量判断 → 主金额分类 → 整票兜底 → 关键词兜底。"""
    from services.purchase import categories as cat_svc

    cats = cat_svc.get_tree(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    joined = " / ".join(d for d in descs[:5] if d)
    from services.expense import category_ai

    cat_id, sub_id, share = _dominant_item_category(cats, items, api_key=api_key)
    if cat_id:
        cat_name, sub_name = _category_names(cats, cat_id, sub_id)
        conf = Decimal("0.96") if share >= Decimal("0.70") else Decimal("0.82")
        return cat_id, sub_id, cat_name, sub_name, conf

    cat_id, sub_id = category_ai.rule_category(vendor, joined, cats)
    if cat_id:
        cat_name, sub_name = _category_names(cats, cat_id, sub_id)
        return cat_id, sub_id, cat_name, sub_name, Decimal("0.90")

    if not cat_id and api_key:
        cat_id, sub_id = category_ai.suggest_category(vendor, joined, cats, api_key=api_key)
        if cat_id:
            cat_name, sub_name = _category_names(cats, cat_id, sub_id)
            return cat_id, sub_id, cat_name, sub_name, Decimal("0.88")

    if not cat_id:
        cat_id, sub_id = ik._match_category(f"{vendor} {descs[0] if descs else ''}", cats)
    if not cat_id:
        return None, None, "", "", Decimal("0")
    cat_name, sub_name = _category_names(cats, cat_id, sub_id)
    return cat_id, sub_id, cat_name, sub_name, Decimal("0.76")


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
    fields = ik.normalize_ocr_fields(fields)
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
    _pretax, _vat = _vat_breakdown(fields)
    card_fields = {
        "document_type": fields.get("document_type") or "",
        "expense_type": "",  # 见下方按分类/描述推导(不硬编码 goods,避免餐饮/服务误显「商品」)
        "date": fields.get("date") or "",
        "category": "",
        "subcategory": "",
        "vendor": fields.get("seller_name") or "",
        "seller_tax": fields.get("seller_tax") or "",
        "seller_addr": fields.get("seller_addr") or "",
        # 税额拆解确定性算(7% 不信 OCR 误读位数·见 _vat_breakdown):税前 = total−VAT,VAT 按 7% 含税。
        "subtotal": _pretax,
        "vat": _vat,
        "wht": fields.get("wht_amount") or "",
        "rounding": fields.get("rounding") or "",
        "invoice_number": fields.get("invoice_number") or "",
        "payment_method": fields.get("payment_method") or "",
        "payment_status": "",  # 见下方:取自 draft 的付款态(仅明确未付/部分付才在卡上显)
        "items": _card_items(fields),
        "detail": (
            " · ".join(_item_names[:3])
            + (f" 等{len(_item_names)}项" if len(_item_names) > 3 else "")
            if _item_names
            else ""
        ),
    }
    fc = res.get("field_confidence") or {}
    draft = res["draft"]
    amount = draft.get("grand_total") or "0"
    # 卡片明细只显 OCR 真行(已滤汇总/标记·去前导符号)。规则:加总 ≤ 票面总额 → 照显(全/不全都行,
    # 不全则「明细可能不全」提示);乱读放大(7-11 单行 845 ≫ 110)或一行没抽到 → 不显假行/卖家名行,
    # 标 items_unread 让卡出「未能逐项识别·去详情页」。账务草稿仍收敛保票面总额,与卡片展示两不冲突。
    raw_items = _card_items(fields)
    items_sum = _items_sum(fields)
    total = _dec(fields.get("total_amount"))
    tol = max(Decimal("1"), total * Decimal("0.02"))
    show_items = bool(raw_items) and total > 0 and 0 < items_sum <= total + tol
    if show_items:
        card_fields["items"] = raw_items
        warn_total = _total_mismatch(fields)
        descs = [it["name"] for it in raw_items]
        card_fields["detail"] = " · ".join(descs[:3]) + (
            f" 等{len(descs)}项" if len(descs) > 3 else ""
        )
        # 0 元 modifier/赠品 → 卡片备注(不占主明细·信息不丢)
        card_fields["modifiers"] = " · ".join(_free_modifier_names(fields)[:8])
    else:
        card_fields["items"] = []
        card_fields["items_unread"] = True
        card_fields["detail"] = ""
        warn_total = False
        descs = []
    # 智能归类(LLM 优先 → 关键词兜底):懂泰文品名,治「分类不对/空」。
    vendor_name = draft["supplier"].get("name") or ""
    cat_id, sub_id, _cat_name, _sub_name, cat_conf = _smart_category(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        vendor=vendor_name,
        descs=descs,
        items=card_fields.get("items") or [],
        api_key=api_key,
    )
    if cat_id:
        draft["category_id"] = cat_id
        card_fields["category"] = _cat_name
        card_fields["subcategory"] = _sub_name
        if cat_conf and cat_conf < Decimal("0.85"):
            fc = dict(fc)
            fc["category"] = float(cat_conf)

    # 付款方式:OCR 票面读到的(QRPayment/เงินสด/บัตร…)归一成规范码 → 卡显「付款方式」。未读到 → 空。
    from services.expense.line_classify import normalize_payment_method

    _pay_raw = str(fields.get("payment_method") or "").strip()
    card_fields["payment_method"] = normalize_payment_method(_pay_raw) or _pay_raw
    # 付款态(仅明确未付/部分付才在卡显·默认 paid 不显)+ 舍入(非 0 才显)→ 取自草稿。
    card_fields["rounding"] = card_fields["rounding"] or (draft.get("rounding") or "")
    card_fields["payment_status"] = draft.get("payment_status") or ""
    # 费用类型:命中服务关键词→服务,否则中性「费用」(OCR 票多为费用·不粗暴显「商品」)。
    from services.expense.line_classify import classify_expense_type

    _et_blob = " ".join([vendor_name or "", _cat_name or "", *descs])
    card_fields["expense_type"] = (
        "service" if classify_expense_type(_et_blob) == "service" else "expense"
    )

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
