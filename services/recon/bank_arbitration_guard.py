# -*- coding: utf-8 -*-
"""services/recon/bank_arbitration_guard.py · 银行对账两法分歧守门(确定性)。

bank_recon_v2 的解析仲裁在「免费解析」与「Gemini 兜底」都出结果时,只比余额链自洽度
(_stmt_bad_ratio)谁低用谁 —— 但自洽 ≠ 正确(2026-06-29 BBL2645:Gemini 读出 −114万
内部首尾相扣、自洽度更低,被静默选中,真值其实 0.00)。

本守门补一层诚实:两法都拿到行、却在期初/期末上显著分歧时,不替用户静默选一个,而是
标记需人工复核(根因③「两法分歧差这么大却静默选一个」)。纯函数:不连模型、不读 IO。

★诚实边界:守门不判「谁对」(两法可能都错,如 BBL 真值 0.00 两法都没读对),只判
「两法对不上 → 别静默信」。判对错要回票面(见 eval ground_truth 的票面锚)。
"""

from __future__ import annotations

from typing import List, Optional

# 相对分歧阈:|a−b| / max(|a|,|b|) 超此比例算分歧(5% 吸收四舍五入/极小尾差)。
_REL_THRESHOLD = 0.05
# 绝对地板:差值 ≤ 此值(泰铢)不算分歧(避免对 0 附近的小额误报)。
_ABS_FLOOR = 1.0


def _diverges(a: float, b: float, rel: float, abs_floor: float) -> bool:
    if abs(a - b) <= abs_floor:
        return False
    # 一正一负(BBL:免费 +346万 vs Gemini −114万)→ 必分歧,不看比例。
    if (a < 0) != (b < 0):
        return True
    denom = max(abs(a), abs(b), 1.0)
    return abs(a - b) / denom > rel


def divergence_reasons(
    free_opening: Optional[float],
    free_closing: Optional[float],
    free_row_count: int,
    gemini_opening: Optional[float],
    gemini_closing: Optional[float],
    gemini_row_count: int,
    *,
    rel: float = _REL_THRESHOLD,
    abs_floor: float = _ABS_FLOOR,
) -> List[str]:
    """两法都出行、期初/期末显著分歧时返回原因列表(空=无分歧/无可比)。

    只在两法都拿到行(>0)时比 —— 一方为空是「兜底接管」不是「分歧」,不在此判。
    """
    if free_row_count <= 0 or gemini_row_count <= 0:
        return []

    reasons: List[str] = []
    for label, a, b in (
        ("期初", free_opening, gemini_opening),
        ("期末", free_closing, gemini_closing),
    ):
        if a is None or b is None:
            continue
        if _diverges(float(a), float(b), rel, abs_floor):
            reasons.append(f"{label}两法分歧:免费解析 {a} vs Gemini {b} — 需人工核票面")
    return reasons
