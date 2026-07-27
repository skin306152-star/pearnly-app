# -*- coding: utf-8 -*-
"""管家会话/消息/任务三表 DAL(steward_sessions / steward_messages / steward_tasks)。

任务不复用工单:工单是会计业务对象(五态机/租约/reaper/SoD),管家任务是交互编排记录,
混用会污染工单语义(矩阵/看板/reaper 会把一次查询当成一张真月度工单)。管家将来真派出去
的业务动作仍落工单表,两者并存不矛盾 —— 迁移 0088 顶注写了同一条理由。

B3 起 steward_tasks 自己就是队列(不另建 job 表):任务表就是进度表,再建一张 job 表会
出现两处状态要对齐。入队即 running(worker_id 空 = 还没被认领),认领走 FOR UPDATE SKIP
LOCKED + 租约,失联/超时由 worker.heal_stale 如实收 failed。

建表:alembic/versions/0088_steward_tables.py + 0089_steward_task_async.py 逐字对齐留档,
ensure_once 首用自愈(prod alembic 指针停 0020,靠 ensure 补建,照 front_desk 先例)。

四态诚实的落点在这里:任务先以 running 落库、跑完再改 done/failed/cancelled —— 进程
中途死掉时左窗看到的是「还在跑」,随后被失联收口成 failed,不会假装「从来没这条任务」。
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

ROLE_USER = "user"
ROLE_STEWARD = "steward"

# 任务态(与前端 B1 状态组件一一对应:ai-i18n-steward.js 的 stw_status_*)。
TASK_RUNNING = "running"
TASK_DONE = "done"
TASK_FAILED = "failed"
TASK_WAITING_USER = "waiting_user"
TASK_CANCELLED = "cancelled"

# 收尾守卫:只有这两个态允许被改成终态 —— cancelled/done/failed 落定后,晚到的
# worker 结果或重复取消都写不动(取消与执行赛跑时,先落者赢)。
_FINISHABLE = (TASK_RUNNING, TASK_WAITING_USER)

# 授权卡态(payload.authorization.status)。状态机在 authz.py,常量放这层是 import 方向
# 决定的:authz 依赖 copy 依赖本模块,反向 import 成环。
AUTH_PENDING = "pending"
AUTH_APPROVED = "approved"
AUTH_REJECTED = "rejected"
AUTH_EXPIRED = "expired"

# 步骤态(同上,stw_step_*)。waiting_auth = 写工具停在授权卡上等人批
# (orchestrator._enqueue 铸卡时落,当前注册表全只读、第一个写工具挂上即出现)。
STEP_DONE = "done"
STEP_RUNNING = "running"
STEP_QUEUED = "queued"
STEP_WAITING_AUTH = "waiting_auth"
STEP_FAILED = "failed"

_DEFAULT_TIMEOUT_S = 300

_SESSION_COLUMNS = "id, tenant_id, user_id, title, created_at, last_active_at"
_MESSAGE_COLUMNS = "id, tenant_id, session_id, role, text, tool_trace, task_id, created_at"
_TASK_COLUMNS = (
    "id, tenant_id, session_id, title, status, steps, artifacts, payload, timeout_s, "
    "worker_id, lease_until, error_code, error_message, created_at, finished_at"
)


def default_timeout_s() -> int:
    """任务超时秒数(env STEWARD_TASK_TIMEOUT_S 可配,默认 300)。入队时定格进任务行,
    改配置只影响新任务 —— 在跑的任务不因配置变化改判。"""
    try:
        value = int(os.environ.get("STEWARD_TASK_TIMEOUT_S", "") or _DEFAULT_TIMEOUT_S)
    except ValueError:
        value = _DEFAULT_TIMEOUT_S
    return max(1, value)


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
        payload jsonb NOT NULL DEFAULT '{}'::jsonb,
        timeout_s integer NOT NULL DEFAULT 300,
        worker_id text,
        lease_until timestamptz,
        error_code text,
        error_message text,
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
    "CREATE INDEX IF NOT EXISTS ix_steward_tasks_active "
    "ON steward_tasks (created_at) WHERE status = 'running'",
)

# 0088 建的存量表补 0089 的列(新装由上面 CREATE 一步到位;两条路都幂等)。
_TASK_ALTERS = (
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS payload jsonb NOT NULL DEFAULT '{}'::jsonb",
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS timeout_s integer NOT NULL DEFAULT 300",
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS worker_id text",
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS lease_until timestamptz",
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS error_code text",
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS error_message text",
)

_RLS_TABLES = ("steward_sessions", "steward_tasks", "steward_messages")

_ensured = False


def ensure_tables() -> None:
    """幂等建三表 + 补列 + 索引 + tenant RLS(首用自愈)。独立事务,先于业务写事务调。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        for ddl in _TASK_ALTERS:
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
    payload: Optional[dict] = None,
    timeout_s: Optional[int] = None,
) -> dict:
    """建任务行。payload 是后台执行所需的全部上下文(tool/args/lang/执行身份)——
    异步执行没有请求可依附,身份必须随行存,worker 绝不"看全租户"。"""
    cur.execute(
        f"""
        INSERT INTO steward_tasks (tenant_id, session_id, title, status, steps, artifacts,
                                   payload, timeout_s)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
        RETURNING {_TASK_COLUMNS}
        """,
        (
            tenant_id,
            session_id,
            title,
            status,
            json.dumps(steps or [], ensure_ascii=False, default=str),
            json.dumps(artifacts or [], ensure_ascii=False, default=str),
            json.dumps(payload or {}, ensure_ascii=False, default=str),
            int(timeout_s or default_timeout_s()),
        ),
    )
    return dict(cur.fetchone())


def claim_next_task(worker_id: str, *, grace_s: int = 60) -> Optional[dict]:
    """原子认领一条没人认的任务(FOR UPDATE SKIP LOCKED,多工人不抢同一条)。
    租约 = 任务自己的 timeout_s + 宽限:工人死了租约必过期,heal_stale 才有判据。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(
            f"""
            UPDATE steward_tasks
            SET worker_id = %s,
                lease_until = now() + make_interval(secs => timeout_s + %s)
            WHERE id = (
                SELECT id FROM steward_tasks
                WHERE status = %s AND worker_id IS NULL
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING {_TASK_COLUMNS}
            """,
            (str(worker_id), int(grace_s), TASK_RUNNING),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_steps(cur, *, tenant_id: str, task_id: str, steps: list) -> bool:
    """中途更新步骤流水,不碰终态。只在还 running 时生效 —— 晚到的进度写不掉终态。"""
    cur.execute(
        "UPDATE steward_tasks SET steps = %s::jsonb "
        "WHERE tenant_id = %s AND id = %s AND status = %s",
        (
            json.dumps(steps or [], ensure_ascii=False, default=str),
            tenant_id,
            task_id,
            TASK_RUNNING,
        ),
    )
    return cur.rowcount > 0


def finish_task(
    cur,
    *,
    tenant_id: str,
    task_id: str,
    status: str,
    steps: list,
    artifacts: Optional[list] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> bool:
    """收尾:改终态 + 覆盖步骤/产物 + 清租约,finished_at 一并落。
    只允许从 running/waiting_user 收(_FINISHABLE)—— 已 cancelled 的任务,晚到的
    worker 结果被这里拒收(返回 False),绝不复活。失败必须带错误码与人话原因。"""
    cur.execute(
        "UPDATE steward_tasks SET status = %s, steps = %s::jsonb, artifacts = %s::jsonb, "
        "error_code = %s, error_message = %s, worker_id = NULL, lease_until = NULL, "
        "finished_at = now() WHERE tenant_id = %s AND id = %s AND status = ANY(%s)",
        (
            status,
            json.dumps(steps or [], ensure_ascii=False, default=str),
            json.dumps(artifacts or [], ensure_ascii=False, default=str),
            error_code,
            error_message,
            tenant_id,
            task_id,
            list(_FINISHABLE),
        ),
    )
    return cur.rowcount > 0


def cancel_task(cur, *, tenant_id: str, task_id: str, steps: list) -> Optional[dict]:
    """取消:只有还在跑的能取消;已收尾的写不动(返回 None,幂等由路由层兜)。"""
    cur.execute(
        f"UPDATE steward_tasks SET status = %s, steps = %s::jsonb, worker_id = NULL, "
        f"lease_until = NULL, finished_at = now() "
        f"WHERE tenant_id = %s AND id = %s AND status = %s RETURNING {_TASK_COLUMNS}",
        (
            TASK_CANCELLED,
            json.dumps(steps or [], ensure_ascii=False, default=str),
            tenant_id,
            task_id,
            TASK_RUNNING,
        ),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def list_stale_tasks(
    cur, *, tenant_id: Optional[str] = None, task_id: Optional[str] = None, grace_s: int = 60
) -> list[dict]:
    """找失联任务并锁行(SKIP LOCKED:工人正拿着的行不算失联)。两类:
    ①认领过但租约过期(进程死在半路);②从没被认领且早超时限(后台执行不在线,
    也覆盖 0089 前同步时代残留的 running 行)。收口动作在 worker.heal_stale。"""
    where = ["status = %s"]
    params: list = [TASK_RUNNING]
    if tenant_id is not None:
        where.append("tenant_id = %s")
        params.append(tenant_id)
    if task_id is not None:
        where.append("id = %s")
        params.append(task_id)
    where.append(
        "((lease_until IS NOT NULL AND lease_until < now()) "
        "OR (lease_until IS NULL AND created_at < now() - make_interval(secs => timeout_s + %s)))"
    )
    params.append(int(grace_s))
    cur.execute(
        f"SELECT {_TASK_COLUMNS} FROM steward_tasks WHERE {' AND '.join(where)} "
        "FOR UPDATE SKIP LOCKED",
        tuple(params),
    )
    return [dict(r) for r in cur.fetchall()]


def cancellable(row: dict) -> bool:
    """这条任务现在还能不能取消(路由的闸 + 前端画不画取消按钮,同一份判据)。

    写工具一旦 running 就已经批准过、多半已经把活投给桥了 —— 取消只能落个 cancelled 假象
    (「后面的步骤没有跑」),票却可能已经进了账套,作业号也一并丢。注册表外的工具名照旧
    可取消:它在 tools.run 那里根本执行不到,取消无害。
    """
    from services.steward import registry

    if (row.get("status") or "") != TASK_RUNNING:
        return False
    spec = registry.get((row.get("payload") or {}).get("tool"))
    return spec is None or spec.readonly


def fail_steps(steps: list, detail: str) -> list:
    """把还没跑完的步骤统一标 failed(第一个被改的步骤带上人话原因)。
    已 done 的保持 done —— 状态诚实:跑完的步骤不因整单失败被抹掉。"""
    out = []
    detail_used = False
    for step in steps or []:
        patched = dict(step)
        if patched.get("state") != STEP_DONE:
            patched["state"] = STEP_FAILED
            if not detail_used:
                patched["detail"] = detail
                detail_used = True
        out.append(patched)
    return out


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

    payload/worker_id/lease_until 不外泄(内部执行上下文与队列机制,含身份信息);
    失败时错误码 + 人话原因一并给(四态诚实:说不清为什么失败 = 假绿的另一种写法)。
    """
    out = {
        "task_id": str(row["id"]),
        "title": row.get("title") or "",
        "status": row.get("status") or TASK_RUNNING,
        "started_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "finished_at": row["finished_at"].isoformat() if row.get("finished_at") else None,
        "agent_count": 1,
        # 前端据此决定画不画「取消」:在跑的写活取消不了(见 cancellable),摆一个点了会 409
        # 的按钮比不摆更糟。
        "cancellable": cancellable(row),
        "steps": row.get("steps") or [],
        "artifacts": row.get("artifacts") or [],
    }
    if row.get("error_code"):
        out["error_code"] = row["error_code"]
        out["error_reason"] = row.get("error_message") or ""
    # 懒 import:authz 模块级依赖本模块,卡片投影只能函数级反向取(不然成环)。
    from services.steward.authz import public_authorization_card

    if card := public_authorization_card((row.get("payload") or {}).get("authorization")):
        out["authorization"] = card
    return out
