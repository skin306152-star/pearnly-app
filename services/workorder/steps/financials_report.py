# -*- coding: utf-8 -*-
"""月度报表交付物装配(批次 G1a · package 附加交付物 · 只渲染不重算)。

reconcile R6 已把影子科目余额过 books 纯变换算好 BS/PL/TB(见
services/accounting/workorder_financials),挂在 gates.r6_financials。本模块只把它渲染成人读的
markdown + 落数字快照,一个钱字段都不重算(与 _write_shadow / pnd_prep 同范式)。

生成条件:reconcile 挂了 r6_financials(闸 pearnly_ai_shadow_draft 开且影子科目余额在场)才出
这件交付物;闸关逐字节维持现状(build 返 {},package 不新增文件/交付物行)。

四态诚实:账龄/折旧块如实转述 r6 的 source=not_wired 降级文案,不冒充 0;呈现层期间以 compute
落的权威 period 为准(报表本体的 period 只是 reconcile 时的标签)。
"""

from __future__ import annotations

from pathlib import Path

KIND_FINANCIALS = "financials_report"


def build(out_dir: Path, numbers: dict) -> dict:
    """package 调用点:有 r6_financials 报表则出 {kind: (path, snapshot)},否则 {}(闸关无痕)。"""
    fin = (numbers.get("gates") or {}).get("r6_financials")
    if not isinstance(fin, dict) or "trial_balance" not in fin or "balance_sheet" not in fin:
        return {}
    return {KIND_FINANCIALS: _write(out_dir, fin, numbers)}


def _amt(v) -> str:
    return v if v not in (None, "") else "-"


def _section(title: str, rows: list[str]) -> list[str]:
    return [f"## {title}", "", *(rows or ["- (无)"]), ""]


def _amount_rows(items: list[dict]) -> list[str]:
    """[{code,name_zh,amount}] → markdown 表体;空则显式 (无),不留白。"""
    if not items:
        return ["- (无)"]
    rows = ["| บัญชี (科目) | จำนวนเงิน (金额) |", "|---|---|"]
    rows += [
        f"| {i.get('code')} {i.get('name_zh') or ''} | {_amt(i.get('amount'))} |" for i in items
    ]
    return rows


def _balance_sheet_lines(bs: dict) -> list[str]:
    balanced = "✔ สมดุล (平)" if bs.get("balanced") else "✘ ไม่สมดุล (不平)"
    return [
        *_section("สินทรัพย์ (资产)", _amount_rows(bs.get("assets"))),
        *_section("หนี้สิน (负债)", _amount_rows(bs.get("liabilities"))),
        *_section(
            "ส่วนของเจ้าของ (权益)",
            _amount_rows(bs.get("equity"))
            + [f"- กำไรสะสมงวดนี้ (本期累计净利): {_amt(bs.get('current_earnings'))}"],
        ),
        *_section(
            "สรุปงบดุล (资产负债表合计)",
            [
                f"รวมสินทรัพย์ (资产合计): {_amt(bs.get('asset_total'))}",
                f"รวมหนี้สิน (负债合计): {_amt(bs.get('liability_total'))}",
                f"รวมส่วนของเจ้าของ (权益合计): {_amt(bs.get('equity_total'))}",
                f"ผลต่าง (资产−负债−权益 差额): {_amt(bs.get('diff'))}",
                f"สถานะ (状态): {balanced}",
            ],
        ),
    ]


def _profit_loss_lines(pnl: dict) -> list[str]:
    return [
        *_section("รายได้ (收入)", _amount_rows(pnl.get("revenue"))),
        *_section("ค่าใช้จ่าย (费用)", _amount_rows(pnl.get("expense"))),
        *_section(
            "กำไรขาดทุน (损益合计)",
            [
                f"รวมรายได้ (收入合计): {_amt(pnl.get('revenue_total'))}",
                f"รวมค่าใช้จ่าย (费用合计): {_amt(pnl.get('expense_total'))}",
                f"กำไรสุทธิ (净利润 = 收入 − 费用): {_amt(pnl.get('net_profit'))}",
            ],
        ),
    ]


def _trial_balance_lines(tb: dict) -> list[str]:
    balanced = "✔ สมดุล (平)" if tb.get("balanced") else "✘ ไม่สมดุล (不平)"
    rows = tb.get("rows") or []
    table = ["- (无)"]
    if rows:
        table = ["| บัญชี (科目) | เดบิต (借) | เครดิต (贷) |", "|---|---|---|"]
        table += [
            f"| {r.get('code')} {r.get('name_zh') or ''} | {_amt(r.get('debit'))} | {_amt(r.get('credit'))} |"
            for r in rows
        ]
    return _section(
        "งบทดลอง (试算平衡)",
        table
        + [
            "",
            f"Σ เดบิต (借方合计): {_amt(tb.get('debit'))}",
            f"Σ เครดิต (贷方合计): {_amt(tb.get('credit'))}",
            f"สถานะ (状态): {balanced}",
        ],
    )


def _not_wired_lines(fin: dict) -> list[str]:
    """账龄/折旧四态降级:如实转述 not_wired,不编 0。"""
    lines = []
    for title, key in (
        ("อายุลูกหนี้/เจ้าหนี้ (应收/应付账龄)", "ar_ap_aging"),
        ("ค่าเสื่อมราคา (折旧)", "depreciation"),
    ):
        block = fin.get(key) or {}
        lines += _section(
            title,
            [f"สถานะ (状态): ยังไม่เชื่อมต่อ / not_wired — {block.get('note') or '未接入'}"],
        )
    return lines


def _write(out_dir: Path, fin: dict, numbers: dict) -> tuple[str, dict]:
    bs = fin.get("balance_sheet") or {}
    pnl = fin.get("profit_loss") or {}
    tb = fin.get("trial_balance") or {}
    period = numbers.get("period") or fin.get("period") or "-"
    lines = [
        "# งบการเงินรายเดือน (月度报表 · 影子底稿派生 · 内部核对用,非法定报表)",
        "",
        f"งวดที่ (期间): {period}",
        "",
        "# งบดุล (资产负债表 · BS)",
        "",
        *_balance_sheet_lines(bs),
        "# งบกำไรขาดทุน (损益表 · PL)",
        "",
        *_profit_loss_lines(pnl),
        *_trial_balance_lines(tb),
        *_not_wired_lines(fin),
    ]
    path = out_dir / "financials_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    snapshot = {
        "period": period,
        "bs_balanced": bool(bs.get("balanced")),
        "bs_diff": bs.get("diff"),
        "asset_total": bs.get("asset_total"),
        "liability_total": bs.get("liability_total"),
        "equity_total": bs.get("equity_total"),
        "net_profit": pnl.get("net_profit"),
        "tb_balanced": bool(tb.get("balanced")),
        "tb_debit": tb.get("debit"),
        "tb_credit": tb.get("credit"),
        "ar_ap_aging_source": (fin.get("ar_ap_aging") or {}).get("source"),
        "depreciation_source": (fin.get("depreciation") or {}).get("source"),
        "unclassified_count": len(fin.get("unclassified_accounts") or []),
    }
    return str(path), snapshot
