# -*- coding: utf-8 -*-
"""管家开工第一问 today_brief(B5 · 只读合成,零新 SQL)。

会计每天上班第一句是「今天先干哪个」。以前她要在矩阵页、看板、推送日志三处各看一眼才拼得
出答案,问管家也得问三四次。本工具把三个既有 handler 的返回合成一张当天的活:

  逾期 / 快到期  tools_close.due_soon      (= 矩阵页同一份义务原料,截止日已法定顺延)
  等你审        tools_close.review_queue  (= /api/workorder/review-queue)
  推 ERP 失败    tools.push_log_query      (= /api/erp/push-logs)

与 matrix_overview 的差别不是数据而是排序轴:矩阵按「客户 × 义务」排格子,这里按「还剩几天」
排行动。早上要的是一份待办,不是一张表。

合成不重算:每条都原样取自被合成的 handler,本模块只分桶和排序;排序键是确定性的
(桶号 → 剩余天数 → 待判件数 → 客户名),同一份数据任何时候跑出来的前几条逐条相同。
某一路查不出来(权限/服务层报错/抛异常)如实进 partial —— 绝不让缺失的那一路在计数里长得
像 0,会计会据此判「今天没这类活」。

推失败这一路的作用域与另外三路不同,答复层必须说出来(push_scope):erp_push_logs 按 user
隔离(RLS 里没有 tenant 维度策略),list_push_logs 只查得到【本人推过的】;而到期/待审/缺料
按分到的账套算。同事替同一批客户推失败的票不在这个数里,把四个数并排说成"今天的活"就是
在说假话 —— 数照给,口径明说。
"""

from __future__ import annotations

import logging

from services.steward.contracts import ToolResult
from services.steward import tool_scope, tools_close
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

TOP_N = 5  # 一屏能扫完的条数;要全量各自去 due_soon / review_queue / push_log_query

KIND_OVERDUE = "overdue"
KIND_DUE_SOON = "due_soon"
KIND_PUSH_FAILED = "push_failed"
KIND_REVIEW = "review"

# 桶序 = 紧急度序。唯一客观的判据是法定截止日:逾期的先做,快到期的次之。推失败与待判件
# 没有自己的钟,但都卡在申报前面,所以排在有钟的两类之后 —— 不引入"轻重缓急"这种主观权重,
# 任何人照这条规则手算都能得到同样的前几条(会计要能复核管家为什么这么排)。
_BUCKET = {KIND_OVERDUE: 0, KIND_DUE_SOON: 1, KIND_PUSH_FAILED: 2, KIND_REVIEW: 3}

PUSH_DAYS = 7  # 与 due_soon 的 7 天窗同宽:一屏里说的都是"这一周",两个数才对得起来

_LANE_DUE = "due_soon"
_LANE_REVIEW = "review_queue"
_LANE_PUSH = "push_log_query"

# 推失败那个数只涵盖本人推过的(见模块顶注)。答复层按它选措辞,不在文案里写死一句
# 「你自己」—— 哪天这一路换成整租户口径,措辞得跟着改而不是继续说旧话。
PUSH_SCOPE_SELF = "self"


def today_brief(ctx: ToolContext, args: dict) -> ToolResult:
    """今天从哪下手:四个数 + 最紧的几条。三路各自失败互不牵连(partial 如实标)。"""
    from services.steward import tools  # 本模块被 tools 汇总进闭集,模块级反向 import 会成环

    period = tool_scope.period_or_current(args.get("period"))
    partial: list[str] = []
    due = _lane(_LANE_DUE, partial, lambda: tools_close.due_soon(ctx, {"period": period}))
    # 待审队列有意不传期:上期没审完的还压在手上,今天照样要处理(review_queue 的跨期口径)。
    queue = _lane(_LANE_REVIEW, partial, lambda: tools_close.review_queue(ctx, {}))
    pushes = _lane(
        _LANE_PUSH,
        partial,
        lambda: tools.push_log_query(ctx, {"days": PUSH_DAYS, "status": "failed"}),
    )

    window = due.get("window_days") or tools_close.DUE_SOON_DAYS
    rows = _due_rows(due, window) + _push_rows(pushes) + _review_rows(queue)
    rows.sort(key=_rank)
    return ToolResult(
        ok=True,
        data={
            "period": period,
            "today": ctx.today.isoformat(),
            "window_days": window,
            "push_days": pushes.get("days") or PUSH_DAYS,
            "push_scope": PUSH_SCOPE_SELF,
            "counts": {
                "overdue": due.get("overdue") or 0,
                "due_soon": due.get("due_soon") or 0,
                "review_orders": queue.get("order_count") or 0,
                "review_flagged": queue.get("flagged_count") or 0,
                "push_failed": pushes.get("failed") or 0,
                "missing_materials": _missing_material_clients(due),
            },
            "partial": partial,
            # 被合成的清单本身是截断的(各自 LIST_LIMIT),缺料家数只数得到列出来的那些 ——
            # 标出来让答复能说"只数了最紧的一批",不冒充全量。
            "truncated": (due.get("total") or 0) > len(due.get("rows") or []),
            "total": len(rows),
            "rows": rows[:TOP_N],
        },
    )


def _lane(name: str, partial: list, call) -> dict:
    """一路取数。失败不拖垮整张简报,记进 partial 由答复层如实说这一路没查出来。

    收异常而不只看 ToolResult.ok:被合成的三个 handler 在真实故障(服务层报错/权限抛)下
    是抛出来的,due_soon 与 push_log_query 根本没有 ok=False 的分支。只认 ok=False 等于降级
    承诺永远不生效 —— 异常会一路上抛到 tools.run 兜成 ERR_TOOL_FAILED,整张简报就没了。
    """
    try:
        res = call()
    except Exception:  # noqa: BLE001 — 一路挂了是"这一路没查出来",不是整张简报没了
        logger.warning("[steward] brief lane %s failed", name, exc_info=True)
        res = None
    if res is not None and res.ok and isinstance(res.data, dict):
        return res.data
    partial.append(name)
    return {}


def _row(kind: str, client_name: str, subject: str, days_left=None, n=None) -> dict:
    """一条待办的机器形状。文本一律留给 copy 层组装(工具不出文案)。"""
    return {
        "kind": kind,
        "client_name": client_name,
        "subject": subject,
        "days_left": days_left,
        "n": n,
    }


def _due_rows(due: dict, window: int) -> list[dict]:
    """义务行。没有截止日的排不进"最紧的几条"(没有钟就没有紧急度),但仍如实计入 counts;
    窗口之外的也不进 —— 一个月后到期的东西挤掉今天该做的事,这张简报就废了。"""
    out = []
    for r in due.get("rows") or []:
        days = r.get("days_left")
        if not isinstance(days, int) or days > window:
            continue
        kind = KIND_OVERDUE if days < 0 else KIND_DUE_SOON
        out.append(
            _row(kind, r.get("client_name") or "", r.get("obligation_code") or "", days_left=days)
        )
    return out


def _push_rows(pushes: dict) -> list[dict]:
    """推失败行。push_log_query 的 subject 就是这条推送归谁(账套名/客户名/卖方名)。"""
    return [
        _row(
            KIND_PUSH_FAILED,
            r.get("subject") or "",
            r.get("invoice_no") or r.get("error_code") or "",
        )
        for r in pushes.get("rows") or []
        if (r.get("status") or "") == "failed"
    ]


def _review_rows(queue: dict) -> list[dict]:
    """待审行。件数进 n,由答复层说成「N 件待判」(工具不出语言相关的字串)。"""
    return [
        _row(KIND_REVIEW, r.get("client_name") or "", "", n=_int_or_zero(r.get("flagged")))
        for r in queue.get("rows") or []
    ]


def _rank(row: dict) -> tuple:
    """确定性排序键:桶 → 剩余天数少的在前 → 待判件多的在前 → 客户名 → 事由。
    末两段是并列时的稳定兜底:没有它,同一句话问两次前几条会换人。"""
    days = row.get("days_left")
    return (
        _BUCKET[row["kind"]],
        days if isinstance(days, int) else 0,
        -(row.get("n") or 0),
        row.get("client_name") or "",
        row.get("subject") or "",
    )


def _missing_material_clients(due: dict) -> int:
    """缺料几家:从到期清单的徽章里数,不另跑一遍矩阵 —— 会计问的"缺料"是"还没交完又缺料"
    的那几家,与本简报另外三个数同一份原料才对得起来(两份原料会得出对不上的两个数)。"""
    from services.workorder import matrix

    return len(
        {
            r.get("client_id")
            for r in due.get("rows") or []
            if r.get("badge") == matrix.BADGE_MISSING_MATERIALS
        }
    )


def _int_or_zero(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
