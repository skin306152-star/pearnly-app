# -*- coding: utf-8 -*-
"""智能分流 intake · AI 判类型 + 方向 + 去向(商户采购 ★ · docs/purchasing/02 §0 · product-vision §三-bis)。

统一入口:图(OCR 结构化结果)/ 文字一句话 → 判「是什么 + 去哪」。
判方向(P0a):比对 OCR 买卖双方税号 vs 本套账主体税号 —— 买方=我 → 进项票(route=purchase);
卖方=我 → 销项(route=sales);非发票/银行单 → recon;低置信/拿不准 → inbox(落 intake_items
待用户一点,绝不静默丢错)。判定 + 草稿构建 + 费用文本归类全做纯函数(可测),OCR 运行/计费
在路由层复用 services/ocr/entrypoints。隔离=每句 WHERE tenant_id;调用方管事务。
"""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.purchase import totals as totals_svc

_TAX_RE = re.compile(r"\d")
_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")

# 费用文本 → 子科目关键词(打车→ค่าแท็กซี่ 等)· 命中即归类,未命中留空待用户选。
_EXPENSE_KEYWORDS = {
    "ค่าแท็กซี่": ("แท็กซี่", "taxi", "grab", "打车", "出租"),
    "ค่าน้ำมัน": ("น้ำมัน", "ปตท", "fuel", "ptt", "油", "加油"),
    "ค่าน้ำ": ("ค่าน้ำ", "ประปา", "water", "水费"),
    "ค่าไฟ": ("ค่าไฟ", "ไฟฟ้า", "electric", "电费"),
    "เครื่องเขียน": ("เครื่องเขียน", "stationery", "文具", "纸"),
    "ค่าทำความสะอาด": ("ทำความสะอาด", "clean", "清洁", "洗"),
    "ค่าเช่า": ("ค่าเช่า", "rent", "租"),
    "ค่าโฆษณา": ("โฆษณา", "ads", "facebook", "广告"),
    "ค่าซ่อมบำรุง": ("ซ่อม", "repair", "维修", "保养"),
}


def _norm_tax(v) -> str:
    """税号归一 = 只留数字(挡空格/连字符差异)。"""
    return "".join(_TAX_RE.findall(str(v or "")))


def _to_decimal(v) -> Decimal:
    try:
        return Decimal(str(v).replace(",", "").strip()) if v not in (None, "") else Decimal("0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def judge_direction(fields: dict, *, my_tax_id) -> tuple[str, str]:
    """判 (kind, route)。fields = OCR 抽取(document_type/seller_tax/buyer_tax/vat/...)。

    买方=本主体 → 进项票;卖方=本主体 → 销项;非发票 → inbox(银行单交由 recon 上层另判)。
    两边都不匹配但确是发票 → 默认进项(商户拍的是收到的票),置信下调由调用方据 confidence 决定。
    """
    if fields.get("is_not_invoice"):
        return "unknown", "inbox"
    dtype = (fields.get("document_type") or "").lower()
    mine = _norm_tax(my_tax_id)
    buyer = _norm_tax(fields.get("buyer_tax"))
    seller = _norm_tax(fields.get("seller_tax"))
    has_vat = _to_decimal(fields.get("vat")) > 0

    if mine and seller == mine and buyer != mine:
        return "sales", "sales"  # 我是卖方 → 销项,不归采购
    if dtype in ("tax_invoice", "receipt") or has_vat:
        # 买方=我,或两边都没匹配上(商户拍收到的票)→ 进项。
        kind = "purchase_invoice" if has_vat else "expense"
        return kind, ("purchase" if has_vat else "expense")
    return "unknown", "inbox"


def build_draft_from_invoice(fields: dict, *, kind: str) -> dict:
    """OCR 抽取 → 进项录入草稿(屏10 预填)。行取自 items,无 items 则按总额单行兜底。"""
    has_vat = _to_decimal(fields.get("vat")) > 0
    vat_rate = 7 if has_vat else 0
    lines = []
    for it in fields.get("items") or []:
        qty = _to_decimal(it.get("qty")) or Decimal("1")
        price = _to_decimal(it.get("price"))
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
    if not lines:
        # 无明细:用税前小计或总额倒推单行,让用户在屏10 补全。
        base = _to_decimal(fields.get("subtotal")) or _to_decimal(fields.get("total_amount"))
        lines = [
            {
                "item_type": "goods",
                "description": (fields.get("seller_name") or "").strip() or "—",
                "qty": "1",
                "unit_price": str(base),
                "vat_rate": vat_rate,
                "wht_rate": 0,
            }
        ]
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


def _my_tax_id(cur, *, tenant_id, workspace_client_id) -> str:
    """本套账主体税号(方向判定基准)。"""
    cur.execute(
        "SELECT tax_id FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tenant_id),
    )
    row = cur.fetchone()
    return (row["tax_id"] or "") if row else ""


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
) -> dict:
    """图路:判方向 → 建草稿 → dedupe 提示;低置信/unknown → 落 inbox。返回分流信封 data。

    confidence_band + field_confidence(逐字段)透出给复核屏「需复核高亮」(契约 05 §1.1)。
    """
    my_tax = _my_tax_id(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    kind, route = judge_direction(fields, my_tax_id=my_tax)
    low_conf = str(confidence or "").lower() in ("needs_review", "low", "")
    fc = dict(field_confidence or {})

    if route in ("sales", "recon"):
        return {
            "kind": kind,
            "confidence": confidence,
            "confidence_band": confidence,
            "field_confidence": fc,
            "route": route,
            "draft": None,
            "dedupe_hit": False,
        }

    draft = None
    calc = None
    if route in ("purchase", "expense"):
        draft = build_draft_from_invoice(fields, kind=kind)
        calc = totals_svc.compute_purchase_totals(draft["lines"])

    # 低置信 / unknown(draft 未建)/ 抽取过空(糊图税号"13"·金额฿0)→ 落待归类,绝不直接进可保存的 ฿0 表单(F5)。
    too_empty = calc is not None and calc["grand_total"] <= 0
    if draft is None or low_conf or too_empty:
        _stash_inbox(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            source=source,
            raw=fields,
            image_url=image_url,
            ai_guess={"kind": kind, "confidence": confidence, "route": route},
        )
        return {
            "kind": kind,
            "confidence": confidence,
            "confidence_band": confidence,
            "field_confidence": fc,
            "route": "inbox",
            "draft": None,
            "dedupe_hit": False,
        }

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
            }
            for it in (getattr(inv, "items", None) or [])
        ],
    }


def line_expense_gate_open(cur, *, tenant_id) -> bool:
    """LINE 记费用门控(单一来源 · 铁律#26 底线集中):商户(非 firm/未选业态)+ 开 expense → True。
    事务所 firm / 未 onboard(business_type=None)/ 未开 expense → False。图(route_line_image)与
    文字(webhook _handle_expense_text)共用,改门控只动这一处,防两路漂移。"""
    from services.modules import store as modules_store

    bt = modules_store.get_business_type(cur, tenant_id=tenant_id)
    if bt in (None, "firm"):
        return False
    return modules_store.is_enabled(cur, tenant_id=tenant_id, module_key="expense")


def route_line_image(*, tenant_id, workspace_client_id, fields, confidence) -> bool:
    """LINE 收图分流(纯加法):商户租户 → 落采购待办 intake_item(等用户在采购 inbox 一点)。

    事务所(firm)/ 未选业态 / 未开 expense → 返回 False 不动,识别中心路径一字不变。自开游标。
    调用方须用 try/except 包裹:本函数任何异常都不得影响既有 LINE 回复。
    """
    if not tenant_id or not workspace_client_id:
        return False
    from core import db

    with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
        if not line_expense_gate_open(cur, tenant_id=str(tenant_id)):
            return False
        kind, route = judge_direction(
            fields,
            my_tax_id=_my_tax_id(
                cur, tenant_id=str(tenant_id), workspace_client_id=workspace_client_id
            ),
        )
        _stash_inbox(
            cur,
            tenant_id=str(tenant_id),
            workspace_client_id=workspace_client_id,
            source="line",
            raw=fields,
            image_url=None,
            ai_guess={"kind": kind, "route": route, "confidence": confidence},
        )
        return True


def list_inbox(cur, *, tenant_id, workspace_client_id) -> list[dict]:
    """待归类收件箱:本套账 status='pending' 的 intake_items(新→旧)。供前端一点归类。"""
    cur.execute(
        "SELECT id, source, raw, image_url, ai_guess, created_at FROM intake_items "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND status = 'pending' "
        "ORDER BY created_at DESC",
        (tenant_id, workspace_client_id),
    )
    return [
        {
            "id": str(r["id"]),
            "source": r["source"],
            "raw": r["raw"] or {},
            "image_url": r["image_url"],
            "ai_guess": r["ai_guess"] or {},
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in cur.fetchall()
    ]


_INBOX_ACTIONS = ("purchase", "expense", "sales", "recon", "dismiss")


def resolve_inbox(
    cur, *, tenant_id, workspace_client_id, item_id, action, created_by, settings
) -> dict:
    """一点归类。purchase/expense → 据 raw 建草稿单(返 doc_id 供前端开录入屏确认);
    sales/recon → 移出收件箱(去对应模块处理);dismiss → 标记非票。绝不静默丢:全留痕。"""
    if action not in _INBOX_ACTIONS:
        from core.pos_api import PosError

        raise PosError("purchase.line_invalid", 422, detail="bad_action")
    cur.execute(
        "SELECT raw FROM intake_items "
        "WHERE id = %s AND tenant_id = %s AND workspace_client_id = %s AND status = 'pending'",
        (item_id, tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if row is None:
        from core.pos_api import PosError

        raise PosError("purchase.forbidden", 404, detail="inbox_item_not_found")

    if action in ("purchase", "expense"):
        from services.purchase import docs as docs_svc

        kind = "purchase_invoice" if action == "purchase" else "expense"
        draft = build_draft_from_invoice(row["raw"] or {}, kind=kind)
        created = docs_svc.create_doc(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            created_by=created_by,
            data=draft,
            settings=settings,
            status="draft",
        )
        doc_id = created["doc"]["id"]
        cur.execute(
            "UPDATE intake_items SET status = 'resolved', resolved_doc_id = %s "
            "WHERE id = %s AND tenant_id = %s AND workspace_client_id = %s",
            (doc_id, item_id, tenant_id, workspace_client_id),
        )
        return {"status": "resolved", "doc_id": str(doc_id), "doc_kind": kind}

    new_status = "dismissed" if action == "dismiss" else "resolved"
    cur.execute(
        "UPDATE intake_items SET status = %s "
        "WHERE id = %s AND tenant_id = %s AND workspace_client_id = %s",
        (new_status, item_id, tenant_id, workspace_client_id),
    )
    return {"status": new_status, "route": action}


def _stash_inbox(cur, *, tenant_id, workspace_client_id, source, raw, image_url, ai_guess) -> None:
    """低置信/拿不准落待归类(绝不静默丢错)。"""
    cur.execute(
        "INSERT INTO intake_items "
        "(tenant_id, workspace_client_id, source, raw, image_url, ai_guess, status) "
        "VALUES (%s, %s, %s, %s::jsonb, %s, %s::jsonb, 'pending')",
        (
            tenant_id,
            workspace_client_id,
            source,
            json.dumps(raw, default=str),
            image_url,
            json.dumps(ai_guess, default=str),
        ),
    )
