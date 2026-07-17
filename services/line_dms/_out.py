# -*- coding: utf-8 -*-
"""DMS LINE 对话流(flow / booking_flow)共享的后台调度 + LINE 出口工具。

两个对话流文件的 _spawn/_reply/_push 逐字节相同(全走 dms channel)→ 收敛到此,
后台任务日志 tag 参数化(各文件传自己的标识)。纯工具:无会话态、无业务分支。
"""

from __future__ import annotations

import asyncio
import logging

from services.line_binding import line_client

logger = logging.getLogger(__name__)

_CHANNEL = "dms"
_thr = asyncio.to_thread


def make_spawn(tag: str):
    """造一个把重活挂到事件循环后台跑的 _spawn(不阻塞 webhook 200 响应)。异常吞掉只记日志。"""

    def _spawn(coro) -> None:
        async def _guard():
            try:
                await coro
            except Exception:
                logger.exception("[%s] background task failed", tag)

        try:
            asyncio.get_running_loop().create_task(_guard())
        except RuntimeError:
            logger.warning("[%s] no running loop; drop background task", tag)

    return _spawn


def _reply(reply_token: str, text: str) -> None:
    if reply_token:
        line_client.reply_text(reply_token, text, channel=_CHANNEL)


def _push(line_user_id: str, text: str) -> None:
    line_client.push_text(line_user_id, text, channel=_CHANNEL)
