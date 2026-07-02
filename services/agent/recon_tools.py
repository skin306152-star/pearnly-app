# -*- coding: utf-8 -*-
"""三个对账的 Agent 只读工具层(RECON-3-LINE-PLAN)—— overview / detail 数据装配。

对账中心三档:bank=银行对账(bank_recon_v2_task)· income=收入对账(gl_vat_task)·
tax=销项税报告核查(vat_recon_tasks)。方案一先通 bank;income/tax 依次通电,
在此模块内扩,executor 只留薄委托。数字全来自 store 现成只读函数,不碰对账计算。
"""

from __future__ import annotations

import json
import logging

from services.agent import copy_map
from services.agent.contracts import AgentContext, ToolResult

logger = logging.getLogger(__name__)

_DETAIL_CAP = 8  # 明细上限:LINE 一屏内讲得清;其余给 omitted 计数,细看去网页

_KIND_ALIASES = {
    "bank": "bank",
    "bank_recon": "bank",
    "statement": "bank",
    "income": "income",
    "gl_vat": "income",
    "revenue": "income",
    "tax": "tax",
    "tax_check": "tax",
    "vat": "tax",
    "sales_vat": "tax",
}


def normalize_kind(kind) -> str:
    """档位归一;空/不认识 → bank(现阶段唯一通电档,也是最常问的)。"""
    return _KIND_ALIASES.get(str(kind or "").strip().lower(), "bank")


def overview(ctx: AgentContext) -> ToolResult:
    """银行对账只读概览(方案二起扩三档)。store 层故障返空表不抛 → 诚实空口径。"""
    from services.recon.bank_recon_v2_store import list_bank_recon_v2_tasks

    tasks = list_bank_recon_v2_tasks(str(ctx.user["id"]), ctx.tenant_id, limit=5)
    recent = [
        {
            "bank": t.get("bank_code"),
            "matched": t.get("matched_count"),
            "unmatched_gl": t.get("unmatched_gl"),
            "unmatched_stmt": t.get("unmatched_stmt"),
            "status": t.get("status"),
            "created_at": str(t.get("created_at") or "")[:16],
        }
        for t in tasks
    ]
    receipt = copy_map.recon_receipt(recent[0]) if recent else ""
    data: dict = {"count": len(recent), "recent": recent}
    if not recent:
        # 在线验证抓到:空数据时模型爱说"结果已准备好请查看"(虚)。给显式提示钉住口径。
        data["hint"] = (
            "no reconciliation runs yet — say so honestly and suggest uploading "
            "a bank statement under Bank Reconciliation on the web"
        )
    return ToolResult(ok=True, data=data, receipt=receipt)


def detail(ctx: AgentContext, *, kind=None, keyword=None) -> ToolResult:
    """对不上的明细钻取(默认最新一次任务;keyword=银行名/文件名定位)。
    v1 只通 bank 档;income/tax 如实答 not_available_yet(方案二/三依次开)。"""
    k = normalize_kind(kind)
    if k != "bank":
        return ToolResult(ok=False, error_code="not_available_yet")
    from services.recon.bank_recon_v2_store import (
        get_bank_recon_v2_task,
        list_bank_recon_v2_tasks,
    )

    tasks = list_bank_recon_v2_tasks(str(ctx.user["id"]), ctx.tenant_id, limit=10)
    task_head = _pick_task(tasks, keyword)
    if not task_head:
        return ToolResult(
            ok=True,
            data={
                "count": 0,
                "hint": (
                    "no matching reconciliation run — say so honestly and suggest "
                    "running one under Bank Reconciliation on the web"
                ),
            },
        )
    full = get_bank_recon_v2_task(int(task_head["id"]), str(ctx.user["id"]), ctx.tenant_id)
    rows = _detail_rows(full)
    unmatched = [_compact_row(r) for r in rows if str(r.get("match_status") or "") != "matched"]
    data = {
        "task": {
            "bank": task_head.get("bank_code"),
            "gl_account": task_head.get("gl_account"),
            "created_at": str(task_head.get("created_at") or "")[:16],
            "matched": task_head.get("matched_count"),
            "unmatched_gl": task_head.get("unmatched_gl"),
            "unmatched_stmt": task_head.get("unmatched_stmt"),
            "stmt_opening": task_head.get("stmt_opening"),
            "stmt_closing": task_head.get("stmt_closing"),
            "gl_opening": task_head.get("gl_opening"),
            "gl_closing": task_head.get("gl_closing"),
            "formula_diff": task_head.get("formula_diff"),
        },
        "unmatched": unmatched[:_DETAIL_CAP],
        "omitted": max(0, len(unmatched) - _DETAIL_CAP),
    }
    return ToolResult(
        ok=True, data=data, receipt=copy_map.recon_detail_receipt(data["task"], data["unmatched"])
    )


def _pick_task(tasks, keyword):
    """keyword 对银行码/文件名松匹配(归一小写去空格);没给/没中 → 最新一条。
    刻意不做"多命中反问":任务按时间倒序,最新即用户语境里的"这次"。"""
    if not tasks:
        return None
    q = "".join(str(keyword or "").lower().split())
    if q:
        for t in tasks:
            hay = "".join(
                str(x or "") for x in (t.get("bank_code"), t.get("stmt_files"), t.get("gl_files"))
            ).lower()
            if q in "".join(hay.split()):
                return t
    return tasks[0]


def _detail_rows(task) -> list:
    raw = (task or {}).get("detail_json")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return []
    return raw if isinstance(raw, list) else []


def _compact_row(r: dict) -> dict:
    """一条不一致行的紧凑形:side(BANK=只在对账单/GL=只在总账)+日期+摘要+金额。"""
    status = str(r.get("match_status") or "")
    side = "BANK" if status.startswith("stmt") else "GL"
    keys = ("stmt_withdrawal", "stmt_deposit") if side == "BANK" else ("gl_debit", "gl_credit")
    amount = ""
    for key in keys:
        v = r.get(key)
        if v not in (None, "", 0, "0", 0.0):
            amount = str(v)
            break
    return {
        "side": side,
        "status": status,
        "date": str(r.get("stmt_date") or r.get("gl_date") or ""),
        "desc": str(r.get("stmt_desc") or r.get("gl_desc") or "")[:40],
        "amount": amount,
    }
