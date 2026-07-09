# -*- coding: utf-8 -*-
"""逐行判定:方向(进项/销项)+ ERP 落点(现金/赊账)+ 缺字段警告。

复用 ERP 侧现成确定性判定,不另造规则:
  - 方向锚点 = services.erp.express_push.direction.detect_by_tax(账套税号 × 票面 seller/buyer),
    MR.ERP 与 Express 推送同用这一套(见 [[model-routing-matrix-contract-lock]] 邻域约定)。
  - 现金/赊账 = services.erp.express_push.common.payment_is_paid(付款字段)。

「智能」的定义(Zihao 拍板):有数据自动落,无数据兜底靠人工。故每个关键字段判三态并给理由:
  auto    读到可信数据,系统自动落
  default 无信号,按政策默认(赊账/含税),标出待用户确认
  human   数据缺失/异常且会挡住 ERP,必须人工补(warning)
"""

from __future__ import annotations

from typing import Any, Dict, List

from services.erp.express_push.common import payment_is_paid
from services.erp.express_push.direction import detect_by_tax
from services.purchase.field_clean import clean_tax_id

# 缺字段警告码(前端映射文案 · 与 ERP 真实拒收口径对齐)。
W_NO_DOC_NO = "no_doc_no"  # 单号空 → ERP 拒收 / 无法定位
W_DUP_DOC_NO = "dup_doc_no"  # 批次内重号 → ERP 拒收
W_NO_TAX_NOT_WALKIN = "no_tax_not_walkin"  # 对方无税号又未勾散客 → 可能判不出/落空壳客户
W_BAD_DATE = "bad_date"  # 日期无法解析 → be_dates 拒 → 建不了账
W_AMOUNT_INCONSISTENT = "amount_inconsistent"  # 税前+税≠总额且非仅总额 → amounts() 拒
W_NO_PRODUCT = "no_product"  # 商品名空 → 明细缺
W_NO_TOTAL = "no_total"  # 总额缺/非正 → 建不了账


def _d(v: Any):
    from decimal import Decimal, InvalidOperation

    try:
        s = str(v).replace(",", "").strip()
        return Decimal(s) if s else None
    except (InvalidOperation, ValueError):
        return None


def judge_direction_row(fields: Dict[str, Any], own_tax_id: Any) -> Dict[str, Any]:
    """方向复核。上游已按用户选择把甲乙方落位,这里用税号锚点复核:
    命中=tax_confirmed(账套税号=某一方);判不出(账套或对方税号缺)=human_declared(按用户选择走)。"""
    declared = str(fields.get("_direction") or "sales").lower()
    derived = detect_by_tax({"fields": fields}, own_tax_id)
    own = clean_tax_id(own_tax_id)
    if derived == declared:
        anchor = "卖方" if declared == "sales" else "买方"
        why = f"账套税号 {own} = 票面{anchor} → {'销项' if declared == 'sales' else '进项'}(税号已复核)"
        return {"direction": declared, "source": "tax_confirmed", "why": why}
    # 判不出:账套税号未设 / 对方税号缺 / 双方都=账套 → 不用税号强判,按用户批次选择走(留痕)。
    why = "账套或对方税号缺失,无法用税号复核 → 按您所选方向处理"
    return {"direction": declared, "source": "human_declared", "why": why}


def judge_payment_row(fields: Dict[str, Any]) -> Dict[str, Any]:
    """现金/赊账落点。paid→现金票(MR.ERP sales_cash / Express HS);unpaid→赊账(sales_credit / IV);
    无信号→按赊账默认(标 default,提示用户确认)。

    payment_is_paid(F3 起)也认票种语义,但这里的 document_type 是 mapping 层从批次「含 VAT」
    复选框合成的代理值(非真实票面证据·见 mapping.py),不能当票种信号摊派现/赊,故判定时剔除,
    只认真实 payment_method/status,无信号照旧兜底赊账待人确认。
    """
    signal_fields = {k: v for k, v in fields.items() if k != "document_type"}
    paid = payment_is_paid(signal_fields)
    if paid is True:
        return {
            "paid": True,
            "target": "cash",
            "source": "auto",
            "why": "付款方式=已付/现金 → 现金票",
        }
    if paid is False:
        return {
            "paid": False,
            "target": "credit",
            "source": "auto",
            "why": "付款方式=未付/赊账 → 赊账票",
        }
    return {
        "paid": None,
        "target": "credit",
        "source": "default",
        "why": "无付款信号 → 默认按赊账,请确认",
    }


def row_warnings(fields: Dict[str, Any], *, dup_doc_nos: List[str]) -> List[str]:
    """逐行缺字段警告(对齐 ERP 真实拒收:单号/日期/金额/税号/商品)。空列表=可推。"""
    w: List[str] = []
    doc_no = str(fields.get("invoice_number") or "").strip()
    if not doc_no:
        w.append(W_NO_DOC_NO)
    elif doc_no in (dup_doc_nos or []):
        w.append(W_DUP_DOC_NO)

    # 对方税号:有效税号 → 静默;散客现金票 → 静默(有意兜底);否则(有名无税又非散客)→ 提醒。
    other_tax = clean_tax_id(
        fields.get("buyer_tax") if fields.get("_direction") == "sales" else fields.get("seller_tax")
    )
    if not other_tax and not fields.get("_walkin"):
        w.append(W_NO_TAX_NOT_WALKIN)

    from services.erp.express_push.common import be_dates

    if be_dates(fields.get("date")) is None:
        w.append(W_BAD_DATE)

    total = _d(fields.get("total_amount"))
    if total is None or total <= 0:
        w.append(W_NO_TOTAL)
    else:
        sub = _d(fields.get("subtotal"))
        vat = _d(fields.get("vat"))
        # 税前+税 与总额都给了却对不上(容差 0.02) → amounts() 会拒;只给总额则不算不一致(可反推)。
        if sub is not None and vat is not None and abs(sub + vat - total) > _d("0.02"):
            w.append(W_AMOUNT_INCONSISTENT)

    if not (fields.get("items") or []):
        w.append(W_NO_PRODUCT)
    return w


def judge_rows(
    mapped: List[Dict[str, Any]], *, own_tax_id: Any, dup_doc_nos: List[str]
) -> List[Dict[str, Any]]:
    """整批判定 → [{row_index, direction, payment, warnings, blocked}]。blocked=有硬缺字段(挡推送)。"""
    out: List[Dict[str, Any]] = []
    hard = {W_NO_DOC_NO, W_DUP_DOC_NO, W_BAD_DATE, W_NO_TOTAL, W_AMOUNT_INCONSISTENT}
    for m in mapped:
        fields = m.get("fields") or {}
        warnings = row_warnings(fields, dup_doc_nos=dup_doc_nos)
        out.append(
            {
                "row_index": m.get("row_index"),
                "direction": judge_direction_row(fields, own_tax_id),
                "payment": judge_payment_row(fields),
                "warnings": warnings,
                "blocked": bool(hard & set(warnings)),
            }
        )
    return out
