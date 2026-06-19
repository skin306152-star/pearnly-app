# -*- coding: utf-8 -*-
"""一句话记账 · 多轮澄清会话态 + 可学习归类词典(doc 10 §4.3/§4.4 · 14 §3/§4)。

多轮澄清:缺金额(但确是记账意图)→ 存半成品 + 反问一句;用户补一句金额 → 合并出卡。
  会话态走 DB(prod 多 worker · 内存不共享)· 短 TTL(默认 15 分钟)· 每 LINE 用户至多一条。
可学习词典:用户改过的 关键词→科目 记下(expense_learned)· 下次同词直接对。归类时学习优先。
钱无关 · 隔离走 tenant_id + workspace_client_id · 参数化。
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Optional

from services.expense.expense_draft import ExpenseDraft

PENDING_TTL_MINUTES = 15


def _draft_to_json(draft: ExpenseDraft) -> str:
    """ExpenseDraft → JSON(Decimal→str · 存 jsonb)。"""
    d = draft.model_dump()
    for k, v in list(d.items()):
        if isinstance(v, Decimal):
            d[k] = str(v)
    return json.dumps(d, ensure_ascii=False)


def _draft_from_json(raw) -> ExpenseDraft:
    data = raw if isinstance(raw, dict) else json.loads(raw or "{}")
    return ExpenseDraft(**{k: v for k, v in data.items() if v is not None})


def save_pending(
    cur,
    *,
    line_user_id: str,
    tenant_id: str,
    workspace_client_id: int,
    draft: ExpenseDraft,
    missing: str,
) -> None:
    """存/覆盖该用户的待补会话态(每用户一条 · upsert)。"""
    cur.execute(
        "INSERT INTO line_pending_entry "
        "(line_user_id, tenant_id, workspace_client_id, draft, missing, created_at) "
        "VALUES (%s, %s, %s, %s::jsonb, %s, now()) "
        "ON CONFLICT (line_user_id) DO UPDATE SET "
        "tenant_id = EXCLUDED.tenant_id, workspace_client_id = EXCLUDED.workspace_client_id, "
        "draft = EXCLUDED.draft, missing = EXCLUDED.missing, created_at = now()",
        (line_user_id, tenant_id, workspace_client_id, _draft_to_json(draft), missing),
    )


def pop_pending(
    cur, *, line_user_id: str, ttl_minutes: int = PENDING_TTL_MINUTES
) -> Optional[dict]:
    """取出并删除该用户未过期的会话态;过期/不存在 → None(过期行也删)。"""
    cur.execute(
        "DELETE FROM line_pending_entry WHERE line_user_id = %s "
        "RETURNING tenant_id, workspace_client_id, draft, missing, "
        "(created_at > now() - (%s || ' minutes')::interval) AS fresh",
        (line_user_id, str(int(ttl_minutes))),
    )
    row = cur.fetchone()
    if not row or not row["fresh"]:
        return None
    return {
        "tenant_id": str(row["tenant_id"]),
        "workspace_client_id": row["workspace_client_id"],
        "draft": _draft_from_json(row["draft"]),
        "missing": row["missing"],
    }


def peek_pending(
    cur, *, line_user_id: str, ttl_minutes: int = PENDING_TTL_MINUTES
) -> Optional[dict]:
    """看一眼会话态(不删 · 带 missing 供分类型:补金额 vs 待确认更正);过期/无 → None。"""
    cur.execute(
        "SELECT tenant_id, workspace_client_id, draft, missing, "
        "(created_at > now() - (%s || ' minutes')::interval) AS fresh "
        "FROM line_pending_entry WHERE line_user_id = %s",
        (str(int(ttl_minutes)), line_user_id),
    )
    row = cur.fetchone()
    if not row or not row["fresh"]:
        return None
    return {
        "tenant_id": str(row["tenant_id"]),
        "workspace_client_id": row["workspace_client_id"],
        "draft": _draft_from_json(row["draft"]),
        "missing": row["missing"],
    }


def clear_pending(cur, *, line_user_id: str) -> None:
    cur.execute("DELETE FROM line_pending_entry WHERE line_user_id = %s", (line_user_id,))


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
) -> None:
    """记住 关键词→科目(用户改过一次 · 网页复核屏纠正时调)。空关键词忽略。"""
    kw = (keyword or "").strip().lower()
    if not kw:
        return
    cur.execute(
        "INSERT INTO expense_learned "
        "(tenant_id, workspace_client_id, keyword, category_id, subcategory_id, "
        "category_name, subcategory_name, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, now()) "
        "ON CONFLICT (tenant_id, workspace_client_id, keyword) DO UPDATE SET "
        "category_id = EXCLUDED.category_id, subcategory_id = EXCLUDED.subcategory_id, "
        "category_name = EXCLUDED.category_name, subcategory_name = EXCLUDED.subcategory_name, "
        "updated_at = now()",
        (
            tenant_id,
            workspace_client_id,
            kw,
            category_id,
            subcategory_id,
            category_name,
            subcategory_name,
        ),
    )
