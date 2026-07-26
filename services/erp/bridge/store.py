# -*- coding: utf-8 -*-
"""ERP 桥 DAL:桥身份 / 写桥唯一闸 / 云端问-桥答的任务信箱。

桥装在客户内网、主动外拨连云端,云端永不回连(内网不开洞)。与小助手 companion 那条
接缝零共享通道:独立表、独立密钥前缀 `brg_`、独立路由前缀 /api/erp/bridge/。

隔离两层:每条 SQL 都显式带 tenant_id / bridge_id 过滤(应用层为主),两表另 enroll
tenant RLS 作第二道防线。密钥所级 —— 一个租户配一次全所会计继承,库里只存 sha256,
明文只在铸造时返一次。

建表与首用自愈在同包 schema.py(prod 不跑 alembic,0087 只留档)。
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
from typing import Any, Dict, Iterable, List, Optional

from services.erp.bridge import BridgeRejected, write_gate
from services.erp.bridge.schema import BRIDGES, JOBS, heal

logger = logging.getLogger(__name__)

TOKEN_PREFIX = "brg_"
# 任务租约:桥领走 60s 内没 ack 就退回队列(桥崩溃不卡死队列)。写活的放宽版在 write_gate。
LEASE_SECONDS = 60
# 在线判据:心跳 60s 一拍,连丢 3 拍才算掉线 —— 写桥唯一闸据此决定要不要让位。
ONLINE_WINDOW_SECONDS = 180
# 排队任务寿命:门面默认只等 20s,超过这个点结果没人要了,别再派给桥白跑一趟。
JOB_TTL_SECONDS = 120
RESULT_MAX_BYTES = 2 * 1024 * 1024
BOOKS_MAX = 200
ROLES = ("read", "write")

_UUID_RE = re.compile(r"^[0-9a-fA-F-]{32,40}$")
_BOOK_KEYS = ("book_id", "dir", "company", "taxid")


def hash_secret(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def normalize_role(role: Any) -> str:
    r = str(role or "read").strip().lower()
    return r if r in ROLES else "read"


def sanitize_books(books: Any) -> List[Dict[str, Any]]:
    """只留协议字段 + 必须有 book_id + 封顶 —— 桥上报的是外部输入,不原样落库。"""
    out: List[Dict[str, Any]] = []
    for item in books if isinstance(books, list) else []:
        if not isinstance(item, dict):
            continue
        book_id = str(item.get("book_id") or "").strip()[:64]
        if not book_id:
            continue
        clean = {"book_id": book_id}
        for key in _BOOK_KEYS[1:]:
            val = item.get(key)
            if val not in (None, ""):
                clean[key] = str(val)[:200]
        out.append(clean)
        if len(out) >= BOOKS_MAX:
            break
    return out


def book_ids(books: Any) -> set:
    return {b["book_id"] for b in sanitize_books(books)}


def assert_book_allowed(bridge: Dict[str, Any], book_id: Optional[str]) -> None:
    """book_id 必须在该桥 hello 上报的清单内 —— 桥只被授权读它真看得见的账套。"""
    if book_id in (None, ""):
        return
    if str(book_id) not in book_ids(bridge.get("books")):
        raise BridgeRejected(
            f"book_id 不在桥上报的账套清单内: {book_id}", "bridge.book_not_reported"
        )


# ── 桥身份 ────────────────────────────────────────────────────────────────


def mint_bridge(tenant_id: str, name: str, role: str = "read") -> Dict[str, str]:
    """铸所级密钥(明文只返一次)· effective_role 起步恒 read,等 hello 过唯一闸才升写。"""
    from core import db

    want = normalize_role(role)

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                f"INSERT INTO {BRIDGES} (tenant_id, name, secret_hash, role, effective_role) "
                "VALUES (%s, %s, '', %s, 'read') RETURNING id",
                (str(tenant_id), (str(name or "").strip() or "bridge")[:60], want),
            )
            bridge_id = str(cur.fetchone()["id"])
            token = f"{TOKEN_PREFIX}{bridge_id}_{secrets.token_urlsafe(32)}"
            cur.execute(
                f"UPDATE {BRIDGES} SET secret_hash = %s WHERE id = %s AND tenant_id = %s",
                (hash_secret(token), bridge_id, str(tenant_id)),
            )
            return {"bridge_id": bridge_id, "token": token, "tail": token[-4:], "role": want}

    return heal(_run)


def authenticate(token: str) -> Optional[Dict[str, Any]]:
    """Bearer brg_<bridge_id>_<secret> → 桥行;失败返 None。常量时间比对防时序泄漏。

    这一步还不知道 tenant(要靠桥行才查得到),故走 owner 连接按主键取单行,
    再用 sha256 比对定身份 —— 后续每条 SQL 都带上这里拿到的 tenant_id。
    """
    if not token or not token.startswith(TOKEN_PREFIX):
        return None
    parts = token.split("_", 2)
    if len(parts) != 3 or not _UUID_RE.match(parts[1]):
        return None
    row = _get_bridge_by_id(parts[1])
    if not row:
        return None
    stored = str(row.get("secret_hash") or "")
    if not stored or not secrets.compare_digest(stored, hash_secret(token)):
        return None
    return row


def _get_bridge_by_id(bridge_id: str) -> Optional[Dict[str, Any]]:
    from core import db

    def _run():
        with db.get_cursor() as cur:
            cur.execute(f"SELECT * FROM {BRIDGES} WHERE id = %s LIMIT 1", (bridge_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    return heal(_run)


def list_bridges(tenant_id: str) -> List[Dict[str, Any]]:
    """列本租户的桥(不含密钥哈希)· 在线判据与写桥唯一闸同源。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                f"SELECT id, name, role, effective_role, books, bridge_version, host, "
                f"last_seen_at, created_at, "
                f"(last_seen_at > now() - make_interval(secs => %s)) AS online "
                f"FROM {BRIDGES} WHERE tenant_id = %s ORDER BY created_at",
                (ONLINE_WINDOW_SECONDS, str(tenant_id)),
            )
            return [dict(r) for r in (cur.fetchall() or [])]

    return heal(_run)


def _write_holder(cur, tenant_id: str, self_id: str, wanted: set) -> Optional[Dict[str, Any]]:
    """同租户里,是否已有别的在线写桥占着 wanted 里任一账套。"""
    cur.execute(
        f"SELECT id, name, books FROM {BRIDGES} "
        "WHERE tenant_id = %s AND id <> %s AND effective_role = 'write' "
        "AND last_seen_at > now() - make_interval(secs => %s)",
        (tenant_id, self_id, ONLINE_WINDOW_SECONDS),
    )
    for row in cur.fetchall() or []:
        if wanted & book_ids(row.get("books")):
            return dict(row)
    return None


def register_hello(
    bridge: Dict[str, Any],
    *,
    role: str,
    books: Any,
    bridge_version: Optional[str] = None,
    host: Optional[str] = None,
) -> Dict[str, Any]:
    """注册 + 心跳:落账套镜像/版本/host/last_seen,并当场判 effective_role。

    写桥唯一闸:同一账套同一时刻只允许一个 write 桥在线,已有在线写桥时后来者降为 read。
    先对本租户桥行 FOR UPDATE 上锁把同租户的 hello 串起来 —— 否则两个写桥同时问"有人占
    了吗"都答没有,双写就漏进来了(桥数量按所计,锁开销可以忽略)。
    """
    from core import db

    tenant_id = str(bridge["tenant_id"])
    self_id = str(bridge["id"])
    clean = sanitize_books(books)
    want = normalize_role(role)

    def _run():
        with db.get_cursor_rls(tenant_id, commit=True) as cur:
            cur.execute(
                f"SELECT id FROM {BRIDGES} WHERE tenant_id = %s ORDER BY id FOR UPDATE",
                (tenant_id,),
            )
            holder = (
                _write_holder(cur, tenant_id, self_id, {b["book_id"] for b in clean})
                if want == "write"
                else None
            )
            effective = "read" if holder else want
            cur.execute(
                f"UPDATE {BRIDGES} SET role = %s, effective_role = %s, books = %s, "
                "bridge_version = %s, host = %s, last_seen_at = now() "
                "WHERE id = %s AND tenant_id = %s",
                (
                    want,
                    effective,
                    json.dumps(clean, ensure_ascii=False),
                    (str(bridge_version)[:40] if bridge_version else None),
                    (str(host)[:120] if host else None),
                    self_id,
                    tenant_id,
                ),
            )
            return {"effective_role": effective, "books": len(clean), "held_by": holder}

    return heal(_run)


# ── 任务信箱 ──────────────────────────────────────────────────────────────


def enqueue_job(
    bridge: Dict[str, Any], kind: str, payload: Dict[str, Any], book_id: Optional[str] = None
) -> str:
    """入队一条任务 · kind 过白名单+写角色闸(write_gate),book_id 必须在桥上报清单内。"""
    from core import db

    write_gate.assert_enqueue_allowed(bridge, kind)
    assert_book_allowed(bridge, book_id)
    tenant_id = str(bridge["tenant_id"])

    def _run():
        with db.get_cursor_rls(tenant_id, commit=True) as cur:
            cur.execute(
                f"INSERT INTO {JOBS} (tenant_id, bridge_id, book_id, kind, payload) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (
                    tenant_id,
                    str(bridge["id"]),
                    (str(book_id) if book_id else None),
                    kind,
                    json.dumps(payload or {}, ensure_ascii=False),
                ),
            )
            return str(cur.fetchone()["id"])

    return heal(_run)


def lease_jobs(bridge: Dict[str, Any], max_n: int = 1) -> List[Dict[str, Any]]:
    """领任务(置租约:query 60s / write 300s)· 只领本桥的、book_id 仍在其上报清单内的。

    同一事务里先做两件自愈:租约过期的退回队列(桥崩溃过),超龄的落 expired
    (门面早不等了;写活超龄放宽到 600s,见 write_gate)。派活用 SKIP LOCKED,
    多进程同时 lease 不会重复派同一条;可领 kind 按生效角色现算(降级兜底)。
    """
    from core import db

    tenant_id = str(bridge["tenant_id"])
    bid = str(bridge["id"])
    allowed = sorted(book_ids(bridge.get("books")))
    kinds = write_gate.leasable_kinds(bridge)
    n = max(1, min(int(max_n or 1), 10))

    def _run():
        with db.get_cursor_rls(tenant_id, commit=True) as cur:
            cur.execute(
                f"UPDATE {JOBS} SET status = 'queued', lease_owner = NULL, lease_expires_at = NULL "
                "WHERE bridge_id = %s AND status = 'leased' AND lease_expires_at < now()",
                (bid,),
            )
            cur.execute(
                f"UPDATE {JOBS} SET status = 'expired', finished_at = now() "
                "WHERE bridge_id = %s AND status = 'queued' AND created_at < now() "
                "- make_interval(secs => CASE WHEN kind = 'write' THEN %s ELSE %s END)",
                (bid, write_gate.WRITE_JOB_TTL_SECONDS, JOB_TTL_SECONDS),
            )
            cur.execute(
                f"""
                WITH due AS (
                    SELECT id FROM {JOBS}
                    WHERE bridge_id = %s AND status = 'queued'
                      AND (book_id IS NULL OR book_id = ANY(%s::text[]))
                      AND kind = ANY(%s::text[])
                    ORDER BY created_at
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE {JOBS} j
                SET status = 'leased', lease_owner = %s,
                    lease_expires_at = now() + make_interval(
                        secs => CASE WHEN j.kind = 'write' THEN %s ELSE %s END)
                FROM due
                WHERE j.id = due.id
                RETURNING j.id, j.kind, j.book_id, j.payload
                """,
                (bid, allowed, kinds, n, bid, write_gate.WRITE_LEASE_SECONDS, LEASE_SECONDS),
            )
            return [dict(r) for r in (cur.fetchall() or [])]

    return heal(_run)


def clamp_result(result: Any) -> tuple:
    """结果体积封顶 2MB:先按实测字节均摊砍 rows,砍不动就只留元信息。返回 (json, truncated)。"""
    payload = dict(result) if isinstance(result, dict) else {"value": result}
    blob = json.dumps(payload, ensure_ascii=False)
    size = len(blob.encode("utf-8"))
    if size <= RESULT_MAX_BYTES:
        return blob, False
    rows = payload.get("rows")
    if isinstance(rows, list) and rows:
        keep = max(1, int(len(rows) * RESULT_MAX_BYTES * 0.9 / size))
        trimmed = {**payload, "rows": rows[:keep], "truncated": True, "rows_total": len(rows)}
        blob = json.dumps(trimmed, ensure_ascii=False)
        if len(blob.encode("utf-8")) <= RESULT_MAX_BYTES:
            return blob, True
    meta = {"truncated": True, "original_bytes": size}
    if isinstance(rows, list):
        meta["rows_total"] = len(rows)
    return json.dumps(meta, ensure_ascii=False), True


def finish_job(
    bridge: Dict[str, Any],
    job_id: str,
    ok: bool,
    result: Any = None,
    error: Any = None,
) -> Dict[str, Any]:
    """桥回结果 → 落 done/failed 唤醒等待方。只有持租约的本桥能回(防越权 ack)。"""
    from core import db

    if not _UUID_RE.match(str(job_id or "")):
        return {"ok": False, "reason": "job_not_found"}
    tenant_id = str(bridge["tenant_id"])
    bid = str(bridge["id"])
    status = "done" if ok else "failed"
    result_json, truncated = clamp_result(result) if ok else (None, False)
    error_json = None if ok else json.dumps(_clean_error(error), ensure_ascii=False)

    def _run():
        with db.get_cursor_rls(tenant_id, commit=True) as cur:
            cur.execute(
                f"UPDATE {JOBS} SET status = %s, result = %s, error = %s, finished_at = now(), "
                "lease_owner = NULL, lease_expires_at = NULL "
                "WHERE id = %s AND bridge_id = %s AND status = 'leased' AND lease_owner = %s",
                (status, result_json, error_json, str(job_id), bid, bid),
            )
            if cur.rowcount == 1:
                return {"ok": True, "status": status, "truncated": truncated}
            cur.execute(
                f"SELECT status, kind FROM {JOBS} WHERE id = %s AND bridge_id = %s",
                (str(job_id), bid),
            )
            row = cur.fetchone()
            if not row:
                return {"ok": False, "reason": "job_not_found"}
            # 任务已 expired(租约被回收后超龄扫尾),桥这才回来 —— 收下不报错,如实标 stale。
            # 写活的迟到结果必须落库:单据可能已真实进了账套,丢掉 ack 就丢了 docnum,
            # 改票号重推的 prior_docnum 防重链会断在这单;状态保持 expired 如实记「没人等到」。
            out = {"ok": True, "status": str(row["status"]), "stale": True}
            if str(row.get("kind") or "") == write_gate.KIND_WRITE and out["status"] == "expired":
                cur.execute(
                    f"UPDATE {JOBS} SET result = %s, error = %s, finished_at = now() "
                    "WHERE id = %s AND bridge_id = %s AND status = 'expired'",
                    (result_json, error_json, str(job_id), bid),
                )
                out["result_saved"] = cur.rowcount == 1
            return out

    return heal(_run)


def _clean_error(error: Any) -> Dict[str, str]:
    src = error if isinstance(error, dict) else {}
    return {
        "code": str(src.get("code") or "bridge.failed")[:64],
        "message": str(src.get("message") or (error if isinstance(error, str) else ""))[:500],
    }


def get_job(tenant_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    from core import db

    if not _UUID_RE.match(str(job_id or "")):
        return None

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                f"SELECT id, status, result, error, book_id, kind FROM {JOBS} "
                "WHERE id = %s AND tenant_id = %s",
                (str(job_id), str(tenant_id)),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    return heal(_run)


def expire_job(tenant_id: str, job_id: str) -> bool:
    """门面等不到了 → 把还没终态的任务落 expired(结果回来也没人要,别让桥白跑)。

    已被领走(leased)的写活不动:桥此刻多半正在备份+写盘+重建索引,落 expired 会造出
    「账套里已有单、云端却记失败」,docnum 随桥的 ack 一起被丢。让它留在 leased,
    桥写完照常 ack 落 done/failed;等待方超时只代表「不再等」,不代表写没发生。
    彻底失联的写活由 lease_jobs 的回收+超龄扫尾兜底(queued 后按 WRITE_JOB_TTL 落 expired)。
    """
    from core import db

    if not _UUID_RE.match(str(job_id or "")):
        return False

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                f"UPDATE {JOBS} SET status = 'expired', finished_at = now() "
                "WHERE id = %s AND tenant_id = %s "
                "AND (status = 'queued' OR (status = 'leased' AND kind <> 'write'))",
                (str(job_id), str(tenant_id)),
            )
            return cur.rowcount == 1

    return heal(_run)


def pick_bridge(tenant_id: str, book_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """挑一个能接这个账套的在线桥:写桥优先(它是主),再按最近心跳。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                f"SELECT * FROM {BRIDGES} WHERE tenant_id = %s "
                "AND last_seen_at > now() - make_interval(secs => %s) "
                "ORDER BY (effective_role = 'write') DESC, last_seen_at DESC",
                (str(tenant_id), ONLINE_WINDOW_SECONDS),
            )
            rows = [dict(r) for r in (cur.fetchall() or [])]
        return _first_with_book(rows, book_id)

    return heal(_run)


def _first_with_book(rows: Iterable[Dict[str, Any]], book_id: Optional[str]):
    for row in rows:
        if not book_id or str(book_id) in book_ids(row.get("books")):
            return row
    return None
