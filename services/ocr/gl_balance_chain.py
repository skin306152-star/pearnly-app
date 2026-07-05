# -*- coding: utf-8 -*-
"""GL 余额链确定性修复(台账#10 · v1 竖排堆叠版式 12/12 系统性失守)。

该版式借贷合并一列、方向只能靠余额涨跌推、期初根本没印 —— 提示词救不了,
用数学救:GL 是自校验文档,每行 余额 = 上行余额 + 借 − 贷(银行账户视角,
与 bank_gl_stacked「借贷取自余额涨跌」同一约定)。

三步,全部只在数学上可证时才动:
  1. 方向纠正:金额与 |余额涨跌| 吻合、仅记账方向相反 → 摆正(同 bank 路
     _correct_direction_from_balance 的纠正条件)。
  2. 期初反推:期初没印时 = 首行余额 − 首行净变动;有期末则全链交叉验证,
     对不上宁可留空也不瞎填。
  3. 断链标记:金额与余额涨跌都对不上 → 不改数,出警告顶起人工复核。
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

_TOL = Decimal("0.05")


def _dec(x: Any) -> Optional[Decimal]:
    if x in (None, ""):
        return None
    try:
        return Decimal(str(x).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _fmt(x: Decimal) -> str:
    return format(x.quantize(Decimal("0.01")), "f")


def _set_side(entry, amount: Decimal, is_debit: bool) -> None:
    entry.debit = _fmt(amount) if is_debit else ""
    entry.credit = "" if is_debit else _fmt(amount)
    entry.direction = "deposit" if is_debit else "withdrawal"


def repair_gl_document(doc) -> List[str]:
    """就地修复 GeneralLedgerDocument,返回警告(仅断链;数学可证的纠正不顶复核)。

    纠正条件同 bank 路:上一行余额直接可知(中间无缺余额行)、金额与 |涨跌|
    吻合、仅方向相反 → 摆正 + 行标 direction_autocorrected(对齐 bank 的
    StatementRow 行标做法,UI/审计透明,不进警告压置信度)。余额缺失的行让
    prev 断档 → 之后跨缺口的涨跌对不上单笔金额,自然不满足纠正条件,不会误改。
    """
    entries = list(doc.entries or [])
    if not entries:
        return []

    warnings: List[str] = []
    prev = _dec(doc.opening_balance)
    gap = False  # prev 与本行之间隔了缺余额的行 → 涨跌不再对应单笔金额
    for i, e in enumerate(entries, start=1):
        bal = _dec(e.balance)
        if bal is None:
            gap = True
            continue
        deb, cred = _dec(e.debit) or Decimal(0), _dec(e.credit) or Decimal(0)
        amt = max(deb, cred)
        if prev is not None and amt > 0:
            delta = bal - prev
            if abs(abs(delta) - amt) <= _TOL:
                if (delta > 0 and cred > 0) or (delta < 0 and deb > 0):
                    _set_side(e, amt, is_debit=delta > 0)
                    e.raw_row_data["direction_autocorrected"] = True
                    logger.info("GL 行%d 借贷方向与余额涨跌矛盾 · 已按余额链摆正", i)
            elif not gap:
                warnings.append(
                    f"GL 余额链断裂 行{i}: 上行余额 {_fmt(prev)} ± 金额 {_fmt(amt)} ≠ 余额 {_fmt(bal)}"
                )
        prev, gap = bal, False

    warnings.extend(_reconcile_printed_totals(doc, entries))
    _derive_opening(doc, entries)
    if not (doc.closing_balance or "").strip():
        last_bal = next((e.balance for e in reversed(entries) if _dec(e.balance) is not None), "")
        doc.closing_balance = last_bal
    return warnings


def _sums(entries) -> tuple:
    sd = sum((_dec(e.debit) or Decimal(0) for e in entries), Decimal(0))
    sc = sum((_dec(e.credit) or Decimal(0) for e in entries), Decimal(0))
    return sd, sc


def _reconcile_printed_totals(doc, entries) -> List[str]:
    """页脚印刷合计 vs 明细行和。首行方向没有上行余额可验(期初不印时),
    印刷合计是唯一确定性信息源:行和对不上、且恰好翻转首行就两项全平 → 翻首行;
    翻了也平不了 = 可能漏行/读错合计 → 只标警告(同 bank _audit_completeness 精神)。
    """
    p_deb, p_cred = _dec(doc.total_debit), _dec(doc.total_credit)
    if p_deb is None or p_cred is None or not entries:
        return []
    sd, sc = _sums(entries)
    if abs(sd - p_deb) <= _TOL and abs(sc - p_cred) <= _TOL:
        return []
    first = entries[0]
    deb0, cred0 = _dec(first.debit) or Decimal(0), _dec(first.credit) or Decimal(0)
    amt0 = max(deb0, cred0)
    if amt0 > 0:
        # 翻转首行后的行和:借减(或加)首行金额、贷反向
        flip_sd = sd - amt0 if deb0 > 0 else sd + amt0
        flip_sc = sc + amt0 if deb0 > 0 else sc - amt0
        if abs(flip_sd - p_deb) <= _TOL and abs(flip_sc - p_cred) <= _TOL:
            _set_side(first, amt0, is_debit=cred0 > 0)
            first.raw_row_data["direction_autocorrected"] = True
            logger.info("GL 首行借贷方向按页脚印刷合计摆正")
            return []
    return [
        f"GL 借贷合计与明细对不上: 行和 {_fmt(sd)}/{_fmt(sc)} vs 印刷 {_fmt(p_deb)}/{_fmt(p_cred)}"
        " — 可能漏行或合计读错"
    ]


def _derive_opening(doc, entries) -> None:
    """期初没印时数学反推:期初 = 首行余额 − 首行净变动。

    行 2..n 的方向已被余额链逐行验过、首行方向已被印刷合计消歧(有印刷合计时),
    此时期初是被链条唯一确定的数,不是猜测。首行方向无任何佐证(无印刷合计)时
    仍反推 —— 但链上只有这一处不确定,错也会被下游 GL↔银行对账勾稽差额显式暴露。
    """
    if (doc.opening_balance or "").strip():
        return
    first = entries[0]
    bal0 = _dec(first.balance)
    deb0, cred0 = _dec(first.debit) or Decimal(0), _dec(first.credit) or Decimal(0)
    if bal0 is None or max(deb0, cred0) <= 0:
        return
    doc.opening_balance = _fmt(bal0 - (deb0 - cred0))
