# -*- coding: utf-8 -*-
"""services/ocr/sanity.py · 发票合理性硬闸(确定性·绝不静默放过)。

triggers.py 决定「要不要再看一眼(L3 视觉复读)」,是软信号;本模块决定「这数压根
不可能对,别让它静默入账」,是硬信号 → 命中即强制转人工(needs_manual_review)。

根因(2026-06-29 vertex 切换实测复盘):
  · 自洽 ≠ 正确:BBL2645 的 −114万、pur05 的 44.67 内部都自洽,容差闸放过了它们。
  · 没有绝对合理性下限:期初负数、总额 < 单条明细,这类该直接拒。
  · 默认不诚实:校验不过仍静默 auto,而非转人工。

只在 document_type ∈ {tax_invoice, simplified_tax_invoice, receipt, credit_note, other}
的发票路调用(GL/银行走各自 validator)。纯函数:不连模型、不读 IO、duck-typed 取属性。

★诚实边界:本闸抓的是「结构上不可能」的错(负数/串税号/总额低于单行/缺VAT勾稽不平),
抓不住「语义选错列且无明细佐证」的 pur05-44.67 那类 —— 那需要供应商历史量级基线(另一道
闸,见 [[ocr-determinism-layer-root-cause]])。不在此夸大覆盖。
"""

from __future__ import annotations

from typing import List

from services.ocr.money import (
    normalize_id as _digits,
    normalize_money as _money,
    valid_thai_tax_id as _valid_tax_id,
)
from services.ocr.sanity_multi import multi_invoice_reasons

# 折扣回填留痕前缀。消费方(direct_read / workorder.classify)按它识别「系统改写过票面钱
# 字段」并强制留人;认前缀不认中文文案——按关键词匹配的话,改一个字就静默失守。
DISCOUNT_INFERRED_PREFIX = "discount_inferred:"

# 钱字段比对容差(泰铢):吸收四舍五入,又抓得住真错。
_TOL = 0.5
# 泰国标准 VAT 7%;缺 VAT 时用它反推「总额−小计」是否落在合理区间。
_VAT_RATE = 0.07
# 缺 VAT 勾稽:|总额−小计| 与「0」或「7%小计」的相对偏离超此比例才判不平(吸收分位四舍五入)。
_RECON_REL = 0.02


def _line_subtotals(invoice) -> List[float]:
    out: List[float] = []
    for it in getattr(invoice, "items", None) or []:
        amt = _money(getattr(it, "subtotal", None))
        if amt is not None and amt > 0:
            out.append(amt)
    return out


def line_sum_mismatch(
    sub,
    lines: List[float],
    symmetric: bool = False,
    *,
    discount: float | None = None,
    total: float | None = None,
) -> float | None:
    """明细行和是否与小计不平,不平则返回行和(供调用方拼消息),平则 None。

    单侧(规则 6·默认)只判「行和 > 小计」——行只会漏读不会多出钱,合法漏行
    (行和 < 小计)不误杀。双侧(规则 7·多票页收紧,见 sanity_multi)连「行和 <
    小计」也判,因为跨票错配会把行和往两边带偏,不能再放过偏低的一侧。
    两侧共用同一容差,消息措辞由调用方按各自语境拼(单票"结构不可能" vs
    多票页"跨票错配"),不在此耦合。
    """
    if sub is None or sub <= 0 or not lines or len(lines) < 2:
        return None
    line_sum = sum(lines)
    tol = max(_TOL, sub * _RECON_REL)
    # 折扣票的明细列常印折前含税价，表尾才列折扣、折后未税小计和含税合计。此时
    # 「明细和 − 折扣 = 含税合计」是合法关系，不能拿折前含税行和直接跟折后未税小计比。
    # 也兼容明细列印未税价的模板（明细和 − 折扣 = 折后小计）。
    if discount and discount > 0:
        after_discount = line_sum - discount
        if abs(after_discount - sub) <= tol:
            return None
        if total is not None and abs(after_discount - total) <= max(tol, total * _RECON_REL):
            return None
    if line_sum > sub + tol or (symmetric and line_sum < sub - tol):
        return line_sum
    return None


def vat_ratio_mismatch(sub: float | None, vat: float | None, discount: float | None) -> str | None:
    """VAT 是否为净额的法定 7% — 与规则 4b(总额勾稽)独立的第二道校验。

    抓「小计/VAT/总额三者被同时误读却仍恰好互相自洽」这类规则 4b 抓不住的自洽性
    幻觉(sanity.py 顶部诚实边界写的缺口之一;NBC 折扣票实案 2026-07-08:69→60/
    8→3 两位误读,sub+vat=total 仍平,但 VAT 不再是净额的 7%)。折扣两种印法
    (折前/折后)任一口径对上即放行,不误杀折扣票(同规则 4b/f003)。
    """
    if vat is None or vat <= 0 or sub is None or sub <= 0:
        return None
    gross_expected = sub * _VAT_RATE
    net_sub = sub - (discount or 0.0)
    net_expected = net_sub * _VAT_RATE if net_sub > 0 else gross_expected
    diff = min(abs(vat - gross_expected), abs(vat - net_expected))
    tol = max(_TOL, min(gross_expected, net_expected) * _RECON_REL)
    if diff <= tol:
        return None
    return (
        f"VAT {vat} 既非小计 {sub} × 7%({gross_expected:.2f})也非净额(折后){net_sub:.2f} × 7%"
        f"({net_expected:.2f})(差 {diff:.2f}) — 疑小计/VAT 单数位误读(自洽性幻觉)"
    )


def evaluate_sanity(invoice) -> List[str]:
    """返回硬否决原因列表(空=通过)。命中任一 → 调用方强制转人工,绝不 auto。

    每条规则都保守:只在「结构上不可能对」时触发,宁可漏抓(交给软闸/人工)也不误杀
    正常票(误杀 = 凭空增加人工量 + 失去信任)。

    同页多票(additional_invoices):附加票逐张过核心规则 + 规则 7 跨票错配核对,
    见 sanity_multi(该模块延迟导入本模块的共享件;本模块可放心顶层导它,无环)。
    """
    if getattr(invoice, "is_not_invoice", False):
        return []

    return _core_reasons(invoice) + multi_invoice_reasons(invoice)


def _core_reasons(invoice) -> List[str]:
    reasons: List[str] = []
    sub = _money(getattr(invoice, "subtotal", None))
    vat = _money(getattr(invoice, "vat", None))
    total = _money(getattr(invoice, "total_amount", None))
    discount = _money(getattr(invoice, "discount", None))

    # 规则 1:负数金额。发票的小计/税额/总额不可能为负(贷项单 credit_note 例外:整单冲红)。
    is_credit_note = getattr(invoice, "document_type", "") == "credit_note"
    if not is_credit_note:
        for name, val in (("total_amount", total), ("subtotal", sub), ("vat", vat)):
            if val is not None and val < 0:
                reasons.append(f"{name} 为负数({val}) — 发票金额不可能为负")

    # 规则 2:卖方税号 == 买方税号。买方表头税号被串进卖方(inv01)→ 方向/抵扣全错。
    st, bt = _digits(getattr(invoice, "seller_tax", None)), _digits(
        getattr(invoice, "buyer_tax", None)
    )
    if st and bt and len(st) >= 10 and st == bt:
        reasons.append(f"卖方税号 == 买方税号({st}) — 大概率串了表头税号")

    # 规则 3:总额 < 最大单行小计(且无折扣)。总额至少 ≥ 任一单行;低于即选错列(pur05 类,
    # 仅当明细在场)。有折扣时总额可能合法地低于单行 → 跳过不误杀。
    lines = _line_subtotals(invoice)
    if total is not None and total > 0 and lines and not (discount and discount > 0):
        biggest = max(lines)
        if total < biggest - _TOL:
            reasons.append(f"总额 {total} < 单条明细 {biggest} — 不可能(疑选错列)")

    # 规则 4(洞④ · triggers.py:85 的盲区):缺 VAT 但小计与总额都在且对不上。
    # 现有数学闸三字段缺一就跳过 → VAT 缺时静默放行。这里补勾稽:净额 = 小计 − 折扣
    # (泰国 VAT 基数在折扣后),总额必须 ≈ 净额(无税/含税)或 ≈ 净额+7%(漏抽销项税)。
    # ★必须减折扣,否则误杀 7-11 类折扣票(小计115−折扣5=总额110·见 [[ocr-determinism-layer-root-cause]])。
    if vat is None and sub is not None and total is not None and sub > 0:
        net = sub - (discount or 0.0)
        diff = total - net
        expected_vat = net * _VAT_RATE
        ok_zero = abs(diff) <= _TOL
        ok_vat = abs(diff - expected_vat) <= max(_TOL, expected_vat * _RECON_REL)
        if not ok_zero and not ok_vat:
            reasons.append(
                f"缺 VAT 且总额 {total} != 净额 {net:.2f}(小计 {sub} − 折扣 {discount or 0}),"
                f"差 {diff:.2f} 既非 0 也非 7%({expected_vat:.2f}) — 勾稽不平"
            )

    # 规则 4b(f003 实案 2026-07-03):VAT 在场但小计−折扣+VAT 对不上总额。泰国票折扣在
    # 小计后、VAT 前(净额 = 小计 − 折扣,总额 = 净额 + VAT);漏抓折扣行 → 存下的税基虚高、
    # 自己勾稽都不平却仍 auto。小计有「折前」「折后」两种印法,两种口径任一平即放行。
    if vat is not None and sub is not None and total is not None and sub > 0:
        gross_diff = abs(sub + vat - total)
        net_diff = abs(sub - (discount or 0.0) + vat - total)
        if min(gross_diff, net_diff) > _TOL:
            reasons.append(
                f"总额 {total} != 小计 {sub} − 折扣 {discount or 0} + VAT {vat}"
                f"(差 {min(gross_diff, net_diff):.2f}) — 勾稽不平(疑漏折扣行/选错列)"
            )

    # 规则 4c:VAT 与小计的 7% 关系独立复核(见 vat_ratio_mismatch 文档字符串)。
    ratio_reason = vat_ratio_mismatch(sub, vat, discount)
    if ratio_reason:
        reasons.append(ratio_reason)

    # 规则 5:税号位数对(13)但 MOD-11 校验位不过 → 八成 OCR 读错一位(Big C 538↔536:
    # 合法税号恒过校验,失败几乎只来自误读)。仅判已是 13 位者,不碰空/残缺(那是别的事)。
    for name, raw in (("seller_tax", st), ("buyer_tax", bt)):
        if len(raw) == 13 and not _valid_tax_id(raw):
            reasons.append(f"{name} {raw} 校验位不符 — 13 位但 MOD-11 不过(疑读错一位)")

    # 规则 6(trap08 实案 2026-07-05):明细行和 > 小计 → 结构不可能(小计=折扣前行和,
    # 行只会漏读不会多出钱)。抓「重影把 8 糊成 3」这类同一位错同时进小计与总额的自洽性
    # 误读——双读/勾稽全绿,但票面明细行和把真数供出来了。只单向判(行和小于小计=漏行,
    # 合法,不误杀);相对 2% + 绝对 0.5 双容差吸掉四舍五入。
    line_sum = line_sum_mismatch(sub, lines, discount=discount, total=total)
    if line_sum is not None:
        reasons.append(f"明细行和 {line_sum:.2f} > 小计 {sub} — 结构不可能(疑小计/总额读错一位)")

    return reasons


def credit_note_review_reason(invoice) -> str | None:
    """贷记单(ใบลดหนี้)= 方向性单据,一律转人工确认,不许当普通发票静默过账。

    P1 台账 #8(2026-07-05 实弹):票面负数被读成正数 → 退货冲销当正常进账,方向反。
    金额符号真伪机器无法自证(真实贷记单正负印法都有),方向只能人工把关。
    两条链(直读/Vision 路)共用本判定。
    """
    if getattr(invoice, "is_not_invoice", False):
        return None
    if getattr(invoice, "document_type", "") != "credit_note":
        return None
    return "credit_note — 冲销方向需人工确认(金额符号以票面为准)"


def infer_missing_discount(invoice) -> str | None:
    """折扣确定性反推:折扣缺失但「小计 + VAT − 总额」的差额 D 恰好使
    (小计 − D) × 7% ≈ VAT 时,票面几乎必然印了一行 ส่วนลด 被漏抓 → 回填 D。

    双重勾稽(差额 + VAT 税基)同时成立才回填,单一差额不动手 —— 那可能是选错列,
    交给规则 4b 转人工。回填成功返回说明文字(进 validation_warnings 留痕),否则 None。

    ⚠️ 回填会改写票面钱字段,且改完 _check_amount_math 与本模块硬闸都自动放行
    (实测 triggers 由 ['amount math fail...'] 变 [])。消费方必须据 DISCOUNT_INFERRED_PREFIX
    强制留人:闸的职责是报告差额,不是把票改到闸能过。
    """
    if getattr(invoice, "is_not_invoice", False):
        return None
    if _money(getattr(invoice, "discount", None)) is not None:
        return None
    sub = _money(getattr(invoice, "subtotal", None))
    vat = _money(getattr(invoice, "vat", None))
    total = _money(getattr(invoice, "total_amount", None))
    if sub is None or vat is None or total is None or sub <= 0 or vat <= 0:
        return None
    d = sub + vat - total
    if d <= _TOL:
        return None
    expected_vat = (sub - d) * _VAT_RATE
    if abs(expected_vat - vat) > max(_TOL, vat * _RECON_REL):
        return None
    invoice.discount = f"{d:.2f}"
    return (
        f"{DISCOUNT_INFERRED_PREFIX} 票面折扣 {d:.2f} 未被提取," "由勾稽差额+7%税基双重校验反推回填"
    )
