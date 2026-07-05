# -*- coding: utf-8 -*-
"""同页多票(additional_invoices)专属 sanity(台账#6 · trap11 实案 2026-07-05)。

两个静默洞:① 附加票拆成独立入库条目却从不过 sanity,结构硬伤直通;
② 整片自洽三元组(小计/VAT/总额)被偷给另一张票时单票勾稽全平——唯一供出
真数的是本票明细行和。多票页把 sanity 规则 6 的单边收紧为双边(规则 7);
单票页不收紧,不误伤服务费/未列项票(行和 < 小计合法)。

evaluate_sanity 是唯一调用方(两条链共用单一挂点)。sanity.py 顶层导入本模块;
本模块反向导入 sanity 的共享件必须延迟到函数体内 —— sanity.py 顶层导入本模块时
本模块还在加载中,若本模块顶层回导 sanity 会在其未定义完时取值,故延迟到调用时。
"""

from __future__ import annotations

from typing import List


def multi_invoice_reasons(invoice) -> List[str]:
    from services.ocr.sanity import _core_reasons, _line_subtotals, _money, line_sum_mismatch

    extras = [
        x
        for x in (getattr(invoice, "additional_invoices", None) or [])
        if not getattr(x, "is_not_invoice", False)
    ]
    if not extras:
        return []

    reasons: List[str] = []
    for i, extra in enumerate(extras, start=2):
        reasons.extend(f"同页第{i}张: {r}" for r in _core_reasons(extra))
    # 规则 7:行和 ≠ 小计即转人工(单边规则 6 在多票页收紧为双边,见 line_sum_mismatch)。
    for i, inv in enumerate([invoice] + extras, start=1):
        sub = _money(getattr(inv, "subtotal", None))
        line_sum = line_sum_mismatch(sub, _line_subtotals(inv), symmetric=True)
        if line_sum is not None:
            reasons.append(
                f"同页第{i}张: 明细行和 {line_sum:.2f} ≠ 小计 {sub} — 多票页疑金额跨票错配"
            )
    return reasons
