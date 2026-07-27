# -*- coding: utf-8 -*-
"""账簿上印哪个科目码 —— 三条路都要走得通,且表头要如实写用的是哪一套。

出这个模块的直接原因:同类工作簿的金标把银行记成 1010(本仓 1010 是现金)、把销项税记成
2010(本仓 2010 是应付账款)。照抄 = 把转账记成现金、把销项税记成应付账款,不是舍入误差,
是记错账。而且 coa_preset 那 27 个码本身也不是客户账套的真码。

于是三条路:
  ① 桥接了且映到了  → 印客户账套的真码(coa_erp_bridge.erp_code)
  ② 桥接了但这个角色没映到 → 退回 preset 码,并把该角色列进 unresolved 交会计裁
  ③ 桥根本没接      → 全退 preset 码,表头明写「未接账套 · 科目码待确认」

宁可标出来让她改,也绝不静默印一个她账套里不存在的码。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Tuple

from services.accounting import coa_preset

ROLE_CASH = "cash"
ROLE_BANK = "bank"
ROLE_REVENUE = "sales_revenue"
ROLE_OUTPUT_VAT = "output_vat"

# 销售票四表用到的全部角色。加配方时在自己的模块里声明自己要哪些角色,不改这里。
SALES_ROLES: Tuple[str, ...] = (ROLE_CASH, ROLE_BANK, ROLE_REVENUE, ROLE_OUTPUT_VAT)

SOURCE_BRIDGE = "bridge"  # 全部角色都取到客户账套真码
SOURCE_PARTIAL = "partial"  # 桥接了,但有角色没映到
SOURCE_PRESET = "preset"  # 桥没接

_PRESET_BY_CODE = {code: (zh, th, kind) for code, zh, th, kind in coa_preset.PRESET_ACCOUNTS}

# 借方常余额的科目类型 —— 分类账的余额列按科目常余额方向标注,不靠科目码前缀猜。
_DEBIT_NORMAL_TYPES = ("asset", "expense")

_BANNER_PRESET = (
    "ผังบัญชีมาตรฐาน · ยังไม่ได้เชื่อมกับชุดบัญชีของลูกค้า · "
    "รหัสบัญชีรอการยืนยัน (通用科目表 · 未接账套 · 科目码待确认)"
)
_BANNER_BRIDGE = "รหัสบัญชีจากชุดบัญชีของลูกค้า ({erp}) (客户账套真码)"
_BANNER_PARTIAL = (
    "รหัสบัญชีจากชุดบัญชีของลูกค้า ({erp}) · ยังจับคู่ไม่ได้: {missing} — "
    "ใช้รหัสมาตรฐานชั่วคราว รอผู้ทำบัญชีตัดสิน (未映到的科目已退回通用码 · 待会计裁定)"
)


@dataclass(frozen=True)
class AccountRef:
    """账簿上的一个科目。code 可能是 preset 码也可能是账套真码,由 source 说清楚。"""

    role: str
    code: str
    name_th: str
    name_zh: str
    acct_type: str
    source: str

    @property
    def label(self) -> str:
        """账簿里科目那一格的文本 —— 码和名一起印,会计不必回头查码表。"""
        return f"{self.code} {self.name_th}".strip()

    @property
    def debit_normal(self) -> bool:
        return self.acct_type in _DEBIT_NORMAL_TYPES


@dataclass(frozen=True)
class ChartResolution:
    """一次科目解析的完整结果。banner 是要印在每张表第二行的那句话。"""

    accounts: Mapping[str, AccountRef]
    source: str
    unresolved: Tuple[str, ...]
    erp_type: str

    def of(self, role: str) -> AccountRef:
        return self.accounts[role]

    @property
    def banner(self) -> str:
        if self.source == SOURCE_PRESET:
            return _BANNER_PRESET
        missing = " / ".join(self.accounts[r].label for r in self.unresolved)
        if self.source == SOURCE_PARTIAL:
            return _BANNER_PARTIAL.format(erp=self.erp_type or "-", missing=missing)
        return _BANNER_BRIDGE.format(erp=self.erp_type or "-")


def _preset_ref(role: str) -> AccountRef:
    code = coa_preset.ROLE_DEFAULTS[role]
    name_zh, name_th, acct_type = _PRESET_BY_CODE[code]
    return AccountRef(
        role=role,
        code=code,
        name_th=name_th,
        name_zh=name_zh,
        acct_type=acct_type,
        source=SOURCE_PRESET,
    )


def resolve_chart(
    *,
    bridge: Optional[Mapping[str, str]] = None,
    bridge_names: Optional[Mapping[str, str]] = None,
    roles: Sequence[str] = SALES_ROLES,
    erp_type: str = "",
) -> ChartResolution:
    """角色 → 印在账簿上的科目。

    bridge 是 services.accounting.bridge_store.load_bridge 的返回值({preset码: 账套真码}),
    bridge_names 可选给真码对应的账套科目名(桥行的 erp_name)。桥空/None = 没接账套。
    """
    unknown = [r for r in roles if r not in coa_preset.ROLE_DEFAULTS]
    if unknown:
        raise KeyError(f"未知科目角色: {unknown}")

    refs = {r: _preset_ref(r) for r in roles}
    if not bridge:
        return ChartResolution(
            accounts=refs, source=SOURCE_PRESET, unresolved=(), erp_type=erp_type
        )

    missing = []
    for role in roles:
        preset = refs[role]
        erp_code = str(bridge.get(preset.code) or "").strip()
        if not erp_code:
            missing.append(role)
            continue
        name_th = str((bridge_names or {}).get(preset.code) or "").strip() or preset.name_th
        refs[role] = AccountRef(
            role=role,
            code=erp_code,
            name_th=name_th,
            name_zh=preset.name_zh,
            acct_type=preset.acct_type,
            source=SOURCE_BRIDGE,
        )
    return ChartResolution(
        accounts=refs,
        source=SOURCE_PARTIAL if missing else SOURCE_BRIDGE,
        unresolved=tuple(missing),
        erp_type=erp_type,
    )
