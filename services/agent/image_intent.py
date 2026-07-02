# -*- coding: utf-8 -*-
"""LINE 图片意图分流决策核(LI 设计 §3 · LI-2)—— 纯决策,零副作用。

一张图该进哪个终端(record/push/both/archive_only/nothing/ask/default)由三层定:
① 用户明说的待决意图(pending)→ 确定性映射,不问大脑;
② 没意图 + 单据普通清晰 → default(今天的自动记账路,主流量无感);
③ 没意图 + 歧义(身份证/读不清)→ 问大脑一次;大脑答不上 → fail-safe 回 default。

钱路红线:大脑只许在只读终端里选(archive_only/nothing/record/ask/default),
push 必须来自用户原话(pending 或后续文本工具),大脑硬答 push 一律矫成 ask;
push 闸关时意图里的 push 被剥除并打 dropped_push 标(执行层据此诚实引导)。
本模块不落库不发消息——执行(终端落地/反问发送)在 line_image_ocr 的接线层(LI-2)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

# 大脑可自主选择的终端(全部可逆);push/both 只能由用户明说进来。
_BRAIN_TERMINALS = frozenset({"default", "record", "archive_only", "nothing", "ask"})
_ALL_TERMINALS = _BRAIN_TERMINALS | {"push", "both"}

# 歧义信号:这些单据形态不该静默记成采购账,值得问一次大脑(或反问用户)。
_AMBIGUOUS_KINDS = frozenset({"id_card", "unknown"})


@dataclass
class ImageRoute:
    """分流结果。terminal=default 表示走现状管线(逐字节不变的那条)。"""

    terminal: str
    endpoint_name: Optional[str] = None  # push 指定端点(未指定→执行层用默认端点)
    workspace: Optional[str] = None  # record 指定套账(未指定→绑定店默认)
    question: Optional[str] = None  # ask 时问什么:"goal"(要干嘛)
    say: str = ""  # 大脑给的人话(ask 的问句 / nothing 的摘要回执)
    dropped_push: bool = False  # 意图含 push 但闸关被剥除 → 执行层出诚实引导


def _from_pending(pending: dict, gates: frozenset) -> ImageRoute:
    """用户明说过的意图 → 确定性映射(唯一可信源,不再问大脑)。"""
    goals = set(pending.get("goals") or [])
    if "dms" in goals:
        # DMS 意图在费用 OCR 之前就被 dms 绕过点接管;走到这=闸中途关/接管失败,
        # 按 default 走现状管线(身份证会被 not_invoice 引导),绝不映成 nothing 吞图。
        return ImageRoute("default")
    endpoint = pending.get("push_to") or None
    # 计划步已解析过套账 → 优先用 id(执行层直接覆盖);裸名只在未解析的老意图里出现。
    workspace = pending.get("book_to_id") or pending.get("book_to") or None
    wants_push = "push" in goals and "record" not in goals
    wants_both = "push" in goals and "record" in goals
    if "push" in goals and "push" not in gates:
        # 推送闸关:剥 push 保其余(能力只降不崩),执行层告知"推送暂不可用"并指路。
        goals.discard("push")
        if not goals:
            # "只推不记"降级:留成识别记录(单据不丢,闸开后还能推),而非 nothing(那是"都不要")。
            return ImageRoute("archive_only", dropped_push=True)
        route = _from_pending({**pending, "goals": sorted(goals)}, gates)
        route.dropped_push = True
        return route
    if wants_both:
        return ImageRoute("both", endpoint_name=endpoint, workspace=workspace)
    if wants_push:
        return ImageRoute("push", endpoint_name=endpoint)
    if "record" in goals:
        return ImageRoute("record", workspace=workspace)
    if "archive_only" in goals:
        return ImageRoute("archive_only")
    return ImageRoute("nothing")  # 明说"都不要"(费已按现行口径计,拍板 2026-07-02)


def _is_ambiguous(summary: dict) -> bool:
    kind = str(summary.get("doc_kind") or "invoice")
    return kind in _AMBIGUOUS_KINDS or str(summary.get("confidence") or "") == "low"


def _consult_brain(decide: Callable, summary: dict, lang: str) -> ImageRoute:
    """歧义单据问一次大脑。任何非法/越权输出 → fail-safe default(现状管线本就会
    处理怪图:not_invoice 拦 / 低置信落草稿),绝不因大脑抖动丢用户的图。"""
    try:
        d = decide(summary, lang=lang)
    except Exception:
        return ImageRoute("default")
    if not isinstance(d, dict):
        return ImageRoute("default")
    terminal = str(d.get("terminal") or "")
    say = str(d.get("say") or "").strip()
    if terminal == "ask":
        return ImageRoute("ask", question="goal", say=say)
    if terminal not in _BRAIN_TERMINALS:
        # 大脑越权(push/both/乱答):不可逆动作必须来自用户原话 → 矫成反问。
        return ImageRoute("ask", question="goal", say=say)
    return ImageRoute(terminal, say=say)


def route_image(
    summary: dict,
    *,
    pending: Optional[dict] = None,
    gates: frozenset = frozenset(),
    decide: Optional[Callable] = None,
    lang: str = "th",
) -> ImageRoute:
    """图片 OCR 完成后的终端分流(见模块 docstring 三层)。

    summary 是 OCR 文字摘要(doc_kind/seller/total/confidence)——大脑不二读图片,
    零新增图像模型成本。闸(gates 含 "image")由接线层判定后才会调进来;
    这里再守一道:没闸 → default(双保险,防误接)。
    """
    if "image" not in gates:
        return ImageRoute("default")
    if pending:
        return _from_pending(pending, gates)
    if not _is_ambiguous(summary):
        return ImageRoute("default")  # 主流量:普通清晰票 + 没说话 = 今天的自动记账
    if decide is None:
        return ImageRoute("default")
    return _consult_brain(decide, summary, lang)
