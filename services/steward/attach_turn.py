# -*- coding: utf-8 -*-
"""传完之后干什么 —— 确定性裁决(万能口 F1 的「不猜」那一层)。

GPT/Claude 传完就自动开干,因为它们的动作免费且只读。这里的动作会按页扣会计的钱、会写进
客户的账套,而且判错方向的票在产品内【无法补救】(只能重传重扣费)。所以照抄的是交互形态,
不是「免费所以随便跑」这个前提。裁决四条,判据全是确定性的,模型一个都碰不到:

  ① 用户把动词说出口了(planner 挑中了工具)→ 派活;
  ② 纯文件零文字,且【确定性认出来 + 只剩一条路 + 不烧模型】→ 直接跑(Detected.auto_runnable);
  ③ 一个工具对上多份料 → 摆按钮让人挑,不替他猜挑哪份;
  ④ 认不出 / 要过模型 → 出回执卡等一次点击。歧义被一次点击解决之后,那一击带着确定性参数
     回来,【不再过 planner】—— 再让模型猜一遍就是把已经解决掉的问题重新引进来。

本模块只出裁决与卡面,不碰任何库表:任务行/授权卡/入队一律回 orchestrator 落,免得两处都能
建任务(状态单一事实源)。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Optional

from services.steward import attach_kinds as ak, copy_file, registry

# 按钮上限:20 份料 × 每份 1-2 条路,全摆出来就是一屏按钮,人反而挑不动。超出的如实说
# 「还有几份没列」,不静默截断。
MAX_ACTION_BUTTONS = 12

ERR_NO_ATTACHMENT = "steward.attachment_missing"


@dataclass(frozen=True)
class Decision:
    """裁决结果:要么派一个工具,要么出一张卡,要么诚实说这轮派不出活。三选一。"""

    tool: Optional[str] = None
    attachment_ids: tuple = ()
    # 执行参数。目前只有 model_ok:「人在卡上点过『会过一次模型』」的凭据,执行侧据此才允许
    # 走模型回退(tools_file.vat_report_check)。派活时点击已经发生,凭据必须随活走。
    args: dict = field(default_factory=dict)
    card: Optional[dict] = None
    error_code: Optional[str] = None
    error_data: dict = field(default_factory=dict)


def view(row: dict) -> dict[str, Any]:
    """附件行 → 裁决用的小视图(识别结果落在 detect 列,不重跑识别)。"""
    detect = row.get("detect") or {}
    return {
        "id": str(row["id"]),
        "name": row.get("original_name") or "",
        "kind": row.get("kind") or ak.UNKNOWN,
        "kind_source": row.get("kind_source") or "",
        "page_count": detect.get("page_count"),
        "needs_model": bool(detect.get("needs_model")),
        "actions": tuple(detect.get("actions") or ()),
    }


def _auto_runnable(item: dict) -> bool:
    """与 attach_kinds.Detected.auto_runnable 同一判据(那边判上传当下,这边判送出当下)。"""
    from services.steward.attachments import SOURCE_RULE

    return (
        item["kind_source"] == SOURCE_RULE and len(item["actions"]) == 1 and not item["needs_model"]
    )


def decide(rows: list[dict], *, tool: Optional[str], confirm_spend: bool, lang: str) -> Decision:
    """本轮该干什么。tool=None 表示会计一个字没打(纯文件手势)。"""
    items = [view(r) for r in rows]
    usable = [i for i in items if i["kind"] != ak.UNSUPPORTED]

    if tool is None:
        if len(usable) == 1 and _auto_runnable(usable[0]):
            return Decision(tool=usable[0]["actions"][0], attachment_ids=(usable[0]["id"],))
        return Decision(card=_receipt_card(items, usable, lang))

    if not usable:
        return Decision(error_code=ERR_NO_ATTACHMENT)
    if len(usable) > 1:
        return Decision(card=_pick_file_card(tool, usable, lang))

    only = usable[0]
    if only["needs_model"] and not confirm_spend:
        return Decision(card=_spend_card(tool, only, lang))
    return Decision(
        tool=tool,
        attachment_ids=(only["id"],),
        args={"model_ok": True} if confirm_spend else {},
    )


# ── 卡面(全部确定性渲染,模型一个字不写)──────────────────


def _receipt_card(items: list[dict], usable: list[dict], lang: str) -> dict[str, Any]:
    """收到料的回执:一张清单表 + 闭集动作按钮(+ 图片料的现有落点深链)。"""
    actions, dropped = _buttons(usable, lang)
    counts = Counter(i["kind"] for i in items)
    artifacts: list[dict] = [copy_file.files_table(_file_rows(items, lang), lang)]
    if actions:
        artifacts.append(copy_file.actions_block(actions, lang))
    if any(i["kind"] == ak.INVOICE for i in items):
        artifacts.append(copy_file.intake_link(lang))
    reply = copy_file.receipt_reply(counts, lang, has_actions=bool(actions))
    if dropped:
        reply = f"{reply}{copy_file.receipt_more(dropped, lang)}"
    return {"title": copy_file.receipt_title(lang), "reply": reply, "artifacts": artifacts}


def _pick_file_card(tool: str, usable: list[dict], lang: str) -> dict[str, Any]:
    """一个工具对上多份料:摆按钮让人挑。挑错文件是无痕的错,所以这一步绝不自动。"""
    actions = [_button(tool, i, lang, with_name=True) for i in usable[:MAX_ACTION_BUTTONS]]
    dropped = max(0, len(usable) - MAX_ACTION_BUTTONS)
    reply = copy_file.pick_file_reply(tool, len(usable), lang)
    if dropped:
        reply = f"{reply}{copy_file.receipt_more(dropped, lang)}"
    return {
        "title": copy_file.action_label(tool, lang),
        "reply": reply,
        "artifacts": [
            copy_file.files_table(_file_rows(usable, lang), lang),
            copy_file.actions_block(actions, lang),
        ],
    }


def _spend_card(tool: str, item: dict, lang: str) -> dict[str, Any]:
    """要过模型才读得出的料:先说清楚再动手。点了按钮 = 同意这一次调用。"""
    action = _button(tool, item, lang, confirm_spend=True)
    action["label"] = copy_file.spend_confirm_label(lang)
    return {
        "title": copy_file.action_label(tool, lang),
        "reply": copy_file.spend_confirm_reply(item["name"], lang),
        "artifacts": [copy_file.actions_block([action], lang)],
    }


def _buttons(usable: list[dict], lang: str) -> tuple[list[dict], int]:
    """逐 (工具, 文件) 一个按钮。同一个工具只对上一份料时不带文件名(标签更短更好点)。"""
    per_tool = Counter(t for i in usable for t in i["actions"])
    pairs = [(t, i) for i in usable for t in i["actions"]]
    kept = pairs[:MAX_ACTION_BUTTONS]
    return (
        [_button(t, i, lang, with_name=per_tool[t] > 1) for t, i in kept],
        len(pairs) - len(kept),
    )


def _button(
    tool: str, item: dict, lang: str, *, with_name: bool = False, confirm_spend: bool = False
) -> dict[str, Any]:
    return {
        "tool": tool,
        "label": copy_file.action_label(tool, lang, filename=item["name"] if with_name else ""),
        "attachment_ids": [item["id"]],
        "confirm_spend": bool(confirm_spend or item["needs_model"]),
        # F1 这两个工具都不动会计的钱包(fileconv / vat_report_parser 全程没有 charge_ocr)。
        # model_call 才是这里真正要说的话:会不会为这份料调一次模型。
        "cost": {
            "wallet_charge": False,
            "model_call": bool(item["needs_model"]),
            "page_count": item["page_count"],
        },
    }


def _file_rows(items: list[dict], lang: str) -> list[dict[str, Any]]:
    return [
        {
            "name": i["name"],
            "kind": copy_file.kind_label(i["kind"], lang),
            "pages": i["page_count"],
            "note": copy_file.note_needs_model(lang) if i["needs_model"] else "",
        }
        for i in items
    ]


def is_attachment_tool(tool: Optional[str]) -> bool:
    return (tool or "") in registry.ATTACHMENT_TOOLS
