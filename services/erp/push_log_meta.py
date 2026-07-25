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

from services.erp.express_push.stock_acc_group import describe_from_request

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
    uncosted_* = 这单有几行没结转成本、是否顺带新建了库存品(见 derive_uncosted);
    unit_guessed_* = 新建库存品时单位是小助手按账套众数填的(见 derive_guessed_unit)。
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
    out.update(derive_guessed_unit(body))
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


def derive_guessed_unit(body: Any) -> Dict[str, Any]:
    """新建库存品时单位是「猜的」的行数 + 猜出来的单位码(没有则空 dict,保列表轻量)。

    小助手建库存主档时票面若没给单位,会按该账套最常用的单位填一个(companion
    product_master._stock_unit)。那是替客户做的主 —— 不标出来,推送日志上就是一条干净的成功,
    会计要等到看 Express 商品档、或按错单位盘点时才发现。

    键名是与小助手的契约:line_modes[].unit_guessed / unit_code(companion dbf_detail.line_mode)。
    改名要两个仓库一起改,否则这里静默取不到值、标记凭空消失还不报错。
    """
    modes = body.get("line_modes") if isinstance(body, dict) else None
    lines = [
        m
        for m in (modes if isinstance(modes, list) else [])
        if isinstance(m, dict) and m.get("unit_guessed")
    ]
    if not lines:
        return {}
    codes: List[str] = []
    for m in lines:  # 去重保序:同一单多行常是同一个单位,列出来三遍反而看不清
        code = str(m.get("unit_code") or "").strip()
        if code and code not in codes:
            codes.append(code)
    return {"unit_guessed_lines": len(lines), "unit_guessed_codes": codes}


# 明细行真进了库存主档的两种模式(小助手回执 line_modes[].mode)。回落成直接科目行的那些也
# 会带 created,但建的是科目行不是库存品,混进来会把「新建了几个库存品」报多。
_STOCK_LINE_MODES = ("stock_item", "stock_sale")


def derive_stock_acc_group(resp_body: Any, req_body: Any, reported: Any) -> Dict[str, Any]:
    """本次在账套里新建了几个库存品 + 挂的哪个存货科目组(码 + 存货科目号/名)。

    合格候选唯一时科目组是系统替客户定的(见 express_push.stock_acc_group)—— 替人做的主必须
    在推送日志上看得见,否则账里凭空多一件商品、还记进了某个他没点过头的存货科目,要等到对
    科目余额时才发现。判据取回执的 created(真建了)+ 载荷里的 stock_acccod(挂了哪个组):
    两者缺一就不标,不拿「这批是库存路」冒充「真建了品」。组名从端点上报的候选表按码反查。
    """
    modes = resp_body.get("line_modes") if isinstance(resp_body, dict) else None
    created = sum(
        1
        for m in (modes if isinstance(modes, list) else [])
        # mode 缺失的老回执照收:漏标一条真新建的库存品,比多一层版本判断更伤
        if isinstance(m, dict)
        and m.get("created")
        and (m.get("mode") or "") in ("", *_STOCK_LINE_MODES)
    )
    if not created:
        return {}
    group = describe_from_request(req_body, reported)
    if not group:
        return {}
    out: Dict[str, Any] = {"stock_created": created, "stock_acccod": group["acccod"]}
    for k in ("stock_acc", "stock_acc_name"):
        if group.get(k):
            out[k] = group[k]
    return out
