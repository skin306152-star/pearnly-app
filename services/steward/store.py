# -*- coding: utf-8 -*-
"""管家会话/消息/任务三表 DAL(steward_sessions / steward_messages / steward_tasks)。

任务不复用工单:工单是会计业务对象(五态机/租约/reaper/SoD),管家任务是交互编排记录,
混用会污染工单语义(矩阵/看板/reaper 会把一次查询当成一张真月度工单)。管家将来真派出去
的业务动作仍落工单表,两者并存不矛盾 —— 迁移 0088 顶注写了同一条理由。

建表:alembic/versions/0088_steward_tables.py 逐字对齐留档 + ensure_once 首用自愈
(prod alembic 指针停 0020,靠 ensure 补建,照 front_desk.contract_store 先例)。

四态诚实的落点在这里:任务先以 running 落库、跑完再改 done/failed/waiting_user —— 进程
中途死掉时左窗看到的是「还在跑」而不是「这条任务从来不存在」。
"""

from __future__ import annotations

import json
from typing import Any, Optional

ROLE_USER = "user"
ROLE_STEWARD = "steward"

# 任务态(与前端 B1 状态组件一一对应:ai-i18n-steward.js 的 stw_status_*)。
TASK_RUNNING = "running"
TASK_DONE = "done"
TASK_FAILED = "failed"
TASK_WAITING_USER = "waiting_user"

# 步骤态(同上,stw_step_*)。waiting_auth 留给 B3 的授权卡,M1 只读不会产出。
STEP_DONE = "done"
STEP_RUNNING = "running"
STEP_QUEUED = "queued"
STEP_WAITING_AUTH = "waiting_auth"
STEP_FAILED = "failed"

_SESSION_COLUMNS = "id, tenant_id, user_id, title, created_at, last_active_at"
_MESSAGE_COLUMNS = "id, tenant_id, session_id, role, text, tool_trace, task_id, created_at"
_TASK_COLUMNS = (
    "id, tenant_id, session_id, title, status, steps, artifacts, created_at, finished_at"
)

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS steward_sessions (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        user_id text NOT NULL,
        title text,
        created_at timestamptz NOT NULL DEFAULT now(),
        last_active_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS steward_tasks (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        session_id uuid REFERENCES steward_sessions (id) ON DELETE CASCADE,
        title text NOT NULL DEFAULT '',
        status text NOT NULL DEFAULT 'running',
        steps jsonb NOT NULL DEFAULT '[]'::jsonb,
        artifacts jsonb NOT NULL DEFAULT '[]'::jsonb,
        created_at timestamptz NOT NULL DEFAULT now(),
        finished_at timestamptz
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS steward_messages (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        session_id uuid NOT NULL REFERENCES steward_sessions (id) ON DELETE CASCADE,
        role text NOT NULL,
        text text NOT NULL DEFAULT '',
        tool_trace jsonb NOT NULL DEFAULT '[]'::jsonb,
        task_id uuid,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
)

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_steward_sessions_tenant "
    "ON steward_sessions (tenant_id, last_active_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_steward_messages_session "
    "ON steward_messages (tenant_id, session_id, created_at)",
    "CREATE INDEX IF NOT EXISTS ix_steward_tasks_session "
    "ON steward_tasks (tenant_id, session_id, created_at DESC)",
)

_RLS_TABLES = ("steward_sessions", "steward_tasks", "steward_messages")

_ensured = False


def ensure_tables() -> None:
    """幂等建三表 + 索引 + tenant RLS(首用自愈)。独立事务,先于业务写事务调。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, *_RLS_TABLES)


def ensure_once() -> None:
    """进程内幂等包装(端点首用调,避免每请求 DDL)。"""
    global _ensured
    if _ensured:
        return
    ensure_tables()
    _ensured = True


# ── 会话 ────────────────────────────────────────────────────


def create_session(cur, *, tenant_id: str, user_id: str, title: Optional[str] = None) -> dict:
    cur.execute(
        f"INSERT INTO steward_sessions (tenant_id, user_id, title) "
        f"VALUES (%s, %s, %s) RETURNING {_SESSION_COLUMNS}",
        (tenant_id, str(user_id), title),
    )
    return dict(cur.fetchone())


def get_session(cur, *, tenant_id: str, session_id: str, user_id: str) -> Optional[dict]:
    """按 (租户, 会话, 建会话的人) 取。管家会话是私人工作记录,同租户别人也不给看。"""
    cur.execute(
        f"SELECT {_SESSION_COLUMNS} FROM steward_sessions "
        "WHERE tenant_id = %s AND id = %s AND user_id = %s",
        (tenant_id, session_id, str(user_id)),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def set_title_if_empty(cur, *, tenant_id: str, session_id: str, title: str) -> None:
    """首句话当会话标题(只在还没标题时写,后面几轮不覆盖)。"""
    cur.execute(
        "UPDATE steward_sessions SET title = %s "
        "WHERE tenant_id = %s AND id = %s AND (title IS NULL OR title = '')",
        (title[:120], tenant_id, session_id),
    )


def touch_session(cur, *, tenant_id: str, session_id: str) -> None:
    cur.execute(
        "UPDATE steward_sessions SET last_active_at = now() WHERE tenant_id = %s AND id = %s",
        (tenant_id, session_id),
    )


# ── 消息 ────────────────────────────────────────────────────


def add_message(
    cur,
    *,
    tenant_id: str,
    session_id: str,
    role: str,
    text: str,
    tool_trace: Optional[list] = None,
    task_id: Optional[str] = None,
) -> dict:
    """落一条消息。tool_trace 是本轮工具轨迹 [{tool, ok, error}](审计留痕,照 agent 先例)。"""
    cur.execute(
        f"""
        INSERT INTO steward_messages (tenant_id, session_id, role, text, tool_trace, task_id)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s)
        RETURNING {_MESSAGE_COLUMNS}
        """,
        (
            tenant_id,
            session_id,
            role,
            text or "",
            json.dumps(tool_trace or [], ensure_ascii=False, default=str),
            task_id,
        ),
    )
    return dict(cur.fetchone())


def list_messages(cur, *, tenant_id: str, session_id: str, limit: int = 200) -> list[dict]:
    cur.execute(
        f"SELECT {_MESSAGE_COLUMNS} FROM steward_messages "
        "WHERE tenant_id = %s AND session_id = %s ORDER BY created_at, id LIMIT %s",
        (tenant_id, session_id, limit),
    )
    return [dict(r) for r in cur.fetchall()]


# ── 任务 ────────────────────────────────────────────────────


def create_task(
    cur,
    *,
    tenant_id: str,
    session_id: str,
    title: str,
    status: str,
    steps: list,
    artifacts: Optional[list] = None,
) -> dict:
    cur.execute(
        f"""
        INSERT INTO steward_tasks (tenant_id, session_id, title, status, steps, artifacts)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb)
        RETURNING {_TASK_COLUMNS}
        """,
        (
            tenant_id,
            session_id,
            title,
            status,
            json.dumps(steps or [], ensure_ascii=False, default=str),
            json.dumps(artifacts or [], ensure_ascii=False, default=str),
        ),
    )
    return dict(cur.fetchone())


def finish_task(
    cur,
    *,
    tenant_id: str,
    task_id: str,
    status: str,
    steps: list,
    artifacts: Optional[list] = None,
) -> None:
    """收尾:改终态 + 覆盖步骤/产物。running 以外的态都算收尾,finished_at 一并落。"""
    cur.execute(
        "UPDATE steward_tasks SET status = %s, steps = %s::jsonb, artifacts = %s::jsonb, "
        "finished_at = now() WHERE tenant_id = %s AND id = %s",
        (
            status,
            json.dumps(steps or [], ensure_ascii=False, default=str),
            json.dumps(artifacts or [], ensure_ascii=False, default=str),
            tenant_id,
            task_id,
        ),
    )


def get_task(cur, *, tenant_id: str, task_id: str) -> Optional[dict]:
    cur.execute(
        f"SELECT {_TASK_COLUMNS} FROM steward_tasks WHERE tenant_id = %s AND id = %s",
        (tenant_id, task_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def latest_task_id(cur, *, tenant_id: str, session_id: str) -> Optional[str]:
    """本会话最近一条任务 id(会话详情的 current_task_id:前端一进来就能挂上左窗)。"""
    cur.execute(
        "SELECT id FROM steward_tasks WHERE tenant_id = %s AND session_id = %s "
        "ORDER BY created_at DESC, id DESC LIMIT 1",
        (tenant_id, session_id),
    )
    row = cur.fetchone()
    return str(row["id"]) if row else None


# ── 前端视图 ────────────────────────────────────────────────


def public_message(row: dict) -> dict[str, Any]:
    """消息 → 前端视图。tool_trace 不外泄(内部审计字段,含工具名/错误码)。"""
    out = {
        "id": str(row["id"]),
        "role": row["role"],
        "text": row.get("text") or "",
        "ts": row["created_at"].isoformat() if row.get("created_at") else None,
    }
    if row.get("task_id"):
        out["task_id"] = str(row["task_id"])
    return out


def public_task(row: dict) -> dict[str, Any]:
    """任务 → 左窗数据(前端直接喂 B1 状态组件)。

    agent_count 恒 1:M1 一轮只派一个工具,诚实报 1;多 Agent 编排是 B3 以后的事,
    这里绝不为了好看写个大于真实值的数(状态诚实)。
    """
    return {
        "task_id": str(row["id"]),
        "title": row.get("title") or "",
        "status": row.get("status") or TASK_RUNNING,
        "started_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "finished_at": row["finished_at"].isoformat() if row.get("finished_at") else None,
        "agent_count": 1,
        "steps": row.get("steps") or [],
        "artifacts": row.get("artifacts") or [],
    }
