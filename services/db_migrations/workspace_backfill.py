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
from typing import Dict, List

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


def _count_orphans(cur, table: str) -> int:
    if not _table_exists(cur, table) or not _column_exists(cur, table, "workspace_client_id"):
        return 0
    cur.execute(f"SELECT count(*) AS c FROM {table} WHERE workspace_client_id IS NULL")
    return int(cur.fetchone()["c"])


def _backfill_table(cur, table: str) -> int:
    """把 workspace_client_id IS NULL 的行回填到"每租户最早套账"。返回回填行数。

    按表是否有 tenant_id 列选映射路径:
      有 tenant_id  → 直接按 t.tenant_id 映射。
      无 tenant_id  → 按 user_id 经 users.tenant_id 映射(对账 v1 session 等)。
    租户无关(tenant_id IS NULL 的个人模式旧数据)→ 不匹配,保持 NULL(dry-run 会报出,单独处理)。
    """
    if not _table_exists(cur, table) or not _column_exists(cur, table, "workspace_client_id"):
        return 0
    dw_cte = (
        "WITH dw AS (SELECT DISTINCT ON (tenant_id) tenant_id, id AS ws "
        "FROM workspace_clients WHERE tenant_id IS NOT NULL "
        "ORDER BY tenant_id, created_at, id)"
    )
    if _column_exists(cur, table, "tenant_id"):
        cur.execute(
            f"{dw_cte} UPDATE {table} t SET workspace_client_id = dw.ws "
            "FROM dw WHERE t.tenant_id = dw.tenant_id AND t.workspace_client_id IS NULL",
        )
    elif _column_exists(cur, table, "user_id"):
        cur.execute(
            f"{dw_cte} UPDATE {table} t SET workspace_client_id = dw.ws "
            "FROM users u JOIN dw ON dw.tenant_id = u.tenant_id "
            "WHERE t.user_id = u.id AND t.workspace_client_id IS NULL",
        )
    else:
        logger.warning("_backfill_table: %s 既无 tenant_id 也无 user_id · 跳过", table)
        return 0
    return cur.rowcount


def report() -> Dict[str, object]:
    """DRY-RUN:不改任何数据,只报"会发生什么"。Zihao 过目用。

    单事务内做完所有改动 → 统计 → ROLLBACK(零残留),从而拿到回填后的真实剩余 NULL 数。
    """
    out: Dict[str, object] = {"tenants_needing_default": 0, "tables": {}, "remaining_null": {}}
    all_tables = _ADD_AND_BACKFILL + _BACKFILL_ONLY
    with db.get_cursor() as cur:  # 不 commit · 块结束自动回滚
        # 会新建几个默认套账
        cur.execute(
            "SELECT count(*) AS c FROM tenants t "
            "WHERE NOT EXISTS (SELECT 1 FROM workspace_clients w WHERE w.tenant_id = t.id)"
        )
        out["tenants_needing_default"] = int(cur.fetchone()["c"])
        # 回填前各表孤儿数
        before = {t: _count_orphans(cur, t) for t in all_tables}
        # 在同一事务里真做一遍(随后回滚)拿到回填后剩余
        ensure_default_workspaces(cur)
        add_workspace_columns(cur)
        filled = {t: _backfill_table(cur, t) for t in all_tables}
        after = {t: _count_orphans(cur, t) for t in all_tables}
        out["tables"] = {t: {"orphans_before": before[t], "filled": filled[t]} for t in all_tables}
        out["remaining_null"] = {t: after[t] for t in all_tables if after[t] > 0}
        # 不 commit → 自动回滚,数据库零变化
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
