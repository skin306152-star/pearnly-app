# -*- coding: utf-8 -*-
"""存货科目组(ISACC ACCCOD)判据层 —— 候选筛选 + 「这次建库存品挂哪个组」三档解析。纯函数。

与 agent_reporting 分工:那边管心跳上报的存取(净化 + 写 config),这里只回答「拿到这份候选
之后怎么办」。销项/采购两个 mapper、端点 PATCH、异常卡认同一份判据,才不会出现「卡里选得到、
推的时候还是拦」。agent_reporting 顶部 re-import fit_stock_acc_groups 当 facade,老调用点不动。
"""

from __future__ import annotations

from typing import Any, Dict, List, NamedTuple, Optional

# 零库存主档的账套要建第一个库存品时,缺的到底是哪一样 —— 两个码分开,补救卡给的指引才不一样:
#   missing  一个合格的存货科目组都没有 → 会计得先去 Express 建(组本身不存在,问他选也没得选)
#   required 合格的有好几个 → 只是没人拍板用哪个 → 弹卡选一次,写进端点 config 后不再问
REASON_ACC_GROUP_MISSING = "stock_acc_group_missing"
REASON_ACC_GROUP_REQUIRED = "stock_acc_group_required"


class StockAccGroupChoice(NamedTuple):
    """acccod = 定下来的组(空 = 没定);fail_reason 非空 → 拦下这张票;auto = 系统替客户定的。"""

    acccod: str
    fail_reason: str
    auto: bool


def fit_stock_acc_groups(config: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """本端点可选的存货科目组(小助手判 fit=True 的候选)· 不查库。

    单一名单源:端点 PATCH 用它校验选择、异常卡用它渲染下拉、下面的三档解析用它数候选 ——
    三处认同一份名单,不会出现「卡里选得到、存的时候 400」。
    """
    raw = (config or {}).get("reported_stock_acc_groups")
    if not isinstance(raw, list):
        return []
    return [g for g in raw if isinstance(g, dict) and g.get("fit") and g.get("acccod")]


def resolve_stock_acc_group(config: Optional[Dict[str, Any]]) -> StockAccGroupChoice:
    """账套零库存主档时,这次建库存品挂哪个存货科目组;定不下来就说清缺的是哪一样。

    端点显式配过 stock_acccod → 一律用它,不看候选数(会计拍过板的决定,不因心跳刷新翻案)。
    没配则按合格候选数分三档:
      1 个  → 自动用它。没得选,问了也是白问 —— 每张票弹一次卡纯粹是挡会计的路。
      0 个  → REASON_ACC_GROUP_MISSING,缺的是科目本身,得先去 Express 建一个。
      ≥2 个 → REASON_ACC_GROUP_REQUIRED,弹卡选一次(选完写端点 config,以后不再问)。

    ★不按 used_by 众数自动选:真账套 69SINCER 的 37 个库存品里 ST01 挂了 19 个(最多),可它的
    存货科目是 14-01-03-00 อุปกรณ์สำนักงาน(办公设备 = 固定资产),挂它的那 19 个商品名全是
    「ห้ามใช้ / ไม่ใช้แล้วนะคะ」的废弃档;真正在用的是 DM(17 个 · 11-04-01-00 วัตถุดิบคงเหลือ)。
    众数会挑中作废的那组,所以这里只认过了存货科目判据的 fit 名单,不看谁挂得多。
    """
    cfg = config or {}
    chosen = str(cfg.get("stock_acccod") or "").strip()
    if chosen:
        return StockAccGroupChoice(chosen, "", False)
    groups = fit_stock_acc_groups(cfg)
    if len(groups) == 1:
        return StockAccGroupChoice(str(groups[0]["acccod"]).strip(), "", True)
    return StockAccGroupChoice(
        "", REASON_ACC_GROUP_REQUIRED if groups else REASON_ACC_GROUP_MISSING, False
    )


def describe_stock_acc_group(reported: Any, acccod: str) -> Dict[str, str]:
    """按 acccod 从上报候选表反查这一组的存货科目号/名(空 dict = 查不到)。

    载荷里只留了码(ST01 / DM 这类账套内部代号),光看码认不出存货记进了哪个科目 —— 推送日志
    和导出表要给人看的是「11-04-01-00 วัตถุดิบคงเหลือ」。查不到就不编,少显一行也别显错科目。
    """
    code = str(acccod or "").strip()
    if not code or not isinstance(reported, list):
        return {}
    for g in reported:
        if isinstance(g, dict) and str(g.get("acccod") or "").strip() == code:
            return {
                "acccod": code,
                "stock_acc": str(g.get("stock_acc") or "").strip(),
                "stock_acc_name": str(g.get("stock_acc_name") or "").strip(),
            }
    return {"acccod": code}
