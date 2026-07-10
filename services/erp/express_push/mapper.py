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
  supplier       {code,name,tax_id,address,prename,supplier_new}
  vat_rate       7.00 | 0.00
  base_amount    税前(字符串化 decimal)
  vat_amount     进项税额
  total_amount   含税合计 = base + vat
  lines          复式分录 [{acc,side(D/C),amount,desc}] · 借贷必平
  doc_lane       "goods"(完整税票·可抵进项)| "expense"(费用票·进项税不可抵扣)

货/费分档(拍板口径):费用票(无完整税票/judge_direction=expense)进项税不可抵扣、VAT 计入
成本——doc_lane=expense 时 base_amount 改含税全额、vat_amount 清零、不产生进项税行,借方
直接落费用科目全额。小助手收到 vat=0 不写 ISVAT → 不进 ภ.พ.30,GL 全由 lines 驱动 → 老版本
小助手零改动天然兼容(见 [[mrerp-expense-453-and-import-honesty]] 453 费用档先例)。
"""

from __future__ import annotations

import logging
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
    extract_line_items,
    fail,
    ITEM_MODE_NONSTOCK,
    ITEMS_OK,
    payment_verdict_for,
    resolve_account,
    resolve_account_sourced,
    sanitize_payload_cp874,
    SRC_DEFAULT,
)
from services.purchase.field_clean import (
    clean_address,
    clean_invoice_no,
    clean_seller,
    clean_tax_id,
)
from services.purchase.item_verdict import item_verdict

logger = logging.getLogger(__name__)


# 费用车道通用物料名(固定值):小助手对 ITEM_MODE_NONSTOCK 行按名 ensure_item 建非库存
# STMAS 主档,行名若吃卖方名会每个供应商长一个费用物料(主档污染)。全账套共用这一个,
# 镜像 MR.ERP 453 的通用 EXPENSE 物料先例(autocreate._provision_expense_item);
# 供应商名不丢——GL 借方行 desc 已带卖方名。
_EXPENSE_ITEM_NAME = "ค่าใช้จ่าย"


def _expense_detail(total: Decimal) -> Dict[str, Any]:
    """费用车道单行明细(镜像 MR.ERP 453「单行含税全额」精神)。

    extract_line_items 的对账闸拿"行合计 ≈ 税前额"当可信基准;费用车道的 base 已改成含税
    全额(进项税不可抵扣 · 计入成本),OCR 行本是净额,直接喂闸会误判 mismatch——费用票
    本就不做逐行进销存匹配(不动库存/COGS),没必要也不该假装逐行对账过关,诚实收成一行。
    """
    line = {
        "name": _EXPENSE_ITEM_NAME,
        "qty": "1",
        "unit": "",
        "unit_price": _s(total),
        "amount": _s(total),
        "item_mode": ITEM_MODE_NONSTOCK,
    }
    return {"items": [line], "status": ITEMS_OK, "line_sum": _s(total)}


def _resolve_supplier(
    clients: List[Dict[str, Any]],
    history: Dict[str, Any],
    name: str,
    tax_id: str,
    address: str = "",
) -> Dict[str, Any]:
    """供应商身份块。命中 erp_client_mappings(express)→ 带 code、supplier_new=False;
    否则 supplier_new=True 让 Agent 在 APMAS 建档(带 tax_id+address 落档)。"""
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
    purchase_acc, acc_source = resolve_account_sourced(
        accounts, category, config.get("fallback_acc")
    )
    if not purchase_acc:
        return fail("no_purchase_account")
    ap_acc = resolve_account(accounts, "accounts_payable", config.get("ap_acc"))
    if not ap_acc:
        return fail("no_ap_account")

    # 货/费判据(单一事实源 · 与 MR.ERP routing.choose_doc_type 同判据,防两车道判据漂移)。
    is_expense, item_src = item_verdict(fields)
    vat_capitalized = _s(vat) if is_expense else None
    if is_expense:
        # 费用票口径(拍板 · intake.py「费用类即便读到 vat 也归 0」同口径 / MR.ERP 453 先例):
        # 进项税不可抵扣、VAT 计入成本 —— base 改含税全额、vat 清零,不产生进项税行;
        # 小助手收到 vat=0 就不写 ISVAT、不进 ภ.พ.30(GL 全由 lines 驱动)——这是本方案
        # 零改动小助手的依据,别把这行改回票面税前额。
        base, vat = total, Decimal("0")

    has_vat = vat > 0
    if has_vat:
        vat_acc = resolve_account(accounts, "input_vat", config.get("vat_input_acc"))
        if not vat_acc:
            return fail("no_input_vat_account")

    # ③ 官方名核验 · 已核验则优先用税局 RD 官方抬头(进账更干净)·否则回落 AI 名
    official = history.get("seller_name_official") if history.get("seller_name_verified") else None
    name = clean_seller(official or fields.get("seller_name") or history.get("seller_name"))
    tax_id = clean_tax_id(fields.get("seller_tax") or fields.get("seller_tax_id"))
    address = clean_address(fields.get("seller_addr"))
    supplier = _resolve_supplier(mappings.get("clients") or [], history, name, tax_id, address)
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

    # V1 安全明细(镜像销项):OCR 行过对账闸,挂采购科目作直接科目行,不碰库存/成本。
    # 费用车道另走单行收尾(_expense_detail·见函数注释,base 已改含税全额喂闸会误判)。
    if is_expense:
        detail = _expense_detail(total)
    else:
        detail = extract_line_items(fields, base, total=total)

    # 现购 HP / 赊购 RR:六级漏斗(common.payment_verdict)—— 人工裁决 > 票面显式字段 >
    # 票种语义(F3)> 供应商过账档案(F4)> 银行佐证(F6)> config 默认(B2B 缺省 RR)。
    # verdict_src 留痕排障用:现/赊哪层定的。
    paid, verdict_src = payment_verdict_for(
        history, fields, mappings, direction="purchase", total=total
    )
    if paid is None:
        paid = str(config.get("default_doctype") or "RR").upper() == "HP"
    doctype = "HP" if paid else "RR"
    doc_lane = "expense" if is_expense else "goods"
    logger.info(
        "[express-purchase] ref_no=%s doctype=%s payment_src=%s doc_lane=%s item_src=%s",
        ref_no,
        doctype,
        verdict_src or "config_default",
        doc_lane,
        item_src,
    )

    payload = {
        "direction": "purchase",
        "doctype": doctype,
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
        "items": detail["items"],
        "items_status": detail["status"],
        "items_account": purchase_acc,  # 明细行挂的采购科目(直接科目行)
        "items_line_sum": detail["line_sum"],
        # 变动科目(采购)的真实解析来源 · config_default=落账套默认→待核(诚实状态)。
        "account_source": acc_source,
        "account_review": acc_source == SRC_DEFAULT,
        "doctype_src": verdict_src or "config_default",  # 现/赊哪层定的(F2-F6 六级漏斗留痕)
        "doc_lane": doc_lane,  # goods=可抵进项 · expense=进项税不可抵扣(VAT 计入成本)
        "item_src": item_src,  # 货/费判据来源:manual | judge_direction=<kind>
        "source": {
            "history_id": str(history.get("id") or ""),
            "filename": history.get("filename"),
        },
    }
    if is_expense:
        # 留痕:这张票原本会读到多少进项税,现改折进成本(VAT capitalized · 排障/对账用)。
        payload["vat_capitalized"] = vat_capitalized
    return ExpressMapResult(True, sanitize_payload_cp874(payload), "ok")
