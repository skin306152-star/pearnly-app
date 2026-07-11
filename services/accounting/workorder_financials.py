# -*- coding: utf-8 -*-
"""工单影子底稿 → 月度报表(批次 G1a · 纯函数 · 零副作用 · 影子非第二账本)。

reconcile R5 影子底稿产出逐科目发生额(见 workorder_shadow_adapter),本模块把它喂进 books 的
注入式纯变换(general_ledger/trial_balance/financials 的 *_from_sums)出三张月度报表:资产负债表
(BS)/损益表(PL)/试算平衡(TB)。科目 acct_type 与中泰名走 coa_preset 预置表(单一事实源)。

架构护栏(与 F 一脉·拍板「影子非第二账本」):只 import books 变换层 + coa_preset,一行不写/
不读 journal_vouchers/journal_lines,不碰 accounting 模块 auto_post。报表是佐证不是税额来源,
不回流改动 pp30 任何数字。

四态诚实:AR/AP 账龄 + 折旧簿本期无独立数据源(需明细账+账期/固定资产簿)→ 显式 source=not_wired
降级「未接入」,绝不编 0 冒充真值。非预置码(学习记忆定死科目)无法按 acct_type 归类 → 收进
unclassified 如实上报,不硬塞进某类扭曲报表(宁可 BS 不平被看见,不静默吞)。

钱全 Decimal,呈现层才转定点串(与 shadow_adapter._fmt 同口径,不落 float)。
"""

from __future__ import annotations

from decimal import Decimal

from services.accounting import books, coa_preset

_ZERO = Decimal("0")

# code → (acct_type, name_zh, name_th):BS/PL 分类与呈现的单一事实源(预置科目表)。
_CODE_META = {
    code: (acct_type, name_zh, name_th)
    for code, name_zh, name_th, acct_type in coa_preset.PRESET_ACCOUNTS
}

# 本期无数据源的报表块(四态诚实降级)。source=not_wired 是机械可断言的诚实标记。
_AR_AP_AGING_NOT_WIRED = {
    "source": "not_wired",
    "status": "unavailable",
    "note": "应收/应付账龄需明细账 + 账期数据源,本期工单管线未接入 → 未接入(不编 0)",
}
_DEPRECIATION_NOT_WIRED = {
    "source": "not_wired",
    "status": "unavailable",
    "note": "折旧簿需固定资产台账,本期工单管线未接入 → 未接入(不编 0)",
}


def _fmt(value: Decimal) -> str:
    """Decimal → 定点字符串(不带科学计数),与 shadow_adapter._fmt 同口径。"""
    return format(value, "f")


def _ser(obj):
    """呈现层序列化:递归把 Decimal 转定点串,dict/list 原样递归(报表纯可 JSON)。"""
    if isinstance(obj, Decimal):
        return _fmt(obj)
    if isinstance(obj, dict):
        return {k: _ser(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_ser(v) for v in obj]
    return obj


def _sums_from_shadow_accounts(accounts: list[dict]) -> tuple[list, list]:
    """影子科目余额 → books 注入式变换要的 account_sums 行。

    影子是单期底稿、无期初 → opening_net=0;发生额直接取影子借/贷。acct_type 与中泰名走预置表;
    非预置码(学习记忆定死科目)无法归类 → 收进 unclassified 如实上报,不硬塞进某类。
    """
    sums, unclassified = [], []
    for a in accounts:
        code = a.get("code")
        debit = Decimal(str(a.get("debit") or "0"))
        credit = Decimal(str(a.get("credit") or "0"))
        meta = _CODE_META.get(code)
        if meta is None:
            unclassified.append(
                {
                    "code": code,
                    "name": a.get("name"),
                    "debit": _fmt(debit),
                    "credit": _fmt(credit),
                }
            )
            continue
        acct_type, name_zh, name_th = meta
        sums.append(
            {
                "id": code,
                "code": code,
                "name_zh": name_zh,
                "name_th": name_th,
                "acct_type": acct_type,
                "period_debit": debit,
                "period_credit": credit,
                "opening_net": _ZERO,
            }
        )
    return sums, unclassified


def build_financials(shadow_payload: dict, *, period: str | None = None) -> dict | None:
    """影子底稿 payload(reconcile gates.r5_shadow)→ BS/PL/TB 三张月度报表 payload。

    返回 None = 无可用影子科目余额(闸关 / 影子跳过残影),调用方据此不挂 r6_financials 键、
    不出 financials 交付物(闸关逐字节维持现状)。BS 会计恒等式(资产=负债+权益)、PL 净利润链、
    TB 借=贷 由 books 纯变换保证;本模块只装配 + 序列化 + 挂四态降级块。
    """
    accounts = shadow_payload.get("accounts")
    if not accounts or "trial_balance" not in shadow_payload:
        return None

    sums, unclassified = _sums_from_shadow_accounts(accounts)
    fin = books.financials_from_sums(sums, period)
    tb = books.trial_balance_from_sums(sums, period)
    bs = fin["balance_sheet"]
    pnl = fin["pnl"]
    bs_diff = bs["asset_total"] - (bs["liability_total"] + bs["equity_total"])

    return {
        "period": period,
        "balance_sheet": {
            "assets": _ser(bs["assets"]),
            "liabilities": _ser(bs["liabilities"]),
            "equity": _ser(bs["equity"]),
            "current_earnings": _fmt(bs["current_earnings"]),
            "asset_total": _fmt(bs["asset_total"]),
            "liability_total": _fmt(bs["liability_total"]),
            "equity_total": _fmt(bs["equity_total"]),
            "diff": _fmt(bs_diff.copy_abs()),
            "balanced": bool(bs["balanced"]),
        },
        "profit_loss": {
            "revenue": _ser(pnl["revenue"]),
            "expense": _ser(pnl["expense"]),
            "revenue_total": _fmt(pnl["revenue_total"]),
            "expense_total": _fmt(pnl["expense_total"]),
            "net_profit": _fmt(pnl["net_profit"]),
        },
        "trial_balance": {
            "rows": _ser(tb["rows"]),
            "debit": _fmt(tb["totals"]["debit"]),
            "credit": _fmt(tb["totals"]["credit"]),
            "balanced": bool(tb["balanced"]),
        },
        "ar_ap_aging": dict(_AR_AP_AGING_NOT_WIRED),
        "depreciation": dict(_DEPRECIATION_NOT_WIRED),
        "unclassified_accounts": unclassified,
    }
