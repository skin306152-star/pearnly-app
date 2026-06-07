# -*- coding: utf-8 -*-
"""套账隔离 PO-1 · 默认套账回填(纯数据 · 加可空列 + 回填孤儿 · 不切任何读路径)。

设计见 docs/workspace-isolation/03-backfill-migration.md · 施工单 04 PO-1。

安全性(为什么这是"涉钱前最后一块安全砖"):
  - 纯加法:为每租户确保一个"默认套账" → 给运营表加【可空】workspace_client_id 列
    → 把 workspace_client_id IS NULL 的孤儿行回填到默认套账。
  - 老读路径不读新列,照跑 → 出问题停在这里零影响。
  - NOT NULL 收口【不在本 PO】:随各模块 PO 切完读写后再逐表收(见 04)。
  - 幂等:重跑不重复建套账、不重复改值(只动仍为 NULL 的行)。

⚠️ 必须先在 prod 库 dry-run(report())看影响行数,Zihao 过目后才 apply()。
   apply() 全程单事务,失败整体回滚。索引建议在事务外 CONCURRENTLY 建(见 runbook 05)。

表结构不确定的处理:运行时查 information_schema 自检——
  表是否存在 / 有没有 tenant_id 列 → 决定按 tenant 直映射还是按 user(经 users.tenant_id)映射。
  避免硬编码我对各表列名的猜测出错。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from core import db

logger = logging.getLogger("mr-pilot")

# 需要"加可空列 + 回填"的运营表(见 01-data-model 待回填清单)。
# ocr_history 不在此列:它早已有 workspace_client_id 列,只回填(见 _BACKFILL_ONLY)。
_ADD_AND_BACKFILL: List[str] = [
    "products",
    "product_units",
    "inventory_batches",
    "sales_documents",
    "document_number_sequences",
    "etax_submissions",
    "etax_channel_settings",
    "bank_reconcile_sessions",
    "recon_jobs",
    "vat_recon_tasks",
    "bank_recon_v2_task",
]

# 列已存在 · 仅回填(不 ADD COLUMN)。
_BACKFILL_ONLY: List[str] = ["ocr_history"]


def _table_exists(cur, table: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.tables " "WHERE table_schema='public' AND table_name=%s",
        (table,),
    )
    return cur.fetchone() is not None


def _column_exists(cur, table: str, column: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=%s AND column_name=%s",
        (table, column),
    )
    return cur.fetchone() is not None


def ensure_default_workspaces(cur) -> int:
    """为每个租户确保 ≥1 个套账;零套账的(B 类老租户)造一个默认套账。返回新建数量。

    默认套账 = 该租户最早的 workspace_clients(回填时也以"每租户最早一条"为默认,二者一致)。
    新建用 tenants.owner_user_id 作 user_id;owner 为空则回退该租户任一 owner/旧数据用户。
    """
    created = 0
    cur.execute("SELECT id, name, owner_user_id FROM tenants")
    tenants = cur.fetchall() or []
    for t in tenants:
        tid = t["id"]
        cur.execute("SELECT 1 FROM workspace_clients WHERE tenant_id = %s LIMIT 1", (tid,))
        if cur.fetchone():
            continue  # 已有套账(A 类)· 幂等跳过
        owner = t.get("owner_user_id")
        if not owner:
            cur.execute(
                "SELECT id FROM users WHERE tenant_id = %s "
                "AND (role = 'owner' OR role IS NULL) ORDER BY created_at LIMIT 1",
                (tid,),
            )
            row = cur.fetchone()
            owner = row["id"] if row else None
        if not owner:
            logger.warning("ensure_default_workspaces: tenant %s 无可用 owner · 跳过", tid)
            continue
        name = (t.get("name") or "默认账套").strip()[:200] or "默认账套"
        cur.execute(
            "INSERT INTO workspace_clients (tenant_id, user_id, name, is_active) "
            "VALUES (%s, %s, %s, TRUE)",
            (tid, owner, name),
        )
        created += 1
    return created


def add_workspace_columns(cur) -> List[str]:
    """给待回填表加【可空】workspace_client_id 列(可空 no-default = 元数据改 · 瞬时安全)。返回实改表。"""
    changed = []
    for table in _ADD_AND_BACKFILL:
        if not _table_exists(cur, table):
            continue
        if _column_exists(cur, table, "workspace_client_id"):
            continue
        cur.execute(f"ALTER TABLE {table} ADD COLUMN workspace_client_id BIGINT")
        changed.append(table)
    return changed


def _row_tenant_expr(cur, table: str) -> Optional[str]:
    """该表每行的"归属租户"SQL 表达式(别名 x = 该表)。

    关键:多张表同时有 tenant_id 和 user_id,且 tenant_id 只填了一部分
    (ocr_history 94/146 · bank_reconcile_sessions 1/4)。**按行** COALESCE:
    优先用行自己的 tenant_id,为空再经 user_id 找 users.tenant_id —— 否则按表二选一
    会让"有 user 无 tenant_id"的行(如 52 条识别记录)一条都回填不上。
    report() 与 _backfill_table 共用本表达式,确保估算 = 实际(不再分叉)。
    """
    has_tenant = _column_exists(cur, table, "tenant_id")
    has_user = _column_exists(cur, table, "user_id")
    user_lookup = "(SELECT u.tenant_id FROM users u WHERE u.id = x.user_id)"
    if has_tenant and has_user:
        return f"COALESCE(x.tenant_id, {user_lookup})"
    if has_tenant:
        return "x.tenant_id"
    if has_user:
        return user_lookup
    return None


def _backfill_table(cur, table: str) -> int:
    """把 workspace_client_id IS NULL 的行回填到其归属租户的"最早套账"。返回回填行数。

    归属租户 = _row_tenant_expr(按行 COALESCE)。租户无关(无 tenant_id 又找不到 user 的租户)
    的行不匹配,保持 NULL(dry-run 会报出,单独处理)。
    """
    if not _table_exists(cur, table) or not _column_exists(cur, table, "workspace_client_id"):
        return 0
    texpr = _row_tenant_expr(cur, table)
    if not texpr:
        logger.warning("_backfill_table: %s 既无 tenant_id 也无 user_id · 跳过", table)
        return 0
    cur.execute(
        "WITH dw AS (SELECT DISTINCT ON (tenant_id) tenant_id, id AS ws "
        "FROM workspace_clients WHERE tenant_id IS NOT NULL "
        "ORDER BY tenant_id, created_at, id) "
        f"UPDATE {table} x SET workspace_client_id = dw.ws FROM dw "
        f"WHERE x.workspace_client_id IS NULL AND dw.tenant_id = {texpr}"
    )
    return cur.rowcount


def _willhave_ws_sql(tenant_col: str) -> str:
    """子条件:tenant_col(某行的租户列)指向的租户在 apply 后【会有】套账可落 —
    要么现在已有套账,要么能建默认套账(owner 非空 / 有可当 owner 的用户)。

    别名 uo/w/t 避免与外层 x/u 冲突('owner' 为 SQL 字面量,非用户输入,安全)。
    """
    return (
        f"(EXISTS (SELECT 1 FROM workspace_clients w WHERE w.tenant_id = {tenant_col}) "
        f"OR EXISTS (SELECT 1 FROM tenants t WHERE t.id = {tenant_col} "
        "AND (t.owner_user_id IS NOT NULL OR EXISTS (SELECT 1 FROM users uo "
        "WHERE uo.tenant_id = t.id AND (uo.role = 'owner' OR uo.role IS NULL)))))"
    )


def report() -> Dict[str, object]:
    """DRY-RUN:**纯 SELECT**,零 mutation、不加锁(和 app 日常读一样安全)。Zihao 过目用。

    不走"做了再回滚"(get_cursor 正常路径不显式 rollback → 会把带 ALTER 锁的未提交事务留在
    连接池阻塞线上)。直接用 SELECT 算 apply 后的真实结果:
      - tenants_needing_default / _creatable:几个租户缺默认套账 / 其中几个能真建(有 owner)。
      - 每表 orphans(列已存在=NULL 行数;列未存在=全表行数,因加列后全为 NULL)
        / would_fill(其租户 apply 后会有套账的)/ remaining(填不了:租户无 owner 或无租户)。
    remaining 用 _willhave_ws_sql 取反计,与 apply 的实际回填范围一致(避免估算 alias 阴影偏差)。
    """
    out: Dict[str, object] = {
        "tenants_needing_default": 0,
        "tenants_default_creatable": 0,
        "tables": {},
    }
    all_tables = _ADD_AND_BACKFILL + _BACKFILL_ONLY
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT count(*) AS c FROM tenants t "
            "WHERE NOT EXISTS (SELECT 1 FROM workspace_clients w WHERE w.tenant_id = t.id)"
        )
        out["tenants_needing_default"] = int(cur.fetchone()["c"])
        cur.execute(
            f"SELECT count(*) AS c FROM tenants x WHERE NOT EXISTS "
            "(SELECT 1 FROM workspace_clients w WHERE w.tenant_id = x.id) "
            f"AND {_willhave_ws_sql('x.id')}"
        )
        out["tenants_default_creatable"] = int(cur.fetchone()["c"])

        tables: Dict[str, object] = {}
        for table in all_tables:
            if not _table_exists(cur, table):
                tables[table] = "(表不存在)"
                continue
            has_col = _column_exists(cur, table, "workspace_client_id")
            orphan = "workspace_client_id IS NULL" if has_col else "TRUE"
            cur.execute(f"SELECT count(*) AS c FROM {table} WHERE {orphan}")
            orphans = int(cur.fetchone()["c"])
            texpr = _row_tenant_expr(cur, table)
            if texpr:
                cur.execute(
                    f"SELECT count(*) AS c FROM {table} x "
                    f"WHERE {orphan} AND NOT {_willhave_ws_sql(texpr)}"
                )
                remaining = int(cur.fetchone()["c"])
            else:
                remaining = orphans
            tables[table] = {
                "orphans": orphans,
                "would_fill": orphans - remaining,
                "remaining": remaining,
                "had_column": has_col,
            }
        out["tables"] = tables
    return out


def apply() -> Dict[str, object]:
    """真执行:单事务内 建默认套账 + 加列 + 回填,失败整体回滚。返回汇总。

    ⚠️ 调用前必须先 report() 过目。索引在事务外 CONCURRENTLY 另建(见 runbook 05)。
    """
    summary: Dict[str, object] = {}
    all_tables = _ADD_AND_BACKFILL + _BACKFILL_ONLY
    with db.get_cursor(commit=True) as cur:
        summary["default_workspaces_created"] = ensure_default_workspaces(cur)
        summary["columns_added"] = add_workspace_columns(cur)
        summary["filled"] = {t: _backfill_table(cur, t) for t in all_tables}
    logger.info("workspace_backfill.apply 完成:%s", summary)
    return summary
