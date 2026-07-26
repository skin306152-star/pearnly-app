# -*- coding: utf-8 -*-
"""ERP 桥的同步门面:调用方只用这里,不碰 bridge_jobs / erp_bridges 两张表。

query() 把一次"问内网"包成同步调用 —— 入队 → 轮询 → 拿结果 / 抛 BridgeTimeout。
调用方看到的就是一个会阻塞几百毫秒的普通函数;async 路由里请 await asyncio.to_thread
包一层(psycopg2 是同步的,直接调会卡住事件循环)。

写路走 submit_write()(投单即返 job_id)+ write_status()(查进度)—— 写活在桥端是
分钟级,同步等不现实;阻塞版 write() 只给测试脚本用。

参数白名单在这里执行:云端下发给内网的 payload 只允许协议内字段,形状不对当场拒,
不给桥"收到什么就照做"的机会(桥侧还会再校一次表名形状 + 目录白名单)。
"""

from __future__ import annotations

import logging
import re
import time
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from services.erp.bridge import (
    BridgeFailed,
    BridgeRejected,
    BridgeTimeout,
    BridgeUnavailable,
)
from services.erp.bridge import store, write_gate
from services.erp.express_push.common import PAYLOAD_VERSION
from services.erp.express_push.doctypes import WRITE_SPECS

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 20.0
# 写活阻塞等待默认 = 排队上限 + 一整个写租约 + 余量:桥端备份+写+CDX 重建跨 SMB 是
# 分钟级,等待窗小于「排队 + 租约」就会在桥还在正常干活时放弃。放弃虽已无害
# (超时只 expire 还没被领走的活,见 store.expire_job),默认值仍须罩住整个合法在途窗。
WRITE_TIMEOUT = float(write_gate.WRITE_JOB_TTL_SECONDS + write_gate.WRITE_LEASE_SECONDS + 30)
# 轮询间隔:桥答一次通常在百毫秒级,250ms 让 p50 只多等半拍,一次 20s 等待也才 80 次
# 主键查询 —— 比给 bridge_jobs 加 LISTEN/NOTIFY 那套的复杂度划算得多。
POLL_INTERVAL = 0.25

# direction → 合法 doctype(契约=express_push mapper/sales_mapper 模块头,逐字):
# 采购 RR(赊购)/HP(现购);销售 IV(赊销)/HS(现销)。
# 会计手录的四类单据(收款 RE / 付款 PS / 手工凭证 GL / 库存调整 OU)不进这张表:
# 它们的形状各不相同(只有手工凭证有 lines),逐类校验在 express_push.doctypes 的
# check_payload 里,这里按 direction 分派。两条路的 direction 不重叠。
_WRITE_DOCTYPES = {"purchase": ("RR", "HP"), "sales": ("IV", "HS")}

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
    # 超时的 expire 只对「还没被领走的活 + 在途查询」生效:在途写活桥可能正写着账套,
    # store.expire_job 会跳过它,结果稍后仍由桥 ack 落库(拿 write_status 对账)。
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


def build_write_payload(payload: Any, book_id: Optional[str]) -> Dict[str, Any]:
    """写载荷轻校验:形状不对当场拒;深校验(科目存在/幂等/主档)在桥端。

    契约与 express_push mapper / doctypes 产物一字不差 —— 云端只把"根本不是一张单"的
    挡下:版本、方向/票种、账套一致、逐类恒等式(借贷平、金额可解析、日期合法)。
    未知 direction 一律拒(桥端"收到什么就照做"的口不能开)。
    """
    if not isinstance(payload, dict):
        raise BridgeRejected("写载荷须为对象", "bridge.bad_payload")
    if payload.get("payload_version") != PAYLOAD_VERSION:
        raise BridgeRejected(
            f"payload_version 不符(须为 {PAYLOAD_VERSION}): {payload.get('payload_version')!r}",
            "bridge.bad_payload",
        )
    direction = payload.get("direction")
    spec = WRITE_SPECS.get(direction)
    doctypes = (spec.doctype,) if spec else _WRITE_DOCTYPES.get(direction)
    if not doctypes:
        raise BridgeRejected(f"direction 非法: {direction!r}", "bridge.bad_payload")
    if payload.get("doctype") not in doctypes:
        raise BridgeRejected(
            f"doctype 与 direction={direction} 不匹配: {payload.get('doctype')!r}",
            "bridge.bad_payload",
        )
    account_set = str(payload.get("account_set") or "").strip()
    if not account_set:
        raise BridgeRejected("account_set 必填", "bridge.bad_payload")
    if book_id is None or account_set != str(book_id):
        raise BridgeRejected(
            f"account_set 与 book_id 不一致: {account_set!r} != {book_id!r}",
            "bridge.bad_payload",
        )
    if spec:
        # 四类手录单据里只有手工凭证带 lines(其余三类的科目要到目标账套查主档才解得出),
        # 各自的恒等式在 doctypes 各模块里,别在这儿铺第二份。
        err = spec.check(payload)
        if err:
            raise BridgeRejected(err, "bridge.bad_payload")
        return payload
    _assert_lines_balanced(payload.get("lines"))
    return payload


def _assert_lines_balanced(lines: Any) -> None:
    """复式分录形状:每行 {acc,side,amount} · 金额可解析成 Decimal · 借贷两侧和相等。"""
    if not isinstance(lines, list) or not lines:
        raise BridgeRejected("lines 须为非空数组", "bridge.bad_payload")
    sums = {"D": Decimal("0"), "C": Decimal("0")}
    for i, line in enumerate(lines):
        if not isinstance(line, dict) or not str(line.get("acc") or "").strip():
            raise BridgeRejected(f"lines[{i}] 缺科目 acc", "bridge.bad_payload")
        side = line.get("side")
        if side not in sums:
            raise BridgeRejected(f"lines[{i}].side 须为 D/C: {side!r}", "bridge.bad_payload")
        try:
            sums[side] += Decimal(str(line.get("amount")))
        except InvalidOperation:
            raise BridgeRejected(
                f"lines[{i}].amount 解析不了: {line.get('amount')!r}", "bridge.bad_payload"
            ) from None
    if sums["D"] != sums["C"]:
        raise BridgeRejected(f"借贷不平: D={sums['D']} C={sums['C']}", "bridge.bad_payload")


def submit_write(tenant_id: str, book_id: str, payload: Dict[str, Any]) -> str:
    """投写活 · 返 job_id 不阻塞。写角色闸在 enqueue(write_gate),这里挑桥+校形状。"""
    body = build_write_payload(payload, book_id)
    bridge = write_gate.pick_write_bridge(tenant_id, book_id)
    return store.enqueue_job(bridge, "write", body, book_id=book_id)


def write_status(tenant_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """写活进度:{job_id,status,result,error};查无此单(或非本租户)返 None。"""
    job = store.get_job(tenant_id, job_id)
    if not job:
        return None
    return {
        "job_id": str(job["id"]),
        "status": job.get("status"),
        "result": job.get("result"),
        "error": job.get("error"),
    }


def write(
    tenant_id: str, book_id: str, payload: Dict[str, Any], *, timeout: float = WRITE_TIMEOUT
) -> Dict[str, Any]:
    """阻塞便捷封装(测试脚本用)· 等到终态,超时抛 BridgeTimeout。

    超时 ≠ 没写进去:任务已被桥领走时不落 expired(桥可能正写账套,写完照常 ack 落
    done/failed);只有还没被领走的活会落 expired。拿到 BridgeTimeout 后用
    write_status 对账,别直接当失败重录。
    """
    job_id = submit_write(tenant_id, book_id, payload)
    return _await_job(str(tenant_id), job_id, timeout)


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
