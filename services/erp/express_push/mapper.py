# -*- coding: utf-8 -*-
"""扁平化 history → Express 记账载荷(确定性纯函数 · 不连库 · 不调 LLM)。

Express 一张赊购/现购发票 = 一笔采购日记账(JNLTYP=04)+ 进项税(喂 ภ.พ.30)+
复式分录。金额/税额/借贷一律由确定性引擎算(铁律 · 见
[[line-accounting-honest-status-boundary]]),LLM 只负责更早的识别/抽取。

输入对齐 erp_push.flatten_history_for_mrerp 的产物(源是 ocr_history,不是
purchase_docs):顶层 history 字段 + `fields`(主页 OCR 字段)。判脏/数不自洽/缺
关键映射 → 不产载荷,返回 ok=False + reason(调用方据此落 manual 留人工)。

载荷契约(写进 enqueue 的 request_body · Agent lease 后照此录入 Express):
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

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from services.purchase.field_clean import clean_invoice_no, clean_seller, clean_tax_id
from services.purchase.totals import vat_from_inclusive

_CENT = Decimal("0.01")
_BALANCE_TOL = Decimal("0.02")  # 税前+税额 与 含税 容差(§4)
_VAT_RATE = Decimal("7")

# 泰国法人前缀(prename)· 按长度降序匹配(长的先,防 หจก. 被 ห้าง 短前缀截断)。
_PRENAMES = (
    "บริษัทจำกัด",
    "บริษัท",
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญ",
    "หจก.",
    "หจก",
    "หสน.",
)

# 付款字段里代表"已付/现购"的信号(归一小写匹配)。
_PAID_TOKENS = ("paid", "cash", "qr", "promptpay", "prompt_pay", "transfer", "เงินสด", "จ่ายแล้ว")


@dataclass(frozen=True)
class ExpressMapResult:
    """映射结果。ok=True → payload 可入队;ok=False → reason 落 manual 留人工。"""

    ok: bool
    payload: Optional[Dict[str, Any]]
    reason: str


def _d(v: Any) -> Optional[Decimal]:
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v).replace(",", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return None


def _q(v: Decimal) -> Decimal:
    return v.quantize(_CENT, rounding=ROUND_HALF_EVEN)


def _s(v: Decimal) -> str:
    """decimal → 定点字符串(钱不用 float · 保两位)。"""
    return format(_q(v), "f")


def _fail(reason: str) -> ExpressMapResult:
    return ExpressMapResult(False, None, reason)


def _detect_prename(name: str) -> str:
    s = (name or "").strip()
    for p in _PRENAMES:
        if s.startswith(p):
            return p
    return ""


def _is_paid(fields: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """已付(现购 HP)还是未付(赊购 RR)。明确 paid/unpaid 优先,否则按 config 默认。"""
    status = str(fields.get("payment_status") or "").strip().lower()
    if status == "paid":
        return True
    if status in ("unpaid", "credit"):
        return False
    method = str(fields.get("payment_method") or "").strip().lower()
    if method and any(tok in method for tok in _PAID_TOKENS):
        return True
    # 默认按 config(B2B 采购票多为赊购 → 缺省 RR · 保守不假装已付)。
    return str(config.get("default_doctype") or "RR").upper() == "HP"


def _be_dates(invoice_date: Any) -> Optional[tuple[str, str]]:
    """公历 ISO 日期 → (docdate_be, vat_period_be)。无法解析 → None(缺日期不建账)。"""
    s = str(invoice_date or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if not m:
        m2 = re.match(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})$", s)  # DD/MM/YYYY
        if not m2:
            return None
        day, month, year = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
    else:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    yy = (year + 543) % 100
    return (f"{yy:02d}{month:02d}{day:02d}", f"{yy:02d}{month:02d}01")


def _resolve_account(
    accounts: List[Dict[str, Any]], category: str, config_code: Optional[str]
) -> Optional[str]:
    """科目解析:先查映射束(erp_type=express · pearnly_category 命中),否则 config 兜底码。"""
    cat = (category or "").strip()
    if cat:
        for a in accounts or []:
            if (a.get("erp_type") or "").lower() == "express" and (
                a.get("pearnly_category") or ""
            ) == cat:
                code = (a.get("erp_code") or "").strip()
                if code:
                    return code
    code = (config_code or "").strip()
    return code or None


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
        "prename": _detect_prename(name),
        "supplier_new": not bool(code),
    }


def _amounts(fields: Dict[str, Any], history: Dict[str, Any]) -> Optional[tuple]:
    """从票面字段确定性求 (base, vat, total)。返回 None = 数不自洽/缺总额(留人工)。

    优先采信票面 税前+税额 自洽;缺 VAT 用 总额−税前;只有总额按 7% 含税反推。
    """
    total = (
        _d(history.get("total_amount")) or _d(fields.get("total_amount")) or _d(fields.get("total"))
    )
    if total is None or total <= 0:
        return None
    base = _d(fields.get("subtotal"))
    vat = _d(fields.get("vat"))

    if base is not None and vat is not None and base > 0:
        pass
    elif base is not None and base > 0:
        vat = total - base
    elif vat is not None and vat >= 0:
        base = total - vat
    else:
        # 只有总额 → 按 7% 含税反推(进项税票默认含税)。
        vat = _q(vat_from_inclusive(total))
        base = total - vat

    base, vat, total = _q(base), _q(vat), _q(total)
    if base <= 0 or vat < 0:
        return None
    if abs(base + vat - total) > _BALANCE_TOL:
        return None
    return base, vat, total


def build_express_payload(
    history: Dict[str, Any],
    *,
    config: Dict[str, Any],
    mappings: Optional[Dict[str, Any]] = None,
    category: str = "",
) -> ExpressMapResult:
    """扁平化 history → Express 载荷。判脏/不自洽 → ok=False(留人工)。

    config 键:account_set(目标账套)· fallback_acc(兜底采购科目)·
    vat_input_acc(进项税科目)· ap_acc(应付科目)· default_doctype(RR/HP)。
    mappings:get_mrerp_mappings_bundle(tenant_id)(accounts/clients)。
    """
    mappings = mappings or {}
    fields = history.get("fields") if isinstance(history.get("fields"), dict) else {}
    fields = fields or {}

    account_set = str(config.get("account_set") or "").strip()
    if not account_set:
        return _fail("no_account_set")

    dates = _be_dates(history.get("invoice_date") or fields.get("date"))
    if not dates:
        return _fail("bad_or_missing_date")
    docdate_be, vat_period_be = dates

    amts = _amounts(fields, history)
    if not amts:
        return _fail("amounts_not_consistent")
    base, vat, total = amts

    accounts = mappings.get("accounts") or []
    purchase_acc = _resolve_account(accounts, category, config.get("fallback_acc"))
    if not purchase_acc:
        return _fail("no_purchase_account")
    ap_acc = _resolve_account(accounts, "accounts_payable", config.get("ap_acc"))
    if not ap_acc:
        return _fail("no_ap_account")

    has_vat = vat > 0
    if has_vat:
        vat_acc = _resolve_account(accounts, "input_vat", config.get("vat_input_acc"))
        if not vat_acc:
            return _fail("no_input_vat_account")

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
        return _fail("entry_not_balanced")

    payload = {
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
