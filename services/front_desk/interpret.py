# -*- coding: utf-8 -*-
"""大脑解析(FD-0a 桩位)· utterance + 盘点摘要 → 意图/客户/期间建议。

FD-0a 只接**桩**:恒返 degraded,不调网关、不写任何业务表。真实装(taxops.intent 车道 +
JSON schema 闭集约束 + 引用校验 + 15s 降级)在 FD-0b,替换本函数产出即可,路由与前端契约不变。

降级契约(fail-closed · §3.3):degraded=True → 前端出降级卡「AI 暂不可用,可用手动开单继续」。
大脑任何故障都不得阻塞手动开单——那是另一条端点,零共享故障面。桩位天然满足此契约。
"""

from __future__ import annotations

from typing import Optional

# FD-0b 接大脑后此原因消失(换成真实 intent/degraded 判据)。前端据 reason 区分「桩未接」
# 与真降级(超时/异常)——都出降级卡,不同 reason 便于观测。
DEGRADED_STUB = "brain_not_wired"


def interpret(
    utterance: str,
    *,
    inventory_summary: Optional[dict] = None,
    tenant_id: Optional[str] = None,
    contract_id: Optional[str] = None,
) -> dict:
    """桩:恒返降级建议(intent/client/period 全空)。FD-0b 实装后返回闭集意图 + 客户建议。

    返回形状与 FD-0b 实装对齐(前端/路由不必改):
      {degraded, intent, client_suggestion, period, reason}
    """
    return {
        "degraded": True,
        "intent": None,
        "client_suggestion": None,
        "period": None,
        "reason": DEGRADED_STUB,
    }
