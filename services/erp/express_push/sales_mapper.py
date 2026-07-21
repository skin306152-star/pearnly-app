# -*- coding: utf-8 -*-
"""扁平化 history → Express 销项(销售)记账载荷(镜像 mapper · 确定性纯函数)。

销售一张赊销/现销发票 = 一笔销售日记账(JNLTYP=03)+ 销项税(喂 ภ.พ.30)+ 复式分录
(借应收 AR = 贷销售收入 + 贷销项税,与采购相反)。共享纯函数在 common.py;这里只留
销项特有(客户身份 + 销售分录装配)。

载荷契约(与 companion `sales_adapter` 一字不差,消费方已建):
  direction     "sales"
  doctype        IV(赊销/未收 · 默认)| HS(现销/已收)
  account_set    DATAT(白名单在 enqueue/agent 再校验)
  docdate_be / vat_period_be   佛历 YYMMDD
  ref_no         销售参考(幂等锚)
  customer       {code,name,tax_id,address,prename,customer_new}
  vat_rate       7.00 | 0.00
  base_amount / vat_amount / total_amount
  lines          [{acc,side(D/C),amount,desc}] · 借应收 = 贷收入 + 贷销项税 · 借贷必平
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from services.erp.express_push.common import (
    ExpressMapResult,
    _d,
    _q,
    _s,
    _VAT_RATE,
    amounts,
    be_dates,
    detect_prename,
    extract_line_items,
    fail,
    finalize_payload,
    item_mode_for,
    payment_verdict_for,
    resolve_account,
    resolve_account_sourced,
    SRC_DEFAULT,
)
from services.erp.express_push import stock_lane_enabled
from services.erp.express_push.posting_profile import profile_from_config
from services.purchase.field_clean import (
    clean_address,
    clean_invoice_no,
    clean_seller,
    clean_tax_id,
)

logger = logging.getLogger(__name__)

# 现金销售客户:ERP 真账套通行约定 —— CUSCOD=CUSNAM="เงินสด"(korn/test 套实测均已建档,
# 应收走 ar_acc)。收现金零售单买方栏 OCR 即「เงินสด」,但被采购卖家清洗器(noise 黑名单含
# "เงินสด"/"cash")误当噪声抹空 → 触发 confirm 的 vendor_missing。这里对销项直接认现金客户:
# 用现成档(customer_new=False · 不新建 · 不冒重客户),让记账挂到固定现金客户名下。
CASH_CUSTOMER_NAME = "เงินสด"
_CASH_BUYER_TOKENS = frozenset({"เงินสด", "ขายสด", "cash"})


def _is_cash_buyer(raw: Any) -> bool:
    """买方是否为现金客人(销项专用判定)。"""
    return str(raw or "").strip().lower() in _CASH_BUYER_TOKENS


def _resolve_customer(
    clients: List[Dict[str, Any]],
    history: Dict[str, Any],
    name: str,
    tax_id: str,
    address: str = "",
) -> Dict[str, Any]:
    """客户身份块。命中 erp_client_mappings(express)→ 带 code、customer_new=False;
    否则 customer_new=True 让 Agent 在 ARMAS 建档(带 tax_id+address 落档,开全额税票用)。"""
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
        "address": address,
        "prename": detect_prename(name),
        "customer_new": not bool(code),
    }


def build_express_sales_payload(
    history: Dict[str, Any],
    *,
    config: Dict[str, Any],
    mappings: Optional[Dict[str, Any]] = None,
    category: str = "",
) -> ExpressMapResult:
    """扁平化 history → Express 销项载荷。判脏/不自洽 → ok=False(留人工)。

    config 键:account_set · revenue_acc(兜底收入科目)· vat_output_acc(销项税科目)·
    ar_acc(应收科目)· default_doctype(IV/HS)。
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
    revenue_acc, acc_source = resolve_account_sourced(accounts, category, config.get("revenue_acc"))
    if not revenue_acc:
        return fail("no_revenue_account")
    ar_acc = resolve_account(accounts, "accounts_receivable", config.get("ar_acc"))
    if not ar_acc:
        return fail("no_ar_account")

    has_vat = vat > 0
    if has_vat:
        vat_acc = resolve_account(accounts, "output_vat", config.get("vat_output_acc"))
        if not vat_acc:
            return fail("no_output_vat_account")

    raw_buyer = fields.get("buyer_name") or fields.get("customer_name") or history.get("buyer_name")
    tax_id = clean_tax_id(
        fields.get("buyer_tax") or fields.get("buyer_tax_id") or fields.get("customer_tax")
    )
    address = clean_address(fields.get("buyer_addr"))
    if _is_cash_buyer(raw_buyer):
        name = CASH_CUSTOMER_NAME
        # 现金/散客客户用现成档(不新建)→ 不带地址(简易税票无须买方地址)。
        customer = {
            "code": CASH_CUSTOMER_NAME,
            "name": CASH_CUSTOMER_NAME,
            "tax_id": tax_id,
            "address": "",
            "prename": "",
            "customer_new": False,
        }
    else:
        name = clean_seller(raw_buyer)
        customer = _resolve_customer(mappings.get("clients") or [], history, name, tax_id, address)
    ref_no = clean_invoice_no(history.get("invoice_no") or fields.get("invoice_number"))

    # 分录反向:借 应收(含税) = 贷 销售收入(税前) + 贷 销项税。
    lines: List[Dict[str, str]] = [
        {"acc": ar_acc, "side": "D", "amount": _s(total), "desc": name or "ลูกหนี้การค้า"},
        {"acc": revenue_acc, "side": "C", "amount": _s(base), "desc": "รายได้จากการขาย"},
    ]
    if has_vat:
        lines.append({"acc": vat_acc, "side": "C", "amount": _s(vat), "desc": "ภาษีขาย"})

    dr = sum((_d(ln["amount"]) for ln in lines if ln["side"] == "D"), Decimal("0"))
    cr = sum((_d(ln["amount"]) for ln in lines if ln["side"] == "C"), Decimal("0"))
    if _q(dr) != _q(cr):
        return fail("entry_not_balanced")

    # 记账画像:永续客户库存路未开时,销售会结转 COGS/扣库存,绝不静默按周期制落 → 交会计。
    # 指纹未上报→unknown→非库存(=今天默认,行为不变)。
    profile = profile_from_config(config, stock_enabled=stock_lane_enabled(config))
    if profile.posting_mode == "manual_review":
        return fail(f"posting_needs_review:{profile.inventory_usage}")

    # V1 安全明细:OCR 行项目过对账闸(行合计≈税前额才采信)。挂收入科目作直接科目行,
    # 不碰库存/成本。status!=ok → companion 退回表头模式 + posted_partial(诚实)。
    detail = extract_line_items(
        fields, base, total=total, item_mode=item_mode_for(profile.posting_mode)
    )

    # 现销 HS / 赊销 IV:六级漏斗(common.payment_verdict)—— 人工裁决 > 票面显式字段 >
    # 票种语义(F3)> 银行佐证(F6)> 无信号默认赊销。销项 v1 不接供应商过账档案(档案锚是
    # 卖方税号,销项无此维度)。verdict_src 留痕排障用:现/赊哪层定的。
    paid, verdict_src = payment_verdict_for(
        history, fields, mappings, direction="sales", total=total
    )
    doctype = "HS" if paid else "IV"
    logger.info(
        "[express-sales] ref_no=%s doctype=%s payment_src=%s",
        ref_no,
        doctype,
        verdict_src or "config_default",
    )
    payload = {
        "direction": "sales",
        "doctype": doctype,  # 默认 IV 赊销(无信号/未收)
        "account_set": account_set,
        "docdate_be": docdate_be,
        "vat_period_be": vat_period_be,
        "ref_no": ref_no,
        "customer": customer,
        "vat_rate": float(_VAT_RATE) if has_vat else 0.0,
        "base_amount": _s(base),
        "vat_amount": _s(vat),
        "total_amount": _s(total),
        "lines": lines,
        "items": detail["items"],
        "items_status": detail["status"],
        "items_account": revenue_acc,  # 明细行挂的收入科目(直接科目行)
        "items_line_sum": detail["line_sum"],
        # 变动科目(收入)的真实解析来源 · config_default=落账套默认→待核(诚实状态)。
        "account_source": acc_source,
        "account_review": acc_source == SRC_DEFAULT,
        "doctype_src": verdict_src or "config_default",  # 现/赊哪层定的(F2-F6 六级漏斗留痕)
        "source": {
            "history_id": str(history.get("id") or ""),
            "filename": history.get("filename"),
        },
    }
    return ExpressMapResult(True, finalize_payload(payload), "ok")
