# -*- coding: utf-8 -*-
"""判据人话 + 置信度只读投影(MC1-b1 · 大脑 GPT 叙述插座的规则填充版)。

纯叶子(同 decisions.py/sod.py 惯例):输入已回放好的 flag_reason / ocr 读数 / 银行 score,
输出 {narrative_key, params, confidence}——不碰 DB、不改引擎、不落库、不重算钱(净+税=总额
只做展示层的差额提示,权威合计仍归 reconcile_gates)。narrative_key 是 i18n 模板键,前端拿
params 渲染人话;规则期由本模块按 flag_reason 填,大脑影子期达标后替换本函数产出、前端结构
不变(方案决策 3 的预留插座)。

confidence 分级(方案决策 3):税号精确=high / 名称锚=mid / OCR 低置信或票面冲突=low。
分级描述「机器对这件判得有多稳」,不是异常严重度(严重度是前端 flagSeverity 的红/黄
分档,两轴独立)。

前端 static/ai 无法 import,narrative_key 命名与前端 i18n 模板键约定(verdict_* 前缀)
靠本文件与 b2 契约小抄同步维护。钱串解析走 reconcile_gates.to_dec(单源)。
"""

from __future__ import annotations

from collections import namedtuple
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from services.workorder.steps.reconcile_gates import to_dec

HIGH = "high"
MID = "mid"
LOW = "low"

# 异常严重度(与置信度两轴独立):红=数学不自洽/OCR 读失败/方向判不出/复件,黄=置信度或
# 校验存疑。未知原因保守当红——没把握的异常不淡化。前端 flagSeverity 政策副本已删,severity
# 单一事实源在本表(review_queue 分组计数与 flagged 投影两处都读 severity_of/hint)。
SEV_CRIT = "crit"
SEV_WARN = "warn"

# narrative_key 命名空间(verdict_*)。前端为每个键配 i18n 模板,用 params 填空;缺模板
# 时前端诚实回退到 flag_reason 原文(总比编假人话强)。
_K_MATH = "verdict_amount_math_fail"
_K_VAT_RATE = "verdict_vat_rate_mismatch"
_K_SALES_DIRECTION = "verdict_sales_direction"
_K_SALES_DOC = "verdict_sales_doc"
_K_DIRECTION = "verdict_direction_ambiguous"
_K_LOW_CONF = "verdict_ocr_low_conf"
_K_VALIDATION = "verdict_ocr_validation"
_K_OCR_ERROR = "verdict_ocr_error"
_K_DUPLICATE = "verdict_duplicate"
_K_DISCOUNT_INFERRED = "verdict_discount_inferred"
_K_TOTALS_RESCUED = "verdict_totals_rescued"


# 泰国标准 VAT 税率。amount_math_fail 的勾稽闸词表(classify._MATH_HINTS)混装了
# 「净+税≠总额」与「VAT≠净额×7%」两类警告,文案在读侧按票面数字重分——分错模板会把
# 三字段自洽的折扣票说成「相差 0.00,票面自身不自洽」(2026-07-14 清单 #1)。
_VAT_RATE = Decimal("0.07")
_CENT = Decimal("0.01")


def _money_str(d: Decimal) -> str:
    return format(d.quantize(_CENT), "f")


def _math_narrative(money: dict) -> tuple[str, dict]:
    """amount_math_fail → (narrative_key, params),按票面数字选对模板:
    ①净+税≠总额 → 自身不自洽(净{net}+税{vat}={sum},与票面{total}差{diff});
    ②三字段自洽但 VAT≠净额×7% → 税率异常(按 7% 应为{expected},票面{vat}差{diff},
      常见于折扣票——这句话直接决定人/大脑能不能裁对折扣票);
    ③两项都过(行和/折扣勾稽类警告)→ 泛化校验模板,绝不硬说「不自洽」。"""
    net = to_dec(money.get("subtotal"))
    vat = to_dec(money.get("vat"))
    total = to_dec(money.get("total_amount"))
    net_plus_vat = net + vat
    diff = (total - net_plus_vat).copy_abs().quantize(_CENT)
    if diff != 0:
        return _K_MATH, {
            "net": _money_str(net),
            "vat": _money_str(vat),
            "sum": _money_str(net_plus_vat),
            "total": _money_str(total),
            "diff": _money_str(diff),
        }
    expected = (net * _VAT_RATE).quantize(_CENT, rounding=ROUND_HALF_UP)
    rate_diff = (vat - expected).copy_abs().quantize(_CENT)
    if rate_diff != 0:
        return _K_VAT_RATE, {
            "net": _money_str(net),
            "vat": _money_str(vat),
            "expected": _money_str(expected),
            "diff": _money_str(rate_diff),
        }
    return _K_VALIDATION, {}


def _seller_params(money: dict, _tail: str) -> dict:
    """方向类判据:卖方税号 + 供应商名(读侧锚,缺则 None,前端诚实降级)。"""
    return {"seller_tax": money.get("seller_tax"), "vendor": money.get("vendor")}


def _band_params(_money: dict, tail: str) -> dict:
    return {"band": tail or None}


def _discount_params(money: dict, _tail: str) -> dict:
    """系统补的那行折扣金额:卡上不说出改了多少钱,「请核对原图」就无从核对起。"""
    return {"discount": money.get("discount")}


def _money_read_params(money: dict, _tail: str) -> dict:
    """第二次读出来的钱面三数 —— 人要核的就是这三个数,得摆在卡上。"""
    return {
        "net": money.get("subtotal"),
        "vat": money.get("vat"),
        "total": money.get("total_amount"),
    }


def _error_params(_money: dict, tail: str) -> dict:
    return {"error": tail or None}


def _dup_params(_money: dict, tail: str) -> dict:
    return {"of": tail or None}


def _empty_params(_money: dict, _tail: str) -> dict:
    return {}


# 批量「全部按建议处理」的安全默认动作(suggested_decision):只有方向精确/复件精确这类
# 有明确安全落点的给建议,低置信/票面自身冲突一律不给,逼人工逐张审。前端 _BULK_TEMPLATES
# 政策副本已删,随 verdict_hint.suggested_decision 下发,前端只渲染不再维护这张表。
_ASSIGN_SALES = {"decision": "assign_kind", "kind": "sales_doc"}
_EXCLUDE = {"decision": "exclude"}

# flag_reason 冒号前缀 → 判据政策。前缀语义单一事实源在 classify.py/kinds.py/decisions.py;
# 本表把「机器码 → 人话模板 + 置信度 + 严重度 + 建议裁决」收成一处读侧政策,跨前后端不再各持副本。
_Policy = namedtuple("_Policy", "narrative_key confidence params severity suggested_decision")
_MAP = {
    # 票面勾稽闸报警 → low 置信、crit 严重、无安全默认(必须人工看数)。narrative_key 是
    # 占位:hint() 对该前缀按票面数字经 _math_narrative 重选模板(不自洽/税率异常/泛化)。
    "amount_math_fail": _Policy(_K_MATH, LOW, _empty_params, SEV_CRIT, None),
    # 税号精确判本方销项 → high 置信,建议确认为销项。
    "sales_direction_unhandled": _Policy(
        _K_SALES_DIRECTION, HIGH, _seller_params, SEV_CRIT, _ASSIGN_SALES
    ),
    # 名称/税号锚判本方销项,读侧保守 mid、黄,建议确认原判。
    "sales_doc_review": _Policy(_K_SALES_DOC, MID, _seller_params, SEV_WARN, _ASSIGN_SALES),
    # 双锚冲突/缺锚判不出 → low、crit(方向漏判会静默漏进项),无安全默认。
    "direction_ambiguous": _Policy(_K_DIRECTION, LOW, _seller_params, SEV_CRIT, None),
    "ocr_low_confidence": _Policy(_K_LOW_CONF, LOW, _band_params, SEV_WARN, None),
    "ocr_validation_warning": _Policy(_K_VALIDATION, LOW, _empty_params, SEV_WARN, None),
    "ocr_error": _Policy(_K_OCR_ERROR, LOW, _error_params, SEV_CRIT, None),
    # 指纹精确命中复件 → high,建议剔除。
    "duplicate_of": _Policy(_K_DUPLICATE, HIGH, _dup_params, SEV_CRIT, _EXCLUDE),
    # 系统按勾稽差额替票面补了一行折扣 → 票面现在自洽,但那份自洽是系统自己造的。
    # crit(直接改了钱面字段)、无安全默认:必须有人对着原图确认真印了这行折扣。
    "discount_inferred": _Policy(_K_DISCOUNT_INFERRED, LOW, _discount_params, SEV_CRIT, None),
    # 钱数是第二个模型重读出来的(L3 复读失败后的窄口径救援)→ 同样 crit、无安全默认:
    # 救援的验收条件只有算术自洽,而第一次读错时它也成立,证明不了这次读对了。
    "totals_rescued": _Policy(_K_TOTALS_RESCUED, LOW, _money_read_params, SEV_CRIT, None),
}


def severity_of(flag_reason: Optional[str]) -> str:
    """flag_reason → 严重度(crit/warn)。政策单一事实源;未知原因保守 crit(异常不淡化)。
    review_queue 的 flagged 分组计数按 flag_reason 现算严重度(那层没有 verdict_hint)走此函数。"""
    entry = _MAP.get(str(flag_reason or "").split(":", 1)[0])
    return entry.severity if entry else SEV_CRIT


def hint(*, flag_reason: Optional[str], ocr_read: Optional[dict] = None) -> dict:
    """一件 flagged 料的判据政策:{narrative_key, params, confidence, severity, suggested_decision}。
    未识别 flag_reason → narrative_key=None(前端回退原文)+ confidence=low + severity=crit
    (未知不淡化)+ suggested_decision=None(无安全默认,逼人工审)。"""
    raw = flag_reason or ""
    head = raw.split(":", 1)[0]
    tail = raw.split(":", 1)[1] if ":" in raw else ""
    entry = _MAP.get(head)
    if entry is None:
        return {
            "narrative_key": None,
            "params": {},
            "confidence": LOW,
            "severity": SEV_CRIT,
            "suggested_decision": None,
        }
    if head == "amount_math_fail":
        key, params = _math_narrative(ocr_read or {})
    else:
        key, params = entry.narrative_key, entry.params(ocr_read or {}, tail)
    return {
        "narrative_key": key,
        "params": params,
        "confidence": entry.confidence,
        "severity": entry.severity,
        "suggested_decision": entry.suggested_decision,
    }
