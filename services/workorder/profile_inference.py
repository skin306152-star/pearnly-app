# -*- coding: utf-8 -*-
"""税务画像卡「诚实推断」候选计算(画像卡智能判断批次)。

诚实边界:只推断 pays_individuals/pays_juristic 两项,数据源=services.workorder.
wht_signals 当期采购 WHT 扫描现成信号——has_employees/pays_foreign/
pays_interest_dividend 目前没有可靠数据源,绝不虚报(画像卡设计稿 v1 的原型演示同款
边界;真实工资流水信号归 H1 批次,不在本批冒领)。

现算不落库:GET 画像端点(routes/tax_profile_routes.py)每次请求都重新现算这份候选,
从不写数据库、不加定时任务——candidates 只活在这一次响应里,用户点"确认"才由
services.workspace.tax_profile_store 的确认路径把某个候选转正落库(source='inferred')。

已确认过 且 候选结论与当前已确认值一致 → 不重复提议(field_meta.confirmed_at 存在
且候选值等于本值列当前值,说明这条判断早就有人点头认过,同一个结论不用再问一次;
候选值与本值不同才算真正的冲突,继续提议好让用户看见并二选一)。
"""

from __future__ import annotations

# field → (命中信号键, 计数键)。value_when_hit/value_when_miss 是三态字段的 yes/no 取值,
# 命中给高置信度,未命中(当期确有采购活动但没扫到对应 WHT)给中置信度——不是没数据,
# 是数据说"没有",置信度自然低一档但仍值得一提(原型 scenarioInferred 同款处理)。
_INFERABLE_FIELDS = {
    "pays_individuals": ("wht_individuals", "wht_individuals_count"),
    "pays_juristic": ("wht_juristic", "wht_juristic_count"),
}

_CONFIDENCE_HIT = "high"
_CONFIDENCE_MISS = "mid"


def _encode_evidence(field: str, *, hit: bool, count: int, period: str) -> str:
    """依据编码成机器可解析串(non-i18n),真正的措辞由前端按当前语言 + 参数拼——
    后端不写死中文一句话,4 语产品不能只在服务器端固定一种语言(field_meta 的
    evidence 列约定是字符串,这里存的是"field:kind:count:period"这种紧凑编码,
    不是给人直接看的文本)。"""
    kind = "hit" if hit else "miss"
    return f"{field}:{kind}:{count}:{period}"


def compute_proposals(*, profile: dict, field_meta: dict, data_signals: dict, period: str) -> dict:
    """profile × field_meta × 当期 wht_signals → {field: {value, confidence, evidence}}。

    纯函数,零 I/O。当期无任何 posted 采购料件(has_any_material=False)时没有信号可推断,
    不硬猜——两个可推断字段都不提议。field_meta 是 tax_profile_store.get_profile() 返回的
    整份 dict(每个字段名 → {source, confidence, evidence, confirmed_at, ...}),缺失/空
    一律当"从未确认过"处理。
    """
    if not data_signals.get("has_any_material"):
        return {}

    out: dict = {}
    for field, (hit_key, count_key) in _INFERABLE_FIELDS.items():
        hit = bool(data_signals.get(hit_key))
        count = int(data_signals.get(count_key) or 0)
        value = "yes" if hit else "no"
        current = profile.get(field, "unknown")
        meta = field_meta.get(field) or {}
        already_confirmed = bool(meta.get("confirmed_at"))
        if already_confirmed and current == value:
            continue  # 已经确认过且结论没变,不重复打扰
        out[field] = {
            "value": value,
            "confidence": _CONFIDENCE_HIT if hit else _CONFIDENCE_MISS,
            "evidence": _encode_evidence(field, hit=hit, count=count, period=period),
        }
    return out


def merge_proposals_into_field_meta(field_meta: dict, proposals: dict) -> dict:
    """把现算的候选合并进(响应用的)field_meta 视图——只在这次响应里存在,绝不落库。

    每个字段的既有出处(source/confidence/evidence/confirmed_at/confirmed_by)原样保留,
    只是多挂一个 proposal 键;没有候选的字段 proposal 恒为 None(前端据此判断"有没有
    待确认的推断")。"""
    merged = {k: dict(v) for k, v in (field_meta or {}).items()}
    for field in set(merged) | set(proposals):
        merged.setdefault(field, {})
        merged[field]["proposal"] = proposals.get(field)
    return merged
