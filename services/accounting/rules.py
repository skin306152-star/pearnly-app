# -*- coding: utf-8 -*-
"""自动记账规则目录 R1-R9(纯函数 · 零副作用 · docs/accounting/02)。

每条规则把一笔业务翻译成平衡的借贷分录模板。entries 元素只声明【角色】(role)或已定科目
(account_id),posting.py 经 account_mappings 解析成真科目。金额全部反解业务单已算好的
合计(不重算);整单折扣/凑整并入最大借方桶,保证 Σ借=Σ贷 机械成立。

uncertainties 是置信扣分点(posting 据此算 confidence):
  item_type_guess        OCR 票商品/服务判不准(影响 WHT)
  reversal_direction     红冲/退货方向易错
  payment_method_unknown 付款没说现金还是转账
  category_unmapped      费用类别没配科目(回落杂项)
"""

from __future__ import annotations

from decimal import Decimal

ZERO = Decimal("0")

UNCERTAINTY_SCORES = {
    "item_type_guess": 60,
    "reversal_direction": 60,
    "payment_method_unknown": 75,
    "category_unmapped": 70,
}

_BANK_METHODS = ("transfer", "promptpay", "card", "bank")


def _d(v) -> Decimal:
    return Decimal(str(v if v is not None else 0))


def _entry(target, dr_cr: str, amount: Decimal, memo=None) -> dict:
    """target:角色名(str)或 {'account_id': uuid}(学习记忆直接定科目)。"""
    e = {"dr_cr": dr_cr, "amount": amount, "memo": memo, "role": None, "account_id": None}
    if isinstance(target, dict):
        e["account_id"] = target["account_id"]
    else:
        e["role"] = target
    return e


def _pay_role(method) -> str:
    return "cash" if method == "cash" else "bank"


def build(ctx: dict):
    """业务上下文 → 规则结果 {rule_key, entries, uncertainties, description, human_note}。

    返回 None = 该业务不生成凭证(R3 采购订单在途 / 报价单)。
    """
    st = ctx["source_type"]
    if st == "purchase":
        if ctx.get("doc_kind") == "purchase_order":
            return None
        return _purchase(ctx)
    if st == "sale":
        return _sale(ctx)
    if st == "pos":
        return _pos(ctx)
    if st == "payment":
        return _payment(ctx)
    if st == "vat_closing":
        return _vat_closing(ctx)
    return None


def _purchase(ctx: dict):
    """R1 进货进项票 / R2 费用单。借 存货+费用+进项税 · 贷 应付(+预扣税应缴)。"""
    a = ctx["amounts"]
    grand, vat, wht = _d(a["grand_total"]), _d(a["vat_amount"]), _d(a["wht_amount"])
    if grand <= ZERO:
        return None
    uncertainties = list(ctx.get("uncertainties") or [])
    learned = ctx.get("learned") or {}

    inventory_amt = ZERO
    buckets: dict = {}
    bucket_order = []
    for ln in ctx.get("lines") or []:
        amt = _d(ln.get("line_total"))
        if amt <= ZERO:
            continue
        if ln.get("item_type") == "goods" and ln.get("product_id"):
            inventory_amt += amt
            continue
        if learned.get("account_id"):
            key = ("account", str(learned["account_id"]))
        elif ln.get("category_id"):
            key = ("role", f"expense:{ln['category_id']}")
        else:
            key = ("role", "expense_default")
        if key not in buckets:
            buckets[key] = ZERO
            bucket_order.append(key)
        buckets[key] += amt

    # OCR 票的商品/服务划分是猜的(影响 WHT);学习记忆命中则视为已确认
    is_expense = ctx.get("doc_kind") == "expense"
    if ctx.get("source_tier") == "ocr" and is_expense and not learned:
        uncertainties.append("item_type_guess")

    entries = []
    if inventory_amt > ZERO:
        entries.append(_entry("inventory", "debit", inventory_amt, "进货入库"))
    for key in bucket_order:
        target = {"account_id": key[1]} if key[0] == "account" else key[1]
        entries.append(_entry(target, "debit", buckets[key], "费用"))
    # 整单折扣/凑整反解:借方合计须 = grand - vat,差额并入最大借方桶
    debit_base = sum(e["amount"] for e in entries)
    adjust = (grand - vat) - debit_base
    if adjust != ZERO:
        if entries:
            biggest = max(entries, key=lambda e: e["amount"])
            biggest["amount"] += adjust
        else:
            entries.append(_entry("expense_default", "debit", adjust, "费用"))
    if vat > ZERO:
        entries.append(_entry("input_vat", "debit", vat, "进项税"))
    if wht > ZERO:
        entries.append(_entry("wht_payable", "credit", wht, "代扣预扣税"))
        entries.append(_entry("ap", "credit", grand - wht, "应付供应商"))
    else:
        entries.append(_entry("ap", "credit", grand, "应付供应商"))

    rule_key = "R2" if is_expense else "R1"
    note = (
        f"这笔花费 ฿{grand}:费用入账,先欠供应商。"
        if is_expense
        else f"这批进货 ฿{grand}:货记入存货,进项税 ฿{vat} 可抵,先欠供应商。"
    )
    return {
        "rule_key": rule_key,
        "entries": entries,
        "uncertainties": uncertainties,
        "description": ctx.get("ref") or ("费用入账" if is_expense else "进货入账"),
        "human_note": note,
    }


def _sale(ctx: dict):
    """R4 销售开票(现结/赊账/客户预扣)· R8 红冲/补开(doc_type=credit_note/debit_note)。"""
    a = ctx["amounts"]
    grand, vat, wht = _d(a["grand_total"]), _d(a["vat_amount"]), _d(a["wht_amount"])
    if grand <= ZERO:
        return None
    doc_type = ctx.get("doc_kind") or ""
    if doc_type == "quotation":
        return None
    uncertainties = list(ctx.get("uncertainties") or [])

    receivable = grand - wht
    paid = min(_d(a.get("paid_amount")), receivable) if ctx.get("paid_at_issue") else ZERO
    debits = []
    if wht > ZERO:
        debits.append(_entry("wht_prepaid", "debit", wht, "客户预扣税(可抵)"))
    if paid > ZERO:
        method = ctx.get("payment_method")
        if method not in _BANK_METHODS and method != "cash":
            uncertainties.append("payment_method_unknown")
        debits.append(_entry(_pay_role(method), "debit", paid, "已收款"))
    if receivable - paid > ZERO:
        debits.append(_entry("ar", "debit", receivable - paid, "应收客户"))
    credits = [
        _entry("sales_revenue", "credit", grand - vat, "销售收入"),
    ]
    if vat > ZERO:
        credits.append(_entry("output_vat", "credit", vat, "销项税"))

    if doc_type == "credit_note":
        entries = _reverse(debits + credits)
        uncertainties.append("reversal_direction")
        return {
            "rule_key": "R8",
            "entries": entries,
            "uncertainties": uncertainties,
            "description": ctx.get("ref") or "红冲",
            "human_note": f"红冲 ฿{grand}:按原票反向冲销收入与税。",
        }
    if doc_type == "debit_note":
        uncertainties.append("reversal_direction")
        return {
            "rule_key": "R8",
            "entries": debits + credits,
            "uncertainties": uncertainties,
            "description": ctx.get("ref") or "补开",
            "human_note": f"补开 ฿{grand}:补记收入与税。",
        }
    return {
        "rule_key": "R4",
        "entries": debits + credits,
        "uncertainties": uncertainties,
        "description": ctx.get("ref") or "销售开票",
        "human_note": f"开出发票 ฿{grand}:收入 ฿{grand - vat},销项税 ฿{vat}"
        + ("。" if paid > ZERO else ",待客户付款。"),
    }


def _pos(ctx: dict):
    """R5 POS 埋单(收款按支付方式分桶;退货走反向 + 待审)。

    成本结转(借 cogs/贷 inventory):默认定期盘存月末统一结(出账本窗口),
    POS 扣库存流水不带成本,逐单结转不可靠。
    """
    a = ctx["amounts"]
    grand, vat = _d(a["grand_total"]), _d(a["vat_amount"])
    if grand <= ZERO:
        return None
    uncertainties = list(ctx.get("uncertainties") or [])

    debits = []
    covered = ZERO
    for p in ctx.get("payments") or []:
        amt = _d(p["amount"])
        if amt <= ZERO:
            continue
        amt = min(amt, grand - covered)
        if amt <= ZERO:
            break
        debits.append(_entry(p["role"], "debit", amt, "POS 收款"))
        covered += amt
    if grand - covered > ZERO:
        debits.append(_entry("ar", "debit", grand - covered, "挂账"))
    credits = [_entry("sales_revenue", "credit", grand - vat, "营业收入")]
    if vat > ZERO:
        credits.append(_entry("output_vat", "credit", vat, "销项税"))

    entries = debits + credits
    if ctx.get("is_refund"):
        entries = _reverse(entries)
        uncertainties.append("reversal_direction")
        note = f"POS 退款 ฿{grand}:反向冲销当日营业收入。"
    else:
        note = f"POS 成交 ฿{grand}:收款入账,收入 ฿{grand - vat},销项税 ฿{vat}。"
    return {
        "rule_key": "R8" if ctx.get("is_refund") else "R5",
        "entries": entries,
        "uncertainties": uncertainties,
        "description": ctx.get("ref") or "POS 成交",
        "human_note": note,
    }


def _payment(ctx: dict):
    """R6 收款(应收回款)/ R7 付款(应付付清)。direction: in=收 out=付。"""
    amount = _d(ctx["amounts"]["amount"])
    if amount <= ZERO:
        return None
    uncertainties = list(ctx.get("uncertainties") or [])
    method = ctx.get("payment_method")
    if method not in _BANK_METHODS and method != "cash":
        uncertainties.append("payment_method_unknown")
    pay = _pay_role(method)
    if ctx.get("direction") == "in":
        entries = [
            _entry(pay, "debit", amount, "收到货款"),
            _entry("ar", "credit", amount, "冲应收"),
        ]
        rule_key, note = "R6", f"收到货款 ฿{amount},应收账款相应减少。"
    else:
        entries = [
            _entry("ap", "debit", amount, "冲应付"),
            _entry(pay, "credit", amount, "付出货款"),
        ]
        rule_key, note = "R7", f"付了供应商 ฿{amount},应付账款相应减少。"
    return {
        "rule_key": rule_key,
        "entries": entries,
        "uncertainties": uncertainties,
        "description": ctx.get("ref") or ("收款" if rule_key == "R6" else "付款"),
        "human_note": note,
    }


def _vat_closing(ctx: dict):
    """R9 月末 VAT 结转:销项−进项,正=应交(vat_payable)负=留抵(vat_receivable)。"""
    a = ctx["amounts"]
    out_vat, in_vat = _d(a["output_vat_total"]), _d(a["input_vat_total"])
    if out_vat == ZERO and in_vat == ZERO:
        return None
    entries = []
    if out_vat > ZERO:
        entries.append(_entry("output_vat", "debit", out_vat, "本月销项税转出"))
    if in_vat > ZERO:
        entries.append(_entry("input_vat", "credit", in_vat, "本月进项税转出"))
    diff = out_vat - in_vat
    if diff > ZERO:
        entries.append(_entry("vat_payable", "credit", diff, "应交 VAT"))
        note = f"本月销项税 ฿{out_vat} − 进项税 ฿{in_vat} = 应交 VAT ฿{diff}。"
    elif diff < ZERO:
        entries.append(_entry("vat_receivable", "debit", -diff, "VAT 留抵"))
        note = f"本月进项税 ฿{in_vat} 大于销项税 ฿{out_vat},留抵 ฿{-diff} 下月可抵。"
    else:
        note = f"本月销项税与进项税相抵(฿{out_vat}),无应交。"
    return {
        "rule_key": "R9",
        "entries": entries,
        "uncertainties": [],
        "description": f"VAT 结转 {ctx.get('ref') or ''}".strip(),
        "human_note": note,
    }


def _reverse(entries: list) -> list:
    """红冲反向:借贷对调,金额不变(R8)。"""
    out = []
    for e in entries:
        r = dict(e)
        r["dr_cr"] = "credit" if e["dr_cr"] == "debit" else "debit"
        out.append(r)
    return out


def compute_confidence(source_tier: str, uncertainties: list) -> Decimal:
    """C1 数据源分级:第一方干净=100 · OCR 干净=95 · 有不确定点取最低分。"""
    if uncertainties:
        return Decimal(min(UNCERTAINTY_SCORES.get(u, 60) for u in uncertainties))
    return Decimal(100 if source_tier == "first_party" else 95)
