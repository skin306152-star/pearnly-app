# -*- coding: utf-8 -*-
"""智能分流 intake · AI 判类型 + 建草稿(商户采购 ★ · docs/purchasing/02 §0 · product-vision §三-bis)。

统一入口:图(OCR 结构化结果)/ 文字一句话 → 建草稿落采购列表。待归类已下线:识别完的票一律
建成草稿(ฉบับร่าง),用户在列表里改方向/补金额/删,系统不再单独兜一个待归类桶。
判方向:有 VAT → 进项票(可抵·route=purchase);无 VAT/截图证据 → 费用(route=expense)。销项分类
后期按上传前选业务类型单独做。判定 + 草稿构建 + 费用文本归类全做纯函数(可测),OCR 运行/计费
在路由层复用 services/ocr/entrypoints。隔离=每句 WHERE tenant_id;调用方管事务。
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.purchase import totals as totals_svc
from services.purchase.expense_keywords import EXPENSE_KEYWORDS as _EXPENSE_KEYWORDS

_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _to_decimal(v) -> Decimal:
    try:
        return Decimal(str(v).replace(",", "").strip()) if v not in (None, "") else Decimal("0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def judge_direction(fields: dict) -> tuple[str, str]:
    """判 (kind, route)。fields = OCR 抽取(document_type/vat/...)。

    待归类已下线:识别完的票一律建草稿落采购列表(用户在列表改方向/删),不再判 inbox/销项分流。
    有 VAT → 进项票(可抵进项税·route=purchase);无 VAT → 费用(route=expense)。
    银行转账/电商订单截图(payment_evidence)非正规税票 → 一律费用、不抵 VAT(用户可改)。
    销项分类(我是卖方)后期按上传前选业务类型单独做,届时再引入主体税号比对。
    """
    dtype = (fields.get("document_type") or "").lower()
    if dtype in ("payment_evidence", "order_evidence"):
        return "expense", "expense"
    if _to_decimal(fields.get("vat")) > 0:
        return "purchase_invoice", "purchase"
    return "expense", "expense"


def default_payment_status(doc_type: str, doc_kind: str) -> str:
    """智能默认付款态(PO-5):现金收据 → 已付;税务发票(多为赊账)→ 未付。用户可一键改。

    无明确单据类型:费用单(快记/无 VAT 多为现金小额)默认已付,其余(进货)未付。
    """
    dt = (doc_type or "").strip().lower()
    if dt == "receipt":
        return "paid"
    if dt in ("tax_invoice", "simplified_tax_invoice", "credit_note"):
        return "unpaid"
    return "paid" if doc_kind == "expense" else "unpaid"


def _single_line(fields: dict, base: Decimal, vat_rate: int) -> dict:
    """兜底/收敛单行:行额 = 票面税前小计或总额(卖家名作品名)。"""
    return {
        "item_type": "goods",
        "description": (fields.get("seller_name") or "").strip() or "—",
        "qty": "1",
        "unit_price": str(base),
        "vat_rate": vat_rate,
        "wht_rate": 0,
    }


def build_draft_from_invoice(fields: dict, *, kind: str) -> dict:
    """OCR 抽取 → 进项录入草稿(屏10 预填)。行取自 items,无 items 则按总额单行兜底。

    费用类(kind=expense·含截图证据)不带可抵进项 VAT,即便 OCR 读到 vat 也归 0(进项票才抵)。
    """
    has_vat = kind != "expense" and _to_decimal(fields.get("vat")) > 0
    vat_rate = 7 if has_vat else 0
    lines = []
    for it in fields.get("items") or []:
        qty = _to_decimal(it.get("qty")) or Decimal("1")
        price = _to_decimal(it.get("price"))
        sub = _to_decimal(it.get("subtotal"))
        # OCR 行小计(印刷值)可信;qty/price 在加油/积分票常被误读(22 积分 × 39.85 = 876.70 ≠
        # 印刷小计 1780)。与印刷 subtotal 不符就信 subtotal(行额 = subtotal,qty=1),别让派生的
        # qty×price 盖过印刷值。一致(差 < 0.05)或无 subtotal 才保留 qty/price 明细。
        if sub > 0 and abs(qty * price - sub) > Decimal("0.05"):
            qty, price = Decimal("1"), sub
        lines.append(
            {
                "item_type": "goods",
                "description": (it.get("name") or "").strip(),
                "qty": str(qty),
                "unit_price": str(price),
                "vat_rate": vat_rate,
                "wht_rate": 0,
            }
        )
    base = _to_decimal(fields.get("subtotal")) or _to_decimal(fields.get("total_amount"))
    if not lines:
        # 无明细:用税前小计或总额倒推单行,让用户在屏10 补全。
        lines = [_single_line(fields, base, vat_rate)]
    elif base > 0:
        # 行明细(税前)之和与票面小计/总额矛盾 → OCR 明细读错(多品项乱读/qty 误读·如 7-11 读成
        # 845 ≠ 票面 110)→ 收敛成单行兜底(=票面值),别让错明细之和冒充总额。
        line_sum = sum(_to_decimal(ln["qty"]) * _to_decimal(ln["unit_price"]) for ln in lines)
        if abs(line_sum - base) > Decimal("1"):
            lines = [_single_line(fields, base, vat_rate)]
    return {
        "doc_kind": kind,
        "supplier": {
            "name": (fields.get("seller_name") or "").strip(),
            "tax_id": (fields.get("seller_tax") or "").strip() or None,
            "address": (fields.get("seller_addr") or "").strip() or None,
        },
        "doc_no": (fields.get("invoice_number") or "").strip() or None,
        "doc_date": (fields.get("date") or "").strip() or None,
        "has_vat": has_vat,
        "currency": "THB",
        "payment_status": default_payment_status(fields.get("document_type"), kind),
        "lines": lines,
    }


def classify_expense_text(text: str, categories: list) -> dict:
    """费用一句话 → {description, amount, category_id, subcategory_id}。关键词归类,未命中留空。"""
    raw = (text or "").strip()
    amount = Decimal("0")
    m = list(_NUM_RE.finditer(raw))
    if m:
        amount = _to_decimal(m[-1].group(0))
        desc = (raw[: m[-1].start()] + raw[m[-1].end() :]).strip(" -·:") or raw
    else:
        desc = raw
    cat_id, sub_id = _match_category(raw, categories)
    return {
        "description": desc,
        "amount": amount,
        "category_id": cat_id,
        "subcategory_id": sub_id,
    }


def expense_line(parsed: dict) -> dict:
    """费用归类结果 → 单条明细行(/intake 文字 与 /expense 共用)。"""
    return {
        "item_type": "goods",
        "description": parsed["description"],
        "qty": "1",
        "unit_price": str(parsed["amount"]),
        "vat_rate": 0,
        "wht_rate": 0,
        "category_id": parsed["category_id"],
        "subcategory_id": parsed["subcategory_id"],
    }


def _match_category(text: str, categories: list) -> tuple[Optional[str], Optional[str]]:
    """文本命中子科目关键词 → (大类id, 子类id);命中大类名 → (大类id, None);否则 (None,None)。"""
    low = text.lower()
    for parent in categories or []:
        for child in parent.get("children") or []:
            kws = _EXPENSE_KEYWORDS.get(child["name"], (child["name"],))
            if any(k.lower() in low for k in kws):
                return parent["id"], child["id"]
        if parent["name"].lower() in low:
            return parent["id"], None
    return None, None


def workspace_name(cur, *, tenant_id, workspace_client_id) -> str:
    """套账(主体)名 —— 数据卡「套账」行显示用。取不到 → 空串(卡不显该行)。"""
    cur.execute(
        "SELECT name FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tenant_id),
    )
    row = cur.fetchone()
    return (row["name"] or "") if row else ""


def resolve_image_intake(
    cur,
    *,
    tenant_id,
    workspace_client_id,
    fields,
    confidence,
    settings,
    source="photo",
    image_url=None,
    field_confidence=None,
    created_by=None,
) -> dict:
    """图路:判方向 → 建草稿 → dedupe 提示;高置信齐全且 auto_book 开 → 直接过账。返回分流信封 data。

    待归类已下线:识别完一律建草稿(糊图/฿0 也建·用户在列表补全/删),不再落 inbox。
    confidence_band + field_confidence(逐字段)透出给复核屏「需复核高亮」(契约 05 §1.1)。
    """
    kind, route = judge_direction(fields)
    low_conf = str(confidence or "").lower() in ("needs_review", "low", "")
    fc = dict(field_confidence or {})

    draft = build_draft_from_invoice(fields, kind=kind)
    # 来源透传到单据(line/photo),否则 create_doc 默认 manual 显「手录」
    draft["source"] = source
    calc = totals_svc.compute_purchase_totals(draft["lines"])

    dkey = totals_svc.dedupe_key(
        supplier_tax=draft["supplier"]["tax_id"],
        doc_no=draft["doc_no"],
        grand_total=calc["grand_total"],
    )
    dup = False
    if dkey:
        from services.purchase import docs as docs_svc

        dup = (
            docs_svc.find_by_dedupe(
                cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, dedupe_key=dkey
            )
            is not None
        )
    draft.update(
        {
            "subtotal": str(calc["subtotal"]),
            "vat_amount": str(calc["vat_amount"]),
            "wht_amount": str(calc["wht_amount"]),
            "grand_total": str(calc["grand_total"]),
            "net_payable": str(calc["net_payable"]),
            # 票图存盘 ref → 确认入账时挂成 bill 附件(C)。
            "bill_image_ref": image_url,
        }
    )
    # 自动入账(采购设置开关 · 默认开):高置信 + 有卖家 + 金额>0 + 无重复 → 直接建单并过账(复用
    # 表单确认链路 create_doc→post_doc),不用逐张复核。低置信/糊图不自动过账,只回草稿等用户复核。
    if (
        not low_conf
        and bool(settings.get("auto_book"))
        and not dup
        and (draft["supplier"]["name"] or "").strip()
        and calc["grand_total"] > 0
        and created_by
    ):
        from services.purchase import docs as _docs, posting as _posting

        created = _docs.create_doc(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            created_by=created_by,
            data=draft,
            settings=settings,
            status="draft",
        )
        booked_id = created["doc"]["id"]
        _posting.post_doc(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_id=booked_id,
            auto_stock_in=bool(settings.get("auto_stock_in")),
            created_by=created_by,
        )
        return {
            "kind": kind,
            "confidence": confidence,
            "confidence_band": confidence,
            "field_confidence": fc,
            "route": "booked",
            "draft": None,
            "dedupe_hit": False,
            "doc_id": booked_id,
        }
    return {
        "kind": kind,
        "confidence": confidence,
        "confidence_band": confidence,
        "field_confidence": fc,
        "route": route,
        "draft": draft,
        "dedupe_hit": dup,
    }


def fields_from_invoice(inv) -> dict:
    """ThaiInvoice(OCR 结构化结果)→ 判方向/建草稿用的扁平 fields。"""
    return {
        "document_type": getattr(inv, "document_type", ""),
        "is_not_invoice": getattr(inv, "is_not_invoice", False),
        "seller_name": getattr(inv, "seller_name", ""),
        "seller_tax": getattr(inv, "seller_tax", ""),
        "seller_addr": getattr(inv, "seller_addr", ""),
        "buyer_name": getattr(inv, "buyer_name", ""),
        "buyer_tax": getattr(inv, "buyer_tax", ""),
        "invoice_number": getattr(inv, "invoice_number", ""),
        "date": getattr(inv, "date", ""),
        "subtotal": getattr(inv, "subtotal", ""),
        "vat": getattr(inv, "vat", ""),
        "total_amount": getattr(inv, "total_amount", ""),
        "items": [
            {
                "name": getattr(it, "name", ""),
                "qty": getattr(it, "qty", ""),
                "price": getattr(it, "price", ""),
                "subtotal": getattr(it, "subtotal", ""),
            }
            for it in (getattr(inv, "items", None) or [])
        ],
    }


def line_expense_gate_open(cur, *, tenant_id) -> bool:
    """LINE 记账门控(单一来源 · 2026-06-15 Zihao 拍板:统一智能通道·不按业态分)。

    所有账号(含事务所 firm)统一走:开 expense 模块即放行。图(route_line_image)与文字
    (line_expense.handle_expense_text)共用,改门控只动这一处,防两路漂移。"""
    from services.modules import store as modules_store

    return modules_store.is_enabled(cur, tenant_id=tenant_id, module_key="expense")
