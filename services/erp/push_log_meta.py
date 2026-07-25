# -*- coding: utf-8 -*-
"""推送日志列表项的 response_body 派生(纯函数 · 无 DB)+「未结转成本」判据单一源。

从 push_log_queries 抽出:那边是 DAL(拼 SQL、开游标),这里只把回执体翻成列表卡要的几个标量。
push_log_queries 顶部 re-import 当 facade(q._derive_v3_meta 等调用点与守门测试不变)。

未结转成本的判据放这里而不是各写各的:SQL 谓词(筛选器)和 Python 派生(卡上标注)一旦分叉,
筛出来的和标出来的就不是同一批单,会计再也不会信这个筛选器。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

# companion stock_sale.NO_COST_REASONS 的镜像:
#   no_cost_basis          有商品档但零/负库存且无标准成本
#   new_item_no_cost_basis 本次新建了库存品,无成本基础
# 加新码得小助手先发版、这里再认,否则新码的单会静默落回「一个干净的成功」。
NO_COST_REASONS = ("no_cost_basis", "new_item_no_cost_basis")

# response_body 是 text 列,历史行混着 HTML 和裸错误串(生产实测 93 行里 16 行不是 JSON),
# 裸 ::jsonb 会让整条查询报错;PG 又不保证 AND 短路,故用嵌套 CASE 逐层守——CASE 只算命中分支。
UNCOSTED_SQL = """EXISTS (
                    SELECT 1 FROM jsonb_array_elements(
                        CASE WHEN pg_input_is_valid(COALESCE(l.response_body, ''), 'jsonb')
                             THEN CASE
                                 WHEN jsonb_typeof(l.response_body::jsonb -> 'line_modes') = 'array'
                                 THEN l.response_body::jsonb -> 'line_modes'
                                 ELSE '[]'::jsonb END
                             ELSE '[]'::jsonb END
                    ) lm WHERE lm->>'reason' = ANY(%s)
                )"""


def _derive_push_accounts(resp_raw: Any) -> Optional[List[Dict[str, str]]]:
    """从 response_body 取 Express 队列响应里的分录科目 → [{acc,side,desc}](列表卡科目列用)。

    response_body 可能是 jsonb dict 或 JSON 字符串;无 accounts → None(只在有时带,保列表轻量)。
    """
    if not resp_raw:
        return None
    try:
        body = resp_raw if isinstance(resp_raw, dict) else json.loads(resp_raw)
    except (ValueError, TypeError):
        return None
    accs = body.get("accounts") if isinstance(body, dict) else None
    if not isinstance(accs, list) or not accs:
        return None
    out: List[Dict[str, str]] = []
    for a in accs:
        if not isinstance(a, dict):
            continue
        code = str(a.get("acc") or "").strip()
        if code:
            out.append(
                {"acc": code, "side": str(a.get("side") or ""), "desc": str(a.get("desc") or "")}
            )
    return out or None


def _derive_v3_meta(body: Any) -> Dict[str, Any]:
    """从 response_body.meta 派生 V3 细粒度态标量进列表项(轻量·只取前端展示要的几个)。

    push_stage = waiting_lock/rolled_back/needs_review/... (status 列的细化·见 common.STAGE_*);
    rolled_back = 写了一半已恢复备份;fallback_count = 明细从非库存回落直接科目的行数;
    uncosted_* = 这单有几行没结转成本、是否顺带新建了库存品(见 derive_uncosted)。
    """
    out: Dict[str, Any] = {}
    meta = body.get("meta") if isinstance(body, dict) else None
    if isinstance(meta, dict):
        stage = str(meta.get("stage") or "").strip()
        if stage:
            out["push_stage"] = stage
        if meta.get("rolled_back"):
            out["rolled_back"] = True
    if isinstance(body, dict) and body.get("fallback_count"):
        out["fallback_count"] = body.get("fallback_count")
    out.update(derive_uncosted(body))
    return out


def uncosted_lines(body: Any) -> List[Dict[str, Any]]:
    """回执里没结转成本的明细行(与 UNCOSTED_SQL 同判据)。"""
    modes = body.get("line_modes") if isinstance(body, dict) else None
    if not isinstance(modes, list):
        return []
    return [m for m in modes if isinstance(m, dict) and m.get("reason") in NO_COST_REASONS]


def derive_uncosted(body: Any) -> Dict[str, Any]:
    """未结转成本的标量:行数 + 本次是否新建了库存品(没有则空 dict,保列表轻量)。

    这两类行只记收入不结 COGS,当期毛利虚高到这批货的进货票补进来为止 —— 推送不标出来就是
    一个干净的「成功」,会计看不出账里还欠着成本。
    created 取行自报的 created,并认 new_item_no_cost_basis:该码本身就是「新建了库存品」,
    账里凭空多一件商品必须当场看得见,不然要等下次盘点才发现。
    """
    lines = uncosted_lines(body)
    if not lines:
        return {}
    created = any(m.get("created") or m.get("reason") == "new_item_no_cost_basis" for m in lines)
    return {"uncosted_lines": len(lines), "uncosted_created": created}
