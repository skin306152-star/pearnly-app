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

from decimal import Decimal
from typing import Optional

from services.workorder.steps.reconcile_gates import to_dec

HIGH = "high"
MID = "mid"
LOW = "low"

# narrative_key 命名空间(verdict_*)。前端为每个键配 i18n 模板,用 params 填空;缺模板
# 时前端诚实回退到 flag_reason 原文(总比编假人话强)。
_K_MATH = "verdict_amount_math_fail"
_K_SALES_DIRECTION = "verdict_sales_direction"
_K_SALES_DOC = "verdict_sales_doc"
_K_DIRECTION = "verdict_direction_ambiguous"
_K_LOW_CONF = "verdict_ocr_low_conf"
_K_VALIDATION = "verdict_ocr_validation"
_K_OCR_ERROR = "verdict_ocr_error"
_K_DUPLICATE = "verdict_duplicate"


def _money_str(d: Decimal) -> str:
    return format(d.quantize(Decimal("0.01")), "f")


def _math_params(money: dict, _tail: str) -> dict:
    """净{net}+税{vat}={sum},与票面{total}差{diff}(方案 §2 给定模板)。"""
    net = to_dec(money.get("subtotal"))
    vat = to_dec(money.get("vat"))
    total = to_dec(money.get("total_amount"))
    net_plus_vat = net + vat
    return {
        "net": _money_str(net),
        "vat": _money_str(vat),
        "sum": _money_str(net_plus_vat),
        "total": _money_str(total),
        "diff": _money_str((total - net_plus_vat).copy_abs()),
    }


def _seller_params(money: dict, _tail: str) -> dict:
    """方向类判据:卖方税号 + 供应商名(读侧锚,缺则 None,前端诚实降级)。"""
    return {"seller_tax": money.get("seller_tax"), "vendor": money.get("vendor")}


def _band_params(_money: dict, tail: str) -> dict:
    return {"band": tail or None}


def _error_params(_money: dict, tail: str) -> dict:
    return {"error": tail or None}


def _dup_params(_money: dict, tail: str) -> dict:
    return {"of": tail or None}


def _empty_params(_money: dict, _tail: str) -> dict:
    return {}


# flag_reason 冒号前缀 → (narrative_key, confidence, params 构造器)。前缀语义单一事实源在
# classify.py/kinds.py/decisions.py;本表只做「机器给的机器码 → 人话模板 + 置信度」的读侧映射。
_MAP = {
    "amount_math_fail": (_K_MATH, LOW, _math_params),  # 票面净+税≠总额=自身冲突 → low
    "sales_direction_unhandled": (_K_SALES_DIRECTION, HIGH, _seller_params),  # 税号精确判本方销项
    "sales_doc_review": (_K_SALES_DOC, MID, _seller_params),  # 名称/税号锚判本方销项,读侧保守 mid
    "direction_ambiguous": (_K_DIRECTION, LOW, _seller_params),  # 双锚冲突/缺锚判不出 → low
    "ocr_low_confidence": (_K_LOW_CONF, LOW, _band_params),
    "ocr_validation_warning": (_K_VALIDATION, LOW, _empty_params),
    "ocr_error": (_K_OCR_ERROR, LOW, _error_params),
    "duplicate_of": (_K_DUPLICATE, HIGH, _dup_params),  # 指纹精确命中复件 → high
}


def hint(*, flag_reason: Optional[str], ocr_read: Optional[dict] = None) -> dict:
    """一件 flagged 料的判据人话 + 置信度。返回恒有三键 {narrative_key, params, confidence};
    未识别 flag_reason → narrative_key=None(前端回退原文)+ confidence=low(未知不淡化)。"""
    raw = flag_reason or ""
    head = raw.split(":", 1)[0]
    tail = raw.split(":", 1)[1] if ":" in raw else ""
    entry = _MAP.get(head)
    if entry is None:
        return {"narrative_key": None, "params": {}, "confidence": LOW}
    key, confidence, build = entry
    return {"narrative_key": key, "params": build(ocr_read or {}, tail), "confidence": confidence}
