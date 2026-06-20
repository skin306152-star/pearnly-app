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

特性开关 ERP_PUSH_ENABLED(默认 off);账套白名单本期只允许 DATAT。
"""

import os

ALLOWED_ACCOUNT_SETS = ("DATAT",)


def express_push_enabled() -> bool:
    """特性开关 · 默认 off。off 时 express 推送分支与 Agent 路由全短路,对现有零影响。"""
    return (os.environ.get("ERP_PUSH_ENABLED") or "").strip().lower() in ("1", "true", "yes", "on")


def account_set_allowed(account_set: str) -> bool:
    """账套白名单(代码级)· 本期只允许 DATAT;真账套/空模板一律拒写。"""
    return (account_set or "").strip() in ALLOWED_ACCOUNT_SETS
