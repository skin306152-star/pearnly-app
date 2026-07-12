# -*- coding: utf-8 -*-
"""工资表列自动猜测(纯启发式 · 只猜不定 · 猜错可改 · 方案 §2.2)。

「任何工资 Excel 都能吃」的核心:对每列采样打特征分,猜它对应哪个语义字段,交人确认。
强特征优先(13 位 + mod-11 通过率几乎无误报);拿不准的字段不臆造,不进候选(UI 留空请人补)。

关键歧义处理:付款方税号(全表同值)与员工身份证(逐员工不同)都是 13 位 mod-11 合法号 ——
以「去重值个数」区分:变化多的列=员工身份证,恒定的列=付款方(表头级,单独识别不当员工)。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from services.recon.field_comparator import mod11_check
from services.payroll import model

CONF_HIGH = "high"
CONF_MEDIUM = "medium"
CONF_LOW = "low"

_SALARY_FLOOR = 500  # 月薪合理下界(排除序号/条件等小整数列被误当金额)
_SALARY_CEIL = 2_000_000
_TITLE_TOKENS = {"นาย", "นาง", "นางสาว", "น.ส.", "ด.ช.", "ด.ญ.", "mr", "ms", "mrs", "miss"}
_ID_RE = re.compile(r"^\d{13}$")


@dataclass(frozen=True)
class GuessCandidate:
    column: int  # 0-based 列号
    confidence: str
    reason: str


@dataclass(frozen=True)
class _ColStats:
    index: int
    samples: list  # 非空原始值
    texts: list  # 归一化字符串
    id_ratio: float  # ^\d{13}$ 且 mod-11 通过占比
    numeric: list  # 可解析为数的值
    numeric_ratio: float
    distinct: int  # 去重值个数
    title_ratio: float
    has_income_code: bool


def _norm(v) -> str:
    return str(v).strip()


def _as_number(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _col_stats(index: int, cells: list) -> _ColStats:
    samples = [c for c in cells if c is not None and _norm(c) != ""]
    texts = [_norm(c) for c in samples]
    if not samples:
        return _ColStats(index, [], [], 0.0, [], 0.0, 0, 0.0, False)

    ids_ok = sum(1 for t in texts if _ID_RE.match(t) and mod11_check(t))
    numbers = [n for n in (_as_number(c) for c in samples) if n is not None]
    titles = sum(1 for t in texts if t.lower() in _TITLE_TOKENS)
    income = any("40(" in t for t in texts)
    n = len(samples)
    return _ColStats(
        index=index,
        samples=samples,
        texts=texts,
        id_ratio=ids_ok / n,
        numeric=numbers,
        numeric_ratio=len(numbers) / n,
        distinct=len(set(texts)),
        title_ratio=titles / n,
        has_income_code=income,
    )


def _score_employee_id(s: _ColStats) -> tuple:
    # 13 位 + mod-11 高通过 = 强特征;多列合格时,去重多者才是员工(恒定者=付款方)。
    if s.id_ratio >= 0.8 and s.distinct >= 2:
        return s.id_ratio + s.distinct * 0.001, CONF_HIGH, "13位+mod-11通过+逐行不同"
    return 0.0, CONF_LOW, ""


def _score_amount(s: _ColStats) -> tuple:
    if s.numeric_ratio < 0.8 or not s.numeric:
        return 0.0, CONF_LOW, ""
    inside = [x for x in s.numeric if _SALARY_FLOOR <= x <= _SALARY_CEIL]
    if len(inside) / len(s.numeric) < 0.6:
        return 0.0, CONF_LOW, ""
    med = sorted(s.numeric)[len(s.numeric) // 2]
    return med, CONF_MEDIUM, "数值列且量级在月薪区间"


def _score_wht(s: _ColStats) -> tuple:
    # 扣税列:数值、多为 0(或远小于金额)。月薪常未达起征 → 大量 0(金标全 0)。
    if s.numeric_ratio < 0.8 or not s.numeric:
        return 0.0, CONF_LOW, ""
    zeros = sum(1 for x in s.numeric if x == 0)
    if zeros / len(s.numeric) >= 0.5:
        return zeros / len(s.numeric), CONF_MEDIUM, "数值列且多为 0"
    return 0.0, CONF_LOW, ""


def _score_title(s: _ColStats) -> tuple:
    if s.title_ratio >= 0.6:
        return s.title_ratio, CONF_HIGH, "值域∈{นาย,นางสาว,...}"
    return 0.0, CONF_LOW, ""


def _score_income(s: _ColStats) -> tuple:
    if s.has_income_code:
        return 1.0, CONF_HIGH, "含 40("
    return 0.0, CONF_LOW, ""


def _score_date(s: _ColStats) -> tuple:
    from services.payroll.intake import parse_paid_date

    ok = sum(1 for c in s.samples if parse_paid_date(c) is not None)
    if s.samples and ok / len(s.samples) >= 0.8 and s.id_ratio < 0.5:
        return ok / len(s.samples), CONF_MEDIUM, "可解析为支付日"
    return 0.0, CONF_LOW, ""


# 名/姓不打独立特征分(泰文文本无强区分特征)——由 guess_columns 按「称谓右侧两列」定位。
_SCORERS = {
    model.F_EMPLOYEE_ID: _score_employee_id,
    model.F_PAID_AMOUNT: _score_amount,
    model.F_WHT_AMOUNT: _score_wht,
    model.F_TITLE: _score_title,
    model.F_INCOME_CODE: _score_income,
    model.F_PAID_DATE: _score_date,
}


def _is_text_name_col(s: _ColStats) -> bool:
    return bool(s.samples) and s.numeric_ratio < 0.3 and s.title_ratio < 0.5 and s.id_ratio < 0.5


def guess_columns(header: list, rows: list) -> dict:
    """采样各列 → 语义字段候选 {field: GuessCandidate}(仅 high/medium)。

    贪心分配:每个字段取得分最高且未被占用的列;称谓右侧两文本列定位名/姓(方案 §2.2)。
    """
    width = max([len(header)] + [len(r) for r in rows], default=0)
    stats = [_col_stats(c, [r[c] if c < len(r) else None for r in rows]) for c in range(width)]

    candidates: dict[int, tuple] = {}  # field → (score, GuessCandidate)
    used: set[int] = set()
    for field_key, scorer in _SCORERS.items():
        best = None
        for s in stats:
            if s.index in used:
                continue
            score, conf, reason = scorer(s)
            if conf in (CONF_HIGH, CONF_MEDIUM) and (best is None or score > best[0]):
                best = (score, GuessCandidate(s.index, conf, reason))
        if best:
            candidates[field_key] = best
            used.add(best[1].column)

    _assign_names(stats, candidates, used)
    return {f: cand for f, (_, cand) in candidates.items()}


def _assign_names(stats: list, candidates: dict, used: set) -> None:
    """名/姓 = 称谓列右侧最近的两个文本列(方案 §2.2:跟在称谓后两列)。"""
    title = candidates.get(model.F_TITLE)
    start = title[1].column + 1 if title else 0
    text_cols = [
        s.index for s in stats if s.index >= start and s.index not in used and _is_text_name_col(s)
    ]
    for field_key, col in zip((model.F_FIRST_NAME, model.F_LAST_NAME), text_cols):
        candidates[field_key] = (0.0, GuessCandidate(col, CONF_MEDIUM, "称谓右侧文本列"))
        used.add(col)


def find_constant_id_column(header: list, rows: list) -> int | None:
    """付款方税号列:13 位 mod-11 合法且全表同一值(表头级,非员工)。返回列号或 None。"""
    width = max([len(header)] + [len(r) for r in rows], default=0)
    for c in range(width):
        stats = _col_stats(c, [r[c] if c < len(r) else None for r in rows])
        if stats.id_ratio >= 0.8 and stats.distinct == 1:
            return c
    return None
