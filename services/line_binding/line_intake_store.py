# -*- coding: utf-8 -*-
"""客户收料暂存池 client_intake_staging(LN-1)· 数据访问层。

客户在 LINE 发的票据先落这张池,不直接进工单——并入工单(LN-2)是会计确认动作。
幂等锚 = line_message_id 全局唯一(LINE 平台消息 id):redelivery / 竞发重投同 id
只落一行。status 词汇 pending|merged|discarded 在此单源化,LN-2 消费不另造词
(C4 血泪:状态词零臆造)。建表范式照 line_client_contact 的首用幂等自愈 +
apply_tenant_rls,alembic 0074 双跑同一 DDL。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

STATUS_PENDING = "pending"
STATUS_MERGED = "merged"
STATUS_DISCARDED = "discarded"

SOURCE_DM = "dm"
SOURCE_GROUP = "group"

_TABLE = """
CREATE TABLE IF NOT EXISTS client_intake_staging (
    id                  uuid   PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           uuid   NOT NULL,
    workspace_client_id bigint NOT NULL,
    line_message_id     text   NOT NULL,
    file_path           text   NOT NULL,
    sha256              text   NOT NULL,
    source              text   NOT NULL,
    sender_line_user_id text,
    suggested_period    text,
    status              text   NOT NULL DEFAULT 'pending',
    created_at          timestamptz NOT NULL DEFAULT now()
)
"""

_INDEX_MSG_UNIQ = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_client_intake_staging_msg
    ON client_intake_staging (line_message_id)
"""

_INDEX_CLIENT_STATUS = """
CREATE INDEX IF NOT EXISTS ix_client_intake_staging_client
    ON client_intake_staging (tenant_id, workspace_client_id, status)
"""

_TABLE_NAME = "client_intake_staging"

_COLUMNS = (
    "id, tenant_id, workspace_client_id, line_message_id, file_path, sha256, "
    "source, sender_line_user_id, suggested_period, status, created_at"
)


def ensure_table() -> None:
    """幂等建表 + 索引 + RLS(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        cur.execute(_INDEX_MSG_UNIQ)
        cur.execute(_INDEX_CLIENT_STATUS)
        apply_tenant_rls(cur, _TABLE_NAME)


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由调用方 fail-safe。"""
    try:
        return fn()
    except Exception as e:
        if _TABLE_NAME not in str(e):
            raise
        ensure_table()
        return fn()


def insert_staging(
    tenant_id,
    workspace_client_id,
    *,
    line_message_id: str,
    file_path: str,
    sha256: str,
    source: str,
    sender_line_user_id: Optional[str] = None,
    suggested_period: Optional[str] = None,
) -> Optional[bool]:
    """落一行暂存。True=新行;False=同 message_id 已在池(幂等不双记);None=故障。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO client_intake_staging "
                "(tenant_id, workspace_client_id, line_message_id, file_path, sha256, "
                " source, sender_line_user_id, suggested_period) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (line_message_id) DO NOTHING "
                "RETURNING id",
                (
                    str(tenant_id),
                    workspace_client_id,
                    line_message_id,
                    file_path,
                    sha256,
                    source,
                    sender_line_user_id,
                    suggested_period,
                ),
            )
            row = cur.fetchone()
        return row is not None

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_intake_store] insert_staging failed", exc_info=True)
        return None


def list_staging(tenant_id, workspace_client_id, period: Optional[str] = None) -> list:
    """LN-2 收料页读侧:该客户的暂存料,period 给了按 suggested_period 过滤(含孤儿留空行
    不过滤掉——查不到账期的料也要有人认领,故 period 过滤只匹配非空相等)。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM client_intake_staging "
                "WHERE tenant_id = %s AND workspace_client_id = %s "
                "AND (%s::text IS NULL OR suggested_period = %s::text OR suggested_period IS NULL) "
                "ORDER BY created_at",
                (str(tenant_id), workspace_client_id, period, period),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_intake_store] list_staging failed", exc_info=True)
        return []


def count_pending(tenant_id, workspace_client_id) -> int:
    """LN-2 收料页角标:该客户待并入的暂存件数。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                "SELECT count(*) AS n FROM client_intake_staging "
                "WHERE tenant_id = %s AND workspace_client_id = %s AND status = %s",
                (str(tenant_id), workspace_client_id, STATUS_PENDING),
            )
            row = cur.fetchone()
        return int(row["n"]) if row else 0

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_intake_store] count_pending failed", exc_info=True)
        return 0


def latest_open_period(tenant_id, workspace_client_id) -> Optional[str]:
    """suggested_period 默认值:该客户最近一张未归档工单的账期,没有 → None(留空,
    月度开单时自动认领)。status 词从 workorder.engine 单源 import,不手打字符串。"""
    from core import db
    from services.workorder import engine

    try:
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                "SELECT period FROM work_orders "
                "WHERE tenant_id = %s AND workspace_client_id = %s AND status <> %s "
                "ORDER BY created_at DESC LIMIT 1",
                (str(tenant_id), workspace_client_id, engine.STATUS_ARCHIVE),
            )
            row = cur.fetchone()
        return row["period"] if row else None
    except Exception:
        logger.warning("[line_intake_store] latest_open_period failed", exc_info=True)
        return None


def client_display_name(tenant_id, workspace_client_id) -> Optional[str]:
    """回执文案用的客户名(workspace 层 get_workspace_client 要 user_id,webhook 没有,
    故这里按 tenant 直查)。查不到 → None,调用方给兜底文案。"""
    from core import db

    try:
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                "SELECT name FROM workspace_clients WHERE id = %s AND tenant_id = %s",
                (workspace_client_id, str(tenant_id)),
            )
            row = cur.fetchone()
        return row["name"] if row else None
    except Exception:
        logger.warning("[line_intake_store] client_display_name failed", exc_info=True)
        return None
