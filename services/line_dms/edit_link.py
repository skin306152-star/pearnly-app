# -*- coding: utf-8 -*-
"""订车预览卡「แก้ไข」深链:只解析绑定所属 OA 的 LIFF。

非 legacy OA 未配自己的 LIFF 时返回空字符串,调用方据此省略按钮 —— 绝不回落到别的 OA 的
LIFF(那会把使用者登进错的 OA)。
"""

from __future__ import annotations

import os
from typing import Optional


def url(nonce: str, channel_key: Optional[str] = None) -> str:
    from services.line_dms import binding_guard
    from services.line_platform import channels

    key = channel_key or binding_guard.current_channel()
    liff_id = channels.liff_id(key)
    if liff_id:
        return f"https://liff.line.me/{liff_id}?draft={nonce}"
    if key != channels.DEFAULT_DMS_CHANNEL:
        return ""
    base = (os.getenv("PEARNLY_BASE_URL") or "https://pearnly.com").rstrip("/")
    return f"{base}/liff/dms-booking?draft={nonce}"
