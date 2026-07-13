# -*- coding: utf-8 -*-
"""LINE 待问暂挂池 store(D2 方案 §2.3 / §7.2 S3)· 持久业务表,非 TTL 临时表。

跨月留存的语义是「不过期」——status='pending' 的行靠状态机 + 三条自动关闭规则(S7)
封口,不靠 TTL 删。建表范式照 line_pending_actions.py 的首用幂等自愈 + apply_tenant_rls。
状态字符串 / question_type / 跳转合法性全部 import client_pool_vocab,本模块零臆造状态词
(裁决状态词仍照旧 import services.workorder.decisions,不在此重造 · 方案 §2.3 明载)。
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from services.line_binding import client_pool_vocab as vocab

logger = logging.getLogger(__name__)

_TABLE = """
CREATE TABLE IF NOT EXISTS line_client_questions (
    id                  bigserial PRIMARY KEY,
    tenant_id           uuid   NOT NULL,
    workspace_client_id bigint NOT NULL,
    work_order_id       uuid   NOT NULL,
    item_id             uuid   NOT NULL,
    period              text   NOT NULL,
    question_type       text   NOT NULL,
    question_payload    jsonb  NOT NULL DEFAULT '{}'::jsonb,
    status              text   NOT NULL DEFAULT 'staged',
    batch_id            uuid,
    batch_seq           smallint,
    answer_raw          text,
    resolution          jsonb,
    created_by          text   NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    sent_at             timestamptz,
    answered_at         timestamptz,
    closed_at           timestamptz,
    updated_at          timestamptz NOT NULL DEFAULT now()
)
"""

# 存量表补列:prod 已有 line_client_questions(alembic 停 0020,靠首用自愈),CREATE TABLE
# IF NOT EXISTS 不会补新列,须显式幂等 ALTER,否则老库永远缺 batch_seq。
_ALTER_BATCH_SEQ = "ALTER TABLE line_client_questions ADD COLUMN IF NOT EXISTS batch_seq smallint"

_INDEX_ACTIVE_ITEM = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_lcq_active_item
    ON line_client_questions (tenant_id, work_order_id, item_id)
    WHERE status IN ('staged','pending','manual_review')
"""

_INDEX_CLIENT_ACTIVE = """
CREATE INDEX IF NOT EXISTS ix_lcq_client_active
    ON line_client_questions (tenant_id, workspace_client_id, status)
"""

_INDEX_PENDING_CHASE = """
CREATE INDEX IF NOT EXISTS ix_lcq_pending_chase
    ON line_client_questions (status, sent_at) WHERE status = 'pending'
"""

_COLUMNS = (
    "id, tenant_id, workspace_client_id, work_order_id, item_id, period, "
    "question_type, question_payload, status, batch_id, batch_seq, answer_raw, resolution, "
    "created_by, created_at, sent_at, answered_at, closed_at, updated_at"
)

# 跳转到该状态时顺带盖的时间戳列(§2.3 sent_at/answered_at/closed_at 语义)。
_STATUS_TIMESTAMP_COLUMN = {
    vocab.PENDING: "sent_at",
    vocab.APPLIED: "answered_at",
    vocab.MANUAL_REVIEW: "answered_at",
    vocab.RESOLVED_INTERNALLY: "closed_at",
    vocab.CANCELLED: "closed_at",
}


class ClientPoolError(Exception):
    """暂挂池域错误基类。"""


class IllegalTransitionError(ClientPoolError):
    """状态跳转不合法(表驱动拒绝 · 不猜、不强推)。"""

    def __init__(self, from_status: str, to_status: str):
        super().__init__(f"illegal transition {from_status} -> {to_status}")
        self.from_status = from_status
        self.to_status = to_status


_table_ensured = False


def ensure_table() -> None:
    """幂等建表 + 三索引 + RLS(首用自愈调)。进程内 once-flag(照 workorder
    store.ensure_runtime 先例):review-queue 等高频读侧每请求都调,DDL 只真跑进程首次;
    自愈路(_with_heal)先重置 flag 强制重跑。"""
    global _table_ensured
    if _table_ensured:
        return
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        cur.execute(_ALTER_BATCH_SEQ)
        cur.execute(_INDEX_ACTIVE_ITEM)
        cur.execute(_INDEX_CLIENT_ACTIVE)
        cur.execute(_INDEX_PENDING_CHASE)
        apply_tenant_rls(cur, "line_client_questions")
    _table_ensured = True


def _with_heal(fn):
    """表不存在(新库/回滚后)或缺 batch_seq 列(存量表未补列)→ 自愈重试一次;
    其余异常向上抛由调用方 fail-safe。"""
    global _table_ensured
    try:
        return fn()
    except Exception as e:
        msg = str(e)
        if "line_client_questions" not in msg and "batch_seq" not in msg:
            raise
        _table_ensured = False
        ensure_table()
        return fn()


def stage(
    tenant_id,
    *,
    workspace_client_id,
    work_order_id,
    item_id,
    period: str,
    question_type: str,
    question_payload: Optional[dict] = None,
    created_by: str,
) -> dict:
    """归集入池(W3「推 LINE 待问」动作)。同票已有 active 问题 → uq_lcq_active_item 兜底,
    幂等原样交回既有行,不重复暂挂、不报错(会计手快点两下不炸)。"""
    from core import db

    if question_type not in vocab.QUESTION_TYPES:
        raise ClientPoolError(f"unknown question_type: {question_type}")

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO line_client_questions "
                "(tenant_id, workspace_client_id, work_order_id, item_id, period, "
                " question_type, question_payload, status, created_by) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s) "
                "ON CONFLICT (tenant_id, work_order_id, item_id) "
                "WHERE status IN ('staged','pending','manual_review') DO NOTHING "
                f"RETURNING {_COLUMNS}",
                (
                    str(tenant_id),
                    workspace_client_id,
                    str(work_order_id),
                    str(item_id),
                    period,
                    question_type,
                    json.dumps(question_payload or {}, ensure_ascii=False),
                    vocab.STAGED,
                    created_by,
                ),
            )
            row = cur.fetchone()
            if row:
                return dict(row)
            cur.execute(
                f"SELECT {_COLUMNS} FROM line_client_questions "
                "WHERE tenant_id = %s AND work_order_id = %s AND item_id = %s "
                "AND status IN ('staged','pending','manual_review')",
                (str(tenant_id), str(work_order_id), str(item_id)),
            )
            existing = cur.fetchone()
            return dict(existing) if existing else {}

    return _with_heal(_run)


def list_for_client(tenant_id, workspace_client_id, *, statuses: Optional[tuple] = None) -> list:
    """按客户查问题(客户池页分组读侧)。statuses 缺省 = 只看 active 三态。"""
    from core import db

    want = tuple(statuses) if statuses else tuple(vocab.ACTIVE_STATUSES)

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM line_client_questions "
                "WHERE tenant_id = %s AND workspace_client_id = %s AND status = ANY(%s) "
                "ORDER BY created_at",
                (str(tenant_id), workspace_client_id, list(want)),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    return _with_heal(_run)


def list_batch(tenant_id, workspace_client_id, batch_id) -> list:
    """按 batch_id 取该批次【全状态】行。答题侧据此定位「客户嘴里的第 N 题」——用行自带的
    batch_seq(推送时 mark_sent 落的固定编号)对号,不随期间某题答完退出 pending、列表
    收缩而位移(R3 串题根因已根治:编号是持久列,不再靠推送/答题两侧现算对齐)。

    ORDER BY created_at 仅为稳定展示序;编号权威来自 batch_seq 列,与本查询排序无关。
    (batch_seq 迁移前的存量批次 batch_seq 为 NULL,答题侧 _consume 对这种批次回落按位序,
    见其注释。)"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM line_client_questions "
                "WHERE tenant_id = %s AND workspace_client_id = %s AND batch_id = %s "
                "ORDER BY created_at",
                (str(tenant_id), workspace_client_id, str(batch_id)),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    return _with_heal(_run)


def list_pending_for_dunning(*, sent_before) -> list:
    """催办 tick 扫全部租户 pending 且 sent_at 早于给定时间的行(跨 tenant 只读扫描,
    走 owner 连接;S6 逐行按行自带的 tenant_id 建 RLS 上下文回写,不代表放弃隔离)。"""
    from core import db

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM line_client_questions "
                "WHERE status = %s AND sent_at IS NOT NULL AND sent_at <= %s "
                "ORDER BY sent_at",
                (vocab.PENDING, sent_before),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    return _with_heal(_run)


def list_active_all() -> list:
    """全部租户 active(staged/pending/manual_review)问题(S6 关闭清扫 tick 用 · 跨 tenant
    只读扫描,走 owner 连接,同 list_pending_for_dunning 口径:逐行按行自带的 tenant_id
    建 RLS 上下文回写,不代表放弃隔离)。"""
    from core import db

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM line_client_questions "
                "WHERE status = ANY(%s) ORDER BY id",
                (list(vocab.ACTIVE_STATUSES),),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    return _with_heal(_run)


def transition(
    tenant_id,
    question_id,
    to_status: str,
    *,
    answer_raw: Optional[str] = None,
    resolution: Optional[dict] = None,
) -> dict:
    """状态跳转(表驱动合法性 + CAS latest-wins)。

    先读当前状态校验 client_pool_vocab.LEGAL_TRANSITIONS,再用 UPDATE ... WHERE
    status = <读到的当前态> 做乐观锁:并发下若该行状态已被别的裁决/催办改写,本次
    UPDATE 影响 0 行 → 视为跳转已失效(latest-wins,绝不覆盖更新的状态),同样报
    IllegalTransitionError 交调用方重读现状。终态(applied/resolved_internally/
    cancelled)在 LEGAL_TRANSITIONS 里出边为空集,天然不可再跳。
    """
    from core import db

    if to_status not in vocab.ALL_STATUSES:
        raise ClientPoolError(f"unknown status: {to_status}")

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "SELECT status FROM line_client_questions WHERE tenant_id = %s AND id = %s",
                (str(tenant_id), question_id),
            )
            row = cur.fetchone()
            if not row:
                raise ClientPoolError(f"question not found: {question_id}")
            current = row["status"]
            if not vocab.is_legal_transition(current, to_status):
                raise IllegalTransitionError(current, to_status)

            ts_col = _STATUS_TIMESTAMP_COLUMN.get(to_status)
            set_ts = f", {ts_col} = now()" if ts_col else ""
            cur.execute(
                "UPDATE line_client_questions SET status = %s, updated_at = now(), "
                "answer_raw = COALESCE(%s, answer_raw), "
                f"resolution = COALESCE(%s::jsonb, resolution){set_ts} "
                "WHERE tenant_id = %s AND id = %s AND status = %s "
                f"RETURNING {_COLUMNS}",
                (
                    to_status,
                    answer_raw,
                    json.dumps(resolution, ensure_ascii=False) if resolution is not None else None,
                    str(tenant_id),
                    question_id,
                    current,
                ),
            )
            updated = cur.fetchone()
            if not updated:
                # 期间被并发改写 → 现状比本次期望的更新(latest-wins),本次跳转失效。
                raise IllegalTransitionError(current, to_status)
            return dict(updated)

    return _with_heal(_run)


def mark_sent(tenant_id, question_id, batch_id, batch_seq) -> dict:
    """staged→pending 且原子盖 batch_id + batch_seq(S4 攒批推送成功后逐行落定 · 方案 §7.2 S4)。

    batch_seq = 该题在推送消息里的固定编号(enumerate start=1),持久落列作为答题定位的
    单一事实源——答题按存的序号定位「客户嘴里的第 N 题」,不再靠推送/答题两侧各自 ORDER BY
    对齐(根治 R3 串题:编号不随期间某题退出 pending、列表收缩而漂移)。

    transition() 没有 batch_id/batch_seq 写入口(通用跳转不知道"这是不是一次批量推送"),
    专开此函数而不是把它们塞进 transition() 的通用签名——避免其余跳转路径(人工裁决/
    自动关闭)误传/误留旧批次标记。合法性仍过 LEGAL_TRANSITIONS,CAS 用 WHERE status=
    <当前值> 同 transition() 语义,不绕状态机。
    """
    from core import db

    to_status = vocab.PENDING

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "SELECT status FROM line_client_questions WHERE tenant_id = %s AND id = %s",
                (str(tenant_id), question_id),
            )
            row = cur.fetchone()
            if not row:
                raise ClientPoolError(f"question not found: {question_id}")
            current = row["status"]
            if not vocab.is_legal_transition(current, to_status):
                raise IllegalTransitionError(current, to_status)

            cur.execute(
                "UPDATE line_client_questions SET status = %s, batch_id = %s, batch_seq = %s, "
                "sent_at = now(), updated_at = now() "
                "WHERE tenant_id = %s AND id = %s AND status = %s "
                f"RETURNING {_COLUMNS}",
                (to_status, str(batch_id), int(batch_seq), str(tenant_id), question_id, current),
            )
            updated = cur.fetchone()
            if not updated:
                raise IllegalTransitionError(current, to_status)
            return dict(updated)

    return _with_heal(_run)
