# -*- coding: utf-8 -*-
"""商品归并:把「按清洗品名分组」的历史行,补认成某个商品主档(v1 · 只在 products 支持
账套级隔离时提供 —— 已勘察确认 services/sales/products.py 每条语句都 WHERE tenant_id +
workspace_client_id,故本功能可安全指向"这个账套已建好的商品")。

只改 product_id 这一个分类字段,不碰任何金额列 —— 对已过账/已开出的历史单据也安全:
财务数字逐字节不变,只是"这行算哪个商品"的标签补上。同一清洗规则(grouping.name_key,
与展示清洗 item_name.clean 同一把尺子)找回的行才会被认领,防止把无关的行错并进去。
v1 不代客建档:目标商品必须已存在,建新商品走商品主档现有 CRUD。

留操作日志(operation_logs,services.audit.store 现成写法):事后要能查"这个商品的历史
进出到底并过哪些行"。
"""

from __future__ import annotations

from typing import Optional

from services.audit import store as audit_store
from services.stockcard import grouping

_ACTION = "stockcard.merge_product"


def _product_exists(cur, *, tenant_id: str, workspace_client_id: int, product_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM products WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, product_id),
    )
    return cur.fetchone() is not None


#  target → (行表, 头表, 行→头的外键列, 头表上的账套归属列)。两侧结构一致,只列名不同;
# 白名单常量(不是外部输入),防以后改成动态目标时悄悄开 SQL 拼接注入面。
_MERGE_TARGETS = {
    "purchase": {
        "lines_table": "purchase_lines",
        "docs_table": "purchase_docs",
        "join_col": "purchase_doc_id",
        "ws_col": "workspace_client_id",
    },
    "sales": {
        "lines_table": "sales_document_lines",
        "docs_table": "sales_documents",
        "join_col": "document_id",
        "ws_col": "seller_workspace_client_id",
    },
}


def _merge_lines(
    cur, *, tenant_id: str, workspace_client_id: int, key: str, product_id: str, target: str
) -> list:
    """归并一侧(采购/销售)清洗品名命中 key 的历史行 → product_id。target 取 _MERGE_TARGETS
    白名单键。"""
    spec = _MERGE_TARGETS[target]
    cur.execute(
        f"SELECT l.id, l.description FROM {spec['lines_table']} l "
        f"JOIN {spec['docs_table']} d ON d.id = l.{spec['join_col']} AND d.tenant_id = l.tenant_id "
        f"WHERE l.tenant_id = %s AND d.{spec['ws_col']} = %s AND l.product_id IS NULL",
        (tenant_id, workspace_client_id),
    )
    ids = [r["id"] for r in cur.fetchall() if grouping.name_key(r["description"]) == key]
    if ids:
        # id 是 uuid 列:psycopg2 把 Python list 适配成 text[],无 ::uuid[] 转型会炸
        # "operator does not exist: uuid = text"(仓库血泪·同 test_workorder_uuid_any_cast.py)。
        cur.execute(
            f"UPDATE {spec['lines_table']} SET product_id = %s "
            "WHERE tenant_id = %s AND id = ANY(%s::uuid[])",
            (product_id, tenant_id, ids),
        )
    return ids


def _merge_purchase_lines(
    cur, *, tenant_id: str, workspace_client_id: int, key: str, product_id: str
) -> list:
    return _merge_lines(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        key=key,
        product_id=product_id,
        target="purchase",
    )


def _merge_sales_lines(
    cur, *, tenant_id: str, workspace_client_id: int, key: str, product_id: str
) -> list:
    return _merge_lines(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        key=key,
        product_id=product_id,
        target="sales",
    )


def merge_into_product(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    name_key: str,
    product_id: Optional[str],
    actor: dict,
) -> Optional[dict]:
    """把归组钥匙 n:<name_key> 下的历史行认领到 product_id。缺 product_id 或商品不存在于
    本账套 → None(路由层翻 422)。返回并过的行数,供前端提示"并了几行"。"""
    key = grouping.name_key(name_key)
    if not key or not product_id:
        return None
    if not _product_exists(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, product_id=product_id
    ):
        return None

    purchase_ids = _merge_purchase_lines(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        key=key,
        product_id=product_id,
    )
    sales_ids = _merge_sales_lines(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        key=key,
        product_id=product_id,
    )

    audit_store.insert_operation_log(
        tenant_id,
        actor.get("id"),
        actor.get("username"),
        bool(actor.get("is_super_admin")),
        _ACTION,
        target_type="product",
        target_id=product_id,
        target_name=key,
        details={
            "workspace_client_id": workspace_client_id,
            "purchase_lines": len(purchase_ids),
            "sales_lines": len(sales_ids),
        },
    )
    return {
        "product_id": product_id,
        "purchase_lines_merged": len(purchase_ids),
        "sales_lines_merged": len(sales_ids),
    }
