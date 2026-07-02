# -*- coding: utf-8 -*-
"""人话渲染 + error_code→i18n key 映射(WP1 持有 · 键名锁定 docs/agent/CONVERSATION-SPEC.md)。

所有用户可见文本只在这一处产出 —— executor 的回执、loop 的反问/超范围/失败说明都过这里。
键名是 WP1↔WP3 对齐的唯一源(抄 spec 表,不互改对方文件):失败一律 agent.failure.*、成功回执
agent.ok.*。M1 返回「key(+slots)」占位串,WP3 在 i18n-data.js 落 4 语;WP5 接 i18n 渲染时
copy_map 内部换成真渲染,调用点(executor/loop)不变。
"""

from __future__ import annotations

from services.agent.contracts import ToolSpec

# 失败码 → i18n key(CONVERSATION-SPEC §1.5 · 前缀 agent.failure.*)。
ERROR_COPY: dict[str, str] = {
    "insufficient_balance": "agent.failure.insufficient_balance",
    "no_endpoint": "agent.failure.no_endpoint",
    "forbidden": "agent.failure.forbidden",
    "history_not_found": "agent.failure.history_not_found",
    "no_tenant": "agent.failure.no_tenant",
    "query_failed": "agent.failure.query_failed",
    "not_available_yet": "agent.failure.not_available_yet",
    "not_implemented_m1": "agent.failure.not_available_yet",  # B 档留桩 → spec 的 not_available_yet
    "unknown": "agent.failure.unknown",
}
_FAILURE_DEFAULT = "agent.failure._default"

# 成功回执 → i18n key(§1.3 · 每个 M1 工具一个 agent.ok.*)。
OK_COPY: dict[str, str] = {
    "list_history": "agent.ok.history",
    "history_summary": "agent.ok.history_summary",
    "balance": "agent.ok.balance",
    "usage_this_month": "agent.ok.usage_this_month",
    "list_notifications": "agent.ok.notifications",
    "recon_overview": "agent.ok.recon",  # 复用预登记键(两侧 parity 已守)
    "recon_detail": "agent.ok.recon_detail",
}

# 反问 slot → i18n key(§1.1)。未登记的 slot → 通用「哪一张」。
ASK_COPY: dict[str, str] = {
    "keyword": "agent.ask.which_doc",
    "status": "agent.ask.which_doc",
    "period": "agent.ask.period",
    "endpoint_id": "agent.ask.endpoint",
    "amount": "agent.ask.amount",
}
_ASK_DEFAULT = "agent.ask.which_doc"

_OOS_DEFAULT = "agent.oos.capability"  # §1.4 超范围必带「我能做什么」出口
_CHAT_DEFAULT = "agent.chat.greeting"  # §1.6 沿用现有语气池


def _clean(v) -> str:
    """槽位值消毒:去掉占位串分隔符,保证 agent_i18n._parse 不被值里的 ;| 破坏。"""
    return str(v).replace(";", ",").replace("|", "/")


def _render(key: str, **slots) -> str:
    """key(+slots)占位串。LINE 侧由 services.agent.agent_i18n.render 翻成 4 语真文案。"""
    if not slots:
        return key
    payload = ";".join(f"{k}={_clean(v)}" for k, v in slots.items())
    return f"{key}|{payload}"


# ── loop 用 ──────────────────────────────────────────────────────────────


def out_of_scope(message: str = "") -> str:
    return _OOS_DEFAULT


def chat(message: str = "") -> str:
    return _CHAT_DEFAULT


def ask(field: str) -> str:
    return ASK_COPY.get(field, _ASK_DEFAULT)


def confirm(spec: ToolSpec, grounded: dict) -> str:
    """B 档执行前复述确认(§1.2 · M3 才有 B 档工具走到这里)。"""
    return f"agent.confirm.{spec.name}"


def failure(error_code: str | None) -> str:
    return ERROR_COPY.get(error_code or "unknown", _FAILURE_DEFAULT)


# ── executor 回执(§1.3) ─────────────────────────────────────────────────


def _doc_line(item: dict) -> str:
    """一条单据的紧凑行:对手方/店名 + 金额(销项时买方名优先,采购时卖方名)。"""
    name = item.get("buyer_name") or item.get("seller_name") or item.get("filename") or "-"
    amount = item.get("total_amount")
    amount_s = f" {float(amount):,.0f}฿" if amount is not None else ""
    return f"· {name}{amount_s}"


def history_receipt(items: list, total: int) -> str:
    # top_list 取真实前 3 条(count 是全量,top_list 只是预览);无条目留空。
    lines = [_doc_line(it) for it in (items or [])[:3]]
    top_list = ("\n" + "\n".join(lines)) if lines else ""
    return _render(OK_COPY["list_history"], count=total, top_list=top_list)


def history_summary_receipt(overview: dict) -> str:
    # 槽位 count/total/by_category 对齐 agent_i18n 的 agent.ok.history_summary(改模板需同步)。
    ov = overview or {}
    cats = ov.get("by_category") or []
    by_category = (" · " + ", ".join(f"{tag} {n}" for tag, n in cats)) if cats else ""
    return _render(
        OK_COPY["history_summary"],
        count=int(ov.get("doc_count") or 0),
        total=f"{float(ov.get('amount_total') or 0):,.0f}",
        by_category=by_category,
    )


def balance_receipt(billing: dict) -> str:
    b = billing or {}
    return _render(
        OK_COPY["balance"],
        balance=f"{float(b.get('balance_thb') or 0):.2f}",
        pages=int(b.get("pages_used_this_month") or 0),
    )


def usage_receipt(billing: dict, docs: int = 0) -> str:
    return _render(
        OK_COPY["usage_this_month"],
        pages=int((billing or {}).get("pages_used_this_month") or 0),
        docs=int(docs or 0),
    )


def notifications_receipt(logs: list) -> str:
    return _render(OK_COPY["list_notifications"], count=len(logs or []))


def _recon_unmatched(t: dict) -> int:
    """归一不一致计数:income 直给 unmatched;bank 老形状回落 GL+对账单两侧之和。"""
    if t.get("unmatched") is not None:
        return int(t.get("unmatched") or 0)
    return int(t.get("unmatched_gl") or 0) + int(t.get("unmatched_stmt") or 0)


def recon_receipt(latest: dict) -> str:
    # 槽位 matched/unmatched 对齐 agent_i18n 的 agent.ok.recon。
    t = latest or {}
    return _render(
        OK_COPY["recon_overview"],
        matched=int(t.get("matched") or 0),
        unmatched=_recon_unmatched(t),
    )


def recon_detail_receipt(task: dict, rows: list) -> str:
    # 槽位 unmatched/top_list 对齐 agent.ok.recon_detail;side 用 GL/BANK/NO-GL/DIFF 通语记号免翻译。
    t = task or {}
    unmatched = _recon_unmatched(t)
    # 行形状统一由 recon_tools 三档构造器保证(date/side/amount/desc·tax 用 doc_no 顶 date 槽)
    lines = [
        "· "
        + " ".join(
            str(x)
            for x in (
                r.get("date") or r.get("doc_no") or "",
                r.get("side") or "",
                r.get("amount") or "",
                r.get("desc") or "",
            )
            if x
        )
        for r in (rows or [])[:3]
    ]
    top_list = ("\n" + "\n".join(lines)) if lines else ""
    return _render(OK_COPY["recon_detail"], unmatched=unmatched, top_list=top_list)


__all__ = [
    "ERROR_COPY",
    "OK_COPY",
    "ASK_COPY",
    "out_of_scope",
    "chat",
    "ask",
    "confirm",
    "failure",
    "history_receipt",
    "history_summary_receipt",
    "balance_receipt",
    "usage_receipt",
    "notifications_receipt",
    "recon_receipt",
    "recon_detail_receipt",
]
