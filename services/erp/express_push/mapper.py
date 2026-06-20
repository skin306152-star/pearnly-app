# -*- coding: utf-8 -*-
"""扁平化 history → Express 进项(采购)记账载荷(确定性纯函数 · 不连库 · 不调 LLM)。

Express 一张赊购/现购发票 = 一笔采购日记账(JNLTYP=04)+ 进项税(喂 ภ.พ.30)+
复式分录。金额/税额/借贷一律由确定性引擎算(铁律 · 见
[[line-accounting-honest-status-boundary]]),LLM 只负责更早的识别/抽取。共享纯函数在
`common.py`(进项/销项共用),这里只留采购特有(供应商身份 + 采购分录装配)。

输入对齐 erp_push.flatten_history_for_mrerp 的产物(源是 ocr_history,不是
purchase_docs):顶层 history 字段 + `fields`(主页 OCR 字段)。判脏/数不自洽/缺
关键映射 → 不产载荷,返回 ok=False + reason(调用方据此落 manual)。

载荷契约(写进 enqueue 的 request_body · Agent lease 后照此录入 Express):
  direction     "purchase"(方向第一类公民 · 见 09)
  doctype        RR(赊购/未付 · RECTYP=3)| HP(现购/已付 · RECTYP=1)
  account_set    目标账套(本期只允许 DATAT · 白名单在 enqueue/agent 再校验)
  docdate_be     佛历单据日 = (公历年+543) 末两位 + MMDD,例 581231
  vat_period_be  佛历税期 = 同年月 + "01",例 581201
  ref_no         供应商票号
  supplier       {code,name,tax_id,prename,supplier_new}
  vat_rate       7.00 | 0.00
  base_amount    税前(字符串化 decimal)
  vat_amount     进项税额
  total_amount   含税合计 = base + vat
  lines          复式分录 [{acc,side(D/C),amount,desc}] · 借贷必平
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from services.erp.express_push.common import (
    ExpressMapResult,
    _d,
    _s,
    _q,
    _VAT_RATE,
    amounts,
    be_dates,
    detect_prename,
    fail,
    payment_is_paid,
    resolve_account,
)
from services.purchase.field_clean import clean_invoice_no, clean_seller, clean_tax_id


def _is_paid(fields: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """已付(现购 HP)还是未付(赊购 RR)。明确信号优先,否则按 config 默认(B2B 缺省 RR)。"""
    paid = payment_is_paid(fields)
    if paid is not None:
        return paid
    return str(config.get("default_doctype") or "RR").upper() == "HP"


def _resolve_supplier(
    clients: List[Dict[str, Any]], history: Dict[str, Any], name: str, tax_id: str
) -> Dict[str, Any]:
    """供应商身份块。命中 erp_client_mappings(express)→ 带 code、supplier_new=False;
    否则 supplier_new=True 让 Agent 决定在 APMAS 建档。"""
    code = ""
    client_id = history.get("client_id")
    if client_id is not None:
        for c in clients or []:
            if (
                str(c.get("client_id")) == str(client_id)
                and (c.get("erp_type") or "").lower() == "express"
            ):
                code = (c.get("erp_code") or "").strip()
                break
    return {
        "code": code,
        "name": name,
        "tax_id": tax_id,
        "prename": detect_prename(name),
        "supplier_new": not bool(code),
    }


def build_express_payload(
    history: Dict[str, Any],
    *,
    config: Dict[str, Any],
    mappings: Optional[Dict[str, Any]] = None,
    category: str = "",
) -> ExpressMapResult:
    """扁平化 history → Express 采购载荷。判脏/不自洽 → ok=False(留人工)。

    config 键:account_set(目标账套)· fallback_acc(兜底采购科目)·
    vat_input_acc(进项税科目)· ap_acc(应付科目)· default_doctype(RR/HP)。
    mappings:get_mrerp_mappings_bundle(tenant_id)(accounts/clients)。
    """
    mappings = mappings or {}
    fields = history.get("fields") if isinstance(history.get("fields"), dict) else {}
    fields = fields or {}

    account_set = str(config.get("account_set") or "").strip()
    if not account_set:
        return fail("no_account_set")

    dates = be_dates(history.get("invoice_date") or fields.get("date"))
    if not dates:
        return fail("bad_or_missing_date")
    docdate_be, vat_period_be = dates

    amts = amounts(fields, history)
    if not amts:
        return fail("amounts_not_consistent")
    base, vat, total = amts

    accounts = mappings.get("accounts") or []
    purchase_acc = resolve_account(accounts, category, config.get("fallback_acc"))
    if not purchase_acc:
        return fail("no_purchase_account")
    ap_acc = resolve_account(accounts, "accounts_payable", config.get("ap_acc"))
    if not ap_acc:
        return fail("no_ap_account")

    has_vat = vat > 0
    if has_vat:
        vat_acc = resolve_account(accounts, "input_vat", config.get("vat_input_acc"))
        if not vat_acc:
            return fail("no_input_vat_account")

    name = clean_seller(fields.get("seller_name") or history.get("seller_name"))
    tax_id = clean_tax_id(fields.get("seller_tax") or fields.get("seller_tax_id"))
    supplier = _resolve_supplier(mappings.get("clients") or [], history, name, tax_id)
    ref_no = clean_invoice_no(history.get("invoice_no") or fields.get("invoice_number"))

    lines: List[Dict[str, str]] = [
        {"acc": purchase_acc, "side": "D", "amount": _s(base), "desc": name or "ซื้อสินค้า/บริการ"}
    ]
    if has_vat:
        lines.append({"acc": vat_acc, "side": "D", "amount": _s(vat), "desc": "ภาษีซื้อ"})
    lines.append({"acc": ap_acc, "side": "C", "amount": _s(total), "desc": "เจ้าหนี้การค้า"})

    # 借贷必平(确定性闸):Σ借 == Σ贷,否则不产载荷。
    dr = sum((_d(ln["amount"]) for ln in lines if ln["side"] == "D"), Decimal("0"))
    cr = sum((_d(ln["amount"]) for ln in lines if ln["side"] == "C"), Decimal("0"))
    if _q(dr) != _q(cr):
        return fail("entry_not_balanced")

    payload = {
        "direction": "purchase",
        "doctype": "HP" if _is_paid(fields, config) else "RR",
        "account_set": account_set,
        "docdate_be": docdate_be,
        "vat_period_be": vat_period_be,
        "ref_no": ref_no,
        "supplier": supplier,
        "vat_rate": float(_VAT_RATE) if has_vat else 0.0,
        "base_amount": _s(base),
        "vat_amount": _s(vat),
        "total_amount": _s(total),
        "lines": lines,
        "source": {
            "history_id": str(history.get("id") or ""),
            "filename": history.get("filename"),
        },
    }
    return ExpressMapResult(True, payload, "ok")
