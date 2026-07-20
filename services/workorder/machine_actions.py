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

from typing import Optional

from services.workorder import evidence, storage
from services.workorder.steps import reconcile_bank

EVT_REGROUPED = "item_regrouped"


def projection(events: list[dict], items: list[dict]) -> list[dict]:
    """order_detail.machine_actions 读侧投影(改判 + 银行行自动纠正)。

    不跟随 bank_recon 那套"只在 reconcile 步回放"的懒加载:签批前(review 态)恰恰是最该
    看到机器改过什么的时刻,那时懒加载已经不算了。事件本就在内存,多扫一遍是 O(n)。"""
    return regroup_actions(events, items) + bank_row_corrections(events)


def regroup_actions(events: list[dict], items: list[dict]) -> list[dict]:
    """料件被引擎改判的痕迹(statement_regroup 落的 item_regrouped)。

    改判会清空 flag_reason 并把件置 ok,之后它既不在 flagged 也不在 excluded——不投影就等于
    从所有清单里凭空消失。回放走 evidence.replay_items_by_type 拿 latest-wins,与其余读侧
    投影同一份语义:同件重复改判只呈现最后一次,不在清单里出两行。"""
    names = {it["id"]: _display_name(it) for it in items}
    replayed = evidence.replay_items_by_type(events, EVT_REGROUPED)
    return [
        {
            "type": EVT_REGROUPED,
            "item_id": item_id,
            "name": names.get(item_id),
            "from_kind": rec["payload"].get("from_kind"),
            "to_kind": rec["payload"].get("to_kind"),
            "reason": rec["payload"].get("reason"),
        }
        for item_id, rec in replayed.items()
    ]


def bank_row_corrections(events: list[dict]) -> list[dict]:
    """银行流水行被余额链改写的痕迹,按件聚合。

    金额改写同时把 balance_ok 从 False 翻成 True(bank_stmt_balance._REPAIR_RATIO 内即改),
    该行因此退出所有待核对清单;方向改写决定这笔算不算销售收入
    (bank_sales_suggest.classify_row 按 withdrawal/deposit 判)。两者都影响销项倒推的基数。

    同件多条解析事件取首条,与 reconcile_bank._replay_parsed_banks 的「首件在先」一致——
    呈现的必须是引擎实际采信的那批行,否则数字对不上人看到的流水。"""
    out = []
    seen: set = set()
    for e in reconcile_bank.active_bank_parse_events(events):
        payload = e.get("payload") or {}
        item_id = payload.get("item_id")
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        rows = payload.get("rows") or []
        amount_rows = sum(1 for r in rows if r.get("amount_autocorrected"))
        direction_rows = sum(1 for r in rows if r.get("direction_autocorrected"))
        if not (amount_rows or direction_rows):
            continue
        out.append(
            {
                "type": "bank_row_autocorrected",
                "item_id": item_id,
                "name": _source_file_of(rows),
                "row_count": len(rows),
                "amount_rows": amount_rows,
                "direction_rows": direction_rows,
            }
        )
    return out


def _display_name(item: dict) -> Optional[str]:
    """件的展示名:优先 DB 存的原名,否则从落盘 file_ref 剥掉 uuid 前缀(与 freeze 同一口径,
    别把 `{uuid}__原名` 这种裸落盘名吐给读侧——剥壳责任不该推给每个前端各写一遍正则)。"""
    return item.get("original_name") or storage.original_name_of(item.get("file_ref"))


def _source_file_of(rows: list[dict]) -> Optional[str]:
    for row in rows:
        name = row.get("source_file")
        if name:
            return storage.original_name_of(name)
    return None
