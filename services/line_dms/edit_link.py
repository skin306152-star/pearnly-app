# -*- coding: utf-8 -*-
"""订车预览卡「แก้ไข」深链:只解析绑定所属 OA 的 LIFF。

解析顺序 = 本 OA 自己的 LIFF env → registry 里显式声明可复用的共享 Provider LIFF;
dms/dms_a/dms_b 同属一个 Provider,所以在没有各自 LIFF 时共用登录 App,但 channel_key
仍随链接下发、绑定查找仍按该 OA 作用域。**只有一个 OA 既没有自己的 LIFF、也没声明共享
Provider LIFF 时才返回空字符串**(调用方据此省略按钮),绝不回落到别的 OA 的链接。
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Optional


def url(nonce: str, channel_key: Optional[str] = None) -> str:
    from services.line_dms import binding_guard
    from services.line_platform import channels

    key = channel_key or binding_guard.current_channel()
    liff_id = channels.liff_id(key)
    if liff_id:
        query = urllib.parse.urlencode({"draft": nonce, "channel": key})
        return f"https://liff.line.me/{liff_id}?{query}"
    if key != channels.DEFAULT_DMS_CHANNEL:
        return ""
    base = (os.getenv("PEARNLY_BASE_URL") or "https://pearnly.com").rstrip("/")
    query = urllib.parse.urlencode({"draft": nonce, "channel": key})
    return f"{base}/liff/dms-booking?{query}"
