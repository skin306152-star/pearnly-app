# -*- coding: utf-8 -*-
"""LINE webhook 事件幂等 + 处理状态机(claim → mark_done / mark_failed)。

LINE 在投递失败/超时后会重投同一事件(redelivery),而文本直录没有消息级幂等 →
同一句「กาแฟ 50」可能被记两笔。每个事件带全局唯一 webhookEventId → 落一张小表,
INSERT ON CONFLICT DO NOTHING 原子抢占。

口径仍是 at-most-once:钱路上重复入账比丢一条消息伤害大(没回复用户会重发,双记账
用户不知道)。但原来「先标记后处理」把处理失败的事件也钉成了已处理:handler 抛异常
→ 行已在表里 → 重投永远被拦 → 消息静默消失,连查都无从查起。故拆三段:claim 占坑
(status='processing')→ 成功 mark_done → 失败 mark_failed(留 last_error + 原始事件
48h 供人工排查,路由据此回一句「请重发」)。

failed 行不自动重跑:handler 可能已经部分写库(建单/扣费/入账),机器重放 = 重复入账;
让用户重发才对——重发是新 webhookEventId,天然干净的一次。唯一的自动补跑是 processing
超时残留(进程被 kill / 部署重启,handler 没跑完就没了),且只补一次,见 claim。

无 event_id 的老格式放行;表故障 fail-open 放行——去重是增强不是闸,绝不许挡正常消息。
prod 无 alembic 钩子 → ensure_table 启动幂等建表 + 补列(alembic 0046/0099 留档)。
"""

from __future__ import annotations

import json
import logging
import random

logger = logging.getLogger(__name__)

TTL_HOURS = 48  # LINE redelivery 窗口远短于此;采样清老行,表恒小
_CLEAN_PROB = 0.02  # 清理采样率:webhook 最热路径,别每个事件都为"几乎总删空"的 DELETE 买单
_STALE_MINUTES = 10  # processing 超过此值 = 进程崩了(正常事件处理有 ~20s 预算,差两个量级)
_MAX_ATTEMPTS = 2  # 崩溃残留只补跑一次:再崩就是稳定崩,重跑只是重复烧钱
_MAX_ERROR_CHARS = 2000
_MAX_PAYLOAD_CHARS = 8000

CLAIM_FRESH = "fresh"  # 首见,该处理
CLAIM_RECLAIM = "reclaim"  # 崩溃残留,补跑一次
CLAIM_SKIP = "skip"  # 已处理完 / 正在处理 / 已失败待人工 —— 一律不碰

_TABLE = """
CREATE TABLE IF NOT EXISTS line_webhook_events (
    event_id text PRIMARY KEY,
    received_at timestamptz NOT NULL DEFAULT now()
)
"""

# status DEFAULT 'done' 是有意的:建列前落下的存量行都是「已经处理过」的语义,ALTER 就地
# 把它们钉成 done,不会因为多了状态列而被当成待处理重跑一遍。
_ADD_COLUMNS = (
    "ALTER TABLE line_webhook_events ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'done'",
    "ALTER TABLE line_webhook_events ADD COLUMN IF NOT EXISTS source text",
    "ALTER TABLE line_webhook_events ADD COLUMN IF NOT EXISTS attempts int NOT NULL DEFAULT 1",
    "ALTER TABLE line_webhook_events ADD COLUMN IF NOT EXISTS last_error text",
    "ALTER TABLE line_webhook_events ADD COLUMN IF NOT EXISTS payload jsonb",
    "ALTER TABLE line_webhook_events ADD COLUMN IF NOT EXISTS updated_at timestamptz",
)

_CLAIM_SQL = (
    "INSERT INTO line_webhook_events (event_id, status, source, attempts, updated_at) "
    "VALUES (%s, 'processing', %s, 1, now()) ON CONFLICT (event_id) DO NOTHING"
)

# 抢占条件全写进 WHERE(不是先 SELECT 再判):并发两投只有一个 UPDATE 得到行,另一个
# rowcount=0 → skip,不会两边同时开跑。done/failed 状态不在谓词内 = 永不被自动重跑。
_RECLAIM_SQL = (
    "UPDATE line_webhook_events SET attempts = attempts + 1, updated_at = now() "
    "WHERE event_id = %s AND status = 'processing' AND attempts < %s "
    "AND updated_at < now() - make_interval(mins => %s) RETURNING event_id"
)

_DONE_SQL = (
    "UPDATE line_webhook_events SET status = 'done', payload = NULL, last_error = NULL, "
    "updated_at = now() WHERE event_id = %s"
)

_FAILED_SQL = (
    "UPDATE line_webhook_events SET status = 'failed', last_error = %s, payload = %s::jsonb, "
    "updated_at = now() WHERE event_id = %s"
)

_CLEANUP_SQL = (
    "DELETE FROM line_webhook_events WHERE received_at < now() - make_interval(hours => %s)"
)


def ensure_table() -> None:
    """幂等建 line_webhook_events + 补状态列(startup 调)。非租户表(webhook 早于身份解析)→
    RLS 显式 DISABLE 钉死,防托管库给新表自动开 RLS 裸成 deny-all 孤儿。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        for stmt in _ADD_COLUMNS:
            cur.execute(stmt)
        cur.execute("ALTER TABLE line_webhook_events DISABLE ROW LEVEL SECURITY")


def claim(event_id, source: str | None = None) -> str:
    """占坑取处理权:CLAIM_FRESH(首见)/ CLAIM_RECLAIM(崩溃残留补跑)/ CLAIM_SKIP(别碰)。

    无 id 或表故障 → CLAIM_FRESH 放行(宁可重复处理,不许误吞)。
    """
    eid = str(event_id or "").strip()
    if not eid:
        return CLAIM_FRESH
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(_CLAIM_SQL, (eid, source))
            if cur.rowcount > 0:
                if random.random() < _CLEAN_PROB:
                    cur.execute(_CLEANUP_SQL, (TTL_HOURS,))
                return CLAIM_FRESH
            cur.execute(_RECLAIM_SQL, (eid, _MAX_ATTEMPTS, _STALE_MINUTES))
            return CLAIM_RECLAIM if cur.rowcount > 0 else CLAIM_SKIP
    except Exception:
        logger.warning("[line webhook] dedup claim failed; processing anyway", exc_info=True)
        return CLAIM_FRESH


def mark_done(event_id) -> None:
    """处理成功 → 钉成 done(此后重投必被拦)。顺手清 payload:消息内容没有留存的理由。"""
    eid = str(event_id or "").strip()
    if eid:
        _write(_DONE_SQL, (eid,), "mark_done")


def mark_failed(event_id, error, payload=None) -> None:
    """处理失败 → 留证据(last_error + 原始事件)48h 供人工排查或手工重放。

    刻意不改回可重跑状态:handler 可能已部分写库,机器重放 = 重复入账。可重投的路是让
    用户重发(新 event_id),由路由负责回执告知。
    """
    eid = str(event_id or "").strip()
    if eid:
        params = (str(error)[:_MAX_ERROR_CHARS], _dump_payload(payload), eid)
        _write(_FAILED_SQL, params, "mark_failed")


def _write(sql: str, params: tuple, what: str) -> None:
    """状态写入:失败只 log。事件已经在出错路径上了,记账簿写不进去不该再掀翻路由。"""
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(sql, params)
    except Exception:
        logger.warning("[line webhook] dedup %s failed", what, exc_info=True)


def _dump_payload(payload) -> str | None:
    """事件转 jsonb 文本。截断的 JSON 不再是合法 jsonb,超长就整体换成带片段的包装对象。"""
    if payload is None:
        return None
    try:
        text = json.dumps(payload, ensure_ascii=False)
    except Exception:
        return None
    if len(text) > _MAX_PAYLOAD_CHARS:
        return json.dumps(
            {"truncated": True, "head": text[:_MAX_PAYLOAD_CHARS]}, ensure_ascii=False
        )
    return text
