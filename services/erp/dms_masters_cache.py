# -*- coding: utf-8 -*-
"""DMS 下拉主档(顾问/车型/颜色…)缓存(DL-4a)· 通道无关。

每次登录 DMS 抓全量太贵 → 缓存 <12h 直接复用。paints 依赖 car,惰性按 car_id 存进同一
jsonb 的 paints_by_car 键。写库走 owner 连接(endpoint_id 非租户键,不施 RLS);登录抓取
复用 erp_dms_intake 的会话范式(_run_logged_in,失败即回退,绝不抛)。表首用 ensure 自愈
(prod 无 alembic 钩子,照 line_dms/store 范式)。

LINE 逐问的取数薄壳(qa_endpoint / qa_masters / qa_paints)在 services/line_dms/masters_cache.py
—— 那是通道相关的一层,本模块只管缓存本身。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 12 * 3600
_TABLE = "dms_masters_cache"

_DDL = """
CREATE TABLE IF NOT EXISTS dms_masters_cache (
    endpoint_id text PRIMARY KEY,
    masters jsonb NOT NULL,
    refreshed_at timestamptz NOT NULL
)
"""


def ensure_table() -> None:
    """幂等建表(首用自愈调)。endpoint_id 非租户键 → 不施 RLS。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(_DDL)


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛。"""
    try:
        return fn()
    except Exception as e:
        if _TABLE not in str(e):
            raise
        ensure_table()
        return fn()


# ── 缓存读写 ─────────────────────────────────────────────────────────────
def _read(endpoint_id: str) -> Optional[Dict[str, Any]]:
    """读缓存行 → {"masters": dict, "age_seconds": float};缺失/异常 → None(视为 miss)。"""
    from core import db

    if not endpoint_id:
        return None

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT masters, EXTRACT(EPOCH FROM (now() - refreshed_at)) AS age "
                "FROM dms_masters_cache WHERE endpoint_id = %s",
                (endpoint_id,),
            )
            return cur.fetchone()

    try:
        row = _with_heal(_run)
    except Exception:
        logger.warning("[dms masters] read failed; treat as miss", exc_info=True)
        return None
    if not row:
        return None
    masters = row.get("masters")
    if not isinstance(masters, dict):
        masters = json.loads(masters or "{}")
    return {"masters": masters, "age_seconds": float(row.get("age") or 0)}


def _write(endpoint_id: str, masters: Dict[str, Any]) -> None:
    from core import db

    if not endpoint_id:
        return

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO dms_masters_cache (endpoint_id, masters, refreshed_at) "
                "VALUES (%s, %s::jsonb, now()) "
                "ON CONFLICT (endpoint_id) DO UPDATE SET "
                "  masters = EXCLUDED.masters, refreshed_at = EXCLUDED.refreshed_at",
                (endpoint_id, json.dumps(masters or {}, ensure_ascii=False)),
            )

    try:
        _with_heal(_run)
    except Exception:
        logger.warning("[dms masters] write failed", exc_info=True)


# ── 登录抓取(失败即软回退) ──────────────────────────────────────────────
def _fetch_masters_via_login(endpoint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """登录 DMS 抓全量主档;登录/抓取失败(_run_logged_in 回 _err dict)→ None。"""
    from services.erp.erp_dms_intake import _run_logged_in

    res = _run_logged_in(endpoint, lambda cl, ad: cl.fetch_masters())
    if isinstance(res, dict) and res.get("ok") is False:
        return None
    return res


def _fetch_paints_via_login(endpoint: Dict[str, Any], car_id: str) -> Optional[List[list]]:
    """登录 DMS 抓某车型的颜色;失败 → None(登录失败回 _err dict,取数失败 _bshsd 自己回 None)。"""
    from services.erp.erp_dms_intake import _run_logged_in

    res = _run_logged_in(endpoint, lambda cl, ad: cl._bshsd("txtcarpaint", idcar=car_id))
    if isinstance(res, dict):
        return None
    return res


# ── 对外:主档 / 颜色 ────────────────────────────────────────────────────
def get_masters(endpoint: Dict[str, Any], *, force_refresh: bool = False) -> Dict[str, Any]:
    """主档:缓存 <12h 直接回;过期/缺失 → 登录抓全量 + 落缓存。

    登录失败时回退陈旧缓存(状态诚实优先于报错),都没有则空 dict。全量刷新保留已惰性
    缓存的 paints_by_car(避免每次刷主档就丢颜色缓存)。
    force_refresh 给「刚在 DMS 改了主档、马上要按新数据判」的调用方(如顾问匹配失败重判),
    否则那句「改完再试一次」在 12 小时内都是假的。"""
    eid = str(endpoint.get("id") or "")
    cached = _read(eid)
    if not force_refresh and cached and cached["age_seconds"] < CACHE_TTL_SECONDS:
        return cached["masters"]
    fresh = _fetch_masters_via_login(endpoint)
    if fresh is None:
        return cached["masters"] if cached else {}
    if cached:
        pbc = (cached["masters"] or {}).get("paints_by_car")
        if pbc:
            fresh = {**fresh, "paints_by_car": pbc}
    _write(eid, fresh)
    return fresh


def read_fresh_masters(endpoint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """只读缓存主档(<12h),绝不触发登录冷抓。miss / 过期 → None。

    submit 校验用:能被提交的选项必来自 data/paints 端点已暖的缓存,请求内再冷抓 = 多余的
    二次登录 → 宁可 None 让调用方重开选车流程。"""
    cached = _read(str(endpoint.get("id") or ""))
    if cached and cached["age_seconds"] < CACHE_TTL_SECONDS:
        return cached["masters"]
    return None


def get_paints(
    endpoint: Dict[str, Any], car_id: str, masters: Optional[Dict[str, Any]] = None
) -> List[list]:
    """某车型的颜色主档(惰性)。已缓存直接回;否则登录抓 + 并入 paints_by_car 落缓存。

    传入 masters(调用方同请求已读的 blob)则复用之,省一次 _read。"""
    eid = str(endpoint.get("id") or "")
    car_id = str(car_id or "")
    if masters is None:
        cached = _read(eid)
        masters = (cached["masters"] if cached else {}) or {}
    pbc = dict(masters.get("paints_by_car") or {})
    if car_id in pbc:
        return pbc[car_id]
    paints = _fetch_paints_via_login(endpoint, car_id)
    if paints is None:
        return []
    pbc[car_id] = paints
    _write(eid, {**masters, "paints_by_car": pbc})
    return paints


def refresh_from_client(endpoint: Dict[str, Any], client: Any) -> None:
    """订车成功后就地全量刷主档(会话已活,零额外登录)。保留 paints_by_car。"""
    try:
        masters = client.fetch_masters()
    except Exception:
        logger.warning("[dms masters] live refresh failed", exc_info=True)
        return
    eid = str(endpoint.get("id") or "")
    cached = _read(eid)
    if cached:
        pbc = (cached["masters"] or {}).get("paints_by_car")
        if pbc:
            masters = {**masters, "paints_by_car": pbc}
    _write(eid, masters)
