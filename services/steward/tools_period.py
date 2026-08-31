# -*- coding: utf-8 -*-
"""管家的本期盘点两问(只读薄封装,零新口径、零直接写库)。

横着看一期(全所)和竖着看一家(全票),都是月中最常问、现有工具答不出的两句:
  tax_matrix       「这个月所有客户的应交税额列个表」
                   services.workorder.matrix.fetch_rows + fetch_step_numbers('compute')
                   (= 矩阵页那份原料 + 工单详情 numbers 的同一批 compute 事件)
  period_invoices  「6 月 A 公司还有几张票没推进去」
                   services.workorder.push_coverage(与 reconcile 的推送回执比对同一份投影)
                   + services.erp.push_log_queries.list_push_logs_by_invoice_nos

两条硬约束,破了就没意义:
  ① 数字一个都不由模型出。表的结构由本模块生成,格子里的钱全部来自已落库的 compute 事件,
     合计走 Decimal(tool_scope.to_decimal)相加,不过 float。
  ② 批量读。30 家客户一条 SQL 取矩阵、一条 SQL 取 compute 事件;逐家回放事件流就是 N+1,
     会把对话拖到超时。period_invoices 只读一家,票号集也是一条 SQL 查完推送日志。

「没有」和「零」分开报:has_numbers=False 的行不填 0,留空由文案说成「还没算到税额」——
会计照着 0 去准备现金和照着「还没算」去催 AI,是两件完全不同的事。
"""

from __future__ import annotations

from decimal import Decimal

from services.steward.contracts import ToolResult
from services.steward import tool_scope
from services.steward.registry import ToolContext
from services.workorder import push_coverage

# 认列结果落在哪一步:compute 的 step_done。工单详情的 numbers(tax_numbers / 签批闸吃的
# 那份)回放的就是这一步,取数时点必须同一个 —— 读 package 落的交付物快照会晚整整一步,
# 而 package 是会 stuck 停住的:同一张单会出现「单查应交 ฿35,000」而「表里还没算到」。
_COMPUTE_STEP = "compute"

# 一行客户在税额表里的三态。ready 之外一律不填钱(假零比说不知道危险得多)。
TAX_READY = "ready"
TAX_NO_NUMBERS = "no_numbers"  # 开了单但引擎还没跑到 compute
TAX_NO_ORDER = "no_order"  # 这期还没开工单

# 全所表按事务所规模给,不用对话清单那个 20 —— 截在 20 家的「全所税额表」不叫全所。
MATRIX_ROW_LIMIT = 100

# 一张票在这期的落点。前两个压过推送态:还没判完的票谈"推没推"没有意义,读不出票号的票
# 根本没法跟推送日志对上(而它恰恰是漏推的头号成因)。其余四态见 push_coverage。
INVOICE_PENDING_REVIEW = "pending_review"
INVOICE_NO_NUMBER = "no_invoice_no"

FILTER_ALL = "all"
FILTER_NOT_PUSHED = "not_pushed"
FILTER_PENDING_REVIEW = "pending_review"
_FILTERS = (FILTER_ALL, FILTER_NOT_PUSHED, FILTER_PENDING_REVIEW)

INVOICE_ROW_LIMIT = 50  # 一家一期的进项票量级

# 六态互斥且穷尽:每张票只落一个桶,counts 之和 = total。答复里「已推 X 张、还差 Y 张」
# 全靠这条成立(守门测试钉着)。
INVOICE_STATES: tuple[str, ...] = (
    push_coverage.STATE_PUSHED,
    push_coverage.STATE_FAILED,
    push_coverage.STATE_IN_FLIGHT,
    push_coverage.STATE_NEVER,
    INVOICE_PENDING_REVIEW,
    INVOICE_NO_NUMBER,
)


def tax_matrix(ctx: ToolContext, args: dict) -> ToolResult:
    """全所一期的税额表:每家一行,销项/进项/销项税/进项税/应交 + 合计。

    数字来源是 compute 步落的认列结果,与 tax_numbers 逐家答的那份同源(它回放同一步的
    step_done)、字段集同一份(tool_scope.TAX_MONEY_KEYS)—— 表里的数与点开工单看到的必须
    逐位相同,取数时点也必须是同一个(见 _COMPUTE_STEP 顶注)。
    """
    from services.workorder import matrix

    period = tool_scope.period_or_current(args.get("period"))
    with tool_scope.cursor() as cur:
        rows = [
            r
            for r in matrix.fetch_rows(cur, tenant_id=ctx.tenant_id, period=period)
            if tool_scope.in_scope(ctx, r["client_id"])
        ]
        order_ids = sorted({str(r["work_order_id"]) for r in rows if r.get("work_order_id")})
        numbers_by_order = matrix.fetch_step_numbers(
            cur, tenant_id=ctx.tenant_id, work_order_ids=order_ids, step=_COMPUTE_STEP
        )

    out_rows = _tax_rows(rows, numbers_by_order)
    ready = [r for r in out_rows if r["state"] == TAX_READY]
    out_rows.sort(key=_tax_sort_key)
    return ToolResult(
        ok=True,
        data={
            "period": period,
            "client_count": len(out_rows),
            "ready": len(ready),
            "no_numbers": sum(1 for r in out_rows if r["state"] == TAX_NO_NUMBERS),
            "no_order": sum(1 for r in out_rows if r["state"] == TAX_NO_ORDER),
            # 留抵(应交为负)单独数一个:合计里它会把别家的应交冲掉,不点出来会被当成"少交了"。
            "credit": sum(1 for r in ready if tool_scope.to_decimal(r["tax_due"]) < 0),
            # 合计取全部 ready 行,不受下面的截断影响(截的是给人看的清单,不是账)。
            "totals": {k: _total(ready, k) for k in tool_scope.TAX_MONEY_KEYS},
            "rows": out_rows[:MATRIX_ROW_LIMIT],
            "truncated": len(out_rows) > MATRIX_ROW_LIMIT,
        },
    )


def _tax_rows(rows: list[dict], numbers_by_order: dict) -> list[dict]:
    """矩阵原料(客户 × 义务,一家可能好几行)→ 每家一行的税额行。

    一家客户这期可能有多张工单(ภ.พ.30 之外还有 ภ.ง.ด. 等义务),只有跑 VAT 的那张会算出
    税额 —— 按"哪张有认列结果"认,不去猜义务码。
    """
    by_client: dict[int, dict] = {}
    for r in rows:
        cid = int(r["client_id"])
        row = by_client.setdefault(
            cid,
            {
                "client_id": cid,
                "client_name": r.get("client_name") or "",
                "state": TAX_NO_ORDER,
                "numbers": None,
            },
        )
        order_id = r.get("work_order_id")
        if not order_id:
            continue
        if row["state"] == TAX_NO_ORDER:
            row["state"] = TAX_NO_NUMBERS
        numbers = _money_only(numbers_by_order.get(str(order_id)))
        if numbers and row["numbers"] is None:
            row["numbers"] = numbers
            row["state"] = TAX_READY
    return [_tax_row(row) for row in by_client.values()]


def _money_only(payload) -> dict:
    """compute 事件 payload 里的钱字段(它还带 period / gates / pp30_form 等)。一个钱字段
    都没有 = 还没算出税额,与 tax_numbers 的 has_numbers 同判据,不拿一条空事件冒充已算。"""
    if not isinstance(payload, dict):
        return {}
    return {k: payload[k] for k in tool_scope.TAX_MONEY_KEYS if payload.get(k) is not None}


def _tax_row(row: dict) -> dict:
    """一行的对外形状。没出数的行钱字段留空串,不填 0 —— 表格里的 0.00 会被当成真的。"""
    numbers = row.pop("numbers") or {}
    money = {
        k: (tool_scope.money(numbers[k]) if numbers.get(k) is not None else "")
        for k in tool_scope.TAX_MONEY_KEYS
    }
    return {**row, **money}


def _tax_sort_key(row: dict) -> tuple:
    """已出数的排前面且按应交从大到小 —— 月中看这张表是为了备现金和挑异常,几百万那家
    要第一眼看见。没出数的按名字排在后面(它们是催 AI 的清单,不是钱的清单)。"""
    if row["state"] != TAX_READY:
        return (1, Decimal(0), row["client_name"])
    return (0, -tool_scope.to_decimal(row["tax_due"]), row["client_name"])


def _total(rows: list[dict], key: str) -> str:
    return tool_scope.money_total(r[key] for r in rows)


def period_invoices(ctx: ToolContext, args: dict) -> ToolResult:
    """某家某期收到的进项票清单 + 每张推进 Express 了没,可筛未推 / 待判。

    「推完了没」是把票送进 ERP 这条产线的终点判据,而 push_log_query 只看得见推过的:没推的
    票压根不在 erp_push_logs 里。这里从工单的件出发(该有哪些票),再去比推送日志(推过哪些),
    差集就是答案 —— 比对口径与 reconcile 的 F2-辅 回执比对是同一份(push_coverage)。
    """
    from services.erp import push_log_queries
    from services.workorder import api as wo_api, store as wo_store

    client, err = tool_scope.resolve_client(ctx, args.get("client_name") or "")
    if err:
        return err
    period = tool_scope.period_or_current(args.get("period"))
    kept = args.get("filter") if args.get("filter") in _FILTERS else FILTER_ALL
    base = {
        "client_id": client["id"],
        "client_name": client["name"],
        "period": period,
        "filter": kept,
    }

    with tool_scope.cursor() as cur:
        listing = wo_api.list_orders(
            cur,
            tenant_id=ctx.tenant_id,
            workspace_client_id=client["id"],
            period=period,
            limit=1,
        )
        orders = listing["orders"]
        if not orders:
            return ToolResult(ok=True, data={**base, "has_order": False, "total": 0, "rows": []})
        work_order_id = str(orders[0]["id"])
        items = wo_store.list_items(cur, tenant_id=ctx.tenant_id, work_order_id=work_order_id)
        events = wo_store.list_events(cur, tenant_id=ctx.tenant_id, work_order_id=work_order_id)
        invoices = push_coverage.counted_purchase_invoices(items, events)
        invoice_nos = [i["invoice_no"] for i in invoices if i["invoice_no"]]
        push_rows = (
            push_log_queries.list_push_logs_by_invoice_nos(
                cur,
                tenant_id=ctx.tenant_id,
                invoice_nos=invoice_nos,
                work_order_id=work_order_id,
            )
            if invoice_nos
            else []
        )

    pushed_by_no = push_coverage.index_by_invoice_no(push_rows)
    rows = [_invoice_row(inv, pushed_by_no) for inv in invoices]
    counts = {state: sum(1 for r in rows if r["state"] == state) for state in INVOICE_STATES}
    shown = [r for r in rows if _keeps(r, kept)]
    return ToolResult(
        ok=True,
        data={
            **base,
            "has_order": True,
            "work_order_id": work_order_id,
            "total": len(rows),
            "counts": counts,
            "not_pushed": len(rows) - counts[push_coverage.STATE_PUSHED],
            "shown": len(shown),
            "rows": shown[:INVOICE_ROW_LIMIT],
            "truncated": len(shown) > INVOICE_ROW_LIMIT,
        },
    )


def _invoice_row(invoice: dict, pushed_by_no: dict) -> dict:
    amount = invoice.get("total_amount")
    return {
        # 票号读不出时退回文件名:会计要能去堆里把这张翻出来,给一行空白等于查无此票。
        "invoice_no": invoice["invoice_no"] or invoice.get("file_ref") or "",
        "vendor": invoice.get("vendor") or "",
        "invoice_date": invoice.get("invoice_date") or "",
        # 金额读不出来留空,不写 0.00(它会被当成一张零元票)。
        "amount": tool_scope.money(amount) if amount is not None else "",
        "state": _invoice_state(invoice, pushed_by_no),
    }


def _invoice_state(invoice: dict, pushed_by_no: dict) -> str:
    if invoice.get("awaiting_decision"):
        return INVOICE_PENDING_REVIEW
    if not invoice["invoice_no"]:
        return INVOICE_NO_NUMBER
    return push_coverage.push_state(pushed_by_no.get(invoice["invoice_no"]))


def _keeps(row: dict, kept: str) -> bool:
    if kept == FILTER_NOT_PUSHED:
        return row["state"] != push_coverage.STATE_PUSHED
    if kept == FILTER_PENDING_REVIEW:
        return row["state"] == INVOICE_PENDING_REVIEW
    return True
