# -*- coding: utf-8 -*-
"""Agent 数据契约(M1-SOCKET-DESIGN §2)。

插座各层只认这些类型,换大脑/换行业都不动。所有用户可见文本不在这里产出,由 copy_map 渲染。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

Bucket = Literal["A", "B", "C", "D"]
# 参数允许的接地来源。model_freeform 仅限纯文本检索类(如 keyword);其余编造一律拦下。
SlotSource = Literal["user_text", "anchor", "endpoint_config", "prior_result", "model_freeform"]


@dataclass(frozen=True)
class SlotSpec:
    name: str
    required: bool
    source: SlotSource
    desc_th: str  # 给大脑看的泰文说明(进提示词)
    desc_zh: str  # 团队看的中文说明
    kind: str = "string"  # 参数形状(string|array)——原生 function-calling 的 schema 用


@dataclass(frozen=True)
class ToolSpec:
    name: str  # 大脑选它用,如 "list_history"
    bucket: Bucket
    title_th: str  # 给大脑/用户看的人话标题
    desc_th: str  # 这个工具干嘛(泰文,进提示词)
    slots: tuple[SlotSpec, ...]
    handler: str  # AgentToolset 上的方法名,如 "list_ocr_history"
    confirm: bool  # True=执行前先复述+确认(不可逆动作如推 ERP);记账=False 高置信直录
    writes: bool = False  # True=写工具(经 write_sink 落确定性执行·大脑无直接写库的手)
    gate: Optional[str] = None  # 子闸名(write/m3/push)· None=恒可见;加新闸=加一个值,不加参数


@dataclass
class AgentAction:
    kind: Literal["tool", "ask", "out_of_scope", "chat"]
    tool: Optional[str] = None
    args: dict[str, Any] = field(default_factory=dict)
    ask_field: Optional[str] = None  # kind=ask 时缺哪个 slot
    message: str = ""  # ask/out_of_scope/chat 时大脑的话(仅作信号,真文案走 copy_map)


@dataclass
class SlotCheck:
    ok: bool
    grounded: dict[str, Any] = field(default_factory=dict)  # 通过接地的可信值
    missing: list[str] = field(default_factory=list)  # 必填但没接地 → 反问
    rejected: dict[str, str] = field(default_factory=dict)  # 被判编造 {slot: 原因}


@dataclass
class ToolResult:
    ok: bool
    # 恒为 dict(契约):list 类结果由 handler 包成 {"items":[...]} → observe/write_sink/fallbacks
    # 一律按 dict 消费,不再逐处 isinstance(历史雷:通知 count 恒 0 = list 被强转空 dict)。
    data: Any = None
    error_code: Optional[str] = None  # 机器码,翻人话由 copy_map(WP3)
    receipt: str = ""  # 给用户的人话回执


@dataclass
class AgentContext:
    """工具以此身份执行 —— 复用现成 RLS/计费/权限,绝不 bypass。

    line_user_id / anchors / endpoint_config / prior_results 供 slots 接地与多轮记忆,
    M1 的 A 档工具只用到 user/tenant_id/workspace_client_id,其余字段由后续里程碑接线。
    """

    user: dict  # get_current_user_from_request 产物(含 id/tenant_id/role)
    tenant_id: Optional[str] = None
    workspace_client_id: Optional[Any] = None
    line_user_id: Optional[str] = None
    quoted_message_id: Optional[str] = None  # 用户长按引用的消息 id(撤销/改错锚定目标)
    user_text: str = ""  # 本轮用户原文(写工具建草稿做金额接地用·loop 每轮注入)
    anchors: dict[str, Any] = field(default_factory=dict)
    anchors_enabled: bool = False  # 锚点闸(agent_anchor_memory)开才采集/消费,关=逐字节现状
    endpoint_config: dict[str, Any] = field(default_factory=dict)
    prior_results: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""  # 本轮追踪号(loop 生成)——串起同轮多次网关调用 + 审计行
    tool_trace: list = field(default_factory=list)  # 本轮工具轨迹 [{tool,ok,error}](审计留痕)
    degraded: str = (
        ""  # 本轮降级标记(loop 标·turn_log 落库):grounded_fb/card_text_fb/card_text_dropped/card_fail
    )
    progress: Any = None  # 慢轮中间反馈回调(bridge 装配·loop 经 fallbacks.progress_ping 一次性调)
