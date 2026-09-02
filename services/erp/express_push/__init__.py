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

import ntpath
import os
from typing import Any, Dict, Optional


def express_push_enabled() -> bool:
    """特性开关 · 默认 off。off 时 express 推送分支与 Agent 路由全短路,对现有零影响。"""
    return (os.environ.get("ERP_PUSH_ENABLED") or "").strip().lower() in ("1", "true", "yes", "on")


def _path(value: object) -> str:
    raw = str(value or "").strip().replace("/", "\\").rstrip("\\")
    return ntpath.normcase(ntpath.normpath(raw)) if raw else ""


def authorized_account_sets(endpoint: Dict[str, Any]) -> list[str]:
    """Return the endpoint default plus writable account sets reported by its agent."""
    config = (endpoint or {}).get("config") or {}
    allowed = {_path(config.get("account_set") or config.get("account_dir"))}
    reported = config.get("reported_account_sets")
    for row in reported if isinstance(reported, list) else []:
        if not isinstance(row, dict) or row.get("writable") is not True:
            continue
        allowed.add(_path(row.get("path")))
    allowed.discard("")
    return sorted(allowed)


def account_set_allowed(
    account_set: str, endpoint: Dict[str, Any], account_root: object = None
) -> bool:
    """Allow only a writable account path reported by this exact Express connection."""
    selected = _path(account_set)
    if not selected or selected not in authorized_account_sets(endpoint):
        return False
    config = (endpoint or {}).get("config") or {}
    default = _path(config.get("account_set") or config.get("account_dir"))
    if selected == default:
        return True
    requested_root = _path(account_root)
    for row in config.get("reported_account_sets") or []:
        if not isinstance(row, dict) or row.get("writable") is not True:
            continue
        if _path(row.get("path")) != selected:
            continue
        reported_root = _path(row.get("root")) or _path(ntpath.dirname(str(row.get("path") or "")))
        return bool(requested_root and requested_root == reported_root)
    return False


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
