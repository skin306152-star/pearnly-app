# -*- coding: utf-8 -*-
"""Express 自动推送(本地 Agent 出站拉取 · 复用现有 ERP 推送骨架)。

Express 是本地 FoxPro/DBF 桌面程序(无 API · 数据在客户内网),云端够不着。
所以 Express 不另起炉灶:它在现有骨架上是一个 `adapter='express'` 的连接,其"推送"
动作 = 把记账载荷写进待领取队列(`erp_push_logs` status='pending'),由客户本地
Agent 出站拉取(lease)、录入 Express、回报(ack)。

净增三件(其余全复用 erp_endpoints / erp_push_logs / 映射 / kms / 前端 Tab):
  · mapper      扁平化 history → Express 复式分录载荷(确定性纯函数 · 不调 LLM)
  · enqueue     置信闸门 → pending(入队)/ manual(留人工)· 不跑服务器 Playwright
  · agent_store Agent 出站拉取的 DAL(token 校验 / heartbeat / lease / ack)

特性开关 ERP_PUSH_ENABLED(默认 off);账套白名单 = 逐端点匹配建连接时配置的 account_set。
"""

import os
from typing import Any, Dict, Optional


def express_push_enabled() -> bool:
    """特性开关 · 默认 off。off 时 express 推送分支与 Agent 路由全短路,对现有零影响。"""
    return (os.environ.get("ERP_PUSH_ENABLED") or "").strip().lower() in ("1", "true", "yes", "on")


def account_set_allowed(account_set: str, endpoint: Dict[str, Any]) -> bool:
    """账套白名单(逐端点)· 只放行 == 本端点配置(建连接时客户选定)的 account_set。

    `endpoint.config.account_set` 即该连接被授权写入的唯一账套 —— 跨账套写入是账务事故,
    故只认配置那一个。不等 / 任一缺失 → 拒(fail-safe)。
    """
    s = (account_set or "").strip()
    if not s:
        return False
    configured = str(((endpoint or {}).get("config") or {}).get("account_set") or "").strip()
    return bool(configured) and s == configured


def stock_lane_enabled(config: Dict[str, Any]) -> bool:
    """V2-b 库存路(STKTYP=0 主档 + 扣库存 + COGS)是否对本端点开启。

    恒 False:库存路未施工(doc31 §3.6「本期不做,仅留接口位」),故画像判 perpetual 的客户
    一律走 escalate 交会计,绝不静默按周期制落。V2-b 落地后改成读端点闸,别提前放这个口。
    """
    return False


def chart_codes(config: Dict[str, Any]) -> Optional[set]:
    """账套上报的可记账科目码集合(写前白名单数据源)。

    未上报(旧 Agent / 心跳还没带科目表)→ None:跳过校验,不阻塞;有上报才钉。
    入队闸(enqueue)与待补科目卡重推(erp_express_account_routes)共用一份口径。
    """
    reported = (config or {}).get("reported_accounts")
    if not isinstance(reported, list) or not reported:
        return None
    codes = {str((a or {}).get("code") or "").strip() for a in reported}
    codes.discard("")
    return codes or None
