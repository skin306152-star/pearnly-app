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
_COMPLETE_KEYS = (
    "cars",
    "place_books",
    "term_sales",
    "branches",
    "regis_behalfs",
    "advisors",
    "company_banks",
    "source_banks",
    "cheque_banks",
    "cashier_banks",
    "card_banks",
)

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
def _fetch_masters_via_login(
    endpoint: Dict[str, Any], *, require_complete: bool = False
) -> Optional[Dict[str, Any]]:
    """登录 DMS 抓全量主档;登录/抓取失败(_run_logged_in 回 _err dict)→ None。

    配了独立管理员凭据组的租户走管理员会话读(app 侧销售账号常看不到车型/银行全表);
    管理员登录失败 → ERR_DMS_ADMIN_AUTH 落成 None 由调用方 fail closed,不静默退回销售。"""
    from services.erp.erp_dms_intake import _run_logged_in

    def _fetch(client, adapter):
        from services.erp.mrerp_dms_company_banks import fetch_payment_bank_masters

        return {
            **client.fetch_masters(strict=require_complete),
            **fetch_payment_bank_masters(adapter, client=client),
        }

    res = _run_logged_in(endpoint, _fetch, authoritative_read=True)
    if isinstance(res, dict) and res.get("ok") is False:
        return None
    return res


def _fetch_paints_via_login(endpoint: Dict[str, Any], car_id: str) -> Optional[List[list]]:
    """登录 DMS 抓某车型的颜色(翻页取全 —— 只取第一页会漏掉第 2 页起的颜色);失败 → None。

    同理走管理员会话读:颜色主档在销售账号下可能被裁成空表,空表会被误判成「这车没颜色」。"""
    from services.erp.erp_dms_intake import _run_logged_in

    res = _run_logged_in(
        endpoint,
        lambda cl, ad: cl._bshsd_all("txtcarpaint", idcar=car_id),
        authoritative_read=True,
    )
    if isinstance(res, dict):
        return None
    return res


# ── 对外:主档 / 颜色 ────────────────────────────────────────────────────
def get_masters(
    endpoint: Dict[str, Any], *, force_refresh: bool = False, require_complete: bool = False
) -> Dict[str, Any]:
    """主档:缓存 <12h 直接回;过期/缺失 → 登录抓全量 + 落缓存。

    普通读取登录失败时回退陈旧缓存(状态诚实优先于报错),都没有则空 dict；强制刷新失败
    则直接返回空 dict，避免把旧主档冒充实时数据。普通刷新保留已惰性缓存的
    paints_by_car，强制刷新则按 DMS 现状清掉旧颜色缓存。
    force_refresh 给「刚在 DMS 改了主档、马上要按新数据判」的调用方(如顾问匹配失败重判)——
    必须真抓:成功时按 DMS 现状落库(旧 paints_by_car 不合并回去,否则 DMS 新增/删除的
    颜色被旧色遮住),失败时返回空 dict(fail closed,不拿旧主档冒充刷新过)。"""
    eid = str(endpoint.get("id") or "")
    cached = None if force_refresh else _read(eid)
    cache_usable = cached and all(key in cached["masters"] for key in _COMPLETE_KEYS)
    if require_complete and cache_usable:
        cache_usable = all(isinstance(cached["masters"].get(key), list) for key in _COMPLETE_KEYS)
    if not force_refresh and cache_usable and cached["age_seconds"] < CACHE_TTL_SECONDS:
        return cached["masters"]
    fresh = (
        _fetch_masters_via_login(endpoint, require_complete=True)
        if require_complete
        else _fetch_masters_via_login(endpoint)
    )
    if fresh is None:
        if force_refresh:
            return {}
        return cached["masters"] if cached else {}
    if not force_refresh and cached:
        # 普通过期刷新才保留惰性颜色缓存;force_refresh 按 DMS 现状重判,旧色不合并。
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
    endpoint: Dict[str, Any],
    car_id: str,
    masters: Optional[Dict[str, Any]] = None,
    *,
    require_complete: bool = False,
    force_refresh: bool = False,
) -> List[list]:
    """某车型的颜色主档(惰性)。已缓存直接回;否则登录抓 + 并入 paints_by_car 落缓存。

    传入 masters(调用方同请求已读的 blob)则复用之,省一次 _read。"""
    eid = str(endpoint.get("id") or "")
    car_id = str(car_id or "")
    if masters is None:
        cached = _read(eid)
        masters = (cached["masters"] if cached else {}) or {}
    pbc = dict(masters.get("paints_by_car") or {})
    if car_id in pbc and not force_refresh:
        return pbc[car_id]
    paints = _fetch_paints_via_login(endpoint, car_id)
    if paints is None:
        if require_complete:
            from services.erp.mrerp_dms_client_base import DMSClientError

            raise DMSClientError(
                f"DMS paint master unavailable for car {car_id!r}",
                "ERR_DMS_MASTER_UNAVAILABLE",
            )
        return []
    pbc[car_id] = paints
    _write(eid, {**masters, "paints_by_car": pbc})
    return paints


# 银行类目录的键(与 mrerp_dms_company_banks.PAYMENT_BANK_MASTERS 同集)。
_BANK_KEYS = ("company_banks", "source_banks", "cheque_banks", "cashier_banks", "card_banks")


def write_authoritative_snapshot(
    endpoint: Dict[str, Any],
    masters: Dict[str, Any],
    *,
    car_id: str = "",
    paints: Optional[List[list]] = None,
) -> None:
    """用**本次权威只读复核已取到的**快照落缓存 —— 成功后再二次登录/抓取一律不做。

    旧路径在订车成功后拿手上的会话再抓一次全量主档:销售会话那一抓会把管理员的完整缓存
    覆盖成销售裁剪视图(车型/银行看起来变空),还白付一轮远程读取。这里只吃调用方已经在
    提交前抓过的权威行:
      · masters 整份来自同一次权威会话(管理员视图),直接覆盖主档;
      · paints 是选中车型的颜色:None = 这次没读到(该车型旧条目原样保留),
        [] = 权威结论「这车已无颜色」→ 必须清掉该车型旧颜色;其它车型的旧条目保留;
      · 银行类目录以本次快照为准(空表 = DMS 已删光,不许被旧值盖回去);只有该 key
        在这次 masters 里根本没有(这次没读这一类目录)才退回旧值。
    """
    eid = str(endpoint.get("id") or "")
    if not eid or not masters:
        return
    cached = _read(eid)
    old = (cached or {}).get("masters") or {}
    merged = dict(masters)
    pbc = dict(old.get("paints_by_car") or {})
    # None 才是「没读到」;[] 是权威读取成功的空表 = DMS 里颜色被删光,必须落成空表
    # (falsy 判断会把旧颜色留在缓存里,和「增删必须实时映射」冲突)。
    if paints is not None and car_id:
        pbc[str(car_id)] = list(paints)
    # 只要这次真读了某车型颜色(含 [])或本来就有其它车型的颜色,就把 paints_by_car 写进去:
    # 用 `if pbc:` 会让「刚清空的最后一条」在下次写入时被旧缓存合并回来。
    if pbc or (paints is not None and car_id):
        merged["paints_by_car"] = pbc
    for key in _BANK_KEYS:
        # 只认「key 不在这次快照里」;存在且为 [] 是权威删除结果,
        # 用 falsy 判断会把管理员刚删掉的银行从旧缓存恢复回来。
        if key not in merged and old.get(key):
            merged[key] = old[key]
    _write(eid, merged)
