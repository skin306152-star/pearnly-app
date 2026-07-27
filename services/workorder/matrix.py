# -*- coding: utf-8 -*-
"""事务所矩阵(C4)只读聚合:客户行 × 当期义务列,一次 JOIN 喂全矩阵。

从 routes/tax_profile_routes.py 下沉(B2-M1):矩阵原先只有 HTTP 一个消费方,SQL 与聚合都
写在路由里;智能管家的 matrix_overview 工具要读同一份矩阵,再抄一遍 SQL 两处必漂——
对话里查到的数与人手点开矩阵看到的必须同源。fetch_rows/build 拆成两半,是因为作用域收窄
(被分派成员只看分到的账套)依赖 HTTP 权限快照,留在各自调用方做,中间那道过滤两边自选。

列集合 = 该租户该期实际物化过的 obligation_code(没物化过的客户/期不会凭空长出列),
没有任何物化记录的客户仍出现在矩阵里,各格子标「未评估」而非编造一个已知徽章。
"""

from __future__ import annotations

from typing import Optional

from services.workorder import engine, obligation_engine

# 矩阵格子徽章(C4 · UI-Canon-v4 §1 四色族:good=顺畅/完结,warn=缺料/催,
# crit=等人判/卡点,sage=AI 在做)。由工单态推出的四个徽章名与 engine.STATUS_GROUPS 的
# 组名同名同义(stuck+review 合成「待审」等口径写在那里一份,管家筛工单共用)——
# 常量留在此处是给消费方一个稳定的徽章词汇入口,值一律从组表来,不另写一套判据。
BADGE_NO_NEED = "no_need"
BADGE_PENDING_ORDER = "pending_order"
BADGE_MISSING_MATERIALS = engine.group_of(engine.STATUS_COLLECTING)
BADGE_IN_PROGRESS = engine.group_of(engine.STATUS_RUNNING)
BADGE_PENDING_REVIEW = engine.group_of(engine.STATUS_REVIEW)
BADGE_FROZEN = engine.group_of(engine.STATUS_ARCHIVE)
BADGE_NOT_EVALUATED = "not_evaluated"

# 客户目录(EN-clients · 2026-07-13)「画像完整度」= 这 6 个默认落 unknown 的画像字段
# 里已被人工确认几个,0..1。挂在矩阵响应(同一 LEFT JOIN,零额外往返,列带 p_ 前缀)
# 与 GET tax-profile 出参(档案页 0% CTA 消费,前端不再手抄一份字段表),不是画像表单
# FIELD_DEFS 全集——sbt_status/filing_disposition 默认值本身就是"已答"(none/active),
# 计入分母只会让每个新客户显得比实际更"完整",故只数真正默认 unknown 的字段。
_COMPLETENESS_FIELDS = (
    "has_employees",
    "pays_individuals",
    "pays_juristic",
    "pays_foreign",
    "pays_interest_dividend",
    "efiling_enrolled",
)

_ROWS_SQL = """
    SELECT wc.id AS client_id, wc.name AS client_name, wc.tax_id AS client_tax_id,
           o.obligation_code, o.status AS obligation_status,
           o.due_paper, o.due_efiling, o.work_order_id,
           wo.status AS order_status, d.display_names,
           COALESCE(p.has_employees, 'unknown') AS p_has_employees,
           COALESCE(p.pays_individuals, 'unknown') AS p_pays_individuals,
           COALESCE(p.pays_juristic, 'unknown') AS p_pays_juristic,
           COALESCE(p.pays_foreign, 'unknown') AS p_pays_foreign,
           COALESCE(p.pays_interest_dividend, 'unknown') AS p_pays_interest_dividend,
           COALESCE(p.efiling_enrolled, 'unknown') AS p_efiling_enrolled
    FROM workspace_clients wc
    LEFT JOIN client_period_obligations o
        ON o.tenant_id = wc.tenant_id
       AND o.workspace_client_id = wc.id
       AND o.period = %s
    LEFT JOIN work_orders wo ON wo.id = o.work_order_id
    LEFT JOIN tax_obligation_defs d ON d.obligation_code = o.obligation_code
    LEFT JOIN client_tax_profiles p
        ON p.tenant_id = wc.tenant_id AND p.workspace_client_id = wc.id
    WHERE wc.tenant_id = %s AND wc.is_active = TRUE
    ORDER BY wc.name, o.obligation_code
"""


def profile_completeness(row: dict, prefix: str = "") -> float:
    """0..1,round 到 2 位。prefix 供矩阵行(画像列 SQL 别名带 p_)复用同一份字段表;
    行里没有画像列(旧调用点/测试 fixture 没带)一律按全 unknown 算,不假装完整——
    client_tax_profiles 缺档时 COALESCE 已在 SQL 层退到 'unknown'。"""
    answered = sum(1 for f in _COMPLETENESS_FIELDS if row.get(prefix + f, "unknown") != "unknown")
    return round(answered / len(_COMPLETENESS_FIELDS), 2)


def badge(obligation_status: Optional[str], order_status: Optional[str]) -> str:
    """(obligation_status, order_status) → 矩阵格子徽章(纯函数,零 I/O,见常量顶注)。

    工单态一律经 engine.group_of 归组(单一事实源,C4-R1:首版手打 "archived"/"signed"
    两个臆造词,真冻结单 status=archive 落 fallthrough 错标「未评估」——测试也用同一套
    错词自证自洽,教训=状态字符串必须来自权威常量)。
    """
    if obligation_status is None:
        return BADGE_NOT_EVALUATED  # 该期从未物化过义务(未存过画像/未开过单)
    if obligation_status == obligation_engine.STATUS_NIL:
        return BADGE_NO_NEED
    if order_status is None:
        return BADGE_PENDING_ORDER
    return engine.group_of(order_status) or BADGE_NOT_EVALUATED  # 未知未来态:诚实降级


def fetch_rows(cur, *, tenant_id: str, period: str) -> list[dict]:
    """一次查询取全矩阵原料(客户 × 当期义务 × 工单 × 画像)。严禁逐客户循环查询。"""
    cur.execute(_ROWS_SQL, (period, tenant_id))
    return [dict(r) for r in cur.fetchall()]


def build(rows: list[dict], *, period: str) -> dict:
    """原料行 → 矩阵视图 {period, clients, obligation_codes, obligation_labels, cells}。

    纯函数(零 I/O):调用方按自己的权限口径先过滤 rows 再进来。
    """
    clients: dict[int, dict] = {}
    client_has_order: dict[int, bool] = {}
    codes: set[str] = set()
    labels: dict[str, dict] = {}
    cells: list[dict] = []
    for r in rows:
        cid = int(r["client_id"])
        clients.setdefault(
            cid,
            {
                "id": cid,
                "name": r["client_name"],
                "tax_id": r.get("client_tax_id"),
                "profile_completeness": profile_completeness(r, prefix="p_"),
            },
        )
        client_has_order.setdefault(cid, False)
        code = r["obligation_code"]
        if code is None:
            continue
        codes.add(code)
        if code not in labels and r.get("display_names"):
            labels[code] = r["display_names"]
        if r["work_order_id"]:
            client_has_order[cid] = True
        cells.append(_cell(r, cid, code))

    out_clients = []
    for cid, c in clients.items():
        # 只答「本期没有工单」不答「该有单」(全 no_need 的也 True)· 催不催单见前端 hasDuty。
        c["missing_order"] = not client_has_order.get(cid, False)
        out_clients.append(c)
    out_clients.sort(key=lambda c: c["name"])
    return {
        "period": period,
        "clients": out_clients,
        "obligation_codes": sorted(codes),
        "obligation_labels": labels,
        "cells": cells,
    }


def _cell(r: dict, client_id: int, code: str) -> dict:
    iso = obligation_engine.iso_or_none
    return {
        "client_id": client_id,
        "obligation_code": code,
        "obligation_status": r["obligation_status"],
        "order_status": r["order_status"],
        "work_order_id": str(r["work_order_id"]) if r["work_order_id"] else None,
        "due_paper": iso(r["due_paper"]),
        "due_efiling": iso(r["due_efiling"]),
        # 顺延(G3 · MC2-B 件2):原始日透传,顺延日现算另加。逾期锚点日以 due_efiling_deferred
        # 为权威(前端 isOverdue 指回此处;管家 tools_close.py 仍锚纸质日晚 8 天,未收口)。
        "due_paper_deferred": iso(obligation_engine.defer_optional(r["due_paper"])),
        "due_efiling_deferred": iso(obligation_engine.defer_optional(r["due_efiling"])),
        "badge": badge(r["obligation_status"], r["order_status"]),
    }
