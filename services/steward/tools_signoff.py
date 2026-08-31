# -*- coding: utf-8 -*-
"""管家签批闸 close_readiness(B5 · 只读投影,零新 SQL)。

回答月结产线上最后那一句:「A 公司 6 月能签了吗?还差什么?」以前会计要在客户页四个 tab
(工单 / 复核 / 交付包 / 数字)之间跳着自己比对。五项判据其实早就在同一个
services.workorder.api.order_detail 的返回里,只是从来没有一处把它们合成一句结论:

  税额     numbers['tax_due']      compute 步认列结果
  银行     bank_recon              R3 四清单投影
  待判件   flagged                 引擎请人裁的口子
  交付包   deliverables            package 步一次出整批
  签批态   signoff                 sod.signoff_projection(P0-1 单一事实源)

第六项负库存(见 _check_negative_stock)不在这份投影里,单独查 services.stockcard.report
—— 与前四项不同,它不是签批前置:缺票是警讯不是硬闸,会计可能明知有缺仍照签(货已经卖了,
补票是后面事务所的事,不能因为它拦住整期收官)。checks 列表里带着,但绝不进 _PREREQ,
verdict/blocking 两个字段都不因它而变。

与 client_status 不重叠:那个答「引擎跑到哪一步」,这个答「够不够格签」——引擎跑完了但
银行还有 3 笔缺票时,两个问题的答案分岔,而签字担责的是后者。

每项判法都是一行确定性代码,模型碰不到判定;不出"看着差不多了"这种综合评价,判据必须能被
会计逐条复核(她签的字是要担责的)。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.steward.contracts import ToolResult
from services.steward import tool_scope
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

CHECK_NUMBERS = "numbers"
CHECK_BANK = "bank_recon"
CHECK_FLAGGED = "flagged"
CHECK_DELIVERABLES = "deliverables"
CHECK_NEGATIVE_STOCK = "negative_stock"
CHECK_SIGNOFF = "signoff"

STATE_OK = "ok"
STATE_BLOCKED = "blocked"
STATE_UNKNOWN = "unknown"
# 提示态:查得到确定的结果,但不拦签批,只是要说给会计听(与"过/没过/不知道"三态并列,
# 目前只有 CHECK_NEGATIVE_STOCK 用得上)。
STATE_WARN = "warn"

VERDICT_NOT_STARTED = "not_started"
VERDICT_SIGNED = "signed"
VERDICT_RESIGN = "resign_needed"
VERDICT_READY = "ready"
VERDICT_BLOCKED = "blocked"

# 签批的前置四项(签批态本身不在内 —— 它是结果不是条件;负库存也不在内 —— 见模块顶注)。
_PREREQ = (CHECK_NUMBERS, CHECK_BANK, CHECK_FLAGGED, CHECK_DELIVERABLES)


def close_readiness(ctx: ToolContext, args: dict) -> ToolResult:
    """这家这期够不够格签批收官:五项逐项过一遍 + 一句结论。"""
    client, period, detail, err = tool_scope.client_order(ctx, args)
    if err:
        return err
    data = {
        "client_id": client["id"],
        "client_name": client["name"],
        "period": period,
        "has_order": bool(detail),
        "work_order_id": str((detail or {}).get("id") or ""),
        "status": (detail or {}).get("status") or "",
        "verdict": VERDICT_NOT_STARTED,
        "blocking": 0,
        "signoff_actor": "",
        "signoff_at": "",
        "checks": [],
    }
    if not detail:
        return ToolResult(ok=True, data=data)

    checks = [
        _check_numbers(detail),
        _check_bank(detail),
        _check_flagged(detail),
        _check_deliverables(detail),
        _check_negative_stock(ctx, client, period),
        _check_signoff(detail),
    ]
    signoff = detail.get("signoff") or {}
    blocking = [c for c in checks if c["check"] in _PREREQ and c["state"] != STATE_OK]
    data.update(
        {
            "verdict": _verdict(signoff, blocking),
            "blocking": len(blocking),
            "signoff_actor": signoff.get("actor") or "",
            "signoff_at": signoff.get("at") or "",
            "checks": checks,
        }
    )
    return ToolResult(ok=True, data=data)


def _verdict(signoff: dict, blocking: list) -> str:
    """签过了先说签过(会计的下一句会变成"要不要重签"),没签才谈够不够格。

    stale=True 是「签完之后引擎又重跑过」——数字已经重生成,那次签名担保的不是眼下这份账,
    当没签处理(沿用 sod.signoff_projection 的语义,不在这里另立一套)。
    """
    if signoff and not signoff.get("stale"):
        return VERDICT_SIGNED
    if signoff:
        return VERDICT_RESIGN
    return VERDICT_BLOCKED if blocking else VERDICT_READY


def _check(name: str, state: str, reason: str, n: Optional[int] = None) -> dict:
    return {"check": name, "state": state, "reason": reason, "n": n}


def _check_numbers(detail: dict) -> dict:
    """税额算了没:compute 步落的 tax_due 在不在。numbers 为空 = 引擎还没算到,不能因为
    别的都齐了就当算过 —— 「应交 0」和「还没算」在签批这一步是两回事。"""
    if (detail.get("numbers") or {}).get("tax_due") is None:
        return _check(CHECK_NUMBERS, STATE_BLOCKED, "not_computed")
    return _check(CHECK_NUMBERS, STATE_OK, "computed")


def _check_bank(detail: dict) -> dict:
    """银行对上没:缺票(有流水无票)+ 待人审两张清单清空才算过。

    有票无流水不拦:赊销票挂账未收款是常态,拿它拦签批会天天误报。
    完全没有对账结果给 unknown 而不是 blocked:没收到银行流水的客户不该被判"没过",
    但也绝不当成"已对平"——投影给 None 时照实说不知道。
    """
    recon = detail.get("bank_recon") or None
    if not recon:
        return _check(CHECK_BANK, STATE_UNKNOWN, "no_recon")
    outstanding = tool_scope.recon_count(recon, "missing_invoice") + tool_scope.recon_count(
        recon, "review"
    )
    if outstanding:
        return _check(CHECK_BANK, STATE_BLOCKED, "outstanding", outstanding)
    return _check(CHECK_BANK, STATE_OK, "balanced")


def _check_flagged(detail: dict) -> dict:
    """待判清了没:flagged 每一件都是引擎请人裁的口子,留一件就是留一处没人认的账。"""
    n = len(detail.get("flagged") or [])
    if n:
        return _check(CHECK_FLAGGED, STATE_BLOCKED, "pending", n)
    return _check(CHECK_FLAGGED, STATE_OK, "clear")


def _check_deliverables(detail: dict) -> dict:
    """报表出了没。package 步一次出整批(ภ.พ.30 草稿 / 底稿 / 证据索引同版本一起落),
    所以「有没有交付物」等价于「出包跑了没」——这里只数份数,不发明"必须有哪几份"的规矩:
    出哪几份随闸与料而变,在这里写死一张清单迟早与 package.py 漂。"""
    n = len(detail.get("deliverables") or [])
    if n:
        return _check(CHECK_DELIVERABLES, STATE_OK, "packaged", n)
    return _check(CHECK_DELIVERABLES, STATE_BLOCKED, "not_packaged")


def _check_negative_stock(ctx: ToolContext, client: dict, period: str) -> dict:
    """负库存商品数(提示项,见模块顶注 —— 查得到就如实说,绝不因此拦签批)。

    数据源与 stock_card_lookup 同一份 services.stockcard.report.summary,不是这里另起一套
    判据 —— 两处对同一期报出的负库存家数必须一致。查询本身抖动(报表侧异常)不该拖垮整张
    签批闸的其余四项,失败当"不知道"处理而不是让 close_readiness 整个报错。
    """
    from services.stockcard import report as report_svc

    try:
        date_from, date_to = tool_scope.period_month_range(period)
        with tool_scope.cursor() as cur:
            summary = report_svc.summary(
                cur,
                tenant_id=ctx.tenant_id,
                workspace_client_id=client["id"],
                date_from=date_from,
                date_to=date_to,
            )
    except Exception:  # noqa: BLE001 — 提示项查不到不该把签批闸其余四项一起拖挂
        logger.warning("[steward] negative stock check failed", exc_info=True)
        return _check(CHECK_NEGATIVE_STOCK, STATE_UNKNOWN, "stock_check_failed")
    n = sum(1 for p in summary["products"] if p.get("negative"))
    if n:
        return _check(CHECK_NEGATIVE_STOCK, STATE_WARN, "negative_stock", n)
    return _check(CHECK_NEGATIVE_STOCK, STATE_OK, "no_negative_stock")


def _check_signoff(detail: dict) -> dict:
    signoff = detail.get("signoff") or None
    if not signoff:
        return _check(CHECK_SIGNOFF, STATE_BLOCKED, "unsigned")
    if signoff.get("stale"):
        return _check(CHECK_SIGNOFF, STATE_BLOCKED, "stale")
    return _check(CHECK_SIGNOFF, STATE_OK, "signed")
