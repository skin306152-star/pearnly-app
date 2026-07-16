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

# run 租约 + 死亡判据 DAL 拆在 run_leases.py(单文件 <500 铁律),re-export 保持调用方
# (runner/reaper/routes/测试)的 store.* 口径不变,实现单源在彼。
from services.workorder.run_leases import (  # noqa: F401
    _DEAD_RUN_PREDICATE,
    acquire_run_lease,
    claim_dead_run,
    list_dead_runs,
    release_run_lease,
    renew_run_lease,
    run_lease_holder,
)

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
    "id, tenant_id, work_order_id, source, kind, file_ref, original_name, ocr_history_id, "
    "status, flag_reason, dedupe_key, created_at, updated_at"
)
_DELIVERABLE_COLUMNS = (
    "id, tenant_id, work_order_id, kind, version, artifact_path, numbers, created_at"
)


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


def list_event_actors(
    cur, *, tenant_id: str, work_order_id: str, step: str, event_type: str
) -> list[str]:
    """某类事件的 actor 序列(按发生序)。收尸人算自动重跑预算只需 run/run_requested 的
    actor,不必整条事件流搬回来(吃 ix_wo_events_wo 前缀,窄读)。"""
    cur.execute(
        "SELECT actor FROM work_order_events "
        "WHERE tenant_id = %s AND work_order_id = %s AND step = %s AND event_type = %s "
        "ORDER BY id",
        (tenant_id, work_order_id, step, event_type),
    )
    return [r["actor"] if isinstance(r, dict) else r[0] for r in cur.fetchall()]


def last_step_done_payload(
    cur, *, tenant_id: str, work_order_id: str, step: str
) -> Optional[dict[str, Any]]:
    """窄取某步最后一条 step_done 的 payload(效率5:银行对账裁决校验免全量事件流回放)。

    与 evidence.replay_step_done 同语义(同一步理论只 done 一次,取最后一条防御重复),但
    走 SQL ORDER BY id DESC LIMIT 1 直取,不把整条事件流搬回内存再线性扫。无该步 step_done
    → None(诚实说查不到,不拿空字典冒充已完成)。"""
    cur.execute(
        "SELECT payload FROM work_order_events "
        "WHERE tenant_id = %s AND work_order_id = %s AND step = %s AND event_type = 'step_done' "
        "ORDER BY id DESC LIMIT 1",
        (tenant_id, work_order_id, step),
    )
    row = cur.fetchone()
    if not row:
        return None
    payload = row["payload"] if isinstance(row, dict) else row[0]
    return payload or {}


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
    original_name: Optional[str] = None,
    ocr_history_id: Optional[str] = None,
    status: str = "pending",
    flag_reason: Optional[str] = None,
    dedupe_key: Optional[str] = None,
) -> dict:
    """登记一件料。带 dedupe_key 时幂等(intake 重跑不重复登记同一份文件)。original_name 留无损
    原始文件名(冻结 manifest 的正规归宿),空时读侧回落 storage.original_name_of 反解落盘名。"""
    cur.execute(
        f"""
        INSERT INTO work_order_items
            (tenant_id, work_order_id, source, kind, file_ref, original_name, ocr_history_id,
             status, flag_reason, dedupe_key)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            original_name,
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
    ocr_history_id: Optional[str] = None,
) -> None:
    """sort/classify 步用:定堆(kind)/判结论(status)/记原因(flag_reason)/回填识别台账
    (ocr_history_id · 件 1)。省略的字段不动——ocr_history_id 缺省 None 即不写,存量 NULL
    不被清跑覆盖(只向前)。"""
    set_clause, params = [], []
    for col, val in (
        ("status", status),
        ("kind", kind),
        ("flag_reason", flag_reason),
        ("ocr_history_id", ocr_history_id),
    ):
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


def next_deliverable_version(cur, *, tenant_id: str, work_order_id: str) -> int:
    """本工单交付物的下一个版本号(现有最大 + 1,无则 1)。package 每次成整批出包用同一版本号,
    未冻结重跑=版本递增、旧版本文件不动(C-2 交付物版本化)。"""
    cur.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 AS v FROM work_order_deliverables "
        "WHERE tenant_id = %s AND work_order_id = %s",
        (tenant_id, work_order_id),
    )
    return int(cur.fetchone()["v"])


def current_deliverable_version(cur, *, tenant_id: str, work_order_id: str) -> int:
    """本工单交付物的最新(最大)版本号,无则 0。冻结把此版本钉进 manifest。"""
    cur.execute(
        "SELECT COALESCE(MAX(version), 0) AS v FROM work_order_deliverables "
        "WHERE tenant_id = %s AND work_order_id = %s",
        (tenant_id, work_order_id),
    )
    return int(cur.fetchone()["v"])


def upsert_deliverable(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    kind: str,
    version: int = 1,
    artifact_path: Optional[str] = None,
    numbers: Optional[dict[str, Any]] = None,
) -> dict:
    """产出一份交付物(某 kind 的某版本)。唯一键 (tenant, wo, kind, version):同版本同 kind
    重写覆盖(单次 package 内幂等),换版本号=新行(未冻结重跑堆积新版本,旧版本文件不动)。"""
    cur.execute(
        f"""
        INSERT INTO work_order_deliverables
            (tenant_id, work_order_id, kind, version, artifact_path, numbers)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (tenant_id, work_order_id, kind, version)
        DO UPDATE SET artifact_path = EXCLUDED.artifact_path, numbers = EXCLUDED.numbers
        RETURNING {_DELIVERABLE_COLUMNS}
        """,
        (
            tenant_id,
            work_order_id,
            kind,
            int(version),
            artifact_path,
            json.dumps(numbers or {}, ensure_ascii=False, default=str),
        ),
    )
    return dict(cur.fetchone())


def list_deliverables(cur, *, tenant_id: str, work_order_id: str) -> list[dict]:
    """读侧默认取每个 kind 的最新版本(DISTINCT ON (kind) 按版本降序取头)——旧版本仍在库,
    列表/详情/下载看到的是最新那版(C-2 交付物版本化读侧口径)。"""
    cur.execute(
        f"SELECT DISTINCT ON (kind) {_DELIVERABLE_COLUMNS} FROM work_order_deliverables "
        "WHERE tenant_id = %s AND work_order_id = %s ORDER BY kind, version DESC",
        (tenant_id, work_order_id),
    )
    return [dict(r) for r in cur.fetchall()]


def sum_workorder_ocr_cost(cur, *, tenant_id: str, item_ids: list) -> float:
    """本工单 classify 的 OCR 累计成本(ai_usage.cost_thb Σ · 单一事实源;trace_id=item_id 由
    classify._ocr_safe 打点)。R1 成本封顶从台账回查用;无行(无 OCR/被裁剪)返 0.0。"""
    if not item_ids:
        return 0.0
    cur.execute(
        "SELECT COALESCE(SUM(cost_thb), 0) AS c FROM ai_usage "
        "WHERE tenant_id = %s AND task = 'workorder_classify' AND trace_id = ANY(%s)",
        (tenant_id, list(item_ids)),
    )
    row = cur.fetchone()
    val = row["c"] if isinstance(row, dict) else row[0]
    return float(val or 0.0)


def reset_quota_deferred_items(cur, *, tenant_id: str, work_order_id: str, flag_reason: str) -> int:
    """把指定 flag_reason 的 flagged 件复位回 pending 并清 reason(R1 quota 待补 · 续跑重试)。
    只动该 reason 的件,不碰其它人审 flagged;返回复位件数。"""
    cur.execute(
        "UPDATE work_order_items SET status = 'pending', flag_reason = NULL, updated_at = now() "
        "WHERE tenant_id = %s AND work_order_id = %s AND status = 'flagged' AND flag_reason = %s",
        (tenant_id, work_order_id, flag_reason),
    )
    return cur.rowcount


def ocr_models_for_items(cur, *, tenant_id: str, item_ids: list) -> list:
    """本工单 classify 用过的模型名(C-1 ai_usage 归因单一事实源,只读不双写;trace_id=
    item_id 由 classify._ocr_safe 打点)。冻结 manifest 模型版本轴的取数口——查询归 DAL,
    freeze 保持纯汇编(其自述契约:不碰 DB)。无行(无 OCR/被裁剪)返空。"""
    if not item_ids:
        return []
    cur.execute(
        "SELECT DISTINCT model FROM ai_usage "
        "WHERE tenant_id = %s AND task = 'workorder_classify' "
        "AND trace_id = ANY(%s) AND model IS NOT NULL",
        (tenant_id, list(item_ids)),
    )
    return [r["model"] if isinstance(r, dict) else r[0] for r in cur.fetchall()]
