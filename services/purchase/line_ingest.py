# -*- coding: utf-8 -*-
"""LINE 图片置信驱动入账(STP+HITL · docs/smart-intake/15 §1)。

从 intake.py 拆出(单一职责 + 控行数)。复用 intake 的判方向/建草稿/查重/落 inbox,叠加置信
分级 → create_doc(post 再 post_doc)。门控由调用方(line_image_ocr)先判 expense 开关。
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

from services.purchase import field_clean
from services.purchase import intake as ik
from services.purchase import totals as totals_svc

logger = logging.getLogger("mr-pilot")


def _dec(v) -> Decimal:
    try:
        return Decimal(str(v).replace(",", "").strip() or "0")
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _same_money(a: Decimal, b: Decimal) -> bool:
    """两金额视作同额的容差 = 固定 2 铢(覆盖凑整 ปัดเศษ + VAT 小数差)。

    不用百分比:百分比在大票上会把几十铢的漏行也当「对得上」(2722×2%≈54 铢);固定小容差能在任意
    票面金额下抓出漏读的小额行(如 Little Betong 漏 6 铢那行)→ 该警告就警告,不静默放过。
    """
    return abs(a - b) <= Decimal("2")


def _item_amount(it: dict) -> Decimal:
    """单行金额:印刷 subtotal 优先,缺则 qty×price(三处明细取值共用一处口径)。"""
    sub = _dec(it.get("subtotal"))
    return sub if sub > 0 else _dec(it.get("qty") or 1) * _dec(it.get("price"))


def _items_sum(fields: dict) -> Decimal:
    items_sum = Decimal("0")
    for it in fields.get("items") or []:
        name = str(it.get("name") or "").strip()
        if name and ik._is_summary_item_name(name):
            continue
        items_sum += _item_amount(it)
    return items_sum


def _items_reconcile_total(fields: dict) -> bool:
    total = _dec(fields.get("total_amount"))
    if total <= 0:
        return False
    items_sum = _items_sum(fields)
    if items_sum <= 0:
        return False
    vat = _dec(fields.get("vat"))
    discount = _dec(fields.get("discount"))
    # 行额合计可与票面 total 对上的几种自洽口径:原值 / 加 VAT(餐饮行印税前)/ 减折扣 / 两者兼有。
    candidates = [items_sum, items_sum + vat]
    if discount > 0:
        candidates += [items_sum - discount, items_sum + vat - discount]
    return any(_same_money(c, total) for c in candidates)


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


def _items_display_decision(fields: dict) -> tuple[list, bool, bool]:
    """卡片明细展示与告警决策(纯函数·可单测)→ (raw_items, show_items, warn_total)。

    show_items:明细可信可展示(OCR 行加总 0 < sum ≤ 票面总额 + 2% 容差)。
    warn_total:① 可展示但加总与总额对不上,② 或 OCR 抽到了行却乱读/放大无法展示 —— 两种都说明明细
    不可信,卡片降级「请核对」、主按钮引导核对(诚实优先)。真没有逐项明细的小票不告警。
    """
    raw_items = _card_items(fields)
    items_sum = _items_sum(fields)
    total = _dec(fields.get("total_amount"))
    discount = _dec(fields.get("discount"))
    # 行额合计上限放宽到「票面总额 + 折扣」:折扣前行额本就高于净应付(7-11 实票 115 行 → 110 净)。
    tol = max(Decimal("1"), total * Decimal("0.02"))
    show_items = bool(raw_items) and total > 0 and 0 < items_sum <= total + discount + tol
    warn_total = _total_mismatch(fields) if show_items else bool(ik._effective_items(fields))
    return raw_items, show_items, warn_total


def _card_amounts(fields: dict) -> tuple[str, str, str]:
    """卡片税额拆解 (税前 ก่อนภาษี, VAT, 舍入 ปัดเศษ)。

    票面同时印了 subtotal + VAT 且与 total 自洽(差 ≤ 1.5 铢凑整)→ 直接采信票面值(舍入 =
    total − subtotal − VAT,通常 ±凑整;治 Seafood 把 2544/178.08/-0.08 反推成 2543.93/178.07)。
    否则按泰国 VAT 7% 确定性重算(治 #21 把 9.16 读成 10 → 仍出 130.84/9.16),不信 OCR 误读位数。
    无 VAT/无总额 → 退回票面 subtotal、VAT 与舍入留空。
    """
    subtotal = _dec(fields.get("subtotal"))
    vat = _dec(fields.get("vat"))
    total = _dec(fields.get("total_amount"))
    subtotal_printed = "subtotal_inferred_from_total_vat" not in (fields.get("_corrections") or [])
    if (
        subtotal_printed
        and subtotal > 0
        and vat > 0
        and total > 0
        and totals_svc.vat_face_consistent(subtotal, vat, total)
    ):
        rnd = total - subtotal - vat
        rnd_str = f"{rnd:,.2f}" if abs(rnd) >= Decimal("0.005") else ""
        return f"{subtotal:,.2f}", f"{vat:,.2f}", rnd_str
    if vat > 0 and total > vat:
        seven = totals_svc.vat_from_inclusive(total)
        if abs(vat - seven) <= max(Decimal("1"), seven * Decimal("0.12")):
            vat = seven.quantize(Decimal("0.01"))
        return f"{(total - vat):,.2f}", f"{vat:,.2f}", ""
    return str(fields.get("subtotal") or ""), str(fields.get("vat") or ""), ""


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
        amt = _item_amount(it)
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
        if _item_amount(it) <= 0:
            out.append(_clean_item_name(name))
    return out


def _category_names(cats: list, cat_id, sub_id) -> tuple[str, str]:
    for p in cats:
        if p["id"] == cat_id:
            sub_name = next((c["name"] for c in (p.get("children") or []) if c["id"] == sub_id), "")
            return p["name"], sub_name
    return "", ""


# 分类 LLM 主路径短超时(P1G-Perf · Zihao 2026-06-18):分类是「在选项里挑编号」的小任务,
# 不该把入账卡拖在 Gemini 上 7–14s(甚至 504)。规则先行,落空才调一次 LLM,且 3s 硬上限;
# 超时即回落规则/中性分类(卡照常出·标「请核对」),绝不阻塞卡片。
_CAT_LLM_TIMEOUT = 3


def _dominant_item_category(cats: list, items: list, *, api_key):
    from services.expense import category_ai

    clean = [
        {"name": str(it.get("name") or "").strip(), "amount": _dec(it.get("amount"))}
        for it in (items or [])
        if str(it.get("name") or "").strip()
    ]
    if not clean:
        return None, None, Decimal("0")
    choices = category_ai.categorize_items(clean, cats, api_key=api_key, timeout=_CAT_LLM_TIMEOUT)
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
    """图片路分类:逐项规则/批量判断 → 主金额分类 → 整票兜底 → 关键词兜底。

    返回 (cat_id, sub_id, cat_name, sub_name, conf, source)。source ∈ item|rule|ai|fallback|none
    (喂主路径日志 category_source)。LLM 步骤走 3s 硬上限,超时回落规则/中性,不阻塞卡片。
    """
    from services.purchase import categories as cat_svc

    cats = cat_svc.get_tree(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    joined = " / ".join(d for d in descs[:5] if d)
    from services.expense import category_ai

    cat_id, sub_id, share = _dominant_item_category(cats, items, api_key=api_key)
    if cat_id:
        cat_name, sub_name = _category_names(cats, cat_id, sub_id)
        conf = Decimal("0.96") if share >= Decimal("0.70") else Decimal("0.82")
        return cat_id, sub_id, cat_name, sub_name, conf, "item"

    cat_id, sub_id = category_ai.rule_category(vendor, joined, cats)
    if cat_id:
        cat_name, sub_name = _category_names(cats, cat_id, sub_id)
        return cat_id, sub_id, cat_name, sub_name, Decimal("0.90"), "rule"

    if not cat_id and api_key:
        cat_id, sub_id = category_ai.suggest_category(
            vendor, joined, cats, api_key=api_key, timeout=_CAT_LLM_TIMEOUT
        )
        if cat_id:
            cat_name, sub_name = _category_names(cats, cat_id, sub_id)
            return cat_id, sub_id, cat_name, sub_name, Decimal("0.88"), "ai"

    if not cat_id:
        cat_id, sub_id = ik._match_category(f"{vendor} {descs[0] if descs else ''}", cats)
    if not cat_id:
        return None, None, "", "", Decimal("0"), "none"
    cat_name, sub_name = _category_names(cats, cat_id, sub_id)
    return cat_id, sub_id, cat_name, sub_name, Decimal("0.76"), "fallback"


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
    image_sha256=None,
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
    # items / detail 由下方明细策略统一决定(此处先占位,避免双算 _card_items)。
    # 税额拆解(税前/VAT/舍入):票面齐全自洽用票面,否则 7% 确定性重算(见 _card_amounts)。
    _pretax, _vat, _rounding = _card_amounts(fields)
    card_fields = {
        "document_type": fields.get("document_type") or "",
        "expense_type": "",  # 见下方按分类/描述推导(不硬编码 goods,避免餐饮/服务误显「商品」)
        "date": fields.get("date") or "",
        "category": "",
        "subcategory": "",
        # 展示清洗(P1F):卖家/税号/票号异常值(纯金额/标签/短数字/日期片段)不上卡(与详情页同一套
        # field_clean 规则)。账务草稿与 OCR raw 不受影响,仅卡片展示。
        "vendor": field_clean.clean_seller(fields.get("seller_name")),
        "seller_tax": field_clean.clean_tax_id(fields.get("seller_tax")),
        "seller_addr": fields.get("seller_addr") or "",
        "subtotal": _pretax,
        "vat": _vat,
        "wht": fields.get("wht_amount") or "",
        # 舍入只来自票面(total−税前−VAT),不回退 draft 的账务调整额(费用单不可抵 VAT 会被折进 draft
        # rounding=整额 VAT → 误显成「ปัดเศษ 178」· Seafood 实票踩过)。
        "rounding": _rounding,
        "discount": fields.get("discount") or "",
        "invoice_number": field_clean.clean_invoice_no(fields.get("invoice_number")),
        "payment_method": fields.get("payment_method") or "",
        # 付款态不上卡:OCR 无真实付款信号,draft 的 payment_status 只是按单据类型推断的默认值(税票默认
        # 未付)。把推断当事实显「未付」会在已付的 QR/现金小票上误报(与文字路一致·只显真识别的付款方式)。
        # 账务草稿仍保留 default_payment_status 供 AP 记账,与卡片展示分离。
        "payment_status": "",
        "items": [],  # 下方明细策略统一赋值(show_items/items_unread)
        "detail": "",
    }
    fc = res.get("field_confidence") or {}
    draft = res["draft"]
    amount = draft.get("grand_total") or "0"
    # 卡片明细只显 OCR 真行(已滤汇总/标记·去前导符号)。规则:加总 ≤ 票面总额 → 照显(全/不全都行,
    # 不全则「明细可能不全」提示);乱读放大(7-11 单行 845 ≫ 110)或一行没抽到 → 不显假行/卖家名行,
    # 标 items_unread 让卡出「未能逐项识别·去详情页」。账务草稿仍收敛保票面总额,与卡片展示两不冲突。
    raw_items, show_items, warn_total = _items_display_decision(fields)
    if show_items:
        card_fields["items"] = raw_items
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
        descs = []
    # 智能归类(LLM 优先 → 关键词兜底):懂泰文品名,治「分类不对/空」。
    vendor_name = draft["supplier"].get("name") or ""
    cat_id, sub_id, _cat_name, _sub_name, cat_conf, cat_source = _smart_category(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        vendor=vendor_name,
        descs=descs,
        items=card_fields.get("items") or [],
        api_key=api_key,
    )
    logger.info("[line_ingest] category_source=%s", cat_source)
    if cat_id:
        draft["category_id"] = cat_id
        card_fields["category"] = _cat_name
        card_fields["subcategory"] = _sub_name
        if cat_conf and cat_conf < Decimal("0.85"):
            fc = dict(fc)
            fc["category"] = float(cat_conf)

    # 付款方式:OCR 票面读到的(QRPayment/เงินสด/บัตร…)归一成规范码 → 卡显「付款方式」。未读到 → 空。
    from services.expense.line_classify import payment_from_ocr

    card_fields["payment_method"] = payment_from_ocr(fields.get("payment_method"))
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
    # 明细与总额对不上(乱读/不全)→ 不自动入正式账,降为草稿请用户先核对(诚实优先·仍可保存)。
    if warn_total and verdict.action == "post":
        verdict = conf.Verdict("confirm", verdict.dup, verdict.reasons + ("items_total_mismatch",))
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
    # 图片指纹挂到单据(P1G-Perf):同张图再次发来时,line_image_fastpath 据此早期短路,
    # 不再重跑 Vision/Gemini,直接重发该单当前状态卡。dup 命中已有单也照挂(便于下次短路)。
    if doc_id and image_sha256:
        from services.purchase import image_dedup

        image_dedup.set_sha(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=doc_id,
            image_sha256=image_sha256,
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
