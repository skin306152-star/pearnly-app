# -*- coding: utf-8 -*-
"""LINE 消息 ↔ 业务对象映射 + 改/删目标解析(引用底座 · Brain OS P1A)。

发回执卡时记下 LINE 消息 id → 绑定该 purchase_doc。用户长按某条回执 reply「删除/改成X/卖家改
成Y」→ webhook 带 quotedMessageId → 反查到那张【确切】的单(不再默认改最近一笔)。
解析优先级固定:quotedMessageId > postback nonce > pending 上下文 > 第 N 笔列表 > 明确「上一笔」。
高风险动作(删/撤/改)对象不明确 → 不执行,提示用户 reply 某条记录(对齐 Paypers)。
prod 无 alembic 钩子 → startup ensure 幂等建表(alembic 0041 留档)· RLS 按 tenant 隔离。
"""

from __future__ import annotations

from typing import Optional

DEFAULT_TTL_DAYS = 90

# 明确指「最近一笔」的口语(仅在无引用/无序号时才据此回落,且仅对已表达动作的句子)。
_LAST_WORDS = (
    "上一笔",
    "上一条",
    "上一个",
    "上笔",
    "最近一笔",
    "最近这笔",
    "刚才那笔",
    "刚记的",
    "ล่าสุด",
    "อันล่าสุด",
    "รายการล่าสุด",
    "เมื่อกี้",
    "last",
    "latest",
    "previous",
)

_TABLE = """
CREATE TABLE IF NOT EXISTS line_message_refs (
    line_message_id text PRIMARY KEY,
    tenant_id uuid NOT NULL,
    workspace_client_id bigint NOT NULL,
    line_user_id text NOT NULL DEFAULT '',
    ref_type text NOT NULL DEFAULT 'purchase_doc',
    ref_id text NOT NULL,
    state text NOT NULL DEFAULT '',
    summary text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL
)
"""
_INDEX = "CREATE INDEX IF NOT EXISTS ix_line_message_refs_expires ON line_message_refs (expires_at)"


def ensure_table() -> None:
    """幂等建 line_message_refs + RLS(startup 调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        cur.execute(_INDEX)
        apply_tenant_rls(cur, "line_message_refs")


def record(
    cur,
    *,
    tenant_id,
    workspace_client_id,
    line_user_id,
    message_ids,
    ref_id,
    ref_type: str = "purchase_doc",
    state: str = "",
    summary: str = "",
    ttl_days: int = DEFAULT_TTL_DAYS,
) -> None:
    """把刚发出的若干 LINE 消息 id 绑到一张业务单(用户可引用其中任一条来操作)。best-effort。

    一条多行 INSERT(回执卡通常 2 条消息)→ 单次 round-trip,不在发卡路径上逐条往返。
    """
    ids = [str(m) for m in (message_ids or []) if m]
    if not ref_id or not ids:
        return
    base = [
        tenant_id,
        workspace_client_id,
        str(line_user_id or ""),
        ref_type,
        str(ref_id),
        state or "",
        summary or "",
        int(ttl_days),
    ]
    rows, params = [], []
    for mid in ids:
        rows.append("(%s, %s, %s, %s, %s, %s, %s, %s, now() + make_interval(days => %s))")
        params.extend([mid, *base])
    cur.execute(
        "INSERT INTO line_message_refs "
        "(line_message_id, tenant_id, workspace_client_id, line_user_id, ref_type, ref_id, "
        " state, summary, expires_at) VALUES " + ", ".join(rows) + " "
        "ON CONFLICT (line_message_id) DO UPDATE SET "
        " ref_id = EXCLUDED.ref_id, state = EXCLUDED.state, summary = EXCLUDED.summary, "
        " expires_at = EXCLUDED.expires_at",
        params,
    )


def record_safe(
    *, tenant_id, workspace_client_id, line_user_id, message_ids, ref_id, state="", summary=""
) -> None:
    """开独立事务记映射(发消息后调 · 失败只记日志不阻塞回执)。"""
    import logging

    from core import db

    if not ref_id or not message_ids or not tenant_id:
        return
    try:
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            record(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                line_user_id=line_user_id,
                message_ids=message_ids,
                ref_id=ref_id,
                state=state,
                summary=summary,
            )
    except Exception:  # noqa: BLE001
        logging.getLogger(__name__).warning("[line refs] record failed; quote-reply 不可用,不阻塞")


def lookup(cur, *, tenant_id, line_message_id) -> Optional[dict]:
    """引用的消息 id → 绑定的业务单(未过期)。无/过期 → None。"""
    if not line_message_id:
        return None
    cur.execute(
        "SELECT ref_type, ref_id, workspace_client_id, state, summary FROM line_message_refs "
        "WHERE tenant_id = %s AND line_message_id = %s AND expires_at > now()",
        (tenant_id, str(line_message_id)),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "ref_type": row["ref_type"],
        "ref_id": row["ref_id"],
        "workspace_client_id": row["workspace_client_id"],
        "state": row["state"],
        "summary": row["summary"],
    }


def find_last_posted(cur, *, tenant_id, ws):
    """该套账最近一笔 LINE 已入账单(明确「上一笔」时用)。"""
    cur.execute(
        "SELECT id, grand_total FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND source = 'line' "
        "AND status = 'posted' ORDER BY created_at DESC LIMIT 1",
        (tenant_id, ws),
    )
    return cur.fetchone()


def mentions_last(text: str) -> bool:
    """句子是否明确指「最近一笔」(上一笔/ล่าสุด/last)。"""
    low = (text or "").lower()
    return any(w.lower() in low for w in _LAST_WORDS)


def resolve_target(cur, *, tenant_id, ws, line_user_id, quoted_message_id, text) -> dict:
    """定位改/删的目标单。返回 {doc_id, ws, how, error}。

    优先级:① 引用具体回执(quotedMessageId)② 查明细后「第 N 笔」③ 明确「上一笔」。
    都不满足 → error='ambiguous'(高风险动作据此提示 reply,绝不默认改最近一笔)。
    引用了但查不到 → error='ref_not_found'(提示重新引用或查明细)。
    """
    from services.expense import conversation
    from services.expense import line_quick_entry as lqe

    if quoted_message_id:
        ref = lookup(cur, tenant_id=tenant_id, line_message_id=quoted_message_id)
        if ref and ref["ref_type"] == "purchase_doc" and ref["ref_id"]:
            return {
                "doc_id": ref["ref_id"],
                "ws": ref["workspace_client_id"],
                "how": "quoted",
                "error": None,
            }
        return {"doc_id": None, "ws": ws, "how": None, "error": "ref_not_found"}

    n = lqe.parse_ordinal(text)
    if n:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
        missing = str((pend or {}).get("missing") or "")
        if missing.startswith("detail:"):
            ids = [x for x in missing[len("detail:") :].split(",") if x]
            if 1 <= n <= len(ids):
                return {"doc_id": ids[n - 1], "ws": ws, "how": "ordinal", "error": None}
        return {"doc_id": None, "ws": ws, "how": None, "error": "ref_not_found"}

    if mentions_last(text):
        row = find_last_posted(cur, tenant_id=tenant_id, ws=ws)
        if row:
            return {"doc_id": str(row["id"]), "ws": ws, "how": "last", "error": None}
        return {"doc_id": None, "ws": ws, "how": None, "error": "none"}

    return {"doc_id": None, "ws": ws, "how": None, "error": "ambiguous"}
