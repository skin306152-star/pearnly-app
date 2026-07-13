# -*- coding: utf-8 -*-
"""月度报表(BS/PL/TB)→ services.fileconv 引擎的 Table/ConvertResult 适配(N1 P0-3)。

数据源是 services/workorder/api.py::order_detail() 已经算好并对外暴露的 financials
字段(reconcile R6 的只读投影,见该函数顶注)——本模块只做形状转换 + 渲染成三张
K2 引擎认识的表,一个钱字段都不重算,不导入 services.workorder 的任何内部实现
(路由层已经用公开的 order_detail() 取到 fin dict 再传进来)。

守恒判定不是本模块重新算的——直接读 fin 里现成的 balanced 布尔(bs/tb 各自的
"资产=负债+权益""借=贷"校验早在 reconcile 阶段做过),不平时补一条 Issue 让
ConvertResult.conserved 如实变 False,PDF/Excel 的"不平"戳跟着诚实。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from services.fileconv.model import STATUS_OK, ConvertResult, Issue, Table
from services.fileconv.model import FINANCIALS_REPORT as _DOC_TYPE

# 不落在任何真实数据行范围内的哨兵行号——不平警示只需要计入 conserved/戳文案,
# 不该让 pdf_out 的行高亮机制误把某一行数字标黄(那是留给"哪一行不平"的场景,
# BS/TB 的不平是整表级结论,没有单一行号可指)。
_NO_ROW = 1_000_000

# bs/pl 表头四语完全相同(分类/科目/金额),共享同一份;消费侧(_h)只读不改。
_BSPL_HEADERS = {
    "zh": ["分类", "科目", "金额"],
    "th": ["หมวด", "บัญชี", "จำนวนเงิน"],
    "en": ["Section", "Account", "Amount"],
    "ja": ["区分", "科目", "金額"],
}

_HEADERS = {
    "bs": _BSPL_HEADERS,
    "pl": _BSPL_HEADERS,
    "tb": {
        "zh": ["科目", "借方", "贷方"],
        "th": ["บัญชี", "เดบิต", "เครดิต"],
        "en": ["Account", "Debit", "Credit"],
        "ja": ["科目", "借方", "貸方"],
    },
}

_SECTION_LABEL = {
    "assets": {"zh": "资产", "th": "สินทรัพย์", "en": "Assets", "ja": "資産"},
    "liabilities": {"zh": "负债", "th": "หนี้สิน", "en": "Liabilities", "ja": "負債"},
    "equity": {"zh": "权益", "th": "ส่วนของเจ้าของ", "en": "Equity", "ja": "純資産"},
    "revenue": {"zh": "收入", "th": "รายได้", "en": "Revenue", "ja": "収益"},
    "expense": {"zh": "费用", "th": "ค่าใช้จ่าย", "en": "Expense", "ja": "費用"},
}

_TABLE_NAME = {
    "bs": {
        "zh": "资产负债表",
        "th": "งบดุล",
        "en": "Balance Sheet",
        "ja": "貸借対照表",
    },
    "pl": {
        "zh": "损益表",
        "th": "งบกำไรขาดทุน",
        "en": "Profit & Loss",
        "ja": "損益計算書",
    },
    "tb": {
        "zh": "试算平衡表",
        "th": "งบทดลอง",
        "en": "Trial Balance",
        "ja": "試算表",
    },
}

_TOTAL_LABEL = {
    "zh": "合计",
    "th": "รวม",
    "en": "Total",
    "ja": "合計",
}

_CURRENT_EARNINGS_LABEL = {
    "zh": "本期损益(计入权益)",
    "th": "กำไร(ขาดทุน)งวดนี้ (รวมในส่วนของเจ้าของ)",
    "en": "Current period earnings (in equity)",
    "ja": "当期損益(純資産に算入)",
}


def _h(key: str, lang: str) -> list[str]:
    d = _HEADERS[key]
    return d.get(lang) or d["th"]


def _label(table: dict, key: str, lang: str) -> str:
    d = table[key]
    return d.get(lang) or d["th"]


def _dec(v: Any) -> Optional[Decimal]:
    if v in (None, ""):
        return None
    try:
        return Decimal(str(v))
    except InvalidOperation:
        return v


def _account_name(row: dict, lang: str) -> str:
    row = row or {}
    if lang == "th":
        return row.get("name_th") or row.get("name_zh") or row.get("code") or ""
    return row.get("name_zh") or row.get("name_th") or row.get("code") or ""


def _account_label(row: dict, lang: str) -> str:
    code = row.get("code")
    name = _account_name(row, lang)
    return f"{code} {name}".strip() if code else name


def _bs_rows(bs: dict, lang: str) -> list[list[Any]]:
    bs = bs or {}
    rows: list[list[Any]] = []
    for section in ("assets", "liabilities", "equity"):
        section_label = _label(_SECTION_LABEL, section, lang)
        for r in bs.get(section) or []:
            rows.append([section_label, _account_label(r, lang), _dec(r.get("amount"))])
        if section == "equity":
            rows.append(
                [
                    section_label,
                    _CURRENT_EARNINGS_LABEL.get(lang) or _CURRENT_EARNINGS_LABEL["th"],
                    _dec(bs.get("current_earnings")),
                ]
            )
    total = _TOTAL_LABEL.get(lang) or _TOTAL_LABEL["th"]
    rows.append([total, _label(_SECTION_LABEL, "assets", lang), _dec(bs.get("asset_total"))])
    rows.append(
        [total, _label(_SECTION_LABEL, "liabilities", lang), _dec(bs.get("liability_total"))]
    )
    rows.append([total, _label(_SECTION_LABEL, "equity", lang), _dec(bs.get("equity_total"))])
    return rows


def _pl_rows(pl: dict, lang: str) -> list[list[Any]]:
    pl = pl or {}
    rows: list[list[Any]] = []
    for section in ("revenue", "expense"):
        section_label = _label(_SECTION_LABEL, section, lang)
        for r in pl.get(section) or []:
            rows.append([section_label, _account_label(r, lang), _dec(r.get("amount"))])
    total = _TOTAL_LABEL.get(lang) or _TOTAL_LABEL["th"]
    rows.append([total, _label(_SECTION_LABEL, "revenue", lang), _dec(pl.get("revenue_total"))])
    rows.append([total, _label(_SECTION_LABEL, "expense", lang), _dec(pl.get("expense_total"))])
    rows.append([total, "-", _dec(pl.get("net_profit"))])
    return rows


def _tb_rows(tb: dict, lang: str) -> list[list[Any]]:
    tb = tb or {}
    rows = [
        [_account_label(r, lang), _dec(r.get("debit")), _dec(r.get("credit"))]
        for r in tb.get("rows") or []
    ]
    total = _TOTAL_LABEL.get(lang) or _TOTAL_LABEL["th"]
    rows.append([total, _dec(tb.get("debit")), _dec(tb.get("credit"))])
    return rows


def build_financials_convert_result(
    fin: dict, *, period: str, source_name: str, lang: str = "th"
) -> ConvertResult:
    """fin = order_detail()['financials'](r6_financials 只读投影)。source_name 建议带
    客户名(渲染到 PDF 页眉),period 只用于表名后缀,便于多期文件混在同一文件夹时肉眼分辨。
    """
    bs = fin.get("balance_sheet") or {}
    pl = fin.get("profit_loss") or {}
    tb = fin.get("trial_balance") or {}

    tables = [
        Table(
            name=f"{_label(_TABLE_NAME, 'bs', lang)} {period}",
            columns=_h("bs", lang),
            rows=_bs_rows(bs, lang),
        ),
        Table(
            name=f"{_label(_TABLE_NAME, 'pl', lang)} {period}",
            columns=_h("pl", lang),
            rows=_pl_rows(pl, lang),
        ),
        Table(
            name=f"{_label(_TABLE_NAME, 'tb', lang)} {period}",
            columns=_h("tb", lang),
            rows=_tb_rows(tb, lang),
        ),
    ]

    issues: list[Issue] = []
    if bs and bs.get("balanced") is False:
        issues.append(
            Issue(
                kind="bs_unbalanced",
                line_no=_NO_ROW,
                message="Balance sheet does not balance (assets ≠ liabilities + equity)",
                expected="0",
                actual=str(bs.get("diff")),
            )
        )
    if tb and tb.get("balanced") is False:
        issues.append(
            Issue(
                kind="tb_unbalanced",
                line_no=_NO_ROW,
                message="Trial balance does not balance (debit ≠ credit)",
                expected="0",
                actual=str(tb.get("diff")),
            )
        )

    return ConvertResult(
        doc_type=_DOC_TYPE,
        status=STATUS_OK,
        source_name=source_name,
        tables=tables,
        issues=issues,
        stats={"period": period},
    )
