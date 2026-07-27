# -*- coding: utf-8 -*-
"""循环的接地语料:把「已跑出来的观测 + 她后来打的字」摊平成接地闸看得见的文本。

为什么非得有这一层:services/agent/slots.py 的接地闸只认「用户原话 + 建任务那一刻的历史」
(slots._texts),而 registry 里 client_name / keyword 一律 source="user_text"。于是

  ① 第 2 步想用第 1 步查出来的客户名 —— 值不在用户原话里,判 not_in_user_text → 必填槽
     missing → 那一步一次都跑不了(「串两步」这条头号能力实际不成立);
  ② 她回答追问给的名字 —— 答案进的是 payload.loop.answers,既不在 text 里也不在冻结的
     history 里,答完照样接不了地(「问也是选择题 + 下一条消息接回同一条任务」走不通)。

放宽的边界严格照 slots.py 顶注列的合法出处【用户原话 / 锚点 / 端点配置 / 上一步结果 /
纯文本检索】—— 这里补的正是「上一步结果」和「她本人后来打的字」,不是给模型开后门:
语料只取本任务真跑成功过的工具返回值(digest.data)与她自己的答案,别的一律不进。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

# 摊平后的条数上限。观测本身已被 copy_loop.digest 截断过,这里只防病态嵌套把接地语料撑爆
# —— 接地是逐值子串比对,语料越长越慢,而多出来的那些值没有一个是会计问得出来的。
_MAX_TEXTS = 400
_MAX_DEPTH = 6


def history_rows(loop: Optional[dict]) -> list[dict]:
    """接地语料 → orchestrator._ground 认的历史行形状({"text": ...})。"""
    return [{"text": t} for t in texts(loop)]


def texts(loop: Optional[dict]) -> list[str]:
    """本任务已经【真跑出来】的值,加上她回答追问时打的字。"""
    out: list[str] = []
    for step in (loop or {}).get("steps") or []:
        digest = step.get("digest")
        if isinstance(digest, dict):
            # 只走 data:tool/ok/error 是执行元信息,不是工具查出来的事实,让它们进语料
            # 等于让模型拿工具名当客户名接地。
            _walk(digest.get("data"), out)
    for answer in (loop or {}).get("answers") or []:
        value = str(answer.get("answer") or "").strip()
        if value:
            out.append(value)
    return out[:_MAX_TEXTS]


def _walk(node, out: list, depth: int = 0) -> None:
    """递归摊平成标量文本。dict 的键跳过:键是字段名,不是查出来的值。"""
    if len(out) >= _MAX_TEXTS or depth > _MAX_DEPTH:
        return
    if isinstance(node, dict):
        for value in node.values():
            _walk(value, out, depth + 1)
        return
    if isinstance(node, (list, tuple)):
        for value in node:
            _walk(value, out, depth + 1)
        return
    if node is None or isinstance(node, bool):
        return  # True/False 摊成 "true" 会让模型把布尔当值接地
    if isinstance(node, (str, int, float, Decimal)):
        text = str(node).strip()
        if text:
            out.append(text)
