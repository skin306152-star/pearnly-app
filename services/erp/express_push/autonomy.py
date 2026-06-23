# -*- coding: utf-8 -*-
"""Express 自治级别(per 连接 · 出厂默认 standard)。

三档(Owner 2026-06-23 拍板):
  · manual   全人工:【自动推送】路径上,高置信本会自动入队的票 → 降级转人工复核
             (autonomy_hold)。手动推送(用户在界面点"推送")不经本函数,照走不拦。
  · standard 标准(默认):高置信自动入队、低置信转人工 —— 即现有行为,不改。
  · auto     全托管:队列决策今同 standard;其"替用户自动建档不询问"的差异在 provisioning
             阶段(S3)体现,不在本函数放宽金额/数据闸(铁律:钱低置信永不自动入账)。

只作用在自动推送编排(auto_push.py)拿到 express 推送结果之后;手动推送走
erp_push_log_routes(trigger='manual')自带落库,不经此处。
"""

from __future__ import annotations

import json
from typing import Any, Dict

from services.erp.express_push.enqueue import MANUAL_PREFIX, QUEUED_SENTINEL

_LEVELS = ("manual", "standard", "auto")
AUTONOMY_HOLD = "autonomy_hold"


def autonomy_level(config: Dict[str, Any]) -> str:
    """读连接自治级别 · 缺失/非法 → standard(出厂默认)。"""
    v = str(((config or {}).get("autonomy") or "")).strip().lower()
    return v if v in _LEVELS else "standard"


def apply_autonomy_auto(result: Dict[str, Any], endpoint: Dict[str, Any]) -> Dict[str, Any]:
    """自动推送路径后处理:按连接自治级别决定是否把"本会自动入队"降级为人工复核。

    只动 express 且本会入队(EXPRESS_QUEUED)的结果;非 express / 已经是人工 / 短路失败
    一律原样返回。manual 档 → 降级 autonomy_hold(payload 留存,供用户手动推送复用)。
    """
    if (endpoint or {}).get("adapter") != "express":
        return result
    if (result or {}).get("error_msg") != QUEUED_SENTINEL:
        return result
    if autonomy_level((endpoint or {}).get("config")) != "manual":
        return result

    body: Dict[str, Any] = {"queued": False, "manual_reason": AUTONOMY_HOLD}
    # 保留体检结果(异常页可显示"其实全绿,只是你设了全人工")。
    try:
        prev = json.loads(result.get("response_body") or "{}")
        if isinstance(prev.get("preflight"), list):
            body["preflight"] = prev["preflight"]
    except (ValueError, TypeError):
        pass

    out = dict(result)
    out["success"] = False
    out["error_msg"] = f"{MANUAL_PREFIX}: {AUTONOMY_HOLD}"
    out["response_body"] = json.dumps(body, ensure_ascii=False)
    out["http_status"] = 0
    return out
