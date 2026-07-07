# -*- coding: utf-8 -*-
"""用户可编辑的费用识别关键词规则(Phase 2 · 费用数据页「识别关键词」)。

不另起引擎:规则就是 关键词→科目,与「纠错自学」同构,故复用 expense_learned 表 + source 列
区分(user_rule)。归类管线本就学习优先(line_expense._fill_category / image_category.smart_category
第一步查 expense_learned)→ 用户加词立即生效,category_ai 写死规则退成出厂默认。见
docs/... 与记忆 expense-product-system-and-rule-center-plan。

本模块只管 user_rule 行的增/删/列 + 本月命中统计 + 灰度闸;读取端零改动(lookup_learned
子串匹配已覆盖)。隔离靠调用方传 tenant_id + workspace_client_id,值一律参数化。
"""

from __future__ import annotations

import logging

from services.expense import conversation

logger = logging.getLogger(__name__)

FLAG_KEY = "expense_keyword_rules"


def rules_enabled(tenant_id: str) -> bool:
    """全量开(Zihao 2026-07-07 拍板放量)· 保留紧急总闸:平台设置 expense_keyword_rules 被超管
    显式 enabled=false 时才关。无记录 / 读失败 → 开(不因设置读抖动关掉已放量功能)。tenant_id
    保留以便日后按租户回收(现全量忽略)。图片路只匹配 user_rule(见 match_category)→ 全量开
    对存量数据零归类变化(user_rule 表为空,要用户自己加词才生效)。"""
    try:
        from services.platform_settings import store as ps

        row = ps.get_setting(FLAG_KEY)
        return row is None or bool(row.get("enabled"))
    except Exception as e:  # noqa: BLE001 — 设置读失败不该关掉已放量功能
        logger.warning("[keyword_rules] flag read defaulted-on: %s", str(e)[:160])
        return True


def match_category(cur, *, tenant_id: str, workspace_client_id: int, text: str):
    """图片路用户关键词步:闸开 + 只匹配用户显式规则(source='user_rule',不含隐式纠错)。票面
    文字子串命中 → 返回该科目 dict;否则 None。只认 user_rule 是有意的:全量开时对存量数据零
    归类变化(表空),要用户在费用数据页明确挂词才影响归类。"""
    if not rules_enabled(tenant_id):
        return None
    low = (text or "").lower()
    cur.execute(
        "SELECT keyword, category_id, subcategory_id, category_name, subcategory_name "
        "FROM expense_learned "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND source = 'user_rule'",
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


def _resolve_target(cur, *, tenant_id: str, workspace_client_id: int, target_id: str):
    """把用户点的那一节点解析成 (category_id, subcategory_id, category_name, subcategory_name)。

    小类(parent_id 非空)→ category=父、subcategory=自身;大类 → category=自身、subcategory=None。
    找不到 → None(拒绝给不存在/跨套账的科目挂词)。
    """
    cur.execute(
        "SELECT c.name AS sub_name, c.parent_id, p.name AS cat_name "
        "FROM expense_categories c LEFT JOIN expense_categories p ON p.id = c.parent_id "
        "WHERE c.tenant_id = %s AND c.workspace_client_id = %s AND c.id = %s",
        (tenant_id, workspace_client_id, target_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    if row["parent_id"]:
        return str(row["parent_id"]), str(target_id), row["cat_name"] or "", row["sub_name"] or ""
    return str(target_id), None, row["sub_name"] or "", ""


def list_rules(cur, *, tenant_id: str, workspace_client_id: int) -> list[dict]:
    """列出本套账所有用户关键词规则(source='user_rule')。按科目分组由前端做。"""
    cur.execute(
        "SELECT keyword, category_id, subcategory_id, category_name, subcategory_name "
        "FROM expense_learned "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND source = 'user_rule' "
        "ORDER BY keyword",
        (tenant_id, workspace_client_id),
    )
    return [
        {
            "keyword": r["keyword"],
            "category_id": str(r["category_id"]) if r["category_id"] else None,
            "subcategory_id": str(r["subcategory_id"]) if r["subcategory_id"] else None,
        }
        for r in cur.fetchall()
    ]


def add_rule(
    cur, *, tenant_id: str, workspace_client_id: int, target_id: str, keyword: str
) -> dict | None:
    """给某科目(通常小类)挂一个识别关键词。返回 {keyword, category_id, subcategory_id};
    空词 / 科目不存在 → None。关键词归一小写(与 lookup_learned 匹配一致)。"""
    kw = (keyword or "").strip().lower()
    if not kw:
        return None
    resolved = _resolve_target(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, target_id=target_id
    )
    if not resolved:
        return None
    cat_id, sub_id, cat_name, sub_name = resolved
    conversation.learn(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        keyword=kw,
        category_id=cat_id,
        subcategory_id=sub_id,
        category_name=cat_name,
        subcategory_name=sub_name,
        source="user_rule",
    )
    return {"keyword": kw, "category_id": cat_id, "subcategory_id": sub_id}


def delete_rule(cur, *, tenant_id: str, workspace_client_id: int, keyword: str) -> bool:
    """删一条用户关键词规则(只删 user_rule,不碰纠错自学行)。返回是否删到。"""
    kw = (keyword or "").strip().lower()
    if not kw:
        return False
    cur.execute(
        "DELETE FROM expense_learned "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND keyword = %s AND source = 'user_rule'",
        (tenant_id, workspace_client_id, kw),
    )
    return cur.rowcount > 0


def hit_counts(cur, *, tenant_id: str, workspace_client_id: int) -> dict[str, int]:
    """本月归到各小类的采购单数(按 doc_date 当月 · 去重 doc)。只读统计,任何异常 → 空(不拖垮页面)。"""
    try:
        cur.execute(
            "SELECT l.subcategory_id AS sid, count(DISTINCT l.purchase_doc_id) AS n "
            "FROM purchase_lines l "
            "JOIN purchase_docs d ON d.id = l.purchase_doc_id AND d.tenant_id = l.tenant_id "
            "WHERE l.tenant_id = %s AND d.workspace_client_id = %s "
            "AND l.subcategory_id IS NOT NULL "
            "AND d.doc_date >= date_trunc('month', now())::date "
            "GROUP BY l.subcategory_id",
            (tenant_id, workspace_client_id),
        )
        return {str(r["sid"]): int(r["n"]) for r in cur.fetchall()}
    except Exception as e:  # noqa: BLE001 — 命中数是锦上添花,查不到就不显,绝不 500
        logger.warning("[keyword_rules] hit_counts skipped: %s", str(e)[:160])
        return {}
