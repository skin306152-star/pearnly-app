# -*- coding: utf-8 -*-
"""置信闸门 + 入队(Express adapter 的"推送"动作 = 写待领取队列,不跑服务器 Playwright)。

push_to_endpoint 命中 adapter=='express' → 调 enqueue_express。它不自己写 erp_push_logs:
返回一个标准 push 结果 dict,由现有调用方(手动 /api/erp/push、自动 _auto_push_history)
照常落库一行。借由 classify_push_status 的 express 哨兵,这一行落成:
  · pending(高置信 + 映射成功)→ 进队列等本地 Agent lease(error_msg=EXPRESS_QUEUED 哨兵)
  · manual (低置信 / 映射判脏 / 账套白名单拒)→ 留人工(error_msg=EXPRESS_MANUAL:<reason>)

闸链(账套/方向/映射/科目白名单/置信)抽在 preflight.preflight_express(纯读 · 单一真相源);
enqueue 只把体检结果翻成推送结果 dict + 把逐项体检写进 response_body(喂异常页红绿灯清单)。
特性开关 off → 直接短路(failed · 不入队)。
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from services.erp.express_push.preflight import preflight_express

# error_msg 哨兵 · 让现有 classify_push_status 把这一行落成 pending / manual(单一状态源 · 铁律 #12)。
QUEUED_SENTINEL = "EXPRESS_QUEUED"
MANUAL_PREFIX = "EXPRESS_MANUAL"


def _result(
    *,
    success: bool,
    error_msg: Optional[str],
    request_body: Optional[Dict[str, Any]],
    response_body: Optional[str],
    http_status: int,
    t0: float,
) -> Dict[str, Any]:
    return {
        "success": success,
        "http_status": http_status,
        "response_body": response_body,
        "error_msg": error_msg,
        "elapsed_ms": int((time.time() - t0) * 1000),
        "request_body": request_body,
        "adapter": "express",
    }


def _manual(
    reason: str,
    request_body: Dict[str, Any],
    t0: float,
    checks: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"queued": False, "manual_reason": reason}
    if checks is not None:
        body["preflight"] = checks
    return _result(
        success=False,
        error_msg=f"{MANUAL_PREFIX}: {reason}",
        request_body=request_body,
        response_body=json.dumps(body, ensure_ascii=False),
        http_status=0,
        t0=t0,
    )


def enqueue_express(endpoint: Dict[str, Any], history: Dict[str, Any]) -> Dict[str, Any]:
    """对一条 history 跑前置体检 + 映射 → 返回标准 push 结果(pending / manual / 短路)。"""
    t0 = time.time()
    pf = preflight_express(endpoint, history)

    if pf.disabled:
        return _result(
            success=False,
            error_msg="ERR_EXPRESS_DISABLED",
            request_body={"adapter": "express"},
            response_body=None,
            http_status=0,
            t0=t0,
        )

    checks = pf.checks_json()
    if pf.blocked:
        return _manual(pf.reason, pf.request_body, t0, checks=checks)

    # 高置信 + 映射成功 → 入队(pending)等本地 Agent。
    payload = pf.payload
    return _result(
        success=False,
        error_msg=QUEUED_SENTINEL,
        request_body=payload,
        response_body=json.dumps(
            {
                "queued": True,
                "doctype": payload.get("doctype"),
                "account_set": payload.get("account_set"),
                "total_amount": payload.get("total_amount"),
                # 推送日志可见性:这张票记到哪几个科目。account_source 是粗略近似(有品类≈走规则
                # 映射·否则账套默认)· 非 mapper 真实解析路径(精确来源待 v2 schema 列)。
                "accounts": [
                    {"acc": ln.get("acc"), "side": ln.get("side"), "desc": ln.get("desc")}
                    for ln in (payload.get("lines") or [])
                ],
                "account_source": "category_map" if pf.category else "config_default",
                "preflight": checks,
            },
            ensure_ascii=False,
        ),
        http_status=202,
        t0=t0,
    )
