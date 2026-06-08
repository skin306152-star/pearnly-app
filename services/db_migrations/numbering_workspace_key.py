# -*- coding: utf-8 -*-
"""套账隔离 PO-7b · 连号计数器按主体(document_number_sequences)。

设计见 docs/workspace-isolation/06-po7b-numbering-proposal.md。RD 合规:事务所代多公司做账时,
每法人主体发票号必须独立连续、跨主体不撞。计号键从 (tenant, doc_type, prefix, period)
扩到 (tenant, ws, doc_type, prefix, period)。

prod 无 alembic 钩子 → 启动 ensure 自应用(部署即随重启迁移,代码与迁移同上,不会"代码先行")。
幂等 + 安全分级:
  1. 列 workspace_client_id(PO-1 已加 · 此处 IF NOT EXISTS 兜底)。
  2. 把仍为 NULL 的行回填到各租户默认套账(最早一条),保证新唯一索引无 NULL 歧义、号序映射正确。
  3. 建唯一索引 uq_dns_ws(单主体下与旧 4 列 PK 等价 · 号序零变化)。
  4. 仅当全表零 NULL 主体时才 DROP 旧 4 列 PK —— 否则保留(旧 PK 在=兼容路径仍安全)。
     DROP 后唯一性由 uq_dns_ws 接管,第二主体首次开票不再撞旧 PK。

为何 DROP 受 NULL 守门:旧 PK 是全表级约束,只要还有一行主体为空就不能安全去掉(否则两条
空主体同键行会重复计号)。回填后正常零 NULL → PK 落地;万一某租户无可落套账留了 NULL →
跳过 DROP,等下次回填补齐再切。单主体 prod 现状即"零 NULL → 切成功"。
"""

from __future__ import annotations

import logging

from core import db

logger = logging.getLogger("mr-pilot")

_TABLE = "document_number_sequences"
_INDEX = "uq_dns_ws"
_OLD_PK = "document_number_sequences_pkey"


def _table_exists(cur) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.tables " "WHERE table_schema='public' AND table_name=%s",
        (_TABLE,),
    )
    return cur.fetchone() is not None


def _migration_done(cur) -> bool:
    """已完全迁移 = 新唯一索引在 + 旧 PK 已下线 → 后续每次重启跳过全表回填/计数扫描。"""
    cur.execute("SELECT 1 FROM pg_indexes WHERE indexname = %s", (_INDEX,))
    if cur.fetchone() is None:
        return False
    cur.execute("SELECT 1 FROM pg_constraint WHERE conname = %s", (_OLD_PK,))
    return cur.fetchone() is None


def ensure_numbering_workspace_key() -> None:
    """幂等迁移连号计数器到按主体键(startup 调 · alembic 缺位时的 prod 自应用)。"""
    with db.get_cursor(commit=True) as cur:
        if not _table_exists(cur):
            return  # 全新/部分库:开票首次取号时建表逻辑另处,无可迁移
        if _migration_done(cur):
            return  # 稳态:索引就绪且旧 PK 已下线,无需再扫表

        cur.execute(f"ALTER TABLE {_TABLE} ADD COLUMN IF NOT EXISTS workspace_client_id BIGINT")
        # NULL 主体回填到本租户最早套账(与 PO-1 / default_workspace_id 口径一致)。
        cur.execute(f"""
            WITH dw AS (
                SELECT DISTINCT ON (tenant_id) tenant_id, id AS ws
                FROM workspace_clients WHERE tenant_id IS NOT NULL
                ORDER BY tenant_id, created_at, id
            )
            UPDATE {_TABLE} s SET workspace_client_id = dw.ws
            FROM dw WHERE s.workspace_client_id IS NULL AND dw.tenant_id = s.tenant_id
            """)
        cur.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {_INDEX} ON {_TABLE} "
            "(tenant_id, workspace_client_id, doc_type, prefix, period)"
        )
        cur.execute(f"SELECT count(*) AS c FROM {_TABLE} WHERE workspace_client_id IS NULL")
        if int(cur.fetchone()["c"]) == 0:
            cur.execute(f"ALTER TABLE {_TABLE} DROP CONSTRAINT IF EXISTS {_OLD_PK}")
            logger.info("numbering_workspace_key: uq_dns_ws 就绪 + 旧 PK 已下线(按主体连号生效)")
        else:
            logger.warning("numbering_workspace_key: 仍有 NULL 主体行 · 保留旧 PK(等回填补齐再切)")
