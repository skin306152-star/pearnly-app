# -*- coding: utf-8 -*-
"""本方销项票逐票聚合(佐证层纯计算叶子 · MC1-c.1)。

sort 把 seller==自家的票归 sales_doc 堆后,本模块把这些逐票 OCR money 聚合成一条「已开票
销售」佐证数:净/税/含税三口径求和 + 票号去重(复用 purchase.totals.dedupe_key)+ 逐票 7%/
含税守恒抽查 + 覆盖率/缺口(对权威销项)。

产出只喂 reconcile 佐证区(gates.r2_sales_corroboration)与前端审核卡,永不覆盖 R2 权威销项
(POS 直读 / 人工申报)——零售客户绝大多数销售不开全额票,逐票汇总天生只覆盖约 1/8,当佐证/
地板不当权威(见方案 §3.3 优先级表)。转正为权威须覆盖率 ≥98% + 完整性外证 + 守恒全绿,按客户
类型判(MC1-c.2),此模块只算佐证不转正。

零副作用、不碰 DB、钱一律 Decimal。去重与守恒违反都点名留痕不静默吞(拍板④ 同款纪律):
重复票号聚合取去重值但双件点名;守恒违反的票仍入合计(人可改判)但单列点名,不带病沉默。
"""

from __future__ import annotations

from decimal import Decimal

from services.purchase.totals import dedupe_key
from services.workorder import decisions, evidence, kinds
from services.workorder.steps import reconcile_gates
from services.workorder.steps.reconcile_gates import STANDARD_VAT_RATE, to_dec

_EVT_CLASSIFIED = "item_classified"
_RECON_STEP = "reconcile"
# 冻结值 vs 现算比对的核心钱字段(算法演进 / reconcile 后补料致分叉时据此判 stale)。
_CORROBORATION_KEYS = (
    "net_total",
    "vat_total",
    "gross_total",
    "authoritative_net",
    "coverage",
    "covered_state",
)

# 守恒抽查容差(与 T0 抽查同口径 0.02):|vat − net×7%| 与 |net+vat − 含税| 超此即点名。
_CONSERV_TOL = Decimal("0.02")
_ZERO = Decimal("0")
# 转正门槛(方案 §4.2):覆盖率 ≥98% 才够格当权威。此处仅用于呈现态判绿,不做真转正(MC1-c.2)。
_COVERAGE_PROMOTE = Decimal("0.98")


def _label(money: dict) -> str:
    """点名用票据标签:优先票号,退税号,再退占位。"""
    return str(money.get("invoice_number") or money.get("seller_tax") or "?")


def aggregate_invoice_sales(money_list: list) -> dict:
    """逐票 money → 聚合佐证。money 形状 = classify._money_fields 快照(subtotal/vat/
    total_amount/invoice_number/seller_tax/invoice_date)。

    返回三口径合计(净/税/含税,票面全量,含守恒违反票——人可改判,不静默剔除)+ 去重后合计
    (票号+税号+含税指纹,重复只算一次)+ 去重/守恒违反点名清单 + 日期覆盖。含税缺失用 净+税 兜底。
    """
    tickets = [m for m in (money_list or []) if m]
    net_total = vat_total = gross_total = _ZERO
    net_dedup = vat_dedup = gross_dedup = _ZERO
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    violations: list[str] = []
    dates: list[str] = []
    for m in tickets:
        net = to_dec(m.get("subtotal"))
        vat = to_dec(m.get("vat"))
        gross = to_dec(m.get("total_amount")) or (net + vat)
        net_total += net
        vat_total += vat
        gross_total += gross
        day = str(m.get("invoice_date") or "").strip()
        if day:
            dates.append(day)
        # 守恒抽查:7% 锚(vat ≈ net×7%)+ 含税自洽(net+vat ≈ 含税)。任一破 → 点名,但仍入
        # 全量合计(不静默剔除,留人审改判);去重后合计同样计入(违反≠重复,两码事)。
        if (
            abs(vat - net * STANDARD_VAT_RATE) > _CONSERV_TOL
            or abs(net + vat - gross) > _CONSERV_TOL
        ):
            violations.append(_label(m))
        key = dedupe_key(
            supplier_tax=m.get("seller_tax"),
            doc_no=m.get("invoice_number"),
            grand_total=m.get("total_amount") or m.get("subtotal"),
        )
        if key is not None and key in seen:
            duplicates.append(_label(m))
            continue
        if key is not None:
            seen[key] = _label(m)
        net_dedup += net
        vat_dedup += vat
        gross_dedup += gross
    return {
        "invoice_count": len(tickets),
        "deduped_count": len(tickets) - len(duplicates),
        "duplicates": duplicates,
        "net_total": str(net_total),
        "vat_total": str(vat_total),
        "gross_total": str(gross_total),
        "net_deduped": str(net_dedup),
        "vat_deduped": str(vat_dedup),
        "gross_deduped": str(gross_dedup),
        "conservation_violations": violations,
        "conserved_count": len(tickets) - len(violations),
        "date_from": min(dates) if dates else None,
        "date_to": max(dates) if dates else None,
    }


def build_corroboration(agg: dict, *, authoritative_net=None, authoritative_vat=None) -> dict:
    """给聚合结果套上对权威销项的覆盖率/缺口 + 呈现态(佐证不夺权威的呈现层)。

    covered_state 三态(守恒违反单列,不并入此态——见前端红线呈现):
      green  覆盖率 ≥98%(高覆盖客户,方案 §4.2 转正候选,但本模块不转正)
      amber  有权威且覆盖不全 → 点名缺口金额(本案:零售客户约 12.5%)
      needs  无权威销项(未申报 POS 直读/人工申报)→ 只显已开票,不编造缺口(现状诚实)

    权威取聚合前的票面全量净(net_total)对比——它是「已开票销售」的实义值;去重/守恒仅作旁注。
    authoritative_net 缺失/≤0 → needs 态,不算缺口(状态诚实优先于凑一个数)。
    """
    out = dict(agg, source="invoice_aggregate")
    net = to_dec(agg.get("net_total"))
    auth = to_dec(authoritative_net) if authoritative_net is not None else _ZERO
    if auth > _ZERO:
        out["authoritative_net"] = str(auth)
        out["authoritative_vat"] = (
            str(to_dec(authoritative_vat)) if authoritative_vat is not None else None
        )
        out["gap_net"] = str(auth - net)
        coverage = net / auth
        out["coverage"] = str(coverage)
        out["covered_state"] = "green" if coverage >= _COVERAGE_PROMOTE else "amber"
    else:
        out["authoritative_net"] = None
        out["authoritative_vat"] = None
        out["gap_net"] = None
        out["coverage"] = None
        out["covered_state"] = "needs"
    return out


def corroboration_for_detail(events: list, items: list, classified: dict | None = None):
    """order_detail 销项佐证读侧(F6 写读归一):优先消费 reconcile 已落库的
    gates.r2_sales_corroboration(与交付包 / step_done 同一份冻结值,详情页不另现算一个数),
    工单未跑到 reconcile / R1·R2 needs 停机时回退现算(corroboration_from_events)。

    冻结值在场且与现算分叉(算法演进,或 reconcile 后又补了人工销项)→ 以冻结值为准并标
    stale=True:诚实呈现「这是交付那一刻的值,现算已不同」,不静默糊成一个数。无 sales_doc
    件两路都 None,前端不渲染佐证卡(现状诚实)。冻结与现算在数据未变时逐字节一致由单测锁死。
    归一逻辑与 SA-2b(edc_corroboration)共用 evidence.frozen_or_live_corroboration,不各写一份。"""
    live = corroboration_from_events(events, items, classified=classified)
    return evidence.frozen_or_live_corroboration(
        events,
        step=_RECON_STEP,
        gate_key="r2_sales_corroboration",
        live=live,
        compare_keys=_CORROBORATION_KEYS,
    )


def corroboration_from_events(events: list, items: list, classified: dict | None = None):
    """order_detail 读侧投影(MC1-c.1):从事件流现算销项佐证,独立于 reconcile 是否 ok。

    sales_doc 件的逐票票面钱 → 聚合;R2 权威取 sales_summary 件的 sales_read 直读聚合(人工申报
    858,780.16 走这条),缺权威 → needs 态只显已开票不编缺口。工单停在 R1/R2 needs 时 step_done
    里没有 r2_sales_corroboration,故不走 replay_step_done——照样出佐证。无 sales_doc 件 → None,
    前端不渲染佐证卡(现状诚实)。R2 权威取值逻辑一行不碰(方案 §7.5 佐证不夺权威护栏)。
    classified 可由调用方传入已回放好的 item_classified 索引(api.order_detail 同请求只算一次)。
    """
    if classified is None:
        classified = evidence.replay_items_by_type(events, _EVT_CLASSIFIED)
    money_list = [
        (classified.get(it["id"]) or {}).get("payload", {}).get("money")
        for it in items
        if it["kind"] == decisions.SALES_DOC
    ]
    money_list = [m for m in money_list if m]
    if not money_list:
        return None
    r2 = authoritative_sales(classified)
    agg = aggregate_invoice_sales(money_list)
    return build_corroboration(
        agg,
        authoritative_net=str(r2["sales_amount"]) if r2["used"] else None,
        authoritative_vat=str(r2["output_vat"]) if r2["used"] else None,
    )


def authoritative_sales(classified: dict) -> dict:
    """R2 权威销项现算(读侧投影共用):sales_summary 件的 sales_read 直读聚合,返回
    reconcile_gates.aggregate_sales 结果({used, sales_amount, output_vat})。c.1 逐票佐证
    与 SA-2 EDC 聚合佐证(edc_corroboration)共用这一份取数,不各自重放一遍事件流。"""
    reads = {
        iid: rec["payload"]["sales_read"]
        for iid, rec in classified.items()
        if rec["payload"].get("kind") == kinds.SALES_SUMMARY and rec["payload"].get("sales_read")
    }
    return reconcile_gates.aggregate_sales(reads)
