# -*- coding: utf-8 -*-
"""DMS LINE 对话流(flow / booking_flow / booking_qa)共享的后台调度 + LINE 出口工具。

各对话流的 _spawn/_reply/_push 逐字节相同(全走 dms channel)→ 收敛到此,后台任务
日志 tag 参数化(各文件传自己的标识)。纯文本走 _reply/_push,结构化消息(quickReply /
Flex)一律走 _send —— 它按有没有 reply_token 自己分流,调用方不再各写一份 push_messages。
纯工具:无会话态、无业务分支。
"""

from __future__ import annotations

import asyncio
import logging

from services.line_platform import client as line_client
from services.line_dms.binding_guard import current_channel, require_current

logger = logging.getLogger(__name__)

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
    require_current()
    if reply_token:
        line_client.reply_text(reply_token, text, channel=current_channel())


def _push(line_user_id: str, text: str, channel: str = "") -> None:
    """Push through the recipient's own OA when given, else the binding in scope."""
    require_current()
    line_client.push_text(line_user_id, text, channel=channel or current_channel())


def _send(line_user_id: str, msg, reply_token: str = "", channel: str = "") -> bool:
    """结构化消息出口(quickReply / Flex 必须走 reply_messages|push_messages)。

    有 reply_token 就 reply,没有就 push —— 逐问既可能应答 postback,也可能由后台任务发起。
    """
    require_current()
    if msg is None:
        return False
    channel = channel or current_channel()
    if reply_token:
        return line_client.reply_messages(reply_token, [msg], channel=channel)
    return line_client.push_messages(line_user_id, [msg], channel=channel)


def start_loading(line_user_id: str) -> None:
    """当前 OA 的「正在输入」动画(阻塞 HTTP,调用方仍须 _thr 离开事件循环)。"""
    line_client.start_loading(line_user_id, 30, channel=current_channel())


def download_content(message_id: str):
    """下载消息内容(图片/附件)用的当前 OA token。"""
    return line_client.download_message_content(message_id, channel=current_channel())
