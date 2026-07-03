# -*- coding: utf-8 -*-
"""大脑原生 function-calling(P2)——决策输出通道换 provider 原生工具调用。

手写单行 JSON 协议的故障类(泰文长回复截断成坏 JSON / 人话忘包 JSON / 抠括号救援)
全部来自"用文本通道传结构"。原生 FC 由 provider 结构化返回 functionCall 或纯文本,
这类 crash 物理消失。范围只换「决策输出通道」:提示词主体、观测拼接、slots 接地闸、
write_sink、TurnResult 五态全不动。闸 agent_native_fc 默认关;后端未实现(aistudio/
selfhost)返 unsupported → loop 当轮自动回落 JSON 路,行为零损失。

JSON 协议里 defer 是一种 kind;FC 没有 kind 概念 → defer 做成一个声明的工具,
loop._parse_step 把 tool=defer 映射回 defer 裁决(两种模式同一条出路)。
"""

from __future__ import annotations

from functools import lru_cache

DEFER = {
    "name": "defer",
    "description": (
        "Hand this message to the deterministic bookkeeping engine. "
        'reason "record": a NEW expense to record but record_expense is not in your tools. '
        'reason "edit": edits/cancels an already-recorded entry but undo_entry/edit_entry '
        "are not in your tools."
    ),
    "parameters": {
        "type": "object",
        "properties": {"reason": {"type": "string", "enum": ["record", "edit"]}},
        "required": ["reason"],
    },
}

# FC 模式协议尾(顶替 JSON 尾);数字纪律与 JSON 尾同款,由 _SYSTEM 主体承担。
PROTOCOL = (
    "Decide by the rules above, then do exactly ONE of:\n"
    "- call one tool (use defer to hand record/edit intents to the bookkeeping engine "
    "when those tools are not available to you), or\n"
    "- reply to the user directly in plain text, in {lang_name} only. Never write JSON."
)

FORCE_REPLY = "\n\nคุณมีข้อมูลจากเครื่องมือครบแล้ว ต้องตอบผู้ใช้เป็นข้อความธรรมดาเดี๋ยวนี้ ห้ามเรียกเครื่องมืออีก"


def enabled_for(user_id) -> bool:
    """闸 agent_native_fc(默认关·fail-closed)。"""
    from core import feature_flags

    return feature_flags.agent_native_fc_enabled_for(str(user_id) if user_id else None)


def _param_schema(slot) -> dict:
    desc = slot.desc_th or slot.desc_zh
    if slot.kind == "array":
        return {"type": "array", "items": {"type": "string"}, "description": desc}
    return {"type": "string", "description": desc}


@lru_cache(maxsize=8)
def declarations(tools: tuple) -> tuple:
    """可见工具 → 通用声明 dict(JSON-schema 形状·provider 再转各家 SDK 类型)。恒附 defer。
    无参工具不带 parameters(空 OBJECT schema 部分后端拒收)。共享缓存,消费方不许改。"""
    out = []
    for t in tools:
        decl = {"name": t.name, "description": f"{t.title_th} — {t.desc_th}"}
        if t.slots:
            decl["parameters"] = {
                "type": "object",
                "properties": {s.name: _param_schema(s) for s in t.slots},
                "required": [s.name for s in t.slots if s.required],
            }
        out.append(decl)
    out.append(DEFER)
    return tuple(out)
