# -*- coding: utf-8 -*-
"""审核队列读模型 + 复核态写动作(MC1-b1 · 审核队列与签批闭环)。

读侧:review_queue 按「客户 × 工单」聚合待审工单——单条 SQL(照 tax_profile 矩阵端点先例:
主表 + 三个分组子查询 LEFT JOIN,无 N+1、EXPLAIN 单遍),Python 只做分组投影不再查库。
写侧:batch_decisions(逐条落 human_decision,部分成功诚实逐条返回)/ reject_review(驳回
重做,append-only 重开受影响步)/ declare_self_review(单人所自审声明留痕)。

编排层职责边界同 api.py:取库→现算→落事件,不碰 FastAPI、不判权限(路由层 authorize_pearnly_ai
已管闸+细码+租户)、cur 由路由注入。事件只追加,新事件词 EVT_* 单一事实源在本模块(review 域,
同 runner/archive 各自持有本域事件词的惯例);step_reopened 是引擎步生命周期词,取自 engine。
"""

from __future__ import annotations

from typing import Optional

from services.line_binding import client_pool_vocab, line_client_pool_store
from services.workorder import api, engine, obligation_engine, review_feed, runner, store, verdict

# review 域 append-only 事件词(单一事实源)。
EVT_REVIEW_REJECTED = "review_rejected"
EVT_SELF_REVIEW_DECLARED = "self_review_declared"
_REVIEW_STEP = "review"

# 批量裁决单批上限(方案决策 4):一次审一屏同类件够用,又封住恶意超大批打爆事务。
MAX_BATCH = 200

# 驳回重做重开的起点:从对账起重算 → 出新版本交付物(reconcile/compute/package)。intake/sort/
# classify 不重开——源料与 OCR 未变,驳回改的是判断不是原件,重跑 OCR 纯烧钱。
_REOPEN_FROM = "reconcile"

# 待审工单纳入队列的状态:review(跑绿待签)+ stuck(有料过不去待人裁)。取 engine 权威常量。
_QUEUE_STATUSES = [engine.STATUS_REVIEW, engine.STATUS_STUCK]

# 三个原分组子查询(义务/客户池/驳回)改 LEFT JOIN LATERAL:聚合只对队列内工单现算,代价随
# 队列长度而非全租户历史增长(效率7);rj 走 ix_wo_events_wo (tenant,wo,id) 前缀窄扫。tenant_id
# 由 wo 相关子句携带,子查询不再各带一个 tenant 谓词。
_QUEUE_SQL = """
SELECT
    wo.id AS work_order_id, wo.workspace_client_id, wo.period, wo.status,
    wo.current_step, wo.updated_at,
    wc.name AS client_name, wc.tax_id AS client_tax_id,
    wi.flag_reason,
    count(wi.id) AS flagged_count,
    ob.next_due_efiling, ob.next_due_paper,
    COALESCE(cp.pending_count, 0) AS pool_pending,
    COALESCE(rj.reject_count, 0) AS reject_count
FROM work_orders wo
JOIN workspace_clients wc
    ON wc.id = wo.workspace_client_id AND wc.tenant_id = wo.tenant_id
LEFT JOIN work_order_items wi
    ON wi.tenant_id = wo.tenant_id AND wi.work_order_id = wo.id AND wi.status = 'flagged'
LEFT JOIN LATERAL (
    SELECT min(o.due_efiling) AS next_due_efiling, min(o.due_paper) AS next_due_paper
    FROM client_period_obligations o
    WHERE o.tenant_id = wo.tenant_id
      AND o.workspace_client_id = wo.workspace_client_id
      AND o.period = wo.period
      AND o.status <> %s
) ob ON true
LEFT JOIN LATERAL (
    SELECT count(*) AS pending_count
    FROM line_client_questions q
    WHERE q.tenant_id = wo.tenant_id
      AND q.workspace_client_id = wo.workspace_client_id
      AND q.status = ANY(%s)
) cp ON true
LEFT JOIN LATERAL (
    SELECT count(*) AS reject_count
    FROM work_order_events e
    WHERE e.tenant_id = wo.tenant_id
      AND e.work_order_id = wo.id
      AND e.event_type = %s
) rj ON true
WHERE wo.tenant_id = %s
  AND wo.status = ANY(%s)
  AND (%s::text IS NULL OR wo.period = %s::text)
  AND (%s::bigint IS NULL OR wo.workspace_client_id = %s::bigint)
GROUP BY wo.id, wo.workspace_client_id, wo.period, wo.status, wo.current_step, wo.updated_at,
         wc.name, wc.tax_id, wi.flag_reason,
         ob.next_due_efiling, ob.next_due_paper, cp.pending_count, rj.reject_count
ORDER BY ob.next_due_efiling NULLS LAST, wo.workspace_client_id, wo.id
"""


def review_queue(
    cur,
    *,
    tenant_id: str,
    period: Optional[str] = None,
    client_id: Optional[int] = None,
    severity: Optional[str] = None,
    actor: Optional[str] = None,
    sod_enforced: bool = False,
) -> dict:
    """按客户 × 工单聚合待审队列。主表 SQL(义务/客户池/驳回三 LATERAL 子查询)出工单行 +
    flagged 按 flag_reason 分组计数/严重度/到期日/客户池 pending/返工标记;再一把批量取回队列内
    工单的事件与 flagged 明细(review_feed),挂 SoD 投影(actor/sod_enforced 决定)并出跨工单
    扁平 flagged item feed(前端纯渲染,不再逐单回放)。severity 传入则只留该严重度。到期近→前。"""
    line_client_pool_store.ensure_table()  # 保证 line_client_questions 存在(首用自愈)再 JOIN
    cur.execute(
        _QUEUE_SQL,
        (
            obligation_engine.STATUS_NIL,
            list(client_pool_vocab.ACTIVE_STATUSES),
            EVT_REVIEW_REJECTED,
            tenant_id,
            _QUEUE_STATUSES,
            period,
            period,
            client_id,
            client_id,
        ),
    )
    orders = _group_rows([dict(r) for r in cur.fetchall()], severity)
    flagged_items = review_feed.enrich(
        cur,
        tenant_id=tenant_id,
        orders=orders,
        actor=actor,
        sod_enforced=sod_enforced,
        severity=severity,
    )
    clients = _group_clients(orders)
    return {
        "period": period,
        "clients": clients,
        "flagged_items": flagged_items,
        "counts": {
            "clients": len(clients),
            "orders": len(orders),
            "flagged": sum(o["flagged_total"] for o in orders),
        },
    }


def _iso(value) -> Optional[str]:
    return value.isoformat() if value is not None and hasattr(value, "isoformat") else value


def _group_rows(rows: list[dict], severity: Optional[str]) -> list[dict]:
    """(工单 × flag_reason) 行 → 每工单一条,flagged 按 flag_reason 分组。severity 过滤在此。"""
    by_order: dict = {}
    order_seq: list = []
    for r in rows:
        wid = r["work_order_id"]
        order = by_order.get(wid)
        if order is None:
            order = {
                "work_order_id": wid,
                "workspace_client_id": r["workspace_client_id"],
                "client_name": r["client_name"],
                "client_tax_id": r["client_tax_id"],
                "period": r["period"],
                "status": r["status"],
                "current_step": r["current_step"],
                "updated_at": _iso(r["updated_at"]),
                "next_due_efiling": _iso(r["next_due_efiling"]),
                "next_due_paper": _iso(r["next_due_paper"]),
                "pool_pending": int(r["pool_pending"] or 0),
                "is_rework": int(r["reject_count"] or 0) > 0,
                "flagged_groups": [],
                "flagged_total": 0,
                "top_severity": None,
            }
            by_order[wid] = order
            order_seq.append(wid)
        reason = r["flag_reason"]
        if reason is None:
            continue  # 无 flagged 件的待审工单:LEFT JOIN 空行,不造分组
        sev = verdict.severity_of(reason)
        order["flagged_groups"].append(
            {"flag_reason": reason, "severity": sev, "count": int(r["flagged_count"] or 0)}
        )
        order["flagged_total"] += int(r["flagged_count"] or 0)

    out = []
    for wid in order_seq:
        order = by_order[wid]
        order["top_severity"] = (
            verdict.SEV_CRIT
            if any(g["severity"] == verdict.SEV_CRIT for g in order["flagged_groups"])
            else (verdict.SEV_WARN if order["flagged_groups"] else None)
        )
        if severity:
            order["flagged_groups"] = [
                g for g in order["flagged_groups"] if g["severity"] == severity
            ]
            if not order["flagged_groups"]:
                continue  # severity 筛选:不含该严重度组的工单整条剔除
            order["flagged_total"] = sum(g["count"] for g in order["flagged_groups"])
        out.append(order)
    return out


def _group_clients(orders: list[dict]) -> list[dict]:
    """工单再按客户归组(客户 × 工单两层结构)。客户级 pool_pending 取该客户任一工单行的值
    (同客户同值,SQL 已按 workspace_client_id JOIN),保序不重排(已按到期日排好)。"""
    by_client: dict = {}
    seq: list = []
    for o in orders:
        cid = o["workspace_client_id"]
        client = by_client.get(cid)
        if client is None:
            client = {
                "workspace_client_id": cid,
                "client_name": o["client_name"],
                "client_tax_id": o["client_tax_id"],
                "pool_pending": o["pool_pending"],
                "orders": [],
            }
            by_client[cid] = client
            seq.append(cid)
        client["orders"].append(o)
    return [by_client[c] for c in seq]


def batch_decisions(
    cur, *, tenant_id: str, work_order_id: str, items: list[dict], actor: str
) -> dict:
    """批量裁决:逐条落 human_decision,部分成功诚实逐条返回(不整批假成功)。单批上限 MAX_BATCH。

    同一事务内逐条 record_decision:失败只会是校验错(WorkOrderApiError——非法裁决在写 SQL 前
    抛、item 不属该单是干净 SELECT 后抛),不会污染事务,故可逐条 catch 继续;真 DB 错(会毒化
    事务)不吞,冒泡成 5xx。幂等语义沿用单条裁决(latest-wins 回放,不另造 dedupe:重放同批
    末条胜、不重复计入)。"""
    if not items:
        raise api.WorkOrderApiError("workorder.batch_empty")
    if len(items) > MAX_BATCH:
        raise api.WorkOrderApiError("workorder.batch_too_large")
    results: list[dict] = []
    ok_count = 0
    for d in items:
        item_id = d.get("item_id")
        try:
            evt = api.record_decision(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                item_id=item_id,
                decision=d.get("decision"),
                values=d.get("values"),
                actor=actor,
                kind=d.get("kind"),
                reason=d.get("reason"),
            )
            results.append({"item_id": item_id, "ok": True, "event_id": evt["id"]})
            ok_count += 1
        except api.WorkOrderApiError as e:
            results.append({"item_id": item_id, "ok": False, "error": e.code})
    return {
        "results": results,
        "ok_count": ok_count,
        "fail_count": len(items) - ok_count,
        "total": len(items),
    }


def reject_and_rerun(
    *, tenant_id: str, work_order_id: str, actor: str, reason: Optional[str], background=None
) -> dict:
    """驳回重做 + 自动重跑,状态翻转与抢租约同一事务(MC2-A1 ②)。

    reject_review 把 status 翻回 running——若翻完事务提交、事后调度才抢租约,中间被杀就留下
    「running + 租约 NULL」孤儿(F3 立案的谎言窗口)。这里把「抢租约 → 驳回翻状态」装进
    request_run 的 lease 闭包:同一事务要么全成(状态=running 且租约在手),要么全滚
    (工单还是 review,可重试);校验错(非 review 态/空原因)在闭包内抛,事务回滚、租约不留。
    抢不到租约(罕见:有 run 正在跑)→ 驳回不落,抛 run_in_progress 交路由 409。"""
    out: dict = {}

    def lease_and_reject(cur, *, tenant_id, work_order_id, owner, ttl_seconds) -> bool:
        if not store.acquire_run_lease(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            owner=owner,
            ttl_seconds=ttl_seconds,
        ):
            return False
        out.update(
            reject_review(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                actor=actor,
                reason=reason,
            )
        )
        return True

    scheduled = runner.request_run(
        tenant_id, work_order_id, actor=actor, lease=lease_and_reject, background=background
    )
    if scheduled is None:
        raise api.WorkOrderApiError("workorder.run_in_progress")
    return out


def reject_review(
    cur, *, tenant_id: str, work_order_id: str, actor: str, reason: Optional[str]
) -> dict:
    """驳回重做:落 review_rejected(原因必填)→ 重开受影响步(append-only step_reopened)→
    状态回可跑态。调用方 reject_and_rerun 把本函数与抢租约装进同一事务并排后台重跑,引擎从
    reconcile 重跑到 package(交付物 version+1,机制现成)再落回 review——二次进队列,
    reject_count>0 标返工件。仅 review 态可驳回。"""
    wo = store.get_work_order(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if not wo:
        raise api.WorkOrderApiError("workorder.not_found")
    if wo["status"] != engine.STATUS_REVIEW:
        raise api.WorkOrderApiError("workorder.not_reviewable")
    # 长度上限由路由层 pydantic RejectIn(max_length=500)把守;这里只挡 strip 后的空原因
    # (pydantic min_length 拦不住纯空白)。
    reason_s = (reason or "").strip()
    if not reason_s:
        raise api.WorkOrderApiError("workorder.reject_reason_required")

    reopened = list(engine.reopen_steps_from(_REOPEN_FROM))
    store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=_REVIEW_STEP,
        event_type=EVT_REVIEW_REJECTED,
        payload={"reason": reason_s, "reopened_steps": reopened},
        actor=actor,
    )
    for step in reopened:
        store.append_event(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            step=step,
            event_type=engine.EVT_REOPENED,
            payload={"cause": EVT_REVIEW_REJECTED},
            actor=actor,
        )
    store.set_status(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        status=engine.STATUS_RUNNING,
        current_step=_REOPEN_FROM,
    )
    return {"status": engine.STATUS_RUNNING, "reopened_steps": reopened}


def declare_self_review(cur, *, tenant_id: str, work_order_id: str, actor: str) -> dict:
    """单人所自审声明(方案决策 5 · 声明制不豁免制):review 态内落 append-only
    self_review_declared,archive 据此放行单人所归档并在归档事件标 self_reviewed(sod.py)。
    同一人重复声明幂等(dedupe_key 含 actor)。仅 review 态可声明。"""
    wo = store.get_work_order(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if not wo:
        raise api.WorkOrderApiError("workorder.not_found")
    if wo["status"] != engine.STATUS_REVIEW:
        raise api.WorkOrderApiError("workorder.not_reviewable")
    evt = store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=_REVIEW_STEP,
        event_type=EVT_SELF_REVIEW_DECLARED,
        payload={"role": "self_reviewer"},
        actor=actor,
        dedupe_key=f"self_review:{work_order_id}:{actor}",
    )
    return {"ok": True, "event_id": evt["id"]}
