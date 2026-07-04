# -*- coding: utf-8 -*-
"""影子双跑落库:B 档(2.5-lite)发票钱字段 vs 3.5 后台复核的逐字段比对结果。
只存数字与 match 布尔(不重复存图·复用已存原图),量 B 真错率 + 现有闸抓取率。
建表照 line_agent_anchors 范式(prod 无 alembic 钩子 → 首用 ensure 幂等自愈)+ 租户 RLS。"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_TABLE = """
CREATE TABLE IF NOT EXISTS shadow_money_log (
    id bigserial PRIMARY KEY,
    tenant_id uuid NOT NULL,
    history_id text NOT NULL,
    b_total numeric, s_total numeric, total_match boolean,
    b_vat numeric, s_vat numeric, vat_match boolean,
    b_discount numeric, s_discount numeric, discount_match boolean,
    b_subtotal numeric, s_subtotal numeric, subtotal_match boolean,
    match_all boolean,
    b_confidence text,
    status text NOT NULL DEFAULT 'ok',
    created_at timestamptz NOT NULL DEFAULT now()
)
"""
_INDEX = "CREATE INDEX IF NOT EXISTS idx_shadow_money_created ON shadow_money_log (created_at)"

# 逐字段列名(short → 三列 b_/s_/_match),insert 与 aggregate 共用一份顺序。
_FIELDS = ("total", "vat", "discount", "subtotal")


def ensure_table() -> None:
    """幂等建 shadow_money_log + 索引 + RLS(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        cur.execute(_INDEX)
        apply_tenant_rls(cur, "shadow_money_log")


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由调用方吞。"""
    try:
        return fn()
    except Exception as e:
        if "shadow_money_log" not in str(e):
            raise
        ensure_table()
        return fn()


def insert(tenant_id, history_id, *, values, matches, match_all, b_confidence, status="ok") -> None:
    """写一行比对结果。values={field:(b,s)} · matches={field:bool|None}。
    故障吞掉——影子层绝不反噬主路径(存不上只是少一个采样点)。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO shadow_money_log "
                "(tenant_id, history_id, b_total, s_total, total_match, "
                " b_vat, s_vat, vat_match, b_discount, s_discount, discount_match, "
                " b_subtotal, s_subtotal, subtotal_match, match_all, b_confidence, status) "
                "VALUES (%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s)",
                (
                    str(tenant_id),
                    str(history_id),
                    values["total"][0],
                    values["total"][1],
                    matches["total"],
                    values["vat"][0],
                    values["vat"][1],
                    matches["vat"],
                    values["discount"][0],
                    values["discount"][1],
                    matches["discount"],
                    values["subtotal"][0],
                    values["subtotal"][1],
                    matches["subtotal"],
                    match_all,
                    b_confidence,
                    status,
                ),
            )

    try:
        _with_heal(_run)
    except Exception:
        logger.warning("[shadow_money] write failed; dropped", exc_info=True)


def aggregate(days: int = 30) -> dict:
    """近 N 天全局读数(admin 引擎页):跑 N 张 · 不一致 M 张 · 不一致率。
    owner 游标跨租户全量(超管视角);只算 status=ok(失败行无有效比对)。"""
    from core import db

    out = {"total": 0, "mismatches": 0, "rate": 0.0, "days": int(days)}

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total, "
                "COUNT(CASE WHEN match_all IS FALSE THEN 1 END) AS mism "
                "FROM shadow_money_log "
                "WHERE status = 'ok' AND created_at >= NOW() - make_interval(days => %s)",
                (int(days),),
            )
            return cur.fetchone() or {}

    try:
        r = _with_heal(_run)
        total = int(r.get("total") or 0)
        mism = int(r.get("mism") or 0)
        out.update(total=total, mismatches=mism, rate=(mism / total if total else 0.0))
    except Exception:
        logger.warning("[shadow_money] aggregate failed", exc_info=True)
    return out
