# -*- coding: utf-8 -*-
"""Express 本地 Agent 出站拉取的数据访问层(token / heartbeat / lease / ack)。

铁律 #12:状态唯一源 = erp_push_logs。Agent 不直连库,只走 routes/erp_agent.py
的 Bearer token 接口,落到本模块的参数化 SQL。隔离沿用现有 ERP 模块约定
(per user_id · 不为 express 另搞 RLS):token 只能取本连接 endpoint 的队列。

token 形如 `exp_<endpoint_id>_<secret>`;库里只存 sha256(token)(明文仅生成时返回
一次)。校验时从 token 解出 endpoint_id → 取该 express endpoint → 比对 hash。
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_LEASE_SECONDS = 120
_MAX_ATTEMPTS = 3

# 「知道了,还是推」的载荷位(桥/小助手 writepath/duplicate_gate.CONFIRM_PARAM)。带这一位的
# 载荷会**关掉写侧的幂等闸**,所以它不能享受这个队列默认的 at-least-once:租约一过期就重投,
# 而一次真写是分钟级,重投等于账上再多一张。判真值取「有这个键且不是明摆着的假」——
# 宁可把不确定的也当成确认(至多一次是安全侧),也不能漏判一个真确认(那就是重复过账)。
_CONFIRMED = (
    "lower(coalesce(request_body->>'duplicate_confirmed', 'false')) "
    "NOT IN ('false', '0', '', 'null', 'no', 'off')"
)
# 租约过期没等到 ack 的确认推送:落人工 + 这个原因码(前端按码翻四语)。绝不能悄悄躺回
# pending —— 那既不重投也不告诉人,会计以为还在排队,而账套里可能已经多了一张。
REASON_CONFIRMED_UNACKED = "confirmed_push_unacked"


def hash_token(plaintext: str) -> str:
    return hashlib.sha256((plaintext or "").encode("utf-8")).hexdigest()


def get_express_endpoint(endpoint_id: str) -> Optional[Dict[str, Any]]:
    """按 id 取 express 连接(不带 user 作用域 · 给 Agent token 校验用)。"""
    if not endpoint_id:
        return None
    try:
        from core import db

        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, adapter, config, enabled, user_id
                FROM erp_endpoints
                WHERE id = %s AND adapter = 'express'
                LIMIT 1
                """,
                (endpoint_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_express_endpoint failed: {e}")
        return None


def set_agent_token(
    user_id: str, endpoint_id: str, reset: bool = False
) -> Optional[Dict[str, Any]]:
    """长效密钥模型(配一次长期有效 · 不再每次生成就作废已配对的小助手)。

    - 尚无密钥 / reset=True:铸新密钥 → 存 sha256 + 末 4 位(掩码显示)+ 生成时间;明文只返一次。
    - 已有密钥且非 reset:**绝不旋转**(否则在跑的小助手立刻 401),返回 status=exists + 掩码尾段。

    返回 {status: created|exists|none, token?, tail, created_at?}。reset=True 是危险动作:
    旧密钥作废,所有已配对电脑须重新配对(调用方须已二次确认)。
    """
    try:
        from core import db

        ep = db.get_erp_endpoint(user_id, endpoint_id)
        if not ep or (ep.get("adapter") or "") != "express":
            return None
        cfg = dict(ep.get("config") or {})
        if cfg.get("agent_token_hash") and not reset:
            return {"status": "exists", "tail": cfg.get("agent_token_tail", "")}
        plaintext = f"exp_{endpoint_id}_{secrets.token_urlsafe(32)}"
        cfg["agent_token_hash"] = hash_token(plaintext)
        cfg["agent_token_tail"] = plaintext[-4:]  # 掩码显示 PEX-••••-tail(非敏感)
        cfg["agent_token_created_at"] = _now_iso()
        if not db.update_erp_endpoint(user_id, endpoint_id, config=cfg):
            return None
        return {"status": "created", "token": plaintext, "tail": plaintext[-4:]}
    except Exception as e:
        logger.error(f"set_agent_token failed: {e}")
        return None


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def authenticate(token: str) -> Optional[Dict[str, Any]]:
    """校验 Bearer token → 返回 endpoint dict;失败返 None。常量时间比对防时序泄漏。"""
    if not token or not token.startswith("exp_"):
        return None
    parts = token.split("_", 2)
    if len(parts) != 3:
        return None
    endpoint_id = parts[1]
    ep = get_express_endpoint(endpoint_id)
    if not ep:
        return None
    stored = str((ep.get("config") or {}).get("agent_token_hash") or "")
    if not stored or not secrets.compare_digest(stored, hash_token(token)):
        return None
    return ep


# 心跳上报数据访问(账套/科目/所选/映射/在线)拆到 agent_reporting(单一职责+控行数)。
# 此处 re-export 保 routes/tests 的 agent_store.<fn> 调用契约不变。
from services.erp.express_push.agent_reporting import (  # noqa: E402,F401
    _sanitize_account_sets,
    _sanitize_accounts,
    _sanitize_catalog,
    mark_offline,
    selected_account_changed,
    store_account_sets,
    store_mapping,
    bump_stock_master_count,
    store_companion_version,
    store_max_payload_version,
    store_reported_accounts,
    store_reported_catalog,
    store_reported_stock_acc_groups,
    store_selected_account,
    touch_heartbeat,
)


def close_unacked_confirmed(cur, endpoint_id: str) -> int:
    """确认推送领走后没回 ack、租约已过期 → 落 manual 并如实说「可能写了也可能没写」。

    这是「至多一次」的收尾。这类行不能重投(见 _CONFIRMED),但也绝不能留在 pending 装作
    还在排队:桥/小助手那边可能已经写完只是 ack 丢了,也可能根本没开始写,系统分不出来 ——
    分不出来就得说分不出来,由会计去 Express 看一眼。返回被收尾的行数。
    """
    from services.erp.express_push import common as C
    from services.erp.express_push.enqueue import MANUAL_PREFIX

    cur.execute(
        f"""
        UPDATE erp_push_logs
        SET status = 'manual',
            error_msg = %s,
            response_body = jsonb_build_object(
                'ok', false,
                'express_docnum', NULL,
                'meta', jsonb_build_object(
                    'stage', %s,
                    'reason', %s,
                    'ref_no', invoice_no
                )
            )::text,
            lease_owner = NULL,
            lease_expires_at = NULL
        WHERE endpoint_id = %s AND status = 'pending' AND {_CONFIRMED}
          AND lease_owner IS NOT NULL
          AND (lease_expires_at IS NULL OR lease_expires_at < NOW())
        RETURNING id, history_id
        """,
        (
            f"{MANUAL_PREFIX}: {REASON_CONFIRMED_UNACKED}",
            C.STAGE_NEEDS_REVIEW,
            REASON_CONFIRMED_UNACKED,
            endpoint_id,
        ),
    )
    swept = cur.fetchall() or []
    history_ids = [r["history_id"] for r in swept if r.get("history_id")]
    if history_ids:
        # 单据记录那边同步落 manual —— 只改推送日志的话,记录页会一直显示"等待中",
        # 会计据此重推,而这张票的下场恰恰是"不知道推没推进去"。
        cur.execute(
            "UPDATE ocr_history SET last_push_status = 'manual', last_pushed_at = NOW() "
            "WHERE id = ANY(%s::uuid[])",
            ([str(h) for h in history_ids],),
        )
    if swept:
        logger.warning(
            "确认推送租约过期未 ack · 已落人工待核对: endpoint=%s n=%d",
            str(endpoint_id)[:8],
            len(swept),
        )
    return len(swept)


def lease_pending(endpoint_id: str, owner: str, max_n: int) -> List[Dict[str, Any]]:
    """领取该 endpoint 未被有效租约占用的 pending 日志(原子置租约)· 返回载荷列表。

    SKIP LOCKED + 租约到期可重领:Agent 崩溃后队列不卡死。owner 标识领取者。

    **带 duplicate_confirmed 的行例外,只领 lease_owner IS NULL 的**(至多一次)。默认的
    at-least-once 靠写侧 find_existing 幂等兜底,而这个键关掉的就是那道闸;租约 120s 而一次
    真写(备份→写 DBF→重建 CDX)是分钟级,照默认走就是「丢一次 ack 多一张」。已领走又超时的
    这类行由 close_unacked_confirmed 就地落 manual —— 不重投,也不装作还在排队。收尾单开一笔
    事务:PG 里一条语句报错整个事务就作废,把它并进领活那笔,收尾一出问题整条队列就停派。
    """
    n = max(1, min(int(max_n or 1), 50))
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            close_unacked_confirmed(cur, endpoint_id)
    except Exception as e:
        logger.error(f"close_unacked_confirmed failed: {e}")

    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                f"""
                WITH due AS (
                    SELECT id FROM erp_push_logs
                    WHERE endpoint_id = %s AND status = 'pending'
                      AND (lease_owner IS NULL
                           OR (NOT ({_CONFIRMED})
                               AND (lease_expires_at IS NULL
                                    OR lease_expires_at < NOW())))
                    ORDER BY created_at ASC
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE erp_push_logs l
                SET lease_owner = %s,
                    lease_expires_at = NOW() + (%s * INTERVAL '1 second')
                FROM due
                WHERE l.id = due.id
                RETURNING l.id, l.history_id, l.invoice_no, l.request_body,
                          l.lease_expires_at
                """,
                (endpoint_id, n, owner, _LEASE_SECONDS),
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"lease_pending failed: {e}")
        return []


def _load_owned_log(cur, endpoint_id: str, log_id: str) -> Optional[Dict[str, Any]]:
    cur.execute(
        """
        SELECT id, status, attempt, lease_owner, response_body, history_id
        FROM erp_push_logs
        WHERE id = %s AND endpoint_id = %s
        FOR UPDATE
        """,
        (log_id, endpoint_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def _build_response_body(
    *,
    ok: bool,
    stage: str,
    express_docnum: Optional[str],
    line_modes: Optional[List[Dict[str, Any]]],
    meta: Dict[str, Any],
) -> str:
    """统一构造 response_body(所有 outcome 都带 meta·诚实展示)。"""
    from services.erp.express_push import common as C

    body_obj: Dict[str, Any] = {"ok": ok, "express_docnum": express_docnum}
    if line_modes:
        body_obj["line_modes"] = line_modes
        fb = [m for m in line_modes if m.get("mode") == C.ITEM_MODE_DIRECT and m.get("reason")]
        if fb:
            body_obj["fallback_count"] = len(fb)
    m = dict(meta or {})
    m.setdefault("stage", stage)
    if line_modes and "created_masters" not in m:
        m["created_masters"] = [x["stkcod"] for x in line_modes if x.get("stkcod")]
    body_obj["meta"] = m
    return json.dumps(body_obj, ensure_ascii=False)


def _bump_created_stock_masters(
    endpoint_id: str, line_modes: Optional[List[Dict[str, Any]]]
) -> None:
    """本次推送真建出的库存主档数 → 就地加进指纹(见 bump_stock_master_count 的 why)。"""
    from services.erp.express_push import common as C

    n = sum(
        1
        for m in (line_modes or [])
        if isinstance(m, dict) and m.get("mode") == C.ITEM_MODE_STOCK and m.get("created")
    )
    if n:
        bump_stock_master_count(endpoint_id, n)


def _mirror_history_status(cur, log: Dict[str, Any], status: str) -> None:
    """把推送终态同步到 ocr_history.last_push_status。

    ack 原先只改 erp_push_logs,单据记录那边永远停在入队时写的 'pending' —— 实际早就
    成功了却显示"等待中",用户可能重推造成重复单;导出的状态列也会照抄这个假状态。
    只镜像终态(success/manual):还要重试的保持 pending 才是诚实的。
    同事务内更新,状态不会出现"日志成功但记录仍 pending"的中间态。
    """
    hid = log.get("history_id")
    if not hid:
        return
    try:
        cur.execute(
            """
            UPDATE ocr_history
            SET last_push_status = %s, last_pushed_at = NOW()
            WHERE id = %s
            """,
            (status, hid),
        )
    except Exception as e:  # noqa: BLE001 — 镜像失败不该回滚推送 ack 本身
        logger.warning(f"mirror history push status failed (hid={hid}): {e}")


def ack(
    endpoint_id: str,
    log_id: str,
    owner: str,
    success: bool,
    express_docnum: Optional[str] = None,
    error: Optional[str] = None,
    line_modes: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
    outcome: Optional[str] = None,
) -> Dict[str, Any]:
    """Agent 回报一条领取结果(V3:富元数据 + 细粒度 outcome)。

    outcome(可选·覆盖 success 布尔·旧客户端不传则按布尔)取值见 common.ACK_OUTCOMES:
      success      → status='success' + docnum,清租约(终态幂等)。
      waiting_lock → Express 占用账套:保持 pending、释放租约可重领、**不烧重试次数**(不算失败)。
      needs_mapping/needs_review → 立即 status='manual'(缺科目映射 / 对账失败·疑重),不重试。
      failed/rolled_back → Agent 失败累计:第 1、2 次回 pending 重领,满 _MAX_ATTEMPTS 转
                           'manual';rolled_back 仅多记"已恢复备份"诚实标(retry 逻辑同 failed)。
    富元数据(companion 版本/账套/写了哪些表/建客户商品/CDX 回查等)落 response_body.meta。
    校验 lease_owner 一致(防越权 ack 别人的租约)。status 列保持粗粒度,meta.stage 是其细化。
    """
    from services.erp.express_push import common as C

    eff = outcome if outcome in C.ACK_OUTCOMES else (C.STAGE_SUCCESS if success else C.STAGE_FAILED)
    clean_meta = C.sanitize_push_meta(meta)
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            log = _load_owned_log(cur, endpoint_id, log_id)
            if not log:
                return {"ok": False, "reason": "log_not_found"}
            if log["status"] == "success":  # 终态幂等
                return {"ok": True, "status": "success", "idempotent": True}
            if (log.get("lease_owner") or "") != owner:
                return {"ok": False, "reason": "lease_mismatch"}

            if eff == C.STAGE_SUCCESS:
                body = _build_response_body(
                    ok=True,
                    stage=C.STAGE_SUCCESS,
                    express_docnum=express_docnum,
                    line_modes=line_modes,
                    meta=clean_meta,
                )
                cur.execute(
                    """
                    UPDATE erp_push_logs
                    SET status = 'success', http_status = 200,
                        response_body = %s, error_msg = NULL,
                        lease_owner = NULL, lease_expires_at = NULL
                    WHERE id = %s
                    """,
                    (body, log_id),
                )
                _mirror_history_status(cur, log, "success")
                _bump_created_stock_masters(endpoint_id, line_modes)
                return {"ok": True, "status": "success", "express_docnum": express_docnum}

            if eff == C.STAGE_WAITING_LOCK:
                # Express 正占用账套 → 不算失败、不烧次数:保持 pending、放租约,稍后自动重领。
                body = _build_response_body(
                    ok=False,
                    stage=C.STAGE_WAITING_LOCK,
                    express_docnum=None,
                    line_modes=None,
                    meta=clean_meta,
                )
                cur.execute(
                    """
                    UPDATE erp_push_logs
                    SET status = 'pending', response_body = %s,
                        lease_owner = NULL, lease_expires_at = NULL
                    WHERE id = %s
                    """,
                    (body, log_id),
                )
                return {
                    "ok": True,
                    "status": "pending",
                    "stage": C.STAGE_WAITING_LOCK,
                    "retry": True,
                }

            if eff in (C.STAGE_NEEDS_MAPPING, C.STAGE_NEEDS_REVIEW):
                # 缺科目映射 / 对账失败·疑似重复 → 立即留人工(重试无益)。
                body = _build_response_body(
                    ok=False,
                    stage=eff,
                    express_docnum=None,
                    line_modes=None,
                    meta=clean_meta,
                )
                cur.execute(
                    """
                    UPDATE erp_push_logs
                    SET status = 'manual', response_body = %s, error_msg = %s,
                        lease_owner = NULL, lease_expires_at = NULL
                    WHERE id = %s
                    """,
                    (body, (error or "")[:500] or eff, log_id),
                )
                _mirror_history_status(cur, log, "manual")
                return {"ok": True, "status": "manual", "stage": eff}

            # failed / rolled_back:Agent 失败累计(off-by-one 见下),满 _MAX_ATTEMPTS 转 manual。
            prior = int(log.get("attempt") or 1)
            agent_failures = prior
            new_attempt = prior + 1
            new_status = "manual" if agent_failures >= _MAX_ATTEMPTS else "pending"
            body = _build_response_body(
                ok=False,
                stage=eff,
                express_docnum=None,
                line_modes=None,
                meta=clean_meta,
            )
            cur.execute(
                """
                UPDATE erp_push_logs
                SET status = %s, attempt = %s,
                    error_msg = %s, response_body = %s,
                    lease_owner = NULL, lease_expires_at = NULL
                WHERE id = %s
                """,
                (new_status, new_attempt, (error or "")[:500] or "agent_failed", body, log_id),
            )
            # 还能重试的保持 pending 不镜像 —— 那时它确实还在排队,写"失败"是撒谎
            if new_status == "manual":
                _mirror_history_status(cur, log, "manual")
            return {
                "ok": True,
                "status": new_status,
                "stage": eff,
                "attempt": new_attempt,
                "agent_failures": agent_failures,
            }
    except Exception as e:
        logger.error(f"ack failed: {e}")
        return {"ok": False, "reason": f"db_error: {type(e).__name__}"}
