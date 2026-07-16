# -*- coding: utf-8 -*-
"""Express 科目表(GLACC)→ coa_preset 桥自动建议(T4b · 确定性纯函数 · 不用 LLM)。

从客户 Express 科目表按泰文科目名精确命中 coa_preset 的 name_th,产出 coa_erp_bridge
可 upsert 的桥行(erp_type='express'、erp_code = Express 四段码、match_source='auto')。
命不中的科目如实进未映射清单交会计补,绝不臆造对应(状态诚实)。同名一对多(汇总头/明细)
取叶子科目——末段为 00 的汇总头让位给带发生额的明细,避免把发生额挂到头上;仍剩多个
叶子同名 = 真歧义,如实进 conflicts 交人裁,不随便挑一个。

匹配键是规范化泰文名;preset 26 码名各不相同,精确名命中天然无歧义。Express ACCTYP
编码在各套账不稳定,不作硬门(如实带出供会计复核),类型语义靠 preset 侧本身钉死。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from services.accounting import coa_preset

ERP_TYPE = "express"

_ZERO_WIDTH = ("​", "﻿", "\xa0")


def _norm_th(name: str) -> str:
    """泰文科目名规范化:去零宽/不换行空格、折叠内部空白、去首尾。精确命中的比较口径。"""
    s = (name or "").strip()
    for z in _ZERO_WIDTH:
        s = s.replace(z, "")
    return " ".join(s.split())


# 规范化泰文名 → coa_code(preset 26 码名各异,精确命中零歧义)
_NAME_TO_COA = {
    _norm_th(name_th): code for code, _name_zh, name_th, _acct_type in coa_preset.PRESET_ACCOUNTS
}


def _is_header_code(code: str) -> bool:
    """Express 四段码汇总头(末段 00)· 明细发生额挂在叶子而非头,建桥优先取叶子。"""
    return bool(code) and code.split("-")[-1] == "00"


@dataclass(frozen=True)
class ExpressAccount:
    """一条 Express 科目(GLACC)。code=ACCNUM 四段码,name_th=ACCNAM,acct_type=ACCTYP。"""

    code: str
    name_th: str
    acct_type: str = ""

    @classmethod
    def from_dbf(cls, row: dict) -> "ExpressAccount":
        """DBF/csv 原始行(大写字段名或已规范键)→ ExpressAccount。"""
        get = lambda *ks: next(
            (str(row[k]).strip() for k in ks if row.get(k) not in (None, "")), ""
        )
        return cls(
            code=get("ACCNUM", "code"),
            name_th=get("ACCNAM", "name_th"),
            acct_type=get("ACCTYP", "acct_type"),
        )


def _bridge_row(coa_code: str, acc: ExpressAccount) -> dict:
    """upsert_rows 可直吃的桥行(多带 confidence 供报告,upsert 忽略未知键)。"""
    return {
        "coa_code": coa_code,
        "erp_code": acc.code,
        "erp_name": acc.name_th,
        "match_source": "auto",
        "confidence": "high",
    }


@dataclass
class CoaMatchResult:
    """建桥器输出。suggestions=可 upsert 桥行;unmapped=名未命中;conflicts=同名多叶子歧义。"""

    total_accounts: int = 0
    suggestions: list[dict] = field(default_factory=list)
    unmapped: list[dict] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)

    def bridge_map(self) -> dict[str, str]:
        """{coa_code: erp_code} · 直接喂 reconcile_gl 的 bridge 参数。"""
        return {s["coa_code"]: s["erp_code"] for s in self.suggestions}

    def coverage(self) -> dict:
        """覆盖率报告:命中/未映射/歧义计数 + 命中率(汇总头被叶子吸收不计入分母噪声)。"""
        mapped = len(self.suggestions)
        ambiguous = sum(len(c["candidates"]) for c in self.conflicts)
        return {
            "total_accounts": self.total_accounts,
            "mapped": mapped,
            "unmapped": len(self.unmapped),
            "ambiguous_accounts": ambiguous,
            "conflict_groups": len(self.conflicts),
            "mapped_ratio": round(mapped / self.total_accounts, 4) if self.total_accounts else 0.0,
        }


def suggest_bridge(rows: list) -> CoaMatchResult:
    """GLACC 行(ExpressAccount 或 dict)→ 建桥建议。纯确定性,命不中不臆造。

    每科目按规范化泰文名精确命中 preset;命中的按 coa_code 归组:单科目直接建议;同名
    多科目取叶子(去汇总头)后仍唯一则建议,否则进 conflicts 交人裁。命不中进 unmapped。
    """
    accounts = [r if isinstance(r, ExpressAccount) else ExpressAccount.from_dbf(r) for r in rows]
    result = CoaMatchResult(total_accounts=len(accounts))
    by_coa: dict[str, list[ExpressAccount]] = {}

    for acc in accounts:
        coa = _NAME_TO_COA.get(_norm_th(acc.name_th))
        if not coa:
            result.unmapped.append(
                {"erp_code": acc.code, "erp_name": acc.name_th, "acct_type": acc.acct_type}
            )
            continue
        by_coa.setdefault(coa, []).append(acc)

    for coa, group in by_coa.items():
        chosen = group
        if len(group) > 1:
            leaves = [a for a in group if not _is_header_code(a.code)]
            chosen = leaves or group  # 全是汇总头则无叶子可取,保留整组交人裁
        if len(chosen) == 1:
            result.suggestions.append(_bridge_row(coa, chosen[0]))
        else:
            result.conflicts.append(
                {
                    "coa_code": coa,
                    "candidates": [{"erp_code": a.code, "erp_name": a.name_th} for a in chosen],
                }
            )
    return result
