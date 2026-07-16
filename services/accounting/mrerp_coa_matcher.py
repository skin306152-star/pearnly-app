# -*- coding: utf-8 -*-
"""MR.ERP 科目(从 GL 标题行提取)→ coa_preset 桥自动建议(T4b-SM · 确定性纯函数 · 不用 LLM)。

从 MR.ERP 分类账标题行拿到的科目(扁平码 1111-01 + 泰文名)按泰文科目名精确命中 coa_preset 的
name_th,产出 coa_erp_bridge 可 upsert 的桥行(erp_type='mrerp'、erp_code=扁平码、match_source=
'auto')。命不中的科目如实进未映射清单交会计补,绝不臆造对应(状态诚实)。

与 express_coa_matcher 分立而非泛化,理由:① 科目码语义不同——Express 四段码 `11-05-04-00` 末段
00 是汇总头(建桥让位给叶子),MR.ERP 扁平码 `3200-00`(กำไรสะสม)本身就是过账叶子,无汇总头
概念,套 Express 的 leaf-preference 会误伤;② 科目来源不同——Express 从 DBF 科目表(ACCNUM/
ACCNAM/ACCTYP),MR.ERP 从 GL 标题行提取(码+名,无类型)。两者匹配核心虽同源,但发散点真实
存在,合并进单一带参函数反而给已上线的 Express 高敏路径增加回归面,收益仅省数十行稳定纯逻辑,
不划算(rule of three:出现第三套 ERP 再抽公共核心)。

匹配键是规范化泰文名;preset 各码名互异,精确名命中天然无歧义。同名多码 = 真歧义(MR.ERP 无
汇总头可让位),如实进 conflicts 交人裁,不随便挑一个。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from services.accounting import coa_preset

ERP_TYPE = "mrerp"

_ZERO_WIDTH = ("​", "﻿", "\xa0")

# 规范化泰文名 → coa_code(preset 各码名互异,精确命中零歧义)
_NAME_TO_COA = {
    " ".join(name_th.split()): code
    for code, _name_zh, name_th, _acct_type in coa_preset.PRESET_ACCOUNTS
}


def _norm_th(name: str) -> str:
    """泰文科目名规范化:去零宽/不换行空格、折叠内部空白、去首尾。精确命中的比较口径。"""
    s = (name or "").strip()
    for z in _ZERO_WIDTH:
        s = s.replace(z, "")
    return " ".join(s.split())


@dataclass(frozen=True)
class MrerpAccount:
    """一条 MR.ERP 科目。code=扁平码(1111-01),name_th=科目名(从 GL 标题行提取)。"""

    code: str
    name_th: str

    @classmethod
    def from_title(cls, row: dict) -> "MrerpAccount":
        """{code, name_th}(iter_account_titles 输出)或含大写键的原始行 → MrerpAccount。"""
        get = lambda *ks: next(
            (str(row[k]).strip() for k in ks if row.get(k) not in (None, "")), ""
        )
        return cls(code=get("code", "ACCNUM"), name_th=get("name_th", "ACCNAM"))


def _bridge_row(coa_code: str, acc: MrerpAccount) -> dict:
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
    """建桥器输出。suggestions=可 upsert 桥行;unmapped=名未命中;conflicts=同名多码歧义。"""

    total_accounts: int = 0
    suggestions: list[dict] = field(default_factory=list)
    unmapped: list[dict] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)

    def bridge_map(self) -> dict[str, str]:
        """{coa_code: erp_code} · 直接喂 reconcile_gl 的 bridge 参数。"""
        return {s["coa_code"]: s["erp_code"] for s in self.suggestions}

    def coverage(self) -> dict:
        """覆盖率报告:命中/未映射/歧义计数 + 命中率。"""
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
    """MR.ERP 科目行(MrerpAccount 或 dict)→ 建桥建议。纯确定性,命不中不臆造。

    每科目按规范化泰文名精确命中 preset;命中的按 coa_code 归组:唯一科目直接建议,同名多码
    进 conflicts 交人裁(MR.ERP 扁平码无汇总头,不做 leaf 挑选)。命不中进 unmapped。
    """
    accounts = [r if isinstance(r, MrerpAccount) else MrerpAccount.from_title(r) for r in rows]
    result = CoaMatchResult(total_accounts=len(accounts))
    by_coa: dict[str, list[MrerpAccount]] = {}

    for acc in accounts:
        coa = _NAME_TO_COA.get(_norm_th(acc.name_th))
        if not coa:
            result.unmapped.append({"erp_code": acc.code, "erp_name": acc.name_th})
            continue
        by_coa.setdefault(coa, []).append(acc)

    for coa, group in by_coa.items():
        if len(group) == 1:
            result.suggestions.append(_bridge_row(coa, group[0]))
        else:
            result.conflicts.append(
                {
                    "coa_code": coa,
                    "candidates": [{"erp_code": a.code, "erp_name": a.name_th} for a in group],
                }
            )
    return result
