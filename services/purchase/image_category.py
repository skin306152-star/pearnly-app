# -*- coding: utf-8 -*-
"""LINE 图片路费用归类(从 line_ingest 拆出 · 单一职责 + 控行数 · docs/smart-intake/15)。

置信驱动的图片分类,优先级:① 用户学习(税号/归一卖家名)② 用户识别关键词(费用数据页可编辑 ·
Phase 2 灰度)③ 确定性规则(品名 → 商户默认)④ LLM 逐项/整票兜底 ⑤ 关键词兜底 / 太糊留未分类。
返回 (cat_id, sub_id, cat_name, sub_name, conf, source) 喂 ingest 置信分级 + 日志 category_source。
学习与规则永不被 LLM 覆盖。
"""

from __future__ import annotations

import logging
from decimal import Decimal

logger = logging.getLogger("mr-pilot")

# 分类 LLM 主路径短超时(P1G-Perf · Zihao 2026-06-18):分类是「在选项里挑编号」的小任务,
# 不该把入账卡拖在 Gemini 上 7–14s(甚至 504)。规则先行,落空才调一次 LLM,且 3s 硬上限;
# 超时即回落规则/中性分类(卡照常出·标「请核对」),绝不阻塞卡片。
_CAT_LLM_TIMEOUT = 3


def _category_names(cats: list, cat_id, sub_id) -> tuple[str, str]:
    for p in cats:
        if p["id"] == cat_id:
            sub_name = next((c["name"] for c in (p.get("children") or []) if c["id"] == sub_id), "")
            return p["name"], sub_name
    return "", ""


def _dominant_item_category(cats: list, items: list, *, api_key):
    from services.expense import category_ai
    from services.purchase.line_ingest import _dec  # 复用金额解析(函数级 · 避免顶层循环)

    clean = [
        {"name": str(it.get("name") or "").strip(), "amount": _dec(it.get("amount"))}
        for it in (items or [])
        if str(it.get("name") or "").strip()
    ]
    if not clean:
        return None, None, Decimal("0")
    choices = category_ai.categorize_items(clean, cats, api_key=api_key, timeout=_CAT_LLM_TIMEOUT)
    weights: dict[tuple, Decimal] = {}
    total_weight = Decimal("0")
    for it, pair in zip(clean, choices):
        cat_id, sub_id = pair
        weight = it["amount"] if it["amount"] > 0 else Decimal("1")
        total_weight += weight
        if not cat_id:
            continue
        weights[(cat_id, sub_id)] = weights.get((cat_id, sub_id), Decimal("0")) + weight
    if not weights:
        return None, None, Decimal("0")
    (cat_id, sub_id), weight = max(weights.items(), key=lambda kv: kv[1])
    share = (weight / total_weight) if total_weight > 0 else Decimal("0")
    return cat_id, sub_id, share


def _learned_category(cur, tenant_id, workspace_client_id, *, tax_id, vendor):
    """用户学习命中:税号键优先(tax:<税号>),其次归一卖家名键(seller:<归一名>)。无命中 → None。

    用户在 LINE 改错或网页详情改过分类后写入(见 line_correct_data / docs.update_draft),此处读出,
    优先级最高 —— 规则与 LLM 都不能覆盖用户明确选过的归类。
    """
    from services.expense import conversation, merchant

    t = (tax_id or "").strip()
    keys = []
    if t:
        keys.append(f"tax:{t}")
    nv = merchant.canonical_merchant(vendor, t)
    if nv:
        keys.append(f"seller:{nv}")
    try:
        for key in keys:
            hit = conversation.find_exact(
                cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, keyword=key
            )
            if hit and hit.get("category_id"):
                return hit
    except Exception as e:  # noqa: BLE001 — 学习查不到只回落规则,绝不拖垮入账
        logger.warning("[line_classify] learned lookup skipped: %s", str(e)[:160])
    return None


def smart_category(cur, *, tenant_id, workspace_client_id, vendor, tax_id, descs, items, api_key):
    """图片路分类(确定性优先 · LLM 仅补充 · 用户学习与规则永不被 LLM 覆盖)。

    顺序:① 用户学习(税号/归一卖家名)② 用户识别关键词(灰度)③ 确定性规则(品名 → 商户默认)
    ④ LLM 逐项主分类 ⑤ LLM 整票兜底 ⑥ 关键词兜底 / 太糊留未分类(不硬猜)。返回
    (cat_id, sub_id, cat_name, sub_name, conf, source);source 喂日志 category_source ∈
    learned|rule|vendor_default|item|ai|fallback|none。LLM 步骤 3s 硬上限,超时回落规则/中性。
    """
    from services.expense import category_ai, keyword_rules, merchant
    from services.purchase import categories as cat_svc
    from services.purchase import intake as ik

    cats = cat_svc.get_tree(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    joined = " / ".join(d for d in descs[:5] if d)

    learned = _learned_category(cur, tenant_id, workspace_client_id, tax_id=tax_id, vendor=vendor)
    if learned and learned.get("category_id"):
        return (
            learned["category_id"],
            learned.get("subcategory_id"),
            learned.get("category_name") or "",
            learned.get("subcategory_name") or "",
            Decimal("0.97"),
            "learned",
        )

    # 用户识别关键词(费用数据页可编辑 · Phase 2):税号/卖家身份没命中 → 按票面文字子串匹配用户
    # 挂的词(只认 user_rule)。总闸控;学习优先仍在写死规则之前。存量表空 → 零行为变化。
    kwhit = keyword_rules.match_category(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        text=f"{vendor or ''} {joined}",
    )
    if kwhit and kwhit.get("category_id"):
        return (
            kwhit["category_id"],
            kwhit.get("subcategory_id"),
            kwhit.get("category_name") or "",
            kwhit.get("subcategory_name") or "",
            Decimal("0.95"),
            "learned",
        )

    # 糊名清税号 → curated 别名喂规则(仅身份解析,分类仍走品名优先)。
    rule_vendor = vendor or merchant.merchant_alias_by_tax(tax_id)

    # ① 确定性逐项主分类(纯规则 · 按金额加权 · 不调 LLM):混合票按金额最大类别,接近五五开打低置信。
    cat_id, sub_id, share = _dominant_item_category(cats, items, api_key=None)
    if cat_id:
        cat_name, sub_name = _category_names(cats, cat_id, sub_id)
        conf = Decimal("0.92") if share >= Decimal("0.70") else Decimal("0.82")
        return cat_id, sub_id, cat_name, sub_name, conf, "rule"

    # ② 整票规则:品名(item)落空 → 商户默认(vendor → vendor_default · 日志可观察)。
    cat_id, sub_id, layer = category_ai.classify_rules(rule_vendor, joined, cats)
    if cat_id:
        cat_name, sub_name = _category_names(cats, cat_id, sub_id)
        if layer == "vendor":
            return cat_id, sub_id, cat_name, sub_name, Decimal("0.85"), "vendor_default"
        return cat_id, sub_id, cat_name, sub_name, Decimal("0.90"), "rule"

    # ③ LLM 逐项主分类(确定性全落空才补充)。
    cat_id, sub_id, share = _dominant_item_category(cats, items, api_key=api_key)
    if cat_id:
        cat_name, sub_name = _category_names(cats, cat_id, sub_id)
        conf = Decimal("0.88") if share >= Decimal("0.70") else Decimal("0.80")
        return cat_id, sub_id, cat_name, sub_name, conf, "item"

    if api_key:
        cat_id, sub_id = category_ai.suggest_category(
            rule_vendor, joined, cats, api_key=api_key, timeout=_CAT_LLM_TIMEOUT
        )
        if cat_id:
            cat_name, sub_name = _category_names(cats, cat_id, sub_id)
            return cat_id, sub_id, cat_name, sub_name, Decimal("0.80"), "ai"

    cat_id, sub_id = ik._match_category(f"{rule_vendor} {descs[0] if descs else ''}", cats)
    if not cat_id:
        return None, None, "", "", Decimal("0"), "none"
    cat_name, sub_name = _category_names(cats, cat_id, sub_id)
    return cat_id, sub_id, cat_name, sub_name, Decimal("0.76"), "fallback"
