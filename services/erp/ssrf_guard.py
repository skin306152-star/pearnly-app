# -*- coding: utf-8 -*-
"""SSRF 防护:校验用户可控的出站 URL 只指向公网,挡私网/loopback/link-local/元数据。

安全评估 2026-07-07:ERP endpoint 的 system_url 用户可控,服务端 test-connection / push 会去连,
攻击者可借此探内网 / 云元数据(盲 SSRF)。在输入边界(测连接 / 存端点)拦截,不动生产推送连接代码。
DNS 解析后逐个校验解析到的 IP;解析失败放行(实际连接自会失败,不误伤 DNS 抖动)。
已知残留:DNS rebinding(解析时公网、连接时内网)本层不覆盖。
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

# 云厂商元数据主机名:即便解析成公网记录也硬挡
_METADATA_HOSTS = {"169.254.169.254", "metadata.google.internal", "metadata"}


def assert_public_url(url: str) -> None:
    """url 指向非公网(私网/loopback/link-local/保留/元数据)时抛 ValueError;公网则放行。"""
    parsed = urlparse(url if "://" in url else "http://" + url)
    host = (parsed.hostname or "").strip()
    if not host:
        raise ValueError("empty host")
    if host.lower() in _METADATA_HOSTS:
        raise ValueError("metadata endpoint blocked")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return  # 解析不了 · 放行(实际连接自会失败)
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValueError(f"non-public address blocked: {ip}")


async def assert_public_config_url(cfg: dict) -> None:
    """从 endpoint config 取 system_url,非空则校验只指公网。

    异步入口 · 供 async 路由复用:getaddrinfo 阻塞 → to_thread 离事件循环(铁律#10)。
    非公网抛 ValueError,交由调用方翻成 HTTPException。
    """
    url = str((cfg or {}).get("system_url") or "").strip()
    if url:
        await asyncio.to_thread(assert_public_url, url)
