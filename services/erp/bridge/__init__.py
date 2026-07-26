# -*- coding: utf-8 -*-
"""ERP 桥(内网 → 云)公共契约:急停开关、长轮询窗口、异常族。

store / client / routes 三方都要用的东西放这里,避免 store ↔ client 互相 import。
"""

from __future__ import annotations

import os


def bridge_enabled() -> bool:
    """急停开关 · 默认开。设 ERP_BRIDGE_ENABLED=0 → 全部桥端点 404。

    桥在内网重试,端点 404 时它只是空转,不会丢数据 —— 所以这是安全的一键停。
    """
    return (os.environ.get("ERP_BRIDGE_ENABLED") or "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def poll_hold_seconds() -> int:
    """lease 长轮询挂起时长(秒)· 桥从 hello 拿到它,据此设自己的读超时。

    默认 20:生产 Nginx 没设 proxy_read_timeout(= 默认 60s,adr-005 已 SSH 实证),
    20s 留足两倍余量,慢查询把单拍拖长也不会撞成 504。上限 45 同理封死。
    """
    try:
        raw = int(os.environ.get("ERP_BRIDGE_POLL_HOLD_SECONDS") or 20)
    except ValueError:
        raw = 20
    return max(1, min(raw, 45))


class BridgeError(Exception):
    """桥调用失败基类 · code 供上层做机读分支。"""

    code = "bridge.error"

    def __init__(self, message: str = "", code: str = ""):
        super().__init__(message or self.code)
        if code:
            self.code = code
        self.message = message or self.code


class BridgeTimeout(BridgeError):
    """等桥回结果超时(桥离线 / 查询太慢)。"""

    code = "bridge.timeout"


class BridgeUnavailable(BridgeError):
    """该账套当下没有在线的桥能接活。"""

    code = "bridge.unavailable"


class BridgeRejected(BridgeError):
    """请求本身不合法:op/参数不在协议白名单,或 book_id 不在桥上报的清单内。"""

    code = "bridge.rejected"


class BridgeFailed(BridgeError):
    """桥执行了但报错(桥侧的 error.code 原样带上来)。"""

    code = "bridge.failed"
