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


def set_agent_token(user_id: str, endpoint_id: str) -> Optional[str]:
    """(重)生成 Agent token · 存 sha256 进 config.agent_token_hash · 明文只返一次。"""
    try:
        from core import db

        ep = db.get_erp_endpoint(user_id, endpoint_id)
        if not ep or (ep.get("adapter") or "") != "express":
            return None
        plaintext = f"exp_{endpoint_id}_{secrets.token_urlsafe(32)}"
        cfg = dict(ep.get("config") or {})
        cfg["agent_token_hash"] = hash_token(plaintext)
        if not db.update_erp_endpoint(user_id, endpoint_id, config=cfg):
            return None
        return plaintext
    except Exception as e:
        logger.error(f"set_agent_token failed: {e}")
        return None


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


_ACCOUNT_SET_KEYS = ("code", "name", "name_en", "tax_id", "path", "writable")
_MAX_ACCOUNT_SETS = 50


def _sanitize_account_sets(raw: Any) -> List[Dict[str, Any]]:
    """净化 Agent 上报的账套列表:只留已知键、限长限量,布尔归一(防被塞脏数据)。"""
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw[:_MAX_ACCOUNT_SETS]:
        if not isinstance(item, dict):
            continue
        clean: Dict[str, Any] = {}
        for k in _ACCOUNT_SET_KEYS:
            v = item.get(k)
            if k == "writable":
                clean[k] = bool(v)
            elif v is not None:
                clean[k] = str(v)[:200]
        if clean.get("code") or clean.get("name"):
            out.append(clean)
    return out


def store_account_sets(endpoint_id: str, account_sets: Any) -> int:
    """存 Agent 探测的可用账套列表进 config.reported_account_sets(供 FE「选账套」读)。

    净化后整体替换(非累加),并记 account_sets_seen_at。返回存入条数。隔离沿用现有约定:
    只更新本 express endpoint 自己的 config。
    """
    sets = _sanitize_account_sets(account_sets)
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            # 两个顶层键 → || 合并(create-or-replace),比嵌套 jsonb_set 平。
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = COALESCE(config, '{}'::jsonb) || jsonb_build_object(
                        'reported_account_sets', %s::jsonb,
                        'account_sets_seen_at', to_jsonb(NOW()::text))
                WHERE id = %s AND adapter = 'express'
                """,
                (json.dumps(sets, ensure_ascii=False), endpoint_id),
            )
        return len(sets)
    except Exception as e:
        logger.error(f"store_account_sets failed: {e}")
        return 0


# ── 科目表(chart of accounts)· 供 FE「科目映射」下拉按名字选 ──────────────────
# 小助手登录 Express 读科目 DBF(如 GLMAS)上报。科目表【可自定义·每账套不同】→ 必须按
# 账套发现,不能在程序里写死默认码(Owner 2026-06-22 拍板)。
_ACCOUNT_KEYS = ("code", "name", "type")
_MAX_ACCOUNTS = 3000


def _sanitize_accounts(raw: Any) -> List[Dict[str, Any]]:
    """净化 Agent 上报的科目表:只留 code/name/type、限长限量。code 必填(科目码=记账锚)。"""
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw[:_MAX_ACCOUNTS]:
        if not isinstance(item, dict):
            continue
        clean: Dict[str, Any] = {}
        for k in _ACCOUNT_KEYS:
            v = item.get(k)
            if v is not None and str(v).strip() != "":
                clean[k] = str(v).strip()[:120]
        if clean.get("code"):
            out.append(clean)
    return out


def store_reported_accounts(endpoint_id: str, accounts: Any) -> int:
    """存小助手探测的【科目表】进 config.reported_accounts(供 FE「科目映射」下拉读)。

    净化后整体替换 + 记 accounts_seen_at;返回存入条数。镜像 store_account_sets,只更新本
    express endpoint。客户在下拉里按【名字】选科目,FE 存科目【码】进 config(revenue_acc 等)。
    """
    accs = _sanitize_accounts(accounts)
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = COALESCE(config, '{}'::jsonb) || jsonb_build_object(
                        'reported_accounts', %s::jsonb,
                        'accounts_seen_at', to_jsonb(NOW()::text))
                WHERE id = %s AND adapter = 'express'
                """,
                (json.dumps(accs, ensure_ascii=False), endpoint_id),
            )
        return len(accs)
    except Exception as e:
        logger.error(f"store_reported_accounts failed: {e}")
        return 0


# 所选账套【整组】· 方法无关(直录/RPA 共用 · 见 11-dispatch 可扩展性契约 §1/§2/§5)。
# account_set 名(白名单)+ account_dir(DBF 写文件)+ account_company(公司名硬闸)
# + account_set_row(RPA 登录后公司 grid 行)。客户选一次整组都推出,RPA 来零新增字段。
_SELECTED_ACCOUNT_KEYS = ("account_set", "account_dir", "account_company", "account_set_row")


def _merge_config(endpoint_id: str, patch: Dict[str, Any]) -> bool:
    """把 patch 以 jsonb `||` 合并进本 express endpoint 的 config(顶层键 create-or-replace)。"""
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = COALESCE(config, '{}'::jsonb) || %s::jsonb
                WHERE id = %s AND adapter = 'express'
                """,
                (json.dumps(patch, ensure_ascii=False), endpoint_id),
            )
        return True
    except Exception as e:
        logger.error(f"_merge_config failed: {e}")
        return False


def _clean_selected(fields: Dict[str, Any]) -> Dict[str, Any]:
    """从上报 dict 取所选账套整组的非空字段(account_set_row 转 int)。"""
    sel: Dict[str, Any] = {}
    for k in _SELECTED_ACCOUNT_KEYS:
        v = (fields or {}).get(k)
        if k == "account_set_row":
            if v is not None and str(v).strip() != "":
                try:
                    sel[k] = int(v)
                except (TypeError, ValueError):
                    pass
        elif v is not None and str(v).strip() != "":
            sel[k] = str(v).strip()
    return sel


def selected_account_changed(current: Dict[str, Any], reported: Dict[str, Any]) -> bool:
    """上报的所选账套整组是否与已存 config 不同(防每拍无谓写库)。"""
    for k in _SELECTED_ACCOUNT_KEYS:
        if str((reported or {}).get(k) or "").strip() != str((current or {}).get(k) or "").strip():
            return True
    return False


def store_selected_account(endpoint_id: str, fields: Dict[str, Any]) -> bool:
    """存小助手上报的【所选账套整组】→ config(方法无关·不按 method 阉割)。

    账套选择唯一真相源 = 本地小助手(客户在那里选)。云端存整组、网页镜像账套名。
    只写上报到的非空字段;`account_set` 名缺失 → 整体跳过(没选不覆盖)。只更新本 express endpoint。
    """
    sel = _clean_selected(fields if isinstance(fields, dict) else {})
    if not sel.get("account_set"):
        return False
    return _merge_config(endpoint_id, sel)


def touch_heartbeat(endpoint_id: str) -> None:
    """更新 config.agent_last_seen_at = NOW(UTC)。"""
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = jsonb_set(
                        COALESCE(config, '{}'::jsonb),
                        '{agent_last_seen_at}', to_jsonb(NOW()::text), true)
                WHERE id = %s AND adapter = 'express'
                """,
                (endpoint_id,),
            )
    except Exception as e:
        logger.error(f"touch_heartbeat failed: {e}")


def lease_pending(endpoint_id: str, owner: str, max_n: int) -> List[Dict[str, Any]]:
    """领取该 endpoint 未被有效租约占用的 pending 日志(原子置租约)· 返回载荷列表。

    SKIP LOCKED + 租约到期可重领:Agent 崩溃后队列不卡死。owner 标识领取者。
    """
    n = max(1, min(int(max_n or 1), 50))
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                WITH due AS (
                    SELECT id FROM erp_push_logs
                    WHERE endpoint_id = %s AND status = 'pending'
                      AND (lease_owner IS NULL
                           OR lease_expires_at IS NULL
                           OR lease_expires_at < NOW())
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
        SELECT id, status, attempt, lease_owner, response_body
        FROM erp_push_logs
        WHERE id = %s AND endpoint_id = %s
        FOR UPDATE
        """,
        (log_id, endpoint_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def ack(
    endpoint_id: str,
    log_id: str,
    owner: str,
    success: bool,
    express_docnum: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Agent 回报一条领取结果。

    success → status='success' + response_body.express_docnum,清租约(终态幂等)。
    failed  → Agent 录入失败累计:第 1、2 次 → 回 pending 释放租约可重领;**满 3 次**
              (_MAX_ATTEMPTS)→ 'manual' 留人工。队列行起始 attempt=1(通用落库约定)= 0
              次失败,故按起始 1 校正阈值(否则 2 次就误转 manual)。
    校验 lease_owner 一致(防越权 ack 别人的租约)。
    """
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            log = _load_owned_log(cur, endpoint_id, log_id)
            if not log:
                return {"ok": False, "reason": "log_not_found"}
            # 终态幂等:已 success 的不再回退。
            if log["status"] == "success":
                return {"ok": True, "status": "success", "idempotent": True}
            if (log.get("lease_owner") or "") != owner:
                return {"ok": False, "reason": "lease_mismatch"}

            if success:
                body = json.dumps(
                    {"ok": True, "express_docnum": express_docnum}, ensure_ascii=False
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
                return {"ok": True, "status": "success", "express_docnum": express_docnum}

            # Express 队列行由通用落库约定起始 attempt=1(= 0 次 Agent 录入失败)。
            # 本次失败 = 第 `prior` 次 Agent 录入失败(prior=1→第1次 … prior=3→第3次);
            # 满 _MAX_ATTEMPTS(3) 次才转 manual,与 docstring 一致(off-by-one 修复)。
            # 起始按 1 兜底,既贴合现有写库约定,也对偶发 0 基线鲁棒。
            prior = int(log.get("attempt") or 1)
            agent_failures = prior
            new_attempt = prior + 1
            new_status = "manual" if agent_failures >= _MAX_ATTEMPTS else "pending"
            cur.execute(
                """
                UPDATE erp_push_logs
                SET status = %s, attempt = %s,
                    error_msg = %s,
                    lease_owner = NULL, lease_expires_at = NULL
                WHERE id = %s
                """,
                (new_status, new_attempt, (error or "")[:500] or "agent_failed", log_id),
            )
            return {
                "ok": True,
                "status": new_status,
                "attempt": new_attempt,
                "agent_failures": agent_failures,
            }
    except Exception as e:
        logger.error(f"ack failed: {e}")
        return {"ok": False, "reason": f"db_error: {type(e).__name__}"}
