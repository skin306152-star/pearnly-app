# -*- coding: utf-8 -*-
"""工单制 DAL(M0 数据地基 · 4 表)。

`cur` 由调用方(engine.py 起)注入,一个状态机步骤内的多次写落在同一事务(同
services/pos/payment_settings.py 惯例),不在本模块内自开连接。金额字段本域暂无
(钱字段落在 work_order_deliverables.numbers 快照 jsonb,由算税 handler 负责精度);
jsonb 载荷一律 json.dumps 走参数化,不拼字符串。

幂等键铁律(任务包 §3):
  - work_orders 靠 (tenant_id, workspace_client_id, period, intent) 唯一索引,
    open_work_order 用 INSERT ... ON CONFLICT DO UPDATE(空操作)+ RETURNING 一次拿到
    「新建或已存在」的行,不必先 SELECT 再 INSERT(避免竞态开出两张单)。
  - work_order_items 靠 (tenant_id, work_order_id, dedupe_key) 唯一索引,同样单句
    upsert;dedupe_key 为空则每次都是新行(intake 阶段允许同工单内多条无指纹项)。
  - work_order_deliverables 靠 (tenant_id, work_order_id, kind) 唯一索引,重跑 package
    步覆盖同一 kind 的产物而不是堆积。
  - work_order_events 只追加:本模块只提供 append_event / list_events,没有
    update/delete 路径——证据链和断点续跑都靠这张表不可变。
"""

from __future__ import annotations

import json
from typing import Any, Optional

_EVENT_COLUMNS = "id, tenant_id, work_order_id, step, event_type, payload, actor, created_at"

_runtime_ensured = False


def ensure_runtime() -> None:
    """建 C-1 运行时加固列/索引(租约 + 事件幂等键),自开独立事务提交(照 ai_usage dual-run)。

    进程内幂等 flag。必须由入口点(routes /run、runner.advance、真库测试 setUp)在「尚未开
    任何锁住工单表的事务」时调——ALTER 要 ACCESS EXCLUSIVE 锁,若在已 SELECT/INSERT 过工单表
    的 open txn 里懒触发会与该 txn 的锁互卡。故这里独立连接 + 入口点提前调,DAL 写函数本身不再
    懒建列(假定列已就位)。prod alembic 停 0020,靠这条自愈补 0066 的列。
    """
    global _runtime_ensured
    if _runtime_ensured:
        return
    from core import db
    from services.workorder import schema

    with db.get_cursor(commit=True) as cur:
        schema.ensure_runtime_hardening(cur)
    _runtime_ensured = True


_ITEM_COLUMNS = (
    "id, tenant_id, work_order_id, source, kind, file_ref, ocr_history_id, "
    "status, flag_reason, dedupe_key, created_at, updated_at"
)
_DELIVERABLE_COLUMNS = "id, tenant_id, work_order_id, kind, artifact_path, numbers, created_at"


def open_work_order(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    period: str,
    intent: str = "monthly_vat",
) -> dict:
    """开单,重复开单幂等返回既有单(同客户同期同意图只有一张)。"""
    cur.execute(
        """
        INSERT INTO work_orders (tenant_id, workspace_client_id, period, intent)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (tenant_id, workspace_client_id, period, intent)
        DO UPDATE SET updated_at = work_orders.updated_at
        RETURNING id, tenant_id, workspace_client_id, period, intent, status,
                  current_step, created_at, updated_at
        """,
        (tenant_id, workspace_client_id, period, intent),
    )
    return dict(cur.fetchone())


_WO_COLUMNS = (
    "id, tenant_id, workspace_client_id, period, intent, status, "
    "current_step, created_at, updated_at"
)


def list_work_orders(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: Optional[int] = None,
    period: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """列该租户工单,可按账套/账期/状态筛,倒序分页。可选筛选走 `%s IS NULL OR col = %s`
    的静态谓词(不动态拼 SQL 结构,值全参数化)——看板/列表读侧用。"""
    cur.execute(
        f"SELECT {_WO_COLUMNS} FROM work_orders "
        "WHERE tenant_id = %s "
        "AND (%s::bigint IS NULL OR workspace_client_id = %s::bigint) "
        "AND (%s::text IS NULL OR period = %s::text) "
        "AND (%s::text IS NULL OR status = %s::text) "
        "ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s",
        (
            tenant_id,
            workspace_client_id,
            workspace_client_id,
            period,
            period,
            status,
            status,
            limit,
            offset,
        ),
    )
    return [dict(r) for r in cur.fetchall()]


def count_work_orders(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: Optional[int] = None,
    period: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    """列表总数(分页 total)。同 list_work_orders 的筛选谓词。"""
    cur.execute(
        "SELECT count(*) AS n FROM work_orders "
        "WHERE tenant_id = %s "
        "AND (%s::bigint IS NULL OR workspace_client_id = %s::bigint) "
        "AND (%s::text IS NULL OR period = %s::text) "
        "AND (%s::text IS NULL OR status = %s::text)",
        (tenant_id, workspace_client_id, workspace_client_id, period, period, status, status),
    )
    return int(cur.fetchone()["n"])


def get_work_order(cur, *, tenant_id: str, work_order_id: str) -> Optional[dict]:
    cur.execute(
        "SELECT id, tenant_id, workspace_client_id, period, intent, status, "
        "current_step, created_at, updated_at FROM work_orders "
        "WHERE tenant_id = %s AND id = %s",
        (tenant_id, work_order_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def set_status(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    status: str,
    current_step: Optional[str] = None,
) -> None:
    """推进/停住工单状态。current_step 省略时只改 status(如 review/archive 两态)。"""
    if current_step is None:
        cur.execute(
            "UPDATE work_orders SET status = %s, updated_at = now() "
            "WHERE tenant_id = %s AND id = %s",
            (status, tenant_id, work_order_id),
        )
    else:
        cur.execute(
            "UPDATE work_orders SET status = %s, current_step = %s, updated_at = now() "
            "WHERE tenant_id = %s AND id = %s",
            (status, current_step, tenant_id, work_order_id),
        )


def acquire_run_lease(
    cur, *, tenant_id: str, work_order_id: str, owner: str, ttl_seconds: int
) -> bool:
    """抢 /run 推进租约(单句条件 UPDATE,原子)。抢到返 True,被他人未过期租约占着返 False。

    可抢条件:无人持有 / 自己已持有(续租)/ 上一持有者租约已过期(接管)。过期由 now()
    与 run_lease_expires_at 比较判定,无需后台回收线程。双终端并发 /run 各自跑这条 UPDATE,
    Postgres 行锁串行化 → 恰一个 RETURNING 到行。
    """
    cur.execute(
        """
        UPDATE work_orders
           SET run_lease_owner = %s,
               run_lease_expires_at = now() + make_interval(secs => %s),
               updated_at = now()
         WHERE tenant_id = %s AND id = %s
           AND (run_lease_owner IS NULL
                OR run_lease_owner = %s
                OR run_lease_expires_at IS NULL
                OR run_lease_expires_at < now())
        RETURNING id
        """,
        (owner, int(ttl_seconds), tenant_id, work_order_id, owner),
    )
    return cur.fetchone() is not None


def release_run_lease(cur, *, tenant_id: str, work_order_id: str, owner: str) -> None:
    """释放租约(仅当仍是自己持有——防误释放别人接管后的租约)。"""
    cur.execute(
        "UPDATE work_orders SET run_lease_owner = NULL, run_lease_expires_at = NULL, "
        "updated_at = now() WHERE tenant_id = %s AND id = %s AND run_lease_owner = %s",
        (tenant_id, work_order_id, owner),
    )


def run_lease_holder(cur, *, tenant_id: str, work_order_id: str) -> Optional[dict]:
    """当前有效租约(过期视为无);无 → None。观测/详情用,不参与抢占决策。"""
    cur.execute(
        "SELECT run_lease_owner, run_lease_expires_at FROM work_orders "
        "WHERE tenant_id = %s AND id = %s AND run_lease_owner IS NOT NULL "
        "AND (run_lease_expires_at IS NULL OR run_lease_expires_at > now())",
        (tenant_id, work_order_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def append_event(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    step: str,
    event_type: str,
    payload: Optional[dict[str, Any]] = None,
    actor: str = "system",
    dedupe_key: Optional[str] = None,
) -> dict:
    """落一条事件,只追加。这是证据链底座和断点续跑的唯一恢复源。

    带 dedupe_key 时幂等:同 (work_order_id, step, event_type, dedupe_key) 只落一条,重放
    (并发/续跑重入)命中部分唯一索引 ON CONFLICT DO NOTHING,返回既有那条而非再插一行。
    dedupe_key 省略 = 老路径逐字节不变(step_started 等可重复事件不受约束)。
    """
    payload_json = json.dumps(payload or {}, ensure_ascii=False, default=str)
    if dedupe_key is None:
        cur.execute(
            f"""
            INSERT INTO work_order_events
                (tenant_id, work_order_id, step, event_type, payload, actor)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            RETURNING {_EVENT_COLUMNS}
            """,
            (tenant_id, work_order_id, step, event_type, payload_json, actor),
        )
        return dict(cur.fetchone())

    cur.execute(
        f"""
        INSERT INTO work_order_events
            (tenant_id, work_order_id, step, event_type, payload, actor, dedupe_key)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
        ON CONFLICT (tenant_id, work_order_id, step, event_type, dedupe_key)
            WHERE dedupe_key IS NOT NULL
        DO NOTHING
        RETURNING {_EVENT_COLUMNS}
        """,
        (tenant_id, work_order_id, step, event_type, payload_json, actor, dedupe_key),
    )
    row = cur.fetchone()
    if row:
        return dict(row)
    # 已存在同幂等键的事件(重放):取既有那条返回,不重记。
    cur.execute(
        f"SELECT {_EVENT_COLUMNS} FROM work_order_events "
        "WHERE tenant_id = %s AND work_order_id = %s AND step = %s "
        "AND event_type = %s AND dedupe_key = %s ORDER BY id LIMIT 1",
        (tenant_id, work_order_id, step, event_type, dedupe_key),
    )
    return dict(cur.fetchone())


def list_events(cur, *, tenant_id: str, work_order_id: str) -> list[dict]:
    """按落库顺序(id 递增 = 发生顺序)返回全部事件,供重放/证据索引用。"""
    cur.execute(
        f"SELECT {_EVENT_COLUMNS} FROM work_order_events "
        "WHERE tenant_id = %s AND work_order_id = %s ORDER BY id",
        (tenant_id, work_order_id),
    )
    return [dict(r) for r in cur.fetchall()]


def add_item(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    source: str,
    kind: str = "unknown",
    file_ref: Optional[str] = None,
    ocr_history_id: Optional[str] = None,
    status: str = "pending",
    flag_reason: Optional[str] = None,
    dedupe_key: Optional[str] = None,
) -> dict:
    """登记一件料。带 dedupe_key 时幂等(intake 重跑不重复登记同一份文件)。"""
    cur.execute(
        f"""
        INSERT INTO work_order_items
            (tenant_id, work_order_id, source, kind, file_ref, ocr_history_id,
             status, flag_reason, dedupe_key)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tenant_id, work_order_id, dedupe_key) WHERE dedupe_key IS NOT NULL
        DO UPDATE SET updated_at = work_order_items.updated_at
        RETURNING {_ITEM_COLUMNS}
        """,
        (
            tenant_id,
            work_order_id,
            source,
            kind,
            file_ref,
            ocr_history_id,
            status,
            flag_reason,
            dedupe_key,
        ),
    )
    return dict(cur.fetchone())


def list_items(
    cur, *, tenant_id: str, work_order_id: str, status: Optional[str] = None
) -> list[dict]:
    if status is None:
        cur.execute(
            f"SELECT {_ITEM_COLUMNS} FROM work_order_items "
            "WHERE tenant_id = %s AND work_order_id = %s ORDER BY created_at",
            (tenant_id, work_order_id),
        )
    else:
        cur.execute(
            f"SELECT {_ITEM_COLUMNS} FROM work_order_items "
            "WHERE tenant_id = %s AND work_order_id = %s AND status = %s ORDER BY created_at",
            (tenant_id, work_order_id, status),
        )
    return [dict(r) for r in cur.fetchall()]


def get_item(cur, *, tenant_id: str, work_order_id: str, item_id: str) -> Optional[dict]:
    """取单件料,并同时校验它属于该工单(裁决接口验 item 归属用)。越界返 None。"""
    cur.execute(
        f"SELECT {_ITEM_COLUMNS} FROM work_order_items "
        "WHERE tenant_id = %s AND work_order_id = %s AND id = %s",
        (tenant_id, work_order_id, item_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def update_item(
    cur,
    *,
    tenant_id: str,
    item_id: str,
    status: Optional[str] = None,
    kind: Optional[str] = None,
    flag_reason: Optional[str] = None,
) -> None:
    """sort/classify 步用:定堆(kind)/判结论(status)/记原因(flag_reason)。省略的字段不动。"""
    set_clause, params = [], []
    for col, val in (("status", status), ("kind", kind), ("flag_reason", flag_reason)):
        if val is not None:
            set_clause.append(f"{col} = %s")
            params.append(val)
    if not set_clause:
        return
    set_clause.append("updated_at = now()")
    params.extend([tenant_id, item_id])
    cur.execute(
        f"UPDATE work_order_items SET {', '.join(set_clause)} WHERE tenant_id = %s AND id = %s",
        tuple(params),
    )


def upsert_deliverable(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    kind: str,
    artifact_path: Optional[str] = None,
    numbers: Optional[dict[str, Any]] = None,
) -> dict:
    """产出一份交付物,重跑同一 kind 覆盖而非累加(package 步幂等)。"""
    cur.execute(
        f"""
        INSERT INTO work_order_deliverables
            (tenant_id, work_order_id, kind, artifact_path, numbers)
        VALUES (%s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (tenant_id, work_order_id, kind)
        DO UPDATE SET artifact_path = EXCLUDED.artifact_path, numbers = EXCLUDED.numbers
        RETURNING {_DELIVERABLE_COLUMNS}
        """,
        (
            tenant_id,
            work_order_id,
            kind,
            artifact_path,
            json.dumps(numbers or {}, ensure_ascii=False, default=str),
        ),
    )
    return dict(cur.fetchone())


def list_deliverables(cur, *, tenant_id: str, work_order_id: str) -> list[dict]:
    cur.execute(
        f"SELECT {_DELIVERABLE_COLUMNS} FROM work_order_deliverables "
        "WHERE tenant_id = %s AND work_order_id = %s ORDER BY created_at",
        (tenant_id, work_order_id),
    )
    return [dict(r) for r in cur.fetchall()]
