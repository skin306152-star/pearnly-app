# -*- coding: utf-8 -*-
"""ERP 桥的同步门面:调用方只用这里,不碰 bridge_jobs / erp_bridges 两张表。

query() 把一次"问内网"包成同步调用 —— 入队 → 轮询 → 拿结果 / 抛 BridgeTimeout。
调用方看到的就是一个会阻塞几百毫秒的普通函数;async 路由里请 await asyncio.to_thread
包一层(psycopg2 是同步的,直接调会卡住事件循环)。

参数白名单在这里执行:云端下发给内网的 payload 只允许协议内字段,形状不对当场拒,
不给桥"收到什么就照做"的机会(桥侧还会再校一次表名形状 + 目录白名单)。
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional

from services.erp.bridge import (
    BridgeFailed,
    BridgeRejected,
    BridgeTimeout,
    BridgeUnavailable,
)
from services.erp.bridge import store

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 20.0
# 轮询间隔:桥答一次通常在百毫秒级,250ms 让 p50 只多等半拍,一次 20s 等待也才 80 次
# 主键查询 —— 比给 bridge_jobs 加 LISTEN/NOTIFY 那套的复杂度划算得多。
POLL_INTERVAL = 0.25

OPS = ("books", "tables", "rows")
_OP_PARAMS = {
    "books": (),
    "tables": ("q", "limit", "offset"),
    "rows": ("table", "filters", "q", "date_field", "from", "to", "limit", "offset"),
}
_REQUIRED = {"rows": ("table",)}

_IDENT_RE = re.compile(r"^[A-Za-z0-9_]{1,32}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LIMIT_MAX = 5000
_OFFSET_MAX = 1_000_000
_FILTER_KEYS_MAX = 32


def build_query_payload(op: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """协议白名单:只放行本 op 允许的字段且形状对得上,其余一律拒。"""
    if op not in OPS:
        raise BridgeRejected(f"未知 op: {op}", "bridge.bad_op")
    allowed = _OP_PARAMS[op]
    given = {k: v for k, v in (params or {}).items() if v is not None}
    stray = set(given) - set(allowed)
    if stray:
        raise BridgeRejected(f"op={op} 不接受字段: {sorted(stray)}", "bridge.bad_param")
    missing = [k for k in _REQUIRED.get(op, ()) if not given.get(k)]
    if missing:
        raise BridgeRejected(f"op={op} 缺必填字段: {missing}", "bridge.bad_param")
    payload: Dict[str, Any] = {"op": op}
    for key, value in given.items():
        payload[key] = _coerce(key, value)
    return payload


def _coerce(key: str, value: Any) -> Any:
    if key in ("table", "date_field"):
        text = str(value).strip()
        if not _IDENT_RE.match(text):
            raise BridgeRejected(f"{key} 形状非法: {value!r}", "bridge.bad_param")
        return text
    if key in ("from", "to"):
        text = str(value).strip()
        if not _DATE_RE.match(text):
            raise BridgeRejected(f"{key} 须为 YYYY-MM-DD: {value!r}", "bridge.bad_param")
        return text
    if key == "q":
        return str(value)[:128]
    if key == "limit":
        return max(1, min(_int(key, value), _LIMIT_MAX))
    if key == "offset":
        return max(0, min(_int(key, value), _OFFSET_MAX))
    if key == "filters":
        return _clean_filters(value)
    raise BridgeRejected(f"未知字段: {key}", "bridge.bad_param")


def _int(key: str, value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise BridgeRejected(f"{key} 须为整数: {value!r}", "bridge.bad_param") from None


def _clean_filters(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise BridgeRejected("filters 须为对象", "bridge.bad_param")
    if len(value) > _FILTER_KEYS_MAX:
        raise BridgeRejected("filters 字段过多", "bridge.bad_param")
    out: Dict[str, Any] = {}
    for key, val in value.items():
        if not _IDENT_RE.match(str(key)):
            raise BridgeRejected(f"filters 字段名非法: {key!r}", "bridge.bad_param")
        if val is not None and not isinstance(val, (str, int, float, bool)):
            raise BridgeRejected(f"filters.{key} 只接受标量", "bridge.bad_param")
        out[str(key)] = val[:200] if isinstance(val, str) else val
    return out


def query(
    tenant_id: str,
    book_id: Optional[str],
    op: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    **params: Any,
) -> Dict[str, Any]:
    """问内网一句话,等它答。超时抛 BridgeTimeout(同时把任务落 expired)。"""
    payload = build_query_payload(op, params)
    bridge = store.pick_bridge(tenant_id, book_id)
    if not bridge:
        raise BridgeUnavailable(f"该账套当前没有在线的桥: {book_id}")
    store.assert_book_allowed(bridge, book_id)
    job_id = store.enqueue_job(bridge, "query", payload, book_id=book_id)
    return _await_job(str(tenant_id), job_id, timeout)


def _await_job(tenant_id: str, job_id: str, timeout: float) -> Dict[str, Any]:
    deadline = time.monotonic() + max(0.5, float(timeout))
    while True:
        job = store.get_job(tenant_id, job_id) or {}
        status = str(job.get("status") or "")
        if status == "done":
            return job.get("result") or {}
        if status == "failed":
            err = job.get("error") or {}
            raise BridgeFailed(str(err.get("message") or ""), str(err.get("code") or ""))
        if status == "expired":
            raise BridgeTimeout(f"任务已过期: {job_id}")
        if time.monotonic() >= deadline:
            store.expire_job(tenant_id, job_id)
            raise BridgeTimeout(f"等桥回结果超时({timeout:g}s): {job_id}")
        time.sleep(POLL_INTERVAL)


def list_books(tenant_id: str) -> List[Dict[str, Any]]:
    """读端点镜像里的账套清单(不入队)· 同一 book_id 被多桥上报时只留一份。"""
    seen: Dict[str, Dict[str, Any]] = {}
    for bridge in store.list_bridges(tenant_id):
        if not bridge.get("online"):
            continue
        for book in store.sanitize_books(bridge.get("books")):
            seen.setdefault(book["book_id"], {**book, "bridge_id": str(bridge["id"])})
    return sorted(seen.values(), key=lambda b: b["book_id"])


def bridge_status(tenant_id: str) -> Dict[str, Any]:
    """桥连通状态(不入队)· 给设置页和调用方做四态展示。"""
    bridges = store.list_bridges(tenant_id)
    online = [b for b in bridges if b.get("online")]
    return {
        "configured": bool(bridges),
        "online": bool(online),
        "bridges": [
            {
                "bridge_id": str(b["id"]),
                "name": b.get("name"),
                "role": b.get("role"),
                "effective_role": b.get("effective_role"),
                "online": bool(b.get("online")),
                "bridge_version": b.get("bridge_version"),
                "host": b.get("host"),
                "last_seen_at": b.get("last_seen_at"),
                "books": len(store.sanitize_books(b.get("books"))),
            }
            for b in bridges
        ],
        "writer": next(
            (str(b["id"]) for b in online if b.get("effective_role") == "write"),
            None,
        ),
    }
