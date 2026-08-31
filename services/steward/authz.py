# -*- coding: utf-8 -*-
"""管家写工具授权闸(B3 · confirm-first)—— 写操作必须人批,批文一次性、短时效、绑参数。

令牌复用平台通用 action nonce 表（mint/consume 原子消费）:
  ① 铸卡 open_request:任务停在 waiting_user,卡上带 token + 工具 + 参数快照;
  ② 决断 decide:批准/拒绝各消费一次 token(双击/重放第二次拿不到),批文落回任务
     payload.authorization,任务据此复跑或收 cancelled;
  ③ 执行闸 execution_error:tools.run 逐次校验批文 —— 工具名 + 参数指纹逐字对上才放行,
     写工具没批文物理拒,不是靠前端不显示按钮。

参数指纹是「批的就是执行的」的落点:铸卡时对 (tool, args) 做 SHA-256 定格进 token ref,批准时
与现参数重算比对,执行时再比一次 —— 铸卡后动过参数旧令牌即失效(同 push_confirm 的金额快照)。

审计走 services/audit/store.insert_operation_log(操作日志唯一落点,fail-open 不阻断主流程):
谁在什么时候批/拒了哪条任务的哪个工具,含参数指纹与 token 前缀(不落完整 token —— 它是凭证)。
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from services.steward import copy, registry, store

logger = logging.getLogger(__name__)

REF_KIND = "steward_write"

# 批文过期(分钟)。授权卡是"看一眼就点"的语境,5 分钟外的卡视为人已走开,重新发起。
_DEFAULT_TTL_MINUTES = 5

# 批准复跑后给 worker 的认领窗(秒):approve 把任务放回 running 但 created_at 是旧值,不续
# 租约会被 heal_stale 的「排队超时限」当场误杀。口径同 worker.STALE_GRACE_S(不 import,成环)。
_RESUME_GRACE_S = 60

ERR_AUTHZ_REQUIRED = "steward.authz_required"
ERR_AUTHZ_MISMATCH = "steward.authz_mismatch"
ERR_AUTHZ_EXPIRED = "steward.authz_expired"
ERR_AUTHZ_USED = "steward.authz_used"
ERR_AUTHZ_STALE = "steward.authz_stale"
ERR_AUTHZ_REJECTED = "steward.authz_rejected"
ERR_NOT_FOUND = "steward.not_found"

AUDIT_APPROVED = "steward.authz_approved"
AUDIT_REJECTED = "steward.authz_rejected"


def ttl_minutes() -> int:
    """批文时效(env STEWARD_AUTHZ_TTL_MIN 可配,默认 5 分钟)。"""
    try:
        value = int(os.environ.get("STEWARD_AUTHZ_TTL_MIN", "") or _DEFAULT_TTL_MINUTES)
    except ValueError:
        value = _DEFAULT_TTL_MINUTES
    return max(1, value)


def args_fingerprint(tool: str, args: Optional[dict]) -> str:
    """(工具, 参数) 的确定性指纹。键排序 + 紧凑分隔,同一份参数任何序列化路径都得同一指纹。"""
    canon = json.dumps(
        {"tool": tool, "args": args or {}},
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def execution_error(
    spec: Optional[registry.StewardTool], grant, *, tool: str, args: dict
) -> Optional[str]:
    """执行层物理闸(tools.run 逐次调):写工具必须持已批准、且盖着当前参数指纹的批文。
    返回错误码 = 拒;None = 放行。只读工具永远放行 —— 闸只加在会落数据的路上。"""
    if spec is None or not registry.requires_authorization(spec):
        return None
    if not isinstance(grant, dict) or grant.get("status") != store.AUTH_APPROVED:
        return ERR_AUTHZ_REQUIRED
    if grant.get("tool") != tool or grant.get("args_fp") != args_fingerprint(tool, args):
        return ERR_AUTHZ_MISMATCH
    return None


def open_request(
    cur,
    *,
    tenant_id: str,
    task_id: str,
    tool: str,
    args: dict,
    requested_by: str,
    workspace_client_id: int = 0,
    title: str = "",
    lang: str = copy.DEFAULT_LANG,
) -> Optional[dict]:
    """铸一张授权卡:一次性 token 入库 + 卡落任务 payload + 任务停 waiting_user。
    【不执行任何工具】。只读工具走不到这里(调用方契约错误,早炸)。
    workspace_client_id 是 nonce 表的必填目标位:写活有目标账套就传,框架级场景传 0 占位。
    title 是卡上那句人话(「对哪个账套做什么、影响几条」· 调用方按接地事实渲染);
    不传回落工具名 —— 卡上宁可笼统,也不摆一句与实际参数不符的漂亮话。"""
    spec = registry.get(tool)
    if spec is None or not registry.requires_authorization(spec):
        raise ValueError(f"steward authz: {tool!r} does not require authorization")
    from services.security import action_nonce

    fp = args_fingerprint(tool, args)
    ref = json.dumps({"kind": REF_KIND, "task_id": str(task_id), "tool": tool, "args_fp": fp})
    token = action_nonce.mint(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        action_ref=ref,
        user_id=str(requested_by or ""),
        ttl_minutes=ttl_minutes(),
    )
    if not token:
        return None
    now = datetime.now(timezone.utc)
    auth = {
        "token": token,
        "tool": tool,
        "title": title or copy.tool_title(tool, lang),
        "risk": spec.risk,
        "args": args or {},
        # 卡面明细定格在铸卡语言下:批的是这几行,批完再换语言也不改已签的那张卡。
        "args_display": copy.authz_arg_rows(tool, args or {}, lang),
        "args_fp": fp,
        "requested_by": str(requested_by or ""),
        "requested_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=ttl_minutes())).isoformat(),
        "status": store.AUTH_PENDING,
    }
    landed = _park_waiting(cur, tenant_id=tenant_id, task_id=str(task_id), auth=auth)
    return auth if landed else None


def decide(cur, *, tenant_id: str, token: str, actor: dict, approve: bool) -> dict:
    """批准/拒绝一张授权卡。token 原子消费(单次单用,第二次进 used);批文与任务里的
    现参数重算指纹比对,铸卡后参数被改过 → 旧令牌作废。返回信封 {ok, ...}:
      ok=True  → task_id + authorization(已含决断人/时间)
      ok=False → http + code(路由层原样抛,错误码即前端契约)
    """
    from services.security import action_nonce as nonce

    # ref_kind 在原子消费时限定授权类别，避免跨子系统烧掉凭证。
    res = nonce.consume(cur, tenant_id=tenant_id, token=token, ref_kind=REF_KIND)
    if res["status"] == "expired":
        return _err(409, ERR_AUTHZ_EXPIRED)
    if res["status"] == "used":
        return _err(409, ERR_AUTHZ_USED)
    ref = _parse_ref(res.get("action_ref")) if res["status"] == "ok" else None
    if ref is None:  # missing/伪造/别家 kind 的 token 统一按不存在,不泄漏存在性
        return _err(404, ERR_NOT_FOUND)

    task_id = ref["task_id"]
    task = store.get_task(cur, tenant_id=tenant_id, task_id=task_id)
    auth = ((task or {}).get("payload") or {}).get("authorization") or {}
    if not task:
        return _err(404, ERR_NOT_FOUND)
    if auth.get("token") != token or auth.get("status") != store.AUTH_PENDING:
        return _err(409, ERR_AUTHZ_STALE)
    if args_fingerprint(auth.get("tool") or "", auth.get("args")) != ref["args_fp"]:
        # 铸卡后参数被改过:卡就地标失效(前端别再画活按钮),这次决断不作数。
        dead = {**auth, "status": store.AUTH_EXPIRED}
        _write_card(cur, tenant_id=tenant_id, task_id=task_id, auth=dead)
        return _err(409, ERR_AUTHZ_MISMATCH)

    decided = {
        **auth,
        "decided_by": str(actor.get("id") or ""),
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    if approve:
        decided["status"] = store.AUTH_APPROVED
        if not _resume_running(cur, tenant_id=tenant_id, task_id=task_id, auth=decided):
            return _err(409, ERR_AUTHZ_STALE)  # 决断与取消赛跑,先落者赢
        _audit(actor, tenant_id, AUDIT_APPROVED, task_id, decided)
        return {"ok": True, "task_id": task_id, "authorization": decided}

    decided["status"] = store.AUTH_REJECTED
    _write_card(cur, tenant_id=tenant_id, task_id=task_id, auth=decided)
    lang = (task.get("payload") or {}).get("lang") or copy.DEFAULT_LANG
    reason = copy.fail_reason(ERR_AUTHZ_REJECTED, lang)
    store.finish_task(
        cur,
        tenant_id=tenant_id,
        task_id=task_id,
        status=store.TASK_CANCELLED,
        steps=store.fail_steps(task.get("steps") or [], reason),
        artifacts=task.get("artifacts") or [],
        error_code=ERR_AUTHZ_REJECTED,
        error_message=reason,
    )
    _audit(actor, tenant_id, AUDIT_REJECTED, task_id, decided)
    return {"ok": True, "task_id": task_id, "authorization": decided}


_CARD_PUBLIC_KEYS = ("token", "tool", "title", "risk", "args", "args_display", "status",
                     "requested_at", "expires_at", "decided_by", "decided_at")  # fmt: skip


def public_authorization_card(auth, lang: str = "") -> Optional[dict]:
    """授权卡 → 前端视图:args_fp 等内部字段不外泄;pending 但过时效的卡读侧就地标 expired
    —— 不等人点了批准才发现是死按钮(状态诚实)。store.public_task 与决断端点共用。"""
    if not isinstance(auth, dict) or not auth.get("token"):
        return None
    card = {k: auth.get(k) for k in _CARD_PUBLIC_KEYS}
    if not card["args_display"]:  # 老卡(2026-07-27 前铸)payload 没这行且不回填,读侧现算
        card["args_display"] = copy.authz_arg_rows(card["tool"], card["args"] or {}, lang)
    if card["status"] == store.AUTH_PENDING and _iso_past(card.get("expires_at")):
        card["status"] = store.AUTH_EXPIRED
    return card


def _iso_past(value) -> bool:
    try:
        return datetime.fromisoformat(str(value)) <= datetime.now(timezone.utc)
    except (TypeError, ValueError):
        return False


def _parse_ref(raw) -> Optional[dict]:
    try:
        ref = json.loads(raw or "")
        if ref.get("kind") == REF_KIND and ref.get("task_id") and ref.get("args_fp"):
            return ref
    except (ValueError, TypeError):
        pass
    return None


def _card_json(auth: dict) -> str:
    return json.dumps(auth, ensure_ascii=False, default=str)


def _park_waiting(cur, *, tenant_id: str, task_id: str, auth: dict) -> bool:
    """卡落 payload + 任务停 waiting_user(释放 worker 认领位,等人来点)。"""
    cur.execute(
        "UPDATE steward_tasks "
        "SET payload = jsonb_set(payload, '{authorization}', %s::jsonb, true), "
        "status = %s, worker_id = NULL, lease_until = NULL "
        "WHERE tenant_id = %s AND id = %s AND status = ANY(%s)",
        (
            _card_json(auth),
            store.TASK_WAITING_USER,
            tenant_id,
            task_id,
            [store.TASK_RUNNING, store.TASK_WAITING_USER],
        ),
    )
    return cur.rowcount > 0


def _resume_running(cur, *, tenant_id: str, task_id: str, auth: dict) -> bool:
    """批文落 payload + 任务放回 running 待认领。带上新租约当认领窗:created_at 是旧值,
    不续租约会被失联收口的「排队超时限」判据当场误杀。"""
    cur.execute(
        "UPDATE steward_tasks "
        "SET payload = jsonb_set(payload, '{authorization}', %s::jsonb, true), "
        "status = %s, worker_id = NULL, "
        "lease_until = now() + make_interval(secs => timeout_s + %s) "
        "WHERE tenant_id = %s AND id = %s AND status = %s",
        (
            _card_json(auth),
            store.TASK_RUNNING,
            _RESUME_GRACE_S,
            tenant_id,
            task_id,
            store.TASK_WAITING_USER,
        ),
    )
    return cur.rowcount > 0


def _write_card(cur, *, tenant_id: str, task_id: str, auth: dict) -> None:
    """只改卡不动任务态(拒绝/作废路:任务收尾另走 finish_task 的终态守卫)。"""
    cur.execute(
        "UPDATE steward_tasks "
        "SET payload = jsonb_set(payload, '{authorization}', %s::jsonb, true) "
        "WHERE tenant_id = %s AND id = %s",
        (_card_json(auth), tenant_id, task_id),
    )


def _err(http: int, code: str) -> dict:
    return {"ok": False, "http": http, "code": code}


def _audit(actor: dict, tenant_id: str, action: str, task_id: str, auth: dict) -> None:
    """决断留痕:谁在什么时候批/拒了哪条任务的哪个工具。insert_operation_log 自带
    fail-open,这里再兜一层 —— 审计写失败不吞掉已经落库的决断(同 file_access 双保险)。"""
    try:
        from services.audit import store as audit_store

        audit_store.insert_operation_log(
            tenant_id=tenant_id,
            actor_user_id=str(actor.get("id") or ""),
            actor_username=actor.get("username"),
            actor_is_super=bool(actor.get("is_super_admin")),
            action=action,
            target_type="steward_task",
            target_id=str(task_id),
            target_name=auth.get("title"),
            details={
                "tool": auth.get("tool"),
                "risk": auth.get("risk"),
                "args_fp": auth.get("args_fp"),
                "token_prefix": (auth.get("token") or "")[:8],
            },
        )
    except Exception:  # noqa: BLE001 — 审计挂不回滚决断
        logger.warning("[steward.authz] audit write failed action=%s", action, exc_info=True)
