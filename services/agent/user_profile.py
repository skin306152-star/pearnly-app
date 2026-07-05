# -*- coding: utf-8 -*-
"""用户画像 v1 + 昨日一句话摘要(W3-1/W3-2)——「星巴克 85」第二次不该再问类目。

画像 = 高频商家/高频类目 top5(近90天) + 近30天单量,来源 ocr_history,可见性与
列表同一事实源(owner_visibility_where·经 get_cursor_rls);昨日摘要 = 昨天(曼谷)
记账笔数+合计 + 提问次数(agent_turn_logs),确定性拼接零 LLM 成本。

缓存表 line_agent_profiles 每用户单行,TTL 内直接用,过期惰性重算(每用户最多
每 6 小时算一次,不给对话轮加固定查询开销)。任何故障一律回空串——画像层不许
挡对话主路(fail-open)。闸 agent_user_profile 由 bridge 把关,关 = 本模块不被调,
提示词逐字节不变。建表照 line_agent_anchors 范式(prod 无 alembic 钩子·首用自愈)。
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

TTL_HOURS = 6
_LOOKBACK_DAYS = 90

_TABLE = """
CREATE TABLE IF NOT EXISTS line_agent_profiles (
    tenant_id uuid NOT NULL,
    line_user_id text NOT NULL,
    profile jsonb NOT NULL,
    refreshed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, line_user_id)
)
"""

# created_at 存 UTC;"昨天"按曼谷本地日历日判(与 docs_overview 同口径)。
_BKK_DATE = "(created_at AT TIME ZONE 'Asia/Bangkok')::date"
_YDAY = f"{_BKK_DATE} = (now() AT TIME ZONE 'Asia/Bangkok')::date - 1"


def ensure_table() -> None:
    """幂等建 line_agent_profiles + RLS(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        apply_tenant_rls(cur, "line_agent_profiles")


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由调用方吞。"""
    try:
        return fn()
    except Exception as e:
        if "line_agent_profiles" not in str(e):
            raise
        ensure_table()
        return fn()


def _compute(user_id, tenant_id) -> dict:
    """从 ocr_history/agent_turn_logs 现算画像。查询全部卡时间下界,不做全表扫。"""
    from core import db
    from services.ocr_history import list_status as ls

    where, params = ls.owner_visibility_where(user_id, tenant_id, None, None)
    vis = " AND ".join(where)
    out = {"merchants": [], "categories": [], "docs_30d": 0, "y_docs": 0, "y_total": 0.0}
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
        cur.execute(
            f"SELECT seller_name, COUNT(*) AS c FROM ocr_history "
            f"WHERE {vis} AND created_at >= now() - make_interval(days => {_LOOKBACK_DAYS}) "
            f"AND COALESCE(seller_name, '') <> '' "
            f"GROUP BY seller_name ORDER BY c DESC LIMIT 5",
            params,
        )
        out["merchants"] = [r["seller_name"] for r in cur.fetchall()]
        cur.execute(
            f"SELECT category_tag, COUNT(*) AS c FROM ocr_history "
            f"WHERE {vis} AND created_at >= now() - make_interval(days => {_LOOKBACK_DAYS}) "
            f"AND COALESCE(category_tag, '') <> '' "
            f"GROUP BY category_tag ORDER BY c DESC LIMIT 5",
            params,
        )
        out["categories"] = [r["category_tag"] for r in cur.fetchall()]
        cur.execute(
            f"SELECT COUNT(*) FILTER (WHERE created_at >= now() - make_interval(days => 30)) "
            f"  AS d30, "
            f"COUNT(*) FILTER (WHERE {_YDAY}) AS yc, "
            f"COALESCE(SUM(total_amount) FILTER (WHERE {_YDAY}), 0) AS yt "
            f"FROM ocr_history "
            f"WHERE {vis} AND created_at >= now() - make_interval(days => 31)",
            params,
        )
        row = cur.fetchone()
        out["docs_30d"] = int(row["d30"])
        out["y_docs"] = int(row["yc"])
        out["y_total"] = float(row["yt"])
    return out


def _yesterday_queries(tenant_id, line_user_id) -> int:
    """昨日提问次数(intent=query_*)。turn_log 层故障不连坐画像主体。"""
    from core import db

    try:
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                f"SELECT COUNT(*) AS c FROM agent_turn_logs "
                f"WHERE tenant_id = %s AND line_user_id = %s "
                f"AND intent LIKE 'query%%' AND {_YDAY}",
                (str(tenant_id), str(line_user_id)),
            )
            return int(cur.fetchone()["c"])
    except Exception:
        return 0


def _load_cached(tenant_id, line_user_id):
    """读缓存行。返回 profile dict 或 None(无/过期)。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                "SELECT profile FROM line_agent_profiles "
                "WHERE tenant_id = %s AND line_user_id = %s "
                "AND refreshed_at > now() - make_interval(hours => %s)",
                (str(tenant_id), str(line_user_id), TTL_HOURS),
            )
            row = cur.fetchone()
        if not row:
            return None
        p = row.get("profile")
        return p if isinstance(p, dict) else json.loads(p or "{}")

    return _with_heal(_run)


def _store(tenant_id, line_user_id, profile: dict) -> None:
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO line_agent_profiles (tenant_id, line_user_id, profile) "
                "VALUES (%s, %s, %s::jsonb) "
                "ON CONFLICT (tenant_id, line_user_id) DO UPDATE "
                "SET profile = EXCLUDED.profile, refreshed_at = now()",
                (str(tenant_id), str(line_user_id), json.dumps(profile, ensure_ascii=False)),
            )

    _with_heal(_run)


def render(profile: dict) -> str:
    """画像 dict → 提示词块。全空(新用户)回空串不加噪音。只列有数据的行。"""
    if not profile or not (profile.get("docs_30d") or profile.get("merchants")):
        return ""
    lines = ["\n\n# User profile (from booking history; do not re-ask what is here):"]
    if profile.get("merchants"):
        lines.append("- Frequent merchants: " + ", ".join(profile["merchants"]))
    if profile.get("categories"):
        lines.append("- Frequent categories: " + ", ".join(profile["categories"]))
    lines.append(f"- Docs booked last 30 days: {profile.get('docs_30d', 0)}")
    if profile.get("y_docs"):
        lines.append(
            f"- Yesterday: booked {profile['y_docs']} docs, ฿{profile['y_total']:,.2f} total"
        )
    if profile.get("y_queries"):
        lines.append(f"- Yesterday: asked {profile['y_queries']} balance/summary questions")
    return "\n".join(lines)


def context_note(user_id, tenant_id, line_user_id) -> str:
    """对话轮入口:取(缓存或现算)画像 → 渲染提示词块。任何故障回空串。"""
    if not (user_id and tenant_id and line_user_id):
        return ""
    try:
        profile = _load_cached(tenant_id, line_user_id)
        if profile is None:
            profile = _compute(user_id, tenant_id)
            profile["y_queries"] = _yesterday_queries(tenant_id, line_user_id)
            _store(tenant_id, line_user_id, profile)
        return render(profile)
    except Exception:
        logger.warning("[user_profile] note failed; empty", exc_info=True)
        return ""
