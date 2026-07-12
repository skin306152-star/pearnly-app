# -*- coding: utf-8 -*-
"""工资进料 → 点亮 pnd1 月度义务(照 D1-2 wht_signals 范式 · 方案 §6)。

工资工具卡校验通过后调本入口:以真信号 employees_paid=True 走 obligation_engine 重物化,
pnd1 落 client_period_obligations、C4 矩阵亮灯。诚实边界(方案 §6.4):只有「本期真有工资
进料且校验通过」才置 employees_paid=True(调用方保证);仅上传未过校验不点亮(宁缺勿滥)。

SSO 社保义务同 has_employees 触发,会一并被点亮 —— 这是义务清单的诚实提醒,不代表我们做
社保申报(方案 §8 不做清单)。work_order_id=None:工具卡无工单,schema ON DELETE SET NULL
本就 Optional,传 None 即可(方案 §5.3)。
"""

from __future__ import annotations

from services.workorder import obligation_engine
from services.workspace import tax_profile_store


def light_pnd1_obligation(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> bool:
    """校验通过的工资进料 → 重物化客户当期义务(pnd1 data_triggered / 画像 no 则 conflict)。

    period 为佛历「YYYY-MM」。跨租户/不存在的客户返 False 不点亮。义务清单是供料层,
    rematerialize_for_profile 已吞异常返 False —— 调用方按返回值决定是否提示,不需自己包 try。
    """
    profile = tax_profile_store.get_profile(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    if profile is None:
        return False
    return obligation_engine.rematerialize_for_profile(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        profile=profile,
        work_order_id=None,
        data_signals={"employees_paid": True, "has_any_material": True},
    )
