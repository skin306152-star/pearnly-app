# -*- coding: utf-8 -*-
"""同页多票(additional_invoices)专属 sanity(台账#6 · trap11 实案 2026-07-05)。

两个静默洞:① 附加票拆成独立入库条目却从不过 sanity,结构硬伤直通;
② 整片自洽三元组(小计/VAT/总额)被偷给另一张票时单票勾稽全平——唯一供出
真数的是本票明细行和。多票页把 sanity 规则 6 的单边收紧为双边(规则 7);
单票页不收紧,不误伤服务费/未列项票(行和 < 小计合法)。

evaluate_sanity 是唯一调用方(两条链共用单一挂点);从 sanity 延迟导入本模块,
本模块顶层回导 sanity 的共享件 —— 单向延迟即无环。
"""

from __future__ import annotations

from typing import List


def multi_invoice_reasons(invoice) -> List[str]:
    from services.ocr.sanity import _RECON_REL, _TOL, _core_reasons, _line_subtotals, _money

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
    # 规则 7:行和 ≠ 小计即转人工(明细 ≥2 行才有判断力,单行自身可能读错)。
    for i, inv in enumerate([invoice] + extras, start=1):
        sub = _money(getattr(inv, "subtotal", None))
        lines = _line_subtotals(inv)
        if sub is not None and sub > 0 and len(lines) >= 2:
            line_sum = sum(lines)
            if abs(line_sum - sub) > max(_TOL, sub * _RECON_REL):
                reasons.append(
                    f"同页第{i}张: 明细行和 {line_sum:.2f} ≠ 小计 {sub} — 多票页疑金额跨票错配"
                )
    return reasons
