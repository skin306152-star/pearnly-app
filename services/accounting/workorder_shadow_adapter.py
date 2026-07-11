# -*- coding: utf-8 -*-
"""工单已裁票据 → 影子底稿适配器(批次 F1 · 纯函数 · 零副作用)。

reconcile 步 R1/R2 已把工单事件流的进项票裁成配平的分录金额({net,vat,grand},裁决全应用:
non_tax 已排除 / assign_kind 方向已归位 / recalc 已按修正税额反推基 / latest-wins),销项聚合成
sales_amount/output_vat。本模块把这两样喂进现成纯函数复式规则引擎 rules.build(一行不改),在内存
聚合成【建议分录 / 科目余额 / 试算平衡】三样影子底稿——影子只算不落法定表。

架构护栏(拍板 1 · 影子非第二账本):只 import rules + coa_preset,绝不碰 posting.py/vouchers.py,
一行不写 journal_vouchers/journal_lines。role→科目码走 coa_preset.ROLE_DEFAULTS 静态映射,无配的
expense:{category_id} 回落 expense_default 并标 category_unmapped。

数据来源单一事实源:采信 reconcile 已裁好的 r1["entries"]/r2 聚合,不回原始事件重算——方向裁决
(non_tax 排除 / assign_kind / latest-wins)由 resolve_input_vat 一处实现,影子继承其结论,不复制
一份易错的裁决逻辑。故 non_tax 件天然不入影子分录、方向裁决优先且后者胜,均由上游保证。

Decimal 全程,float 禁。金额反解工单已算好的数(不重算),与 rules.py 一致。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from services.accounting import coa_preset, rules

_ZERO = Decimal("0")
_TOL = Decimal("0.01")

# 科目码 → 中文名(建议分录/科目余额渲染用;role 经 ROLE_DEFAULTS 转码后按此取名)。
_CODE_TO_NAME = {code: name_zh for code, name_zh, _th, _t in coa_preset.PRESET_ACCOUNTS}
_EXPENSE_DEFAULT_CODE = coa_preset.ROLE_DEFAULTS["expense_default"]
_EXPENSE_ROLE_PREFIX = "expense:"


def _fmt(value: Decimal) -> str:
    """Decimal → 定点字符串(不带科学计数),与 recon 适配器 _fmt 同口径。"""
    return format(value, "f")


def _account_for_role(role: str, uncertainties: set[str]) -> str:
    """role → 预置科目码。expense:{category_id} 无静态配 → 回落 expense_default 并标 category_unmapped
    (如实反映"这笔费用没配到具体费用科目",不假装配上了)。"""
    code = coa_preset.ROLE_DEFAULTS.get(role)
    if code:
        return code
    if role.startswith(_EXPENSE_ROLE_PREFIX):
        uncertainties.add("category_unmapped")
        return _EXPENSE_DEFAULT_CODE
    # 未知 role 兜底进杂项费用,标不确定(引擎产出新 role 时不静默丢分录)。
    uncertainties.add("category_unmapped")
    return _EXPENSE_DEFAULT_CODE


@dataclass
class ShadowResult:
    """一次工单影子底稿(佐证层 · 挂 gates.r5_shadow · 不落法定表)。

    entries : 建议分录逐条(source/rule_key/dr_cr/科目码+名/金额/备注)。
    accounts: 科目余额(每科目借/贷发生额合计 + 净额)。
    trial_balance: 试算平衡(Σ借/Σ贷/差额/是否配平,容差 0.01)。
    sources : 每笔业务的规则命中 + 人话说明(rules.build 的 human_note)。
    uncertainties: 影子层置信扣分点(如 category_unmapped),去重排序。
    """

    entries: list[dict] = field(default_factory=list)
    accounts: list[dict] = field(default_factory=list)
    trial_balance: dict = field(default_factory=dict)
    sources: list[dict] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)

    def as_gate_payload(self) -> dict:
        """gates.r5_shadow / 交付物落库形态(纯可 JSON 序列化 dict)。"""
        return {
            "entries": self.entries,
            "accounts": self.accounts,
            "trial_balance": self.trial_balance,
            "sources": self.sources,
            "uncertainties": self.uncertainties,
            "entry_count": len(self.entries),
            "source_count": len(self.sources),
        }


def _purchase_ctx(net: Decimal, vat: Decimal, grand: Decimal, ref: str) -> dict:
    """一张进项票 → rules._purchase 期望的 ctx。line_total=净额但 product_id 缺(OCR 票面无行级
    商品/科目)→ 走费用桶回落 expense_default;借[净+进项税]=贷[应付],与 R4 试算同口径。"""
    return {
        "source_type": "purchase",
        "source_tier": "ocr",
        "doc_kind": "purchase_invoice",
        "amounts": {"grand_total": grand, "vat_amount": vat, "wht_amount": _ZERO},
        "lines": [
            {"item_type": "goods", "product_id": None, "line_total": net, "category_id": None}
        ],
        "ref": ref,
    }


def _sale_ctx(sales_amount: Decimal, output_vat: Decimal) -> dict:
    """聚合销项 → rules._sale 期望的 ctx(赊账口径:借 应收 = 贷 收入 + 销项税)。工单销项是聚合
    数(POS 直读/人工申报),不逐票——一条 source_type=sale 承载整期销项。"""
    return {
        "source_type": "sale",
        "source_tier": "first_party",
        "doc_kind": "tax_invoice",
        "amounts": {
            "grand_total": sales_amount + output_vat,
            "vat_amount": output_vat,
            "wht_amount": _ZERO,
            "paid_amount": _ZERO,
        },
        "paid_at_issue": False,
        "payment_method": None,
        "ref": "聚合销项",
    }


def _vat_closing_ctx(input_vat: Decimal, output_vat: Decimal, period: str | None) -> dict:
    """VAT 结转 → rules._vat_closing 期望的 ctx。让试算平衡收到应交/留抵,进项税/销项税科目
    经结转对冲归零(与月末 R9 真账口径一致)。"""
    return {
        "source_type": "vat_closing",
        "amounts": {"output_vat_total": output_vat, "input_vat_total": input_vat},
        "ref": period or "",
    }


def _emit(result: dict, source_label: str, accounts: dict, uncertainties: set[str]) -> list[dict]:
    """一条 rules.build 结果 → 影子分录行 + 科目余额累加。account_id 目标(学习记忆定死科目)
    直接用其码;role 目标经 ROLE_DEFAULTS 转码。金额 Decimal 累加,呈现层才转字符串。"""
    rows = []
    rule_key = result["rule_key"]
    for e in result["entries"]:
        amount = e["amount"]
        if amount <= _ZERO:
            continue
        code = e["account_id"] if e["account_id"] else _account_for_role(e["role"], uncertainties)
        bucket = accounts.setdefault(code, {"debit": _ZERO, "credit": _ZERO})
        bucket[e["dr_cr"]] += amount
        rows.append(
            {
                "source": source_label,
                "rule_key": rule_key,
                "dr_cr": e["dr_cr"],
                "account_code": code,
                "account_name": _CODE_TO_NAME.get(code, code),
                "amount": _fmt(amount),
                "memo": e.get("memo"),
            }
        )
    return rows


def build_shadow(
    *,
    purchase_entries: list[dict],
    sales_amount: Decimal,
    output_vat: Decimal,
    period: str | None = None,
) -> ShadowResult:
    """reconcile 已裁的进项分录金额 + 聚合销项 → 影子底稿三件套。

    purchase_entries: r1["entries"],逐张 {net, vat, grand}(裁决全应用后的票面反解值)。
    sales_amount/output_vat: r2 聚合销项净额 / 销项税。
    每张进项票 → R1 分录;聚合销项 → R4 分录;进/销项税 → R9 结转分录。科目按发生额聚合,
    末尾出试算平衡(Σ借=Σ贷,容差 0.01)。
    """
    accounts: dict = {}
    uncertainties: set[str] = set()
    entries: list[dict] = []
    sources: list[dict] = []
    input_vat_total = _ZERO

    for idx, ent in enumerate(purchase_entries, start=1):
        net, vat, grand = ent["net"], ent["vat"], ent["grand"]
        input_vat_total += vat
        label = f"进项票 #{idx}"
        result = rules.build(_purchase_ctx(net, vat, grand, label))
        if not result:
            continue
        entries.extend(_emit(result, label, accounts, uncertainties))
        uncertainties.update(result.get("uncertainties") or [])
        sources.append(
            {"label": label, "rule_key": result["rule_key"], "human_note": result["human_note"]}
        )

    if sales_amount + output_vat > _ZERO:
        result = rules.build(_sale_ctx(sales_amount, output_vat))
        if result:
            entries.extend(_emit(result, "聚合销项", accounts, uncertainties))
            sources.append(
                {
                    "label": "聚合销项",
                    "rule_key": result["rule_key"],
                    "human_note": result["human_note"],
                }
            )

    closing = rules.build(_vat_closing_ctx(input_vat_total, output_vat, period))
    if closing:
        entries.extend(_emit(closing, "VAT 结转", accounts, uncertainties))
        sources.append(
            {
                "label": "VAT 结转",
                "rule_key": closing["rule_key"],
                "human_note": closing["human_note"],
            }
        )

    account_rows = [
        {
            "code": code,
            "name": _CODE_TO_NAME.get(code, code),
            "debit": _fmt(b["debit"]),
            "credit": _fmt(b["credit"]),
            "balance": _fmt(b["debit"] - b["credit"]),
        }
        for code, b in sorted(accounts.items())
    ]
    total_debit = sum((b["debit"] for b in accounts.values()), _ZERO)
    total_credit = sum((b["credit"] for b in accounts.values()), _ZERO)
    diff = (total_debit - total_credit).copy_abs()

    return ShadowResult(
        entries=entries,
        accounts=account_rows,
        trial_balance={
            "debit": _fmt(total_debit),
            "credit": _fmt(total_credit),
            "diff": _fmt(diff),
            "balanced": diff <= _TOL,
        },
        sources=sources,
        uncertainties=sorted(uncertainties),
    )
