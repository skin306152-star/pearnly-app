# -*- coding: utf-8 -*-
"""管家工具的共用接地件:账套作用域、客户名 → 真实名录、期间缺省、金额规范化。

从 tools.py 抽出来是为了让新工具模块(tools_close / tools_invoice)与原六只读共用同一份
判据而不互相 import —— 三个模块都 import 本模块,tools.py 再把执行器汇总成闭集,没有环。

四条口径收在这里,别处不许另起一份:
  ① 作用域:allowed_client_ids=None 表示不限(老板/超管),给了集合就只看分到的账套,
     与 /api/tax-profile/matrix 的收窄口径同源;
  ② 客户名:必须在真实名录里命中唯一一家才作数 —— 查无/多义都退回可追问的错误,
     挂错账套是红线;
  ③ 票:关键词必须命中唯一一张识别记录才作数。查票的 invoice_detail 与推票的 erp_push
     共用同一段定位 —— 同一句话在"先查清楚"和"那就推吧"两步里给出不同的候选集,会计就
     无从下手;
  ④ 钱:一律 decimal 两位字符串,不过 float(卡上印的、比对的、答复里说的是同一个值)。

工单详情的取法(client_order)也收在这里:税额 / 银行对账 / 签批闸三个工具都是「客户名 + 期
→ 那张工单的投影」,取法漂了会让同一家同一期在三句答复里对不上。

S2 附件工具(file_convert / vat_report_check / doc_read_qa / table_generate)的共用接地件也
住这里:取本轮唯一那件料、产物落回附件表、随文件说的那句话、ask_model 注入点 —— 四个模块
都 import 本模块,私有名不再跨模块借用。
"""

from __future__ import annotations

import logging
from pathlib import Path
from decimal import Context, Decimal, InvalidOperation, localcontext
from typing import Any, Optional

from fastapi import HTTPException

from services.steward.contracts import ToolResult
from services.steward import attachments, store
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

LIST_LIMIT = 20  # 对话里回的清单只给前几条,详情去深链看

INVOICE_SEARCH_LIMIT = 20
INVOICE_CANDIDATE_LIMIT = 5

ERR_CLIENT_NOT_FOUND = "steward.client_not_found"
ERR_CLIENT_AMBIGUOUS = "steward.client_ambiguous"
ERR_HISTORY_FORBIDDEN = "steward.history_forbidden"
ERR_INVOICE_NOT_FOUND = "steward.invoice_not_found"
ERR_INVOICE_AMBIGUOUS = "steward.invoice_ambiguous"

# 附件三锚错误的码也收在这里(single_attachment 是四个附件工具共用的取件路)。
ERR_NO_ATTACHMENT = "steward.attachment_missing"
ERR_MANY_ATTACHMENTS = "steward.attachment_ambiguous"
ERR_UNREADABLE = "steward.attachment_unreadable"

# 量化金额用的独立上下文(见 money 的注释:默认 28 位精度撑不住全所合计)。舍入沿用默认的
# ROUND_HALF_EVEN —— 只放宽位数,不顺手改既有工具算出来的分位。
_MONEY_CONTEXT = Context(prec=38)

# 税额表的五个钱字段(compute 步认列结果的键)。tax_numbers 逐家答、tax_matrix 整表答,
# 字段集必须是同一份 —— 两处各写一遍就会出现"表里有的数,单查却没有"。
TAX_MONEY_KEYS = ("sales_amount", "output_vat", "purchase_amount", "input_vat", "tax_due")


def cursor():
    from core import db

    return db.get_cursor()


def scope_ids(ctx: ToolContext) -> Optional[list]:
    """账套作用域 → list(供 DAL 的 restrict_ids)· None = 不限(老板/超管)。"""
    return None if ctx.allowed_client_ids is None else [int(i) for i in ctx.allowed_client_ids]


def in_scope(ctx: ToolContext, client_id) -> bool:
    return ctx.allowed_client_ids is None or int(client_id) in ctx.allowed_client_ids


def clients(ctx: ToolContext) -> list[dict]:
    """本租户账套主体名录(一次查询,给名字解析/列表补名共用,防 N+1)。"""
    from services.workspace import store as ws_store

    rows = ws_store.list_workspace_clients(ctx.user_id, ctx.tenant_id, restrict_ids=scope_ids(ctx))
    return [
        {"id": int(r["id"]), "name": r.get("name") or "", "tax_id": r.get("tax_id")} for r in rows
    ]


def match_clients(rows: list[dict], keyword: str) -> list[dict]:
    """名字/税号模糊命中(精确同名优先)。纯函数,便于单测。"""
    kw = (keyword or "").strip().lower()
    if not kw:
        return []
    exact = [c for c in rows if c["name"].lower() == kw]
    if exact:
        return exact
    return [
        c for c in rows if kw in c["name"].lower() or (c.get("tax_id") and kw in str(c["tax_id"]))
    ]


def resolve_client(ctx: ToolContext, keyword: str) -> tuple[Optional[dict], Optional[ToolResult]]:
    """客户名 → 真实名录里的一家。查无/多义都不猜,退回可追问的错误(挂错账套是红线)。"""
    hits = match_clients(clients(ctx), keyword)
    if not hits:
        return None, ToolResult(
            ok=False, error_code=ERR_CLIENT_NOT_FOUND, data={"keyword": keyword, "candidates": []}
        )
    if len(hits) > 1:
        return None, ToolResult(
            ok=False,
            error_code=ERR_CLIENT_AMBIGUOUS,
            data={"keyword": keyword, "candidates": hits[:LIST_LIMIT]},
        )
    return hits[0], None


def search_invoices(ctx: ToolContext, keyword: str) -> list[dict]:
    """按关键词找票(与 history_query 同一个 DAL、同一套保留期与可见性口径)。

    套餐门在这里就把人挡住(HTTPException 上抛给调用方翻错误码):看不了识别记录的人,
    既不该查到票的详情,也不该推得动票。
    """
    from core import db
    from core.route_helpers import _check_history_access
    from services.ocr_history import queries as history_queries

    res = history_queries.list_ocr_history(
        user_id=ctx.user_id,
        retention_days=_check_history_access(ctx.user),
        keyword=keyword,
        limit=INVOICE_SEARCH_LIMIT,
        tenant_id=ctx.tenant_id,
        restrict_client_ids=db.get_visible_client_ids_for_user(ctx.user),
    )
    return list(res.get("items") or [])


def invoice_candidate(row: dict) -> dict:
    """多义时给人挑的一行(单号 + 卖方 + 票面日期,足够认出是哪张)。"""
    return {
        "history_id": str(row.get("id") or ""),
        "invoice_no": row.get("invoice_no") or "",
        "seller_name": row.get("seller_name") or "",
        "invoice_date": row.get("invoice_date") or "",
    }


def resolve_invoice(ctx: ToolContext, keyword: str) -> tuple[Optional[dict], Optional[ToolResult]]:
    """关键词 → 识别记录里唯一一张票。空关键词也算查无:空串会捞回"最近 20 张",
    在这条路上绝不默认"就是最近那张"。"""
    keyword = (keyword or "").strip()
    if not keyword:
        return None, ToolResult(ok=False, error_code=ERR_INVOICE_NOT_FOUND, data={"keyword": ""})
    try:
        hits = search_invoices(ctx, keyword)
    except HTTPException:
        return None, ToolResult(ok=False, error_code=ERR_HISTORY_FORBIDDEN)
    if not hits:
        return None, ToolResult(
            ok=False, error_code=ERR_INVOICE_NOT_FOUND, data={"keyword": keyword}
        )
    if len(hits) > 1:
        return None, ToolResult(
            ok=False,
            error_code=ERR_INVOICE_AMBIGUOUS,
            data={
                "keyword": keyword,
                "total": len(hits),
                "candidates": [invoice_candidate(h) for h in hits[:INVOICE_CANDIDATE_LIMIT]],
            },
        )
    return hits[0], None


def period_or_current(period: Optional[str]) -> str:
    from services.workorder import obligation_engine

    return period or obligation_engine.current_be_period()


def period_month_range(period: str) -> tuple:
    """佛历期「YYYY-MM」→ 该期对应公历月的 [月首, 月末](闭区间)。

    收发存报表(stockcard.report)按真实日历日筛,不认账期串,取数前要先落成一对 date。
    换算走 core.thai_date.gregorian_period —— 该模块顶注点名它是当前的换算权威(另外三处
    旧实现待收编),新代码一律走这条,不再另起一份 +543/-543。传入的 period 一律先经
    period_or_current,格式已经是印证过的「YYYY-MM」,解不出来当输入非法直接抛,交
    tools.run 的兜底转成"这条没查成",不静默拿今天的月份顶替(那会把查错期的人蒙混过去)。
    """
    from calendar import monthrange
    from datetime import date as _date

    from core import thai_date

    ad_period = thai_date.gregorian_period(period)
    if not ad_period:
        raise ValueError(f"steward: invalid period {period!r}")
    year, month = int(ad_period[:4]), int(ad_period[5:7])
    return _date(year, month, 1), _date(year, month, monthrange(year, month)[1])


def client_order(
    ctx: ToolContext, args: dict
) -> tuple[dict, str, Optional[dict], Optional[ToolResult]]:
    """客户名 + 期 → (客户, 期, 工单详情 或 None, 错误)。按工单口径读的工具共用这一段。

    没开工单不是错误 —— 是「这期还没开工」这个诚实答案,detail=None 交给各自的 data 表述。
    """
    from services.workorder import api as wo_api

    client, err = resolve_client(ctx, args.get("client_name") or "")
    if err:
        return {}, "", None, err
    period = period_or_current(args.get("period"))
    with cursor() as cur:
        listing = wo_api.list_orders(
            cur,
            tenant_id=ctx.tenant_id,
            workspace_client_id=client["id"],
            period=period,
            limit=1,
        )
        orders = listing["orders"]
        detail = (
            wo_api.order_detail(cur, tenant_id=ctx.tenant_id, work_order_id=str(orders[0]["id"]))
            if orders
            else None
        )
    return client, period, detail, None


def recon_count(recon: dict, key: str) -> int:
    """R3 清单条数:优先落库时算好的 *_count,没有就数清单本身(两种形态的 gate 载荷都认)。"""
    counted = recon.get(f"{key}_count")
    if isinstance(counted, int):
        return counted
    return len(recon.get(key) or [])


def to_decimal(value: Any) -> Decimal:
    """金额 → Decimal(读不出来给 0)。合计一律走它,不过 float —— 钱的加法只有一处入口。"""
    try:
        return Decimal(str(value if value is not None else "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def money(value: Any) -> str:
    """金额 → decimal 两位字符串。读不出来给 "0.00" 而不是抛,答复层永远拿得到可印的值。

    量化用 38 位精度的独立上下文:默认上下文只有 28 位,全所合计这种十几位的数一旦超出就抛
    InvalidOperation 被这里吞成 "0.00" —— 把一个大数印成零比印错还危险。NaN/Infinity 仍走
    "0.00"(它们本来就不是钱)。
    """
    try:
        return str(to_decimal(value).quantize(Decimal("0.01"), context=_MONEY_CONTEXT))
    except (InvalidOperation, ValueError):
        return "0.00"


def money_total(values) -> str:
    """一批金额的合计 → 两位字符串。加法也在放宽精度的上下文里做 —— 默认 28 位会把全所
    合计的低位悄悄四舍五入掉,而合计对不上明细是会计最不能忍的那类错。"""
    with localcontext(_MONEY_CONTEXT):
        total = sum((to_decimal(v) for v in values), Decimal("0"))
    return money(total)


# ── S2 附件工具共用件 ────────────────────────────────────────


def single_attachment(ctx: ToolContext) -> tuple[Optional[dict], Optional[ToolResult]]:
    """取本轮唯一那件料 + 明文字节。租户/会话/上传人三锚再验一次(worker 没有请求可依附,
    身份闸在这里补);盘上路径再过一次防穿越 —— 库里存的字符串不当可信输入。"""
    from core import db

    ids = [str(i) for i in (ctx.attachment_ids or ())]
    if not ids:
        return None, ToolResult(ok=False, error_code=ERR_NO_ATTACHMENT)
    if len(ids) > 1:
        return None, ToolResult(ok=False, error_code=ERR_MANY_ATTACHMENTS, data={"n": len(ids)})
    with db.get_cursor() as cur:
        rows = attachments.list_by_ids(
            cur, tenant_id=ctx.tenant_id, session_id=ctx.session_id, ids=ids
        )
    row = rows[0] if rows else None
    if not row or str(row.get("user_id") or "") != str(ctx.user_id):
        return None, ToolResult(ok=False, error_code=ERR_NO_ATTACHMENT)
    path = attachments.resolve_within_session(
        ctx.tenant_id, ctx.session_id, row.get("file_ref") or ""
    )
    if not path:
        return None, ToolResult(ok=False, error_code=ERR_UNREADABLE, data=attachment_name(row))
    try:
        row = {**row, "content": attachments.read_content(str(path))}
    except OSError:
        return None, ToolResult(ok=False, error_code=ERR_UNREADABLE, data=attachment_name(row))
    return row, None


def attachment_name(row: dict) -> dict[str, Any]:
    """错误/答复里点名是哪一份料的最小投影(文件名)。"""
    return {"filename": row.get("original_name") or ""}


def save_xlsx(ctx: ToolContext, content: bytes, source_name: str) -> dict[str, Any]:
    """产物落回附件表。落不下(盘满/库炸)不翻已经跑成的转换 —— 如实回空,答复少一个下载链,
    不把一次成功的转换报成失败。"""
    from core import db

    out_name = f"{Path(source_name).stem or 'convert'}.xlsx"
    try:
        path = attachments.save(
            content,
            tenant_id=ctx.tenant_id,
            session_id=ctx.session_id,
            original_name=out_name,
        )
        with db.get_cursor(commit=True) as cur:
            row = attachments.insert(
                cur,
                tenant_id=ctx.tenant_id,
                session_id=ctx.session_id,
                user_id=ctx.user_id,
                original_name=out_name,
                file_ref=str(path),
                size_bytes=len(content),
                sha256=attachments.sha256_of(content),
                mime=attachments.guess_mime(out_name),
                kind="converted",
                kind_source=attachments.SOURCE_RULE,
                kind_reason="file_convert_output",
                status=attachments.STATUS_ARTIFACT,
            )
    except Exception:  # noqa: BLE001
        logger.warning("[steward] artifact save failed", exc_info=True)
        return {}
    return {"attachment_id": str(row["id"]), "name": out_name, "size_bytes": len(content)}


def attached_message_text(ctx: ToolContext, row: dict) -> str:
    """随文件一起说的那句话(问题/整理指令):附件不经模型 slot,从挂着这份附件的那条用户
    消息(attachment.message_id)原样取回,同一次 handle_message 落的,不新开机制。"""
    from core import db

    with db.get_cursor() as cur:
        text = store.message_text(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=ctx.session_id,
            message_id=row.get("message_id"),
        )
    return text.strip()


def make_ask_model(task: str, timeout_s: int):
    """生成模块级 ask_model 注入点:测试直接 patch 模块属性,零真调用(同 planner 先例)。

    两套 S2 工具各带自己的 TASK/超时,逐字 6 行 wiring 收成一份工厂;模块级名字保留不动,
    否则 monkeypatch 打桩的测试全部落空。
    """

    def _default_ask(prompt: str, *, ctx: ToolContext):
        from services.ai_gateway import transport

        return transport.text_to_json(
            prompt,
            task=task,
            timeout_s=timeout_s,
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            trace_id=ctx.session_id,
        )

    return _default_ask
