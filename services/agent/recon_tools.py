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
    """对账只读概览:bank+income 双档一次给齐(问法含糊时模型两档都讲一句)。
    每档最近 3 条,条目带归一 matched/unmatched;store 层故障返空表不抛 → 诚实空口径。"""
    bank = _bank_recent(ctx, limit=3)
    income = _income_recent(ctx, limit=3)
    latest = bank[0] if bank else (income[0] if income else None)
    receipt = copy_map.recon_receipt(latest) if latest else ""
    data: dict = {"bank": {"recent": bank}, "income": {"recent": income}}
    if not latest:
        # 在线验证抓到:空数据时模型爱说"结果已准备好请查看"(虚)。给显式提示钉住口径。
        data["hint"] = (
            "no reconciliation runs yet — say so honestly and suggest uploading "
            "files under Reconciliation Center on the web"
        )
    return ToolResult(ok=True, data=data, receipt=receipt)


def _bank_recent(ctx, *, limit) -> list:
    from services.recon.bank_recon_v2_store import list_bank_recon_v2_tasks

    tasks = list_bank_recon_v2_tasks(str(ctx.user["id"]), ctx.tenant_id, limit=limit)
    return [
        {
            "bank": t.get("bank_code"),
            "matched": _i(t.get("matched_count")),
            "unmatched": _i(t.get("unmatched_gl")) + _i(t.get("unmatched_stmt")),
            "unmatched_gl": _i(t.get("unmatched_gl")),
            "unmatched_stmt": _i(t.get("unmatched_stmt")),
            "status": t.get("status"),
            "created_at": str(t.get("created_at") or "")[:16],
        }
        for t in tasks
    ]


def _income_recent(ctx, *, limit) -> list:
    from services.recon.gl_vat_store import list_gl_vat_tasks

    tasks = list_gl_vat_tasks(str(ctx.user["id"]), ctx.tenant_id, limit=limit)
    return [
        {
            "gl_file": t.get("gl_filename"),
            "vat_file": t.get("vat_filename"),
            "matched": _i(t.get("matched_count")),
            # unmatched 归一口径 = 缺 GL(unmatched_count)+ 金额不一致(diff_count)
            "unmatched": _i(t.get("unmatched_count")) + _i(t.get("diff_count")),
            "missing_in_gl": _i(t.get("unmatched_count")),
            "amount_diff": _i(t.get("diff_count")),
            "status": t.get("status"),
            "created_at": str(t.get("created_at") or "")[:16],
        }
        for t in tasks
    ]


def detail(ctx: AgentContext, *, kind=None, keyword=None) -> ToolResult:
    """对不上的明细钻取(默认最新一次任务;keyword=银行名/文件名定位)。
    bank/income 已通;tax 如实答 not_available_yet(方案三开)。"""
    k = normalize_kind(kind)
    if k == "income":
        return _income_detail(ctx, keyword)
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
        # 锚点余额列是 DB Decimal,不转 str 会炸 prompt 的 json.dumps(真机雷 2026-07-03)。
        "task": {
            "bank": task_head.get("bank_code"),
            "gl_account": task_head.get("gl_account"),
            "created_at": str(task_head.get("created_at") or "")[:16],
            "matched": _i(task_head.get("matched_count")),
            "unmatched": _i(task_head.get("unmatched_gl")) + _i(task_head.get("unmatched_stmt")),
            "unmatched_gl": _i(task_head.get("unmatched_gl")),
            "unmatched_stmt": _i(task_head.get("unmatched_stmt")),
            "stmt_opening": _s(task_head.get("stmt_opening")),
            "stmt_closing": _s(task_head.get("stmt_closing")),
            "gl_opening": _s(task_head.get("gl_opening")),
            "gl_closing": _s(task_head.get("gl_closing")),
            "formula_diff": _s(task_head.get("formula_diff")),
        },
        "unmatched": unmatched[:_DETAIL_CAP],
        "omitted": max(0, len(unmatched) - _DETAIL_CAP),
    }
    return ToolResult(
        ok=True, data=data, receipt=copy_map.recon_detail_receipt(data["task"], data["unmatched"])
    )


def _income_detail(ctx: AgentContext, keyword) -> ToolResult:
    """收入对账(GL 收入科目 ↔ 销项税报告)不一致明细:缺 GL(gl_amount=None)+
    金额不一致(diff≠0)。行形状来自 gl_vat_task.detail_json(以 VAT 报表为主表)。"""
    from services.recon.gl_vat_store import get_gl_vat_task, list_gl_vat_tasks

    tasks = list_gl_vat_tasks(str(ctx.user["id"]), ctx.tenant_id, limit=10)
    head = None
    q = "".join(str(keyword or "").lower().split())
    if q:
        for t in tasks:
            hay = "".join(
                f"{t.get('gl_filename') or ''}{t.get('vat_filename') or ''}".lower().split()
            )
            if q in hay:
                head = t
                break
    head = head or (tasks[0] if tasks else None)
    if not head:
        return ToolResult(
            ok=True,
            data={
                "count": 0,
                "hint": (
                    "no income reconciliation runs yet — say so honestly and suggest "
                    "running one under Reconciliation Center (income tab) on the web"
                ),
            },
        )
    full = get_gl_vat_task(int(head["id"]), str(ctx.user["id"]), ctx.tenant_id) or {}
    rows = _detail_rows(full)
    bad = [
        {
            "issue": "missing_in_gl" if r.get("gl_amount") is None else "amount_diff",
            "side": "NO-GL" if r.get("gl_amount") is None else "DIFF",
            "doc_no": str(r.get("doc_no") or ""),
            "date": str(r.get("date") or ""),
            "desc": str(r.get("customer_name") or "")[:40],
            "amount": _s(r.get("vat_amount")),
            "gl_amount": _s(r.get("gl_amount")),
            "diff": _s(r.get("diff")),
        }
        for r in rows
        if r.get("gl_amount") is None or (r.get("diff") not in (None, 0, 0.0))
    ]
    data = {
        "task": {
            "gl_file": head.get("gl_filename"),
            "vat_file": head.get("vat_filename"),
            "created_at": str(head.get("created_at") or "")[:16],
            "matched": _i(head.get("matched_count")),
            "unmatched": _i(head.get("unmatched_count")) + _i(head.get("diff_count")),
            "missing_in_gl": _i(head.get("unmatched_count")),
            "amount_diff": _i(head.get("diff_count")),
        },
        "unmatched": bad[:_DETAIL_CAP],
        "omitted": max(0, len(bad) - _DETAIL_CAP),
    }
    return ToolResult(
        ok=True, data=data, receipt=copy_map.recon_detail_receipt(data["task"], data["unmatched"])
    )


def _s(v):
    return None if v is None else str(v)


def _i(v):
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


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
