# -*- coding: utf-8 -*-
"""引擎替人做过的改动 —— 读侧投影(SA-1)。

管线有几处会在无人确认的情况下改写料件归类或钱数:续页改判把已排除的件拉回银行流水堆
(statement_regroup)、余额链按前后余额反推改写行金额与借贷方向(bank_stmt_balance)。这些
动作此前只落事件流,order_detail 与交付包都不呈现——会计看到的是改后的结果,看不到"改过"
这件事本身,连事后追责都没有入口。

本模块只回放、只聚合,不改任何判断逻辑,不碰 store/DB。这些改动该不该拦是另一回事:
看不见的东西没法判断该不该拦,所以先让它们可见。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from services.workorder.steps import reconcile_bank

EVT_REGROUPED = "item_regrouped"

# 每件银行流水最多列几行样本。760 行的单子全列等于没列,超限留 truncated 标供前端提示。
_MAX_SAMPLES = 5


def projection(events: list[dict], items: list[dict]) -> list[dict]:
    """order_detail.machine_actions 读侧投影(改判 + 银行行自动纠正)。

    不跟随 bank_recon 那套"只在 reconcile 步回放"的懒加载:签批前(review 态)恰恰是最该
    看到机器改过什么的时刻,那时懒加载已经不算了。事件本就在内存,多扫一遍是 O(n)。"""
    return regroup_actions(events, items) + bank_row_corrections(events)


def regroup_actions(events: list[dict], items: list[dict]) -> list[dict]:
    """料件被引擎改判的痕迹(statement_regroup 落的 item_regrouped)。

    改判会清空 flag_reason 并把件置 ok,之后它既不在 flagged 也不在 excluded——不投影就等于
    从所有清单里凭空消失。"""
    names = {it["id"]: _name_of(it) for it in items}
    out = []
    for e in events:
        if e["event_type"] != EVT_REGROUPED:
            continue
        payload = e.get("payload") or {}
        item_id = payload.get("item_id")
        if not item_id:
            continue
        out.append(
            {
                "type": EVT_REGROUPED,
                "item_id": item_id,
                "name": names.get(item_id),
                "from_kind": payload.get("from_kind"),
                "to_kind": payload.get("to_kind"),
                "reason": payload.get("reason"),
                "actor": e.get("actor"),
                "at": e.get("created_at"),
            }
        )
    return out


def bank_row_corrections(events: list[dict]) -> list[dict]:
    """银行流水行被余额链改写的痕迹,按件聚合。

    金额改写同时把 balance_ok 从 False 翻成 True(bank_stmt_balance._REPAIR_RATIO 内即改),
    该行因此退出所有待核对清单;方向改写决定这笔算不算销售收入
    (bank_sales_suggest.classify_row 按 withdrawal/deposit 判)。两者都影响销项倒推的基数。"""
    out = []
    for e in reconcile_bank.active_bank_parse_events(events):
        payload = e.get("payload") or {}
        item_id = payload.get("item_id")
        rows = payload.get("rows") or []
        if not item_id:
            continue
        corrected = [
            r for r in rows if r.get("amount_autocorrected") or r.get("direction_autocorrected")
        ]
        if not corrected:
            continue
        out.append(
            {
                "type": "bank_row_autocorrected",
                "item_id": item_id,
                "name": _source_file_of(rows),
                "row_count": len(rows),
                "amount_rows": sum(1 for r in corrected if r.get("amount_autocorrected")),
                "direction_rows": sum(1 for r in corrected if r.get("direction_autocorrected")),
                "samples": [_sample(r) for r in corrected[:_MAX_SAMPLES]],
                "truncated": len(corrected) > _MAX_SAMPLES,
            }
        )
    return out


def memo_lines(actions: list[dict]) -> list[str]:
    """交付包备忘的「机器自动改动」节。空列表由调用方按既有 _bullets 约定渲染成"无"。"""
    lines = []
    for a in actions:
        if a["type"] == EVT_REGROUPED:
            lines.append(
                f"- {a.get('name') or a['item_id']}: {a.get('from_kind')} → {a.get('to_kind')}"
                f" (依据 {a.get('reason')})"
            )
        else:
            lines.append(
                f"- {a.get('name') or a['item_id']}: 改金额 {a['amount_rows']} 行 ·"
                f" 改方向 {a['direction_rows']} 行 (共 {a['row_count']} 行)"
            )
    return lines


def _sample(row: dict) -> dict:
    return {
        "date": row.get("date"),
        "description": row.get("description"),
        "withdrawal": row.get("withdrawal"),
        "deposit": row.get("deposit"),
        "amount_autocorrected": bool(row.get("amount_autocorrected")),
        "direction_autocorrected": bool(row.get("direction_autocorrected")),
    }


def _source_file_of(rows: list[dict]) -> Optional[str]:
    for row in rows:
        name = row.get("source_file")
        if name:
            return Path(name).name
    return None


def _name_of(item: dict) -> str:
    return item.get("original_name") or Path(item.get("file_ref") or "").name
