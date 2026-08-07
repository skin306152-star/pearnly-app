# -*- coding: utf-8 -*-
"""商品归并:把「按清洗品名分组」的历史行认领到一个商品主档。

目标两种给法(v1.1 · 2026-08-08):
  - target_product_id:并入本账套已存在的商品档;
  - new_product_name:目标本身还是名字轨(事务所账套常见 —— 整本账一个商品档都没有,
    v1 要求"目标必须已建档"等于主场景永远无解),代客建最小商品档(只 name_th + unit,
    其余列走表默认)再认领,目标自己的清洗名一并入组 —— 否则并完会留下一个同名的
    空名字轨行,报表上一件货两张卡。

只改 product_id 这一个分类字段,不碰任何金额列 —— 对已过账/已开出的历史单据也安全:
财务数字逐字节不变,只是"这行算哪个商品"的标签补上。同一清洗规则(grouping.name_key,
与展示清洗 item_name.clean 同一把尺子)找回的行才会被认领,防止把无关的行错并进去。

留操作日志(operation_logs,services.audit.store 现成写法):事后要能查"这个商品的历史
进出到底并过哪些行"。
"""

from __future__ import annotations

from typing import Optional

from services.audit import store as audit_store
from services.sales import products as products_svc
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
    cur, *, tenant_id: str, workspace_client_id: int, keys: set, product_id: str, target: str
) -> list:
    """归并一侧(采购/销售)清洗品名命中 keys 的历史行 → product_id。target 取 _MERGE_TARGETS
    白名单键。整侧一次扫描,不按 key 逐个跑 N 遍。"""
    spec = _MERGE_TARGETS[target]
    cur.execute(
        f"SELECT l.id, l.description FROM {spec['lines_table']} l "
        f"JOIN {spec['docs_table']} d ON d.id = l.{spec['join_col']} AND d.tenant_id = l.tenant_id "
        f"WHERE l.tenant_id = %s AND d.{spec['ws_col']} = %s AND l.product_id IS NULL",
        (tenant_id, workspace_client_id),
    )
    ids = [r["id"] for r in cur.fetchall() if grouping.name_key(r["description"]) in keys]
    if ids:
        # id 是 uuid 列:psycopg2 把 Python list 适配成 text[],无 ::uuid[] 转型会炸
        # "operator does not exist: uuid = text"(仓库血泪·同 test_workorder_uuid_any_cast.py)。
        cur.execute(
            f"UPDATE {spec['lines_table']} SET product_id = %s "
            "WHERE tenant_id = %s AND id = ANY(%s::uuid[])",
            (product_id, tenant_id, ids),
        )
    return ids


def _resolve_target(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    target_product_id: Optional[str],
    new_product_name: Optional[str],
    unit: Optional[str],
) -> Optional[tuple]:
    """(product_id, created) 或 None(目标非法)。二选一:已有商品档优先。"""
    if target_product_id:
        if not _product_exists(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            product_id=target_product_id,
        ):
            return None
        return target_product_id, False
    name = (new_product_name or "").strip()
    if not name:
        return None
    fields = {"name_th": name}
    if unit:
        fields["unit"] = unit
    row = products_svc.create_product(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, fields=fields
    )
    return str(row["id"]), True


def merge_into_product(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    name_keys: list,
    target_product_id: Optional[str],
    new_product_name: Optional[str],
    unit: Optional[str],
    actor: dict,
) -> Optional[dict]:
    """把一批归组钥匙 n:<name_key> 下的历史行认领到目标商品。目标非法或清洗后没有可并的
    名字 → None(路由层翻 422)。返回并过的行数,供前端提示"并了几行"。"""
    resolved = _resolve_target(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        target_product_id=target_product_id,
        new_product_name=new_product_name,
        unit=unit,
    )
    if resolved is None:
        return None
    product_id, created = resolved

    keys = {k for k in (grouping.name_key(n) for n in name_keys) if k}
    if created:
        # 代建目标自己的名字也入组,不留同名空名字轨。
        own = grouping.name_key(new_product_name)
        if own:
            keys.add(own)
    if not keys:
        return None

    purchase_ids = _merge_lines(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        keys=keys,
        product_id=product_id,
        target="purchase",
    )
    sales_ids = _merge_lines(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        keys=keys,
        product_id=product_id,
        target="sales",
    )

    audit_store.insert_operation_log(
        tenant_id,
        actor.get("id"),
        actor.get("username"),
        bool(actor.get("is_super_admin")),
        _ACTION,
        target_type="product",
        target_id=product_id,
        target_name=sorted(keys)[0],
        details={
            "workspace_client_id": workspace_client_id,
            "name_keys": sorted(keys),
            "product_created": created,
            "purchase_lines": len(purchase_ids),
            "sales_lines": len(sales_ids),
        },
    )
    return {
        "product_id": product_id,
        "product_created": created,
        "purchase_lines_merged": len(purchase_ids),
        "sales_lines_merged": len(sales_ids),
    }
