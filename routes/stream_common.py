# -*- coding: utf-8 -*-
"""流式响应公共件(SSE 帧 + NDJSON 行 + 反代直通头)。

steward_stream_routes(SSE 推任务投影变化)与 workspace_purge_routes(NDJSON 推清除
进度)各管一条常驻流,帧格式不同,但收尾三件事一样:关反代缓冲、禁中间层缓存、
逐帧独立编码成字节即时 yield。此前两处各写一份,抽这里一次写对,两条路由各自
import,不留各抄一份的漂移面。
"""

from __future__ import annotations

import json
from typing import Any

# nginx 反代默认攒缓冲,流式响应会被整段扣到连接关闭才吐 —— 必须关;
# no-store 防中间层/浏览器把这条只读一次的流当普通响应缓存。
NO_BUFFER_HEADERS = {
    "Cache-Control": "no-store",
    "X-Accel-Buffering": "no",
}


def sse_frame(event: str, payload: dict) -> str:
    """SSE 一帧:event 行 + data 行(JSON)+ 空行收尾。"""
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"


def ndjson_line(payload: dict[str, Any]) -> bytes:
    """NDJSON 一行:一个 JSON 对象 + 换行,编码成字节直接 yield。"""
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode()
