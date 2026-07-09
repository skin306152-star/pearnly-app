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


def append_event(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    step: str,
    event_type: str,
    payload: Optional[dict[str, Any]] = None,
    actor: str = "system",
) -> dict:
    """落一条事件,只追加。这是证据链底座和断点续跑的唯一恢复源。"""
    cur.execute(
        f"""
        INSERT INTO work_order_events (tenant_id, work_order_id, step, event_type, payload, actor)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s)
        RETURNING {_EVENT_COLUMNS}
        """,
        (
            tenant_id,
            work_order_id,
            step,
            event_type,
            json.dumps(payload or {}, ensure_ascii=False, default=str),
            actor,
        ),
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
