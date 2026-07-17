# -*- coding: utf-8 -*-
"""确定性读数解歧:票面三数(净/税/含税)内部不自洽时,用有限「混淆数字替换」反解唯一自洽建议值。

零 AI 成本、纯 Decimal、零副作用。动机见 J 闸实锤:针打票的 9 顶弧印淡被 OCR 读成 0,票面
净+税≠含税(IMG_2647:税 4060.05 实为 4069.05、含税 62108.40 实为 62198.40,净随之从 58048.40
反解回 58129.35)。这类错读可由两条恒等式反锁:净+税=含税 且 净×7%≈税——三数被钉成一个自由度,
把错读位替换回真数即自洽。

净不参与替换:它是被两条恒等式钉死的因变量(净=含税−税),故只对税/含税各做有限混淆替换、
反解净、再验 7% 恒等式。这样 OCR 把净读错(哪怕整段错)也不影响结果——净的真值由税/含税推出。

建议永不落库:本模块只产出「建议值」,采不采由人工改数裁决端点定(钱路径一分不改)。宁缺勿滥:
仅当存在「改动位数最少且唯一」的自洽解才出建议;多解或无解一律不出,不把猜测当答案误导会计。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from itertools import combinations, product
from typing import Optional

from services.workorder.steps.reconcile_gates import STANDARD_VAT_RATE, ZERO

# |净×7%−税| 容差:票面税=round(净×7%, 2),理论残差 ≤0.005;留 0.02 兜双侧二次舍入,与
# reconcile_gates 的申报口径一致(该值不放宽判定,只作解歧候选的自洽性门槛)。
RATE_TOL = Decimal("0.02")

# 单个数至多纠正的错读位数。真针打错读通常 1 位(IMG_2647 税/含税各 1 位);放到 2 位仍属
# 「宁缺勿滥」的极小改动量,再多即从纠错滑向猜数,故设硬上限。
MAX_FLIPS_PER_NUMBER = 2

# 确定性错读对(单一事实源)。只收 9↔0:针打/热敏印淡时 9 的右上弧丢失被读成 0(反之亦然),
# 是 J 闸实锤的唯一失效模式。刻意不扩表(8↔0/6↔8 等):任意两个「单区段」替换要同时闭合
# 净×7%=税,需含税增量≈税增量×15.29,而单位替换的增量比恒为 10 的幂,永不等于 15.29——
# 故本配置下两个替换解不可能并存(无假阳性,见模块测试的存在性论证)。扩表会打破这条保证,
# 须有真样证据再逐对加,不预支。
_CONFUSABLE: dict[str, tuple[str, ...]] = {"0": ("9",), "9": ("0",)}


def _clean(value: object) -> str:
    """去千分位/空白,保留符号与小数点,得可逐字符替换的规范串。"""
    return str(value).replace(",", "").strip()


def _to_decimal(value: object) -> Optional[Decimal]:
    try:
        return Decimal(_clean(value))
    except (InvalidOperation, ValueError):
        return None


def _variants(num_str: str) -> dict[Decimal, int]:
    """某数的混淆替换变体 → {值: 最小改动位数}。含原值(0 位);至多 MAX_FLIPS_PER_NUMBER 位。

    只替换 _CONFUSABLE 命中的位;同一结果值经不同路径达到时保留最小位数(改动量优先级唯一)。
    """
    s = _clean(num_str)
    positions = [i for i, ch in enumerate(s) if ch in _CONFUSABLE]
    out: dict[Decimal, int] = {}

    def _record(text: str, cost: int) -> None:
        val = _to_decimal(text)
        if val is not None and (val not in out or cost < out[val]):
            out[val] = cost

    _record(s, 0)
    for k in range(1, min(MAX_FLIPS_PER_NUMBER, len(positions)) + 1):
        for combo in combinations(positions, k):
            for alts in product(*(_CONFUSABLE[s[i]] for i in combo)):
                chars = list(s)
                for pos, alt in zip(combo, alts):
                    chars[pos] = alt
                _record("".join(chars), k)
    return out


def _is_self_consistent(net: Decimal, vat: Decimal, grand: Decimal) -> bool:
    """票面自洽:净+税=含税(精确)且 净×7%≈税(容差内)。自洽票非解歧对象。"""
    if net + vat != grand:
        return False
    return (net * STANDARD_VAT_RATE - vat).copy_abs() <= RATE_TOL


def suggest(net: object, vat: object, grand: object) -> Optional[dict]:
    """票面三数 → 唯一自洽建议 {net, vat, grand}(Decimal)或 None。

    仅当票面不自洽(净+税≠含税)才解;自洽票直接放行(None)。候选:对税/含税各做混淆替换,
    净由 含税−税 反解;接受条件 净>0、税>0、|净×7%−税|≤RATE_TOL。取改动位数最少的自洽解,
    该最小解唯一 → 建议;并列(多解)或无解 → None。建议与原读数一致时也不出(无可改)。
    """
    n0, v0, g0 = _to_decimal(net), _to_decimal(vat), _to_decimal(grand)
    if n0 is None or v0 is None or g0 is None:
        return None
    # 自洽的定义是两条恒等式都成立。真料 IN26-00575 净+税=含税 却 净×7%≠税(净被读错但
    # 加总恰好抵平),只查加总会漏解——必须两条都过才算自洽、才放行。
    if _is_self_consistent(n0, v0, g0):
        return None

    accepted: dict[tuple, int] = {}
    for vat_val, vat_cost in _variants(vat).items():
        for grand_val, grand_cost in _variants(grand).items():
            net_val = grand_val - vat_val
            if net_val <= ZERO or vat_val <= ZERO:
                continue
            if (net_val * STANDARD_VAT_RATE - vat_val).copy_abs() > RATE_TOL:
                continue
            triple = (net_val, vat_val, grand_val)
            cost = vat_cost + grand_cost
            if triple not in accepted or cost < accepted[triple]:
                accepted[triple] = cost
    if not accepted:
        return None

    best_cost = min(accepted.values())
    winners = [t for t, c in accepted.items() if c == best_cost]
    if len(winners) != 1:
        return None
    net_val, vat_val, grand_val = winners[0]
    if (net_val, vat_val, grand_val) == (n0, v0, g0):
        return None
    return {"net": net_val, "vat": vat_val, "grand": grand_val}
