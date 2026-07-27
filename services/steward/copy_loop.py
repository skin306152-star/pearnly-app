# -*- coding: utf-8 -*-
"""循环里那些「不能让模型写」的东西:步骤流水的 detail、观测截断、兜底人话。

分工是硬的(设计报告 §2.2):步骤标题(label)归模型 —— 它在想什么;detail 里的数字
全部由这里按工具真实返回值确定性渲染 —— 模型永远不往 detail 里写数。这是「模型可以推理
编表、但数字必须来自工具」的具体落点。

观测截断(§5)不是优化项:提示词是无状态重发的,第 N 步要重付前 N-1 步观测的输入费,
成本随步数二次增长。tax_matrix / period_invoices 这类 20 行结果连续几步下来,最坏一条
消息 ฿2+ 直接顶穿会话闸。完整结果照旧进产物给【人】看,只对模型截断。
"""

from __future__ import annotations

import json
from typing import Optional

from services.steward import copy, store

# 单条观测进提示词的上限(字符)。见设计报告 §5 的成本表:6 步不截断 ฿2.13 → 截断后 ฿1.29。
OBS_MAX_CHARS = 1200
_MAX_ROWS = 5  # 列表型结果只给模型看前几行 + 总数,它要的是「有多少、长什么样」
_MAX_FIELD_CHARS = 200
_MAX_CELL_CHARS = 60

_STEP_ASK = {"zh": "问你一件事", "th": "ขอถามหนึ่งข้อ"}
_STEP_FINAL = {"zh": "整理答复", "th": "เรียบเรียงคำตอบ"}

_STALL = {
    "zh": "这几步没查出结果:{tried}。指定客户和账期,或换个说法。",
    "th": "ขั้นตอนเหล่านี้ไม่ได้ผล: {tried} ระบุลูกค้าและงวด หรือพิมพ์ใหม่",
}
_CAPPED = {
    "zh": "这条问题的额度已用完,先给出目前的结论。再问一次可继续。",
    "th": "คำถามนี้ใช้งบครบแล้ว สรุปเท่าที่ได้ก่อน ถามอีกครั้งเพื่อค้นต่อ",
}
_NO_RESULT = {
    "zh": "这几步都没查到数据。指定客户和账期,或换个说法。",
    "th": "หลายขั้นที่ลองไปไม่พบข้อมูล ระบุลูกค้าและงวด หรือพิมพ์ใหม่",
}
_OPTIONS = {"zh": "候选:{options}", "th": "ตัวเลือก: {options}"}
_TRIED_NONE = {"zh": "几步查询", "th": "หลายขั้นตอน"}
_RESUMED = {"zh": "继续执行。", "th": "ทำต่อ"}


def _t(table: dict, lang: str) -> str:
    return table.get(lang) or table.get(copy.DEFAULT_LANG) or ""


def step_ask(lang: str) -> str:
    return _t(_STEP_ASK, lang)


def step_final(lang: str) -> str:
    return _t(_STEP_FINAL, lang)


def intent_label(tool: str, intent: str, lang: str) -> str:
    """步骤标题:模型给的 intent 优先(会计看得懂「它在想什么」),没给就回落工具名。
    intent 已在 brain_loop 过了出口护栏与长度闸,这里只补空。"""
    return (intent or "").strip() or copy.tool_title(tool, lang)


def question_text(question: str, options: Optional[list], lang: str) -> str:
    """追问那句话 + 候选(发进对话流的那一条)。左窗那一步只落问题本身,候选在那边由
    loop.question.options 画成可点的按钮 —— 同一屏不摆两份候选。"""
    text = (question or "").strip()
    picks = [str(o).strip() for o in (options or []) if str(o or "").strip()]
    if picks:
        text = f"{text}\n{_t(_OPTIONS, lang).format(options=' / '.join(picks))}".strip()
    return text


def stall(tried: list, lang: str) -> str:
    """打转/连续失败的诚实收场:说清试过什么,别静默转到超时(那是四态不诚实)。"""
    names = [t for t in (tried or []) if t]
    return _t(_STALL, lang).format(tried="、".join(names) or _t(_TRIED_NONE, lang))


def capped(lang: str) -> str:
    return _t(_CAPPED, lang)


def resumed(lang: str) -> str:
    """她回答了追问那一下的应承:接着办的是【同一条】任务,不是又开了一条。"""
    return _t(_RESUMED, lang)


def no_result(lang: str) -> str:
    return _t(_NO_RESULT, lang)


def grounded_summary(results: list, lang: str) -> Optional[str]:
    """成文调不起来时的兜底:拿最后一条成功的工具结果,走既有的确定性渲染器 copy.reply。

    为什么必须是 copy.reply 而不是自己拼:同一份数据,兜底句与正常答复必须是同一句话 ——
    两套渲染迟早漂,漂出来的那句就是会计看到的假数。失败观测一律不兜底(零命中 ≠ 查询失败)。
    """
    for tool, data in reversed(results or []):
        try:
            text = copy.reply(tool, data or {}, lang)
        except Exception:  # noqa: BLE001 — 兜底渲染炸了就当没有兜底,不连坐收尾
            continue
        if (text or "").strip():
            return text
    return None


def landed_detail(steps: Optional[list]) -> str:
    """已落库步骤里最后一条跑成了的 detail —— 续跑的兜底成文靠它。

    续跑开局手上没有本进程的结果(观测只从 digest 重建),而 digest 是给模型看的截断版,
    拿它重渲染会把「前 5 行」当成总数说出去。步骤 detail 是上一轮 copy.reply 渲染的原句,
    同一份渲染器、同一句话,不会漂。
    """
    for step in reversed(steps or []):
        if step.get("kind") != "tool" or step.get("state") != store.STEP_DONE:
            continue
        detail = str(step.get("detail") or "").strip()
        if detail:
            return detail
    return ""


def digest(tool: str, ok: bool, error: Optional[str], data: Optional[dict]) -> dict:
    """工具结果 → 喂模型的观测。列表只留前几行 + 总数 + truncated 标记。

    truncated 必须如实标:模型看不出「这是全部还是前 5 行」,不标它就会拿 5 当总数说出去。
    """
    obs = {"tool": tool, "ok": bool(ok)}
    if error:
        obs["error"] = error
    if ok and isinstance(data, dict):
        obs["data"] = _shrink(data)
    return _fit(obs)


def _shrink(data: dict) -> dict:
    out = {}
    for key, value in data.items():
        if isinstance(value, list):
            out[key] = [_shrink_row(r) for r in value[:_MAX_ROWS]]
            out[f"{key}_count"] = len(value)
            if len(value) > _MAX_ROWS:
                out[f"{key}_truncated"] = True
        elif isinstance(value, dict):
            out[key] = _shrink_row(value)
        elif isinstance(value, str):
            out[key] = value[:_MAX_FIELD_CHARS]
        else:
            out[key] = value
    return out


def _shrink_row(row):
    if not isinstance(row, dict):
        return str(row)[:_MAX_CELL_CHARS]
    return {
        str(k): (str(v)[:_MAX_CELL_CHARS] if isinstance(v, (str, dict, list)) else v)
        for k, v in row.items()
    }


def _fit(obs: dict) -> dict:
    """兜底硬闸:整条观测序列化后仍超上限就砍掉 data,只留「跑过、成功了」的事实。
    宁可让模型少看见,也不让一条观测把提示词撑爆(成本上限必须真管用)。"""
    if len(json.dumps(obs, ensure_ascii=False, default=str)) <= OBS_MAX_CHARS:
        return obs
    trimmed = {k: v for k, v in obs.items() if k != "data"}
    trimmed["data_omitted"] = "too_large"
    return trimmed
