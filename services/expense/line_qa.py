# -*- coding: utf-8 -*-
"""一句话记账 · 查账(query)+ 问答(question)+ 越界挡回(doc 10 §1.3/§1.4/§1.5)。

护栏:用户数据问题走 DB 真查(不让模型凭记忆给数字);产品/税务问题接知识中心带出处,
查不到诚实兜底;越界(闲聊/通用税务咨询)礼貌挡回 + Quick Reply 引导,绝不硬答。
用户可见文案:查账数字 + 知识答案(接地带出处)走模板填值;挡回话术纯 i18n。
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


def month_spending(cur, *, tenant_id: str, workspace_client_id: int) -> Decimal:
    """本月已入账支出合计(DB 真查 · 不让模型编数字)。

    查 purchase_docs 已过账(status='posted')的费用/进项单 —— expense_draft 表已废,LINE
    记账现直落 purchase_docs(见 docs/smart-intake/15)。旧版查死表恒返 ฿0 是真 bug,已修。
    """
    cur.execute(
        "SELECT COALESCE(SUM(grand_total), 0) AS total FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND status = 'posted' "
        "AND doc_kind IN ('expense', 'purchase_invoice') "
        "AND doc_date >= date_trunc('month', now())::date",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    return Decimal(str(row["total"])) if row and row["total"] is not None else Decimal("0")


def month_summary(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    """本月已入账汇总 + 按分类拆解(对标竞品「本月总消费」)。返回 {total,count,by_category:[..]}。

    by_category:[{name, amount, count}] 按金额降序;name 为空(无分类)归「未分类」由调用方填。
    """
    cur.execute(
        "SELECT c.name AS cat, COALESCE(SUM(d.grand_total), 0) AS amt, count(*) AS n "
        "FROM purchase_docs d "
        "LEFT JOIN expense_categories c "
        "  ON c.id = d.category_id AND c.tenant_id = d.tenant_id "
        "WHERE d.tenant_id = %s AND d.workspace_client_id = %s AND d.status = 'posted' "
        "AND d.doc_kind IN ('expense', 'purchase_invoice') "
        "AND d.doc_date >= date_trunc('month', now())::date "
        "GROUP BY c.name ORDER BY amt DESC",
        (tenant_id, workspace_client_id),
    )
    rows = cur.fetchall()
    by_cat = [
        {"name": r["cat"], "amount": Decimal(str(r["amt"])), "count": int(r["n"])} for r in rows
    ]
    total = sum((c["amount"] for c in by_cat), Decimal("0"))
    count = sum(c["count"] for c in by_cat)
    return {"total": total, "count": count, "by_category": by_cat}


def month_detail(cur, *, tenant_id: str, workspace_client_id: int, limit: int = 10) -> list[dict]:
    """本月已入账逐笔(对标竞品「查明细」)。新→旧,返回 [{date,amount,category,vendor}]。"""
    cur.execute(
        "SELECT d.doc_date, d.grand_total AS amt, c.name AS cat, s.name AS vendor "
        "FROM purchase_docs d "
        "LEFT JOIN expense_categories c ON c.id = d.category_id AND c.tenant_id = d.tenant_id "
        "LEFT JOIN suppliers s ON s.id = d.supplier_id AND s.tenant_id = d.tenant_id "
        "WHERE d.tenant_id = %s AND d.workspace_client_id = %s AND d.status = 'posted' "
        "AND d.doc_kind IN ('expense', 'purchase_invoice') "
        "AND d.doc_date >= date_trunc('month', now())::date "
        "ORDER BY d.doc_date DESC, d.created_at DESC LIMIT %s",
        (tenant_id, workspace_client_id, int(limit)),
    )
    return [
        {
            "date": r["doc_date"].isoformat() if r["doc_date"] else "",
            "amount": Decimal(str(r["amt"] or 0)),
            "category": r["cat"] or "",
            "vendor": r["vendor"] or "",
        }
        for r in cur.fetchall()
    ]


def knowledge_answer(cur, *, tenant_id: str, question: str) -> Optional[dict]:
    """接知识中心问答(带出处)。无来源/任何异常 → None(调用方诚实兜底"没找到")。

    accessible_ids=None:LINE 绑定者=本租户用户,可见本租户知识(租户内不限作用域)。
    """
    try:
        from services.knowledge import ask, embedding, search

        vec = embedding.embed_texts([question], is_query=True)[0]
        hits = search.search_chunks(
            cur, tenant_id=tenant_id, accessible_ids=None, query_vector=vec, limit=5
        )
        res = ask.answer_question(question, hits)
        if getattr(res, "no_answer", True):
            return None
        cites = [getattr(c, "filename", "") for c in (res.citations or [])]
        return {"answer": res.answer, "citations": [c for c in cites if c]}
    except Exception as e:  # noqa: BLE001
        logger.warning("[line qa] knowledge answer failed: %s", str(e)[:160])
        return None
