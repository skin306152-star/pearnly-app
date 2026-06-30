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


@dataclass(frozen=True)
class ToolSpec:
    name: str  # 大脑选它用,如 "list_history"
    bucket: Bucket
    title_th: str  # 给大脑/用户看的人话标题
    desc_th: str  # 这个工具干嘛(泰文,进提示词)
    slots: tuple[SlotSpec, ...]
    handler: str  # AgentToolset 上的方法名,如 "list_ocr_history"
    confirm: bool  # B 档=True,执行前必复述确认


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
    lang: str = "th"  # 本轮用户语言(渲染在表现层用 · agent 核心保持文案无关)
    anchors: dict[str, Any] = field(default_factory=dict)
    endpoint_config: dict[str, Any] = field(default_factory=dict)
    prior_results: dict[str, Any] = field(default_factory=dict)
