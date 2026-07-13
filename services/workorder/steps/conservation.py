# -*- coding: utf-8 -*-
"""料件守恒纯闸(package 步的出包前置门 · 任务包 §5 步 6 的 fail-closed 收尾)。

每件 item 按 status + kind + 最新人工裁决,分进 7 个互斥终态桶。核心不变式:Σ桶 == N
且每件恰落一桶——落不进任何明确终态的畸形件一律 fail-closed 归「待裁决」,绝不静默放过。
根治 G1R2 黑洞:sales_direction_unhandled 这类 kind=unknown 的方向票过去既不进 R1、又不
被出包闸拦,无裁决照样出包;守恒闸在出包前把「每件是否都有明确去向」问死。

零副作用、不碰 store/DB、不算钱:只回答终态归属。钱的合计/试算是 reconcile 的活,本闸
不重算(与 reconcile_gates 一样是可脱库单测的纯算法层)。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from services.workorder import decisions, kinds

# 终态桶键。BUCKET_ORDER 固定顺序,给确定性输出(利于快照/诊断复核)。
INPUT_COUNTED = "input_counted"  # 已计入进项(purchase_invoice ok/裁决保留,或方向票裁进项)
SALES_MATERIAL = "sales_material"  # 销项材料(sales_summary 直读/人工申报,已就绪)
BANK = "bank"  # 佐证件(银行流水 + GL 上传件:只供佐证层消费,不进税额)
EXCLUDED = "excluded"  # 排除(non_tax·duplicate·exclude 裁决·方向票裁非税)
SALES_REASSIGNED = "sales_reassigned"  # 改判销项(方向票裁 assign_sales:票面不进 R1,归销项侧)
PENDING = "pending_decision"  # 待裁决(fail-closed 兜底:无明确终态一律落此,出包被拦)
WAIVED = "waived"  # 已豁免(人工 waive:带 reason 显式放行,出包但交付物留痕)

BUCKET_ORDER = (
    INPUT_COUNTED,
    SALES_MATERIAL,
    BANK,
    EXCLUDED,
    SALES_REASSIGNED,
    WAIVED,
    PENDING,
)

_KEEP_DECISIONS = (decisions.FACE_VALUE, decisions.RECALC)  # 保留进合计的金额裁决

# item.kind 取值(与裁决动词分属两套命名空间 · 单一事实源 kinds.py)。
_KIND_PURCHASE = kinds.PURCHASE_INVOICE
_KIND_SALES = kinds.SALES_SUMMARY
_KIND_BANK = kinds.BANK_STATEMENT
_KIND_GL = kinds.GL_LEDGER
_KIND_NON_TAX = kinds.NON_TAX
_KIND_DUPLICATE = kinds.DUPLICATE
_KIND_UNKNOWN = kinds.UNKNOWN

# 方向票 assign_kind 裁定 kind → 终态桶。裁进项计入 R1、裁销项归销项侧、裁非税排除;
# 裁定 kind 非法(不在表内)→ _bucket_of 兜底 PENDING。
_ASSIGN_BUCKET = {
    decisions.PURCHASE_INVOICE: INPUT_COUNTED,
    decisions.SALES_DOC: SALES_REASSIGNED,
    decisions.NON_TAX: EXCLUDED,
}


@dataclass(frozen=True)
class Conservation:
    """守恒归堆结果。buckets 是 {桶键: [item,...]} 的完整划分(每件恰在一桶)。"""

    buckets: dict

    @property
    def pending(self) -> list:
        return self.buckets.get(PENDING, [])

    @property
    def total(self) -> int:
        return sum(len(v) for v in self.buckets.values())

    def conserved(self, n: int) -> bool:
        """守恒成立:待裁决为空 且 Σ桶 == N(每件都有明确去向)。"""
        return not self.pending and self.total == n


def _is_direction(kind: str, flag_reason: str) -> bool:
    return kind == _KIND_UNKNOWN and flag_reason.startswith(decisions.DIRECTION_PREFIXES)


def _bucket_of(item: dict, dec: dict | None) -> str:
    """单件终态归属。fail-closed:任何未落进明确终态的形态一律归 PENDING(待裁决)。"""
    decision = (dec or {}).get("decision")
    if decision == decisions.WAIVE:  # 豁免是显式人工放行,优先级高于其余判据
        return WAIVED

    kind = item.get("kind")
    flag_reason = str(item.get("flag_reason") or "")

    if _is_direction(kind, flag_reason):
        if decision == decisions.ASSIGN_KIND:
            return _ASSIGN_BUCKET.get((dec or {}).get("kind"), PENDING)
        return PENDING  # 方向票无 assign_kind 裁决 → 待裁决

    if kind == decisions.SALES_DOC:
        # 自动判本方销项票(MC1-c.1):佐证材料,不进 R1。人工可 assign_kind 改判(拍错票兜底);
        # 改判走 _ASSIGN_BUCKET(进项→计入 / 销项→归销项侧 / 非税→排除)。flagged 且无裁决 →
        # 待人工过目(拍板① 留一次触碰,配 MC1-b 批量确认);status=ok(MC1-c.2 放宽后)免裁归销项侧。
        if decision == decisions.ASSIGN_KIND:
            return _ASSIGN_BUCKET.get((dec or {}).get("kind"), PENDING)
        if item.get("status") == "ok":
            return SALES_REASSIGNED
        return PENDING

    if kind == _KIND_PURCHASE:
        status = item.get("status")
        if status == "ok":
            return INPUT_COUNTED
        if status == "flagged":
            if decision in _KEEP_DECISIONS:
                return INPUT_COUNTED
            if decision == decisions.EXCLUDE:
                return EXCLUDED
            return PENDING  # flagged 进项无裁决 → 待裁决(与 reconcile R1 同口径)
        if status == "excluded":
            return EXCLUDED
        return PENDING

    if kind == _KIND_SALES:
        return SALES_MATERIAL if item.get("status") == "ok" else PENDING

    if kind in (_KIND_BANK, _KIND_GL):
        # GL 上传件与银行件同型:佐证材料,不进税额、不需裁决,归佐证桶(T4a)。
        return BANK

    if kind in (_KIND_NON_TAX, _KIND_DUPLICATE):
        return EXCLUDED if item.get("status") == "excluded" else PENDING

    return PENDING  # kind=unknown 非方向类 / pending / 任何未知形态 → fail-closed


def bucket_items(items: list[dict], decisions: dict) -> Conservation:
    """把每件按终态归堆。decisions = {item_id: 最新 human_decision payload}(latest-wins,
    与 reconcile 回放同源)。返回完整划分——不变式:Σ桶 == len(items),每件恰一桶。"""
    buckets: dict = {b: [] for b in BUCKET_ORDER}
    for item in items:
        buckets[_bucket_of(item, decisions.get(item["id"]))].append(item)
    return Conservation(buckets=buckets)


def stuck_reasons(cons: Conservation, n: int) -> list[str]:
    """守恒违例 → 逐件点名的停机原因(沿用停机点名范式)。待裁决件逐张点名;若 Σ桶≠N
    (划分逻辑本身出错的防御性兜底)追加一条守恒违例。守恒成立则返回空列表。"""
    if cons.conserved(n):
        return []
    reasons = [_pending_reason(it) for it in cons.pending]
    if cons.total != n:
        reasons.append(f"conservation_violation: Σ桶={cons.total} ≠ 料件数={n}(划分未覆盖全部件)")
    return reasons


def _pending_reason(item: dict) -> str:
    name = Path(item.get("file_ref") or "").name or item.get("id") or "?"
    flag = item.get("flag_reason") or "-"
    return f"{name}: 待裁决(kind={item.get('kind')}/flag_reason={flag})— 未裁决未豁免,不出包"
