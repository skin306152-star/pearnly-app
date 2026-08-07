# -*- coding: utf-8 -*-
"""管家商品收发存查询 stock_card_lookup(只读薄封装,零新 SQL)。

数据源是事务所记账台账 services.stockcard.report(summary/card),不是 services.inventory
——那一支是 POS 商户侧库存,两套账、两回事,不共用一行代码(勘察已核实,写错就是把商户的
POS 库存冒充事务所记账台账答给会计)。

只答两种问法:
  ① 不给商品关键词:全表概况(商品数 / 负库存家数 / 未归并家数 / 结存总额),最多列几行样例;
  ② 给了商品关键词:在 summary 的 products 里按名字/编码宽松匹配,命中唯一才调 report.card
     答单品明细,命中多个退回候选让人挑(与 tool_scope.resolve_client 同一条"不猜"铁律)。

完整逐笔流水这里答不出来(report.card 的 rows 是全期明细,对话里念不完也没意义)——回复统一
指路去事务所端『商品 → 收发存报表』页面看,产物层不摆一个「导出」按钮出来。
"""

from __future__ import annotations

from services.agent.contracts import ToolResult
from services.steward import tool_scope
from services.steward.registry import ToolContext
from services.stockcard import report as report_svc

ERR_PRODUCT_NOT_FOUND = "steward.stockcard_product_not_found"
ERR_PRODUCT_AMBIGUOUS = "steward.stockcard_product_ambiguous"

CANDIDATE_LIMIT = 8  # 候选多到这个数就没法在对话里逐条念,截断后仍如实标总数
SAMPLE_LIMIT = 8  # 全表概况最多列几个商品当样例(其余的数进汇总统计里)
NEGATIVE_LIMIT = 8  # 负库存清单最多列几个(其余仍计入 negative_count)


def stock_card_lookup(ctx: ToolContext, args: dict) -> ToolResult:
    """某家某期的商品收发存:不给商品名答全表概况,给了商品名答单品明细。"""
    client, err = tool_scope.resolve_client(ctx, args.get("client_name") or "")
    if err:
        return err
    period = tool_scope.period_or_current(args.get("period"))
    date_from, date_to = tool_scope.period_month_range(period)
    base = {
        "client_id": client["id"],
        "client_name": client["name"],
        "period": period,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }

    with tool_scope.cursor() as cur:
        # 同一次提问常先答概况再钻某个商品(下面的 card 分支),两次各自全表 load 是重复
        # 扫描 —— 装一次传给 summary/card 共用(services.stockcard.report.load_context)。
        context = report_svc.load_context(
            cur, tenant_id=ctx.tenant_id, workspace_client_id=client["id"], date_to=date_to
        )
        summary = report_svc.summary(
            cur,
            tenant_id=ctx.tenant_id,
            workspace_client_id=client["id"],
            date_from=date_from,
            date_to=date_to,
            context=context,
        )
    products = summary["products"]

    keyword = (args.get("keyword") or "").strip()
    if not keyword:
        return ToolResult(ok=True, data={**base, **_summary_view(products, summary)})

    hits = _match_products(products, keyword)
    if not hits:
        return ToolResult(
            ok=False, error_code=ERR_PRODUCT_NOT_FOUND, data={**base, "keyword": keyword}
        )
    if len(hits) > 1:
        return ToolResult(
            ok=False,
            error_code=ERR_PRODUCT_AMBIGUOUS,
            data={
                **base,
                "keyword": keyword,
                "total": len(hits),
                "candidates": [_candidate(p) for p in hits[:CANDIDATE_LIMIT]],
            },
        )

    with tool_scope.cursor() as cur:
        card = report_svc.card(
            cur,
            tenant_id=ctx.tenant_id,
            workspace_client_id=client["id"],
            key=hits[0]["key"],
            date_from=date_from,
            date_to=date_to,
            context=context,
        )
    if not card:
        # summary 刚给过这个 key,card 理应查得到;查无当查询抖动处理,不硬凑一份假数据。
        return ToolResult(
            ok=False, error_code=ERR_PRODUCT_NOT_FOUND, data={**base, "keyword": keyword}
        )
    return ToolResult(
        ok=True,
        data={
            **base,
            "keyword": keyword,
            "product": card["product"],
            # rows[0] 是 report.card 合成的"期初"行(报表口径:期初一次性填表 + 期初日之前
            # 全部流水滚出来的一行),永远存在 —— 不是 totals 的字段,得单独取。
            "opening_qty": card["rows"][0]["bal_qty"],
            "totals": card["totals"],
        },
    )


def _match_products(products: list[dict], keyword: str) -> list[dict]:
    """名字/编码宽松命中(精确同名优先),纯函数复用 tool_scope.match_clients 同一条思路。"""
    kw = keyword.lower()
    exact = [p for p in products if (p.get("name") or "").lower() == kw]
    if exact:
        return exact
    return [
        p
        for p in products
        if kw in (p.get("name") or "").lower() or kw in (p.get("product_id") or "").lower()
    ]


def _candidate(p: dict) -> dict:
    return {"key": p["key"], "name": p.get("name") or "", "bal_qty": p.get("bal_qty") or "0"}


def _summary_view(products: list[dict], summary: dict) -> dict:
    negatives = [p for p in products if p.get("negative")]
    unmatched = [p for p in products if not p.get("matched")]
    return {
        "product_count": len(products),
        "negative_count": len(negatives),
        "unmatched_count": len(unmatched),
        "bal_value_total": tool_scope.money_total(p.get("bal_value") for p in products),
        "excluded_count": summary.get("excluded_count", 0),
        "negative_rows": [_sample_row(p) for p in negatives[:NEGATIVE_LIMIT]],
        "sample_rows": [_sample_row(p) for p in products[:SAMPLE_LIMIT]],
    }


def _sample_row(p: dict) -> dict:
    return {
        "name": p.get("name") or "",
        "bal_qty": p.get("bal_qty") or "0",
        "bal_unit_cost": p.get("bal_unit_cost") or "",
        "bal_value": p.get("bal_value") or "",
        "negative": bool(p.get("negative")),
    }
