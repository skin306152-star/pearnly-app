# -*- coding: utf-8 -*-
"""EDC 结算票 → 销项聚合佐证(SA-2b · 事件流适配器,照 E1 workorder_recon_adapter 范式)。

职责边界:
  - SA-1(services/sales_agg)是唯一聚合算法——本模块只把 item_classified 回放出的 edc
    快照映射成它已经能吃的 payload,一行聚合逻辑不重写。同料喂 CLI(sales_agg.cli)与本
    适配器结果逐字节一致,由金标测试锁死(没有第二套口径)。
  - 聚合结果只做佐证:挂 gates.r2_edc_corroboration(reconcile)/ order_detail.
    edc_corroboration(读侧),与 c.1 逐票聚合佐证并排展示。R2 权威销项(POS 直读/人工
    申报)一行不碰——会计看到「EDC 聚合=X、覆盖 N 张结算票」,采不采纳自己定(人在环)。
  - 覆盖率诚实:输出带件数/金额对权威销项的覆盖事实;权威缺席 → needs 态只显聚合值,
    不编造缺口(与 c.1 build_corroboration 同一份呈现纪律,阈值同源)。

纯函数、零副作用:输入是已查出的事件列表,不碰 DB、不碰 feature flag(佐证层无闸,
零 EDC 件时上游不挂键,存量工单 payload 逐字节不变)。
"""

from __future__ import annotations

from typing import Optional

from services.workorder import evidence, kinds
from services.workorder.steps import sales_aggregate

_EVT_CLASSIFIED = "item_classified"
_RECON_STEP = "reconcile"
GATE_KEY = "r2_edc_corroboration"

# 冻结值 vs 现算比对的核心钱字段(与 c.1 的 stale 判据同族:算法演进/补料分叉据此点破)。
_COMPARE_KEYS = (
    "invoice_count",
    "net_total",
    "vat_total",
    "gross_total",
    "authoritative_net",
    "coverage",
    "covered_state",
)


def payloads_from_events(events: list, classified: Optional[dict] = None) -> list[dict]:
    """回放 kind=edc_settlement 且带 edc 快照的件 → SA-1 EdcSettlement payload 列表。

    ref=item_id(聚合输出的源行引用可回查原件);按 item_id 排序——回放 dict 序受事件
    插入序影响,排序后重跑/续跑的聚合输出(refs 列表序)确定一致。快照缺失的 EDC 件
    (理论上只有手工造的事件)不硬造空毛额行,直接跳过。"""
    if classified is None:
        classified = evidence.replay_items_by_type(events, _EVT_CLASSIFIED)
    out = []
    for item_id, rec in sorted(classified.items()):
        payload = rec["payload"]
        if payload.get("kind") != kinds.EDC_SETTLEMENT:
            continue
        edc = payload.get("edc")
        if edc:
            out.append({**edc, "ref": item_id})
    return out


def aggregate_report(payloads: list[dict]) -> dict:
    """喂 SA-1 聚合(EDC 单渠道)。银行渠道不在此混入——E1 银行对账已有专线,票据渠道
    归 c.1 逐票佐证,佐证层各管一段不双计;SA-1 会如实落 bank_channel_absent note。"""
    from services.sales_agg.aggregate import aggregate_month

    return aggregate_month(payloads, [], [])


def build_corroboration(report: dict, *, authoritative_net=None, authoritative_vat=None) -> dict:
    """SA-1 月度报告 → 佐证卡形态。键名对齐 c.1(sales_aggregate.build_corroboration 的
    invoice_count/net_total/coverage/covered_state…),前端佐证卡同一套渲染只换文案;
    覆盖率/呈现态直接复用 c.1 的实现(转正阈值单一事实源)。daily/conflicts/notes 原样
    带出——按日聚合与点名是会计核对官方数的工作底稿,不在呈现层裁剪。"""
    ch = report["by_channel"]["edc_settlement"]
    daily = report["daily"]
    total = report["month_total"]
    agg = {
        "invoice_count": ch["count"],
        "deduped_count": ch["included_count"],
        "duplicates": [d["ref"] for d in ch["duplicates"]],
        "gross_total": total["gross"],
        "net_total": total["sales_amount"],
        "vat_total": total["output_vat"],
        "vat_method": total["vat_method"],
        "fee_missing_count": ch["fee_missing_count"],
        "date_from": daily[0]["date"] if daily else None,
        "date_to": daily[-1]["date"] if daily else None,
        "daily": daily,
        "conflicts": report["conflicts"],
        "notes": report["notes"],
    }
    out = sales_aggregate.build_corroboration(
        agg, authoritative_net=authoritative_net, authoritative_vat=authoritative_vat
    )
    out["source"] = "edc_aggregate"
    return out


def corroboration_from_events(events: list, classified: Optional[dict] = None) -> Optional[dict]:
    """order_detail 读侧现算(独立于 reconcile 是否跑到):EDC 快照 → SA-1 聚合 → 佐证。

    R2 权威取 sales_summary 直读/人工申报的聚合(与 c.1 共用 authoritative_sales 取数),
    工单停在 R1/R2 needs 时照样出佐证——MC0 P-6 的真场景恰是「销项没数,EDC 聚合给个
    可采纳的候选」。零 EDC 件 → None,前端不渲染(现状诚实)。"""
    if classified is None:
        classified = evidence.replay_items_by_type(events, _EVT_CLASSIFIED)
    payloads = payloads_from_events(events, classified)
    if not payloads:
        return None
    r2 = sales_aggregate.authoritative_sales(classified)
    return build_corroboration(
        aggregate_report(payloads),
        authoritative_net=str(r2["sales_amount"]) if r2["used"] else None,
        authoritative_vat=str(r2["output_vat"]) if r2["used"] else None,
    )


def corroboration_for_detail(events: list, classified: Optional[dict] = None) -> Optional[dict]:
    """读侧写读归一(F6/A2 同款):优先消费 reconcile 落库的 gates.r2_edc_corroboration
    冻结值;未跑到 reconcile 时回退现算。冻结与现算核心钱字段分叉 → 以冻结值为准并标
    stale=True,诚实呈现「这是交付那一刻的值」,不静默糊成一个数。"""
    live = corroboration_from_events(events, classified)
    frozen = _frozen(events)
    if frozen is None:
        return live
    if live is not None and any(frozen.get(k) != live.get(k) for k in _COMPARE_KEYS):
        return dict(frozen, stale=True)
    return frozen


def _frozen(events: list) -> Optional[dict]:
    payload = evidence.replay_step_done(events, _RECON_STEP)
    if not payload:
        return None
    frozen = (payload.get("gates") or {}).get(GATE_KEY)
    return frozen if isinstance(frozen, dict) else None
