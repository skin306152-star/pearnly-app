# -*- coding: utf-8 -*-
"""Tenant-scoped learned expense category mappings."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def lookup_learned(cur, *, tenant_id: str, workspace_client_id: int, text: str) -> Optional[dict]:
    """文本命中已学习的关键词 → 返回该科目(学习优先于内置字典)。无命中 → None。"""
    low = (text or "").lower()
    cur.execute(
        "SELECT keyword, category_id, subcategory_id, category_name, subcategory_name "
        "FROM expense_learned WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    for r in cur.fetchall():
        if r["keyword"] and r["keyword"].lower() in low:
            return {
                "category_id": str(r["category_id"]) if r["category_id"] else None,
                "subcategory_id": str(r["subcategory_id"]) if r["subcategory_id"] else None,
                "category_name": r["category_name"],
                "subcategory_name": r["subcategory_name"],
            }
    return None


def find_exact(cur, *, tenant_id: str, workspace_client_id: int, keyword: str) -> Optional[dict]:
    """精确命中已学习键 → 该科目。用于前缀键(tax:<税号> / seller:<归一卖家名>)按身份精确查,
    区别于 lookup_learned 的自由文本子串匹配。无命中 → None。"""
    kw = (keyword or "").strip().lower()
    if not kw:
        return None
    cur.execute(
        "SELECT category_id, subcategory_id, category_name, subcategory_name "
        "FROM expense_learned "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND keyword = %s",
        (tenant_id, workspace_client_id, kw),
    )
    r = cur.fetchone()
    if not r:
        return None
    return {
        "category_id": str(r["category_id"]) if r["category_id"] else None,
        "subcategory_id": str(r["subcategory_id"]) if r["subcategory_id"] else None,
        "category_name": r["category_name"],
        "subcategory_name": r["subcategory_name"],
    }


def lookup_learned_for_text(
    cur, *, tenant_id: str, workspace_client_id: int, text: str, vendor: str = ""
) -> Optional[dict]:
    """文字路归类的学习命中(用户学习恒高于品名/商户默认规则)。无命中 → None。

    ① 商户身份键:从卖家名/文本归一出商户(merchant.canonical_merchant)→ 精确查 seller:<归一名>,
       与图片路 image_category._learned_category、与学习按钮存键同一把。治「711 水」漏掉「以后711都记X」
       —— 子串匹配桥不了 711→7-eleven,品牌归一才能。
    ② 关键词子串:品名/卖家裸词(lookup_learned)。"""
    from services.expense import merchant

    try:
        for src in (vendor, text):
            canon = merchant.canonical_merchant(src or "", "")
            if not canon:
                continue
            hit = find_exact(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                keyword=f"seller:{canon}",
            )
            if hit and hit.get("category_id"):
                return hit
    except Exception as e:  # noqa: BLE001 — 学习查不到只回落品名/LLM,绝不拖垮记账
        logger.warning("[conversation] seller-key lookup skipped: %s", str(e)[:160])
    return lookup_learned(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, text=text
    )


def learn(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    keyword: str,
    category_id: Optional[str],
    subcategory_id: Optional[str],
    category_name: str = "",
    subcategory_name: str = "",
    source: str = "correction",
) -> None:
    """记住 关键词→科目(用户改过一次 · 网页复核屏纠正时调)。空关键词忽略。

    source='user_rule' = 用户在费用数据页显式挂的规则(免疫纠错覆盖);'correction' = 纠错自学。
    冲突时:纠错(correction)不许覆盖已有 user_rule 行(用户明确设过的优先),user_rule 可覆盖任意。
    """
    kw = (keyword or "").strip().lower()
    if not kw:
        return
    cur.execute(
        "INSERT INTO expense_learned "
        "(tenant_id, workspace_client_id, keyword, category_id, subcategory_id, "
        "category_name, subcategory_name, source, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now()) "
        "ON CONFLICT (tenant_id, workspace_client_id, keyword) DO UPDATE SET "
        "category_id = EXCLUDED.category_id, subcategory_id = EXCLUDED.subcategory_id, "
        "category_name = EXCLUDED.category_name, subcategory_name = EXCLUDED.subcategory_name, "
        "source = EXCLUDED.source, updated_at = now() "
        "WHERE expense_learned.source <> 'user_rule' OR EXCLUDED.source = 'user_rule'",
        (
            tenant_id,
            workspace_client_id,
            kw,
            category_id,
            subcategory_id,
            category_name,
            subcategory_name,
            source,
        ),
    )
