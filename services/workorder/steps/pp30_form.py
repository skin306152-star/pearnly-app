# -*- coding: utf-8 -*-
"""ภ.พ.30 官方申报表全字段契约(纯计算,零副作用)。

把 reconcile 产出的四个基数(销售额/销项税/可抵扣采购额/进项税)组装成税局 ภ.พ.30 表的
全字段结构。派生字段(应税销售额 = 总销售 − 0%销售 − 免税销售;应缴/超缴 = 销项 − 进项;
本期净应缴 = 应缴 − 上期留抵)在此算一次——compute 的减法层顺延到全字段,package 只渲染
本结构、绝不重算(上游产出→compute 汇集→package 呈现分层)。

本期无独立数据源的字段(0%销售、免税销售、上期留抵、加算金 เงินเพิ่ม、罚金 ค่าปรับ)按
数据诚实原则显式置 0 并标注 source=no_source_m1——不编造、不静默省略。其中上期留抵抵减
(line 8/12)与加算金/罚金(line 15/16)需要跨期账与逾期判定,M1 不支持,诚实置 0 待 M1.x。

字段行号对齐真客户 Sister Makeup 已申报原件(T0 语料盘点 §二读自 ภ.พ.30 电子签收件)。
"""

from __future__ import annotations

from decimal import Decimal

# 字段来源标注。derived=本表内派生;reconcile=上游对账基数直落;no_source_m1=本期无数据源诚实置 0。
SRC_RECONCILE = "reconcile"
SRC_DERIVED = "derived"
SRC_NO_SOURCE_M1 = "no_source_m1"

_ZERO = Decimal("0")


def _dec(v) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


def _field(line: str, key: str, th: str, zh: str, amount: Decimal, source: str) -> dict:
    return {
        "line": line,
        "key": key,
        "label_th": th,
        "label_zh": zh,
        "amount": str(amount),
        "source": source,
    }


def build(*, sales_amount, output_vat, purchase_amount, input_vat) -> dict:
    """组装 ภ.พ.30 全字段。入参是 reconcile/compute 已定的四基数(str/Decimal 皆可)。

    返回 {"fields": [有序字段行...], "net_tax_due": str}。net_tax_due 是本期净应缴(line 13,
    正=应缴/负=留抵),与 compute 的 tax_due 同源同值(销项 − 进项,本期无上期留抵抵减)。
    """
    sales = _dec(sales_amount)
    out_vat = _dec(output_vat)
    purchase = _dec(purchase_amount)
    in_vat = _dec(input_vat)

    sales_taxable = sales  # = line1 − 0%销售 − 免税销售,本期后两项为 0
    tax_before_carry = out_vat - in_vat
    tax_payable = tax_before_carry if tax_before_carry > _ZERO else _ZERO
    tax_overpaid = -tax_before_carry if tax_before_carry < _ZERO else _ZERO
    prior_carry = _ZERO  # 上期留抵抵减:M1 不支持跨期账,诚实置 0
    net_tax_due = tax_before_carry - prior_carry  # 本期净应缴(带符号,负=留抵)
    surcharge = _ZERO
    penalty = _ZERO
    total_payable = (net_tax_due if net_tax_due > _ZERO else _ZERO) + surcharge + penalty

    fields = [
        _field("1", "sales_total", "ยอดขายในเดือนนี้", "本月销售额", sales, SRC_RECONCILE),
        _field(
            "2",
            "sales_zero_rated",
            "ยอดขายที่เสียภาษีอัตราร้อยละ 0",
            "0% 税率销售额",
            _ZERO,
            SRC_NO_SOURCE_M1,
        ),
        _field("3", "sales_exempt", "ยอดขายที่ได้รับยกเว้น", "免税销售额", _ZERO, SRC_NO_SOURCE_M1),
        _field(
            "4", "sales_taxable", "ยอดขายที่ต้องเสียภาษี", "应税销售额", sales_taxable, SRC_DERIVED
        ),
        _field("5", "output_vat", "ภาษีขายเดือนนี้", "本月销项税", out_vat, SRC_RECONCILE),
        _field(
            "6",
            "purchase_creditable",
            "ยอดซื้อที่มีสิทธินำภาษีซื้อมาหักได้",
            "可抵扣采购额",
            purchase,
            SRC_RECONCILE,
        ),
        _field("7", "input_vat", "ภาษีซื้อเดือนนี้", "本月进项税", in_vat, SRC_RECONCILE),
        _field(
            "8", "tax_payable", "ภาษีที่ต้องชำระเดือนนี้", "本月应缴税额", tax_payable, SRC_DERIVED
        ),
        _field(
            "9",
            "tax_overpaid",
            "ภาษีที่ชำระเกินเดือนนี้",
            "本月超缴税额",
            tax_overpaid,
            SRC_DERIVED,
        ),
        _field(
            "12",
            "prior_credit",
            "ภาษีที่ชำระเกินยกมา",
            "上期留抵抵减",
            prior_carry,
            SRC_NO_SOURCE_M1,
        ),
        _field(
            "13",
            "net_tax_due",
            "ภาษีสุทธิที่ต้องชำระ/ชำระเกิน",
            "本期净应缴税额",
            net_tax_due,
            SRC_DERIVED,
        ),
        _field("15", "surcharge", "เงินเพิ่ม", "加算金", surcharge, SRC_NO_SOURCE_M1),
        _field("16", "penalty", "ค่าปรับ", "罚金", penalty, SRC_NO_SOURCE_M1),
        _field(
            "17",
            "total_payable",
            "รวมภาษีที่ต้องชำระทั้งสิ้น",
            "合计应缴",
            total_payable,
            SRC_DERIVED,
        ),
    ]
    return {"fields": fields, "net_tax_due": str(net_tax_due)}


def amounts(form: dict) -> dict:
    """把 build() 的字段行折成 {key: amount(str)} 便于快照对比/断言。"""
    return {f["key"]: f["amount"] for f in form["fields"]}
