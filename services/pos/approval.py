# -*- coding: utf-8 -*-
"""POS 退货/作废店长授权(PS-1 · 防内盗 · docs/pos/04 §6)。

闸(core.feature_flags.pos_refund_approval)关时调用方跳过本模块,退货/作废逐字节走历史。
闸开时的判定:

  1. 操作者本人持 pos.refund.approve(老板/管理员用主账号切到收银台)→ 直接放行,无需外部授权。
  2. 收银员令牌(role=cashier)天然只认 CASHIER_CODES,不持该码 → 必须店长 PIN 覆盖:
     校验店长 pos_cashiers PIN(bcrypt,复用登录同一栈)+ 其关联主账号经 RBAC 确有
     pos.refund.approve,才放行,并回传授权人身份供审计。

店长授权 = 复用既有 PIN 栈 + 既有权限码 pos.refund.approve,不另造凭证/权限体系。授权人
认定走「关联用户(pos_cashiers.user_id)的 RBAC 生效码集」这一单一事实源,POS 前台不自持权限。
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from core import feature_flags, pos_api
from core.pos_api import PosError
from services.authz import deps
from services.authz.resolver import resolve
from services.pos import auth as pos_auth
from services.pos import cashier as cashier_dal

APPROVE_CODE = "pos.refund.approve"


class ManagerApproval(BaseModel):
    # PS-1:收银员无 pos.refund.approve 时,店长在授权窗输入本人收银员身份 + PIN 覆盖。
    cashier_id: str
    pin: str


def _actor_holds_code(request, user: dict) -> bool:
    """操作者本人是否已持授权码。收银员令牌恒 False(交给店长覆盖流)。"""
    if user.get("is_super_admin"):
        return True
    if user.get("role") == "cashier":
        return False
    return deps.actor_has_perm(request, user, APPROVE_CODE)


def _load_user(cur, tenant_id: str, user_id: str) -> Optional[dict]:
    """按 (id, tenant) 取授权人主账号最小字段(RBAC 解析 + 超管短路用)。跨租户取不到。"""
    cur.execute(
        "SELECT id, role, tenant_id, invited_by, "
        "COALESCE(is_super_admin, FALSE) AS is_super_admin "
        "FROM users WHERE id = %s AND tenant_id = %s",
        (str(user_id), str(tenant_id)),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def _verify_approver(
    cur, *, tenant_id: str, workspace_client_id: int, cashier_id: Optional[str], pin: Optional[str]
) -> dict:
    """校验店长凭据 → 授权人身份 dict。任一环不符抛 PosError(不区分细节,防枚举)。"""
    if not cashier_id or not pin:
        raise PosError("pos.approval_denied", 403)
    row = cashier_dal.get_cashier(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, cashier_id=cashier_id
    )
    if not row or not row.get("is_active", True):
        raise PosError("pos.approval_denied", 403)
    if not pos_auth.verify_pin(pin, row["pin_hash"]):
        raise PosError("pos.pin_invalid", 401)
    approver_user_id = row.get("user_id")
    if not approver_user_id:
        # 该收银员没绑主账号 → 无从核验其 RBAC 权限,不是合格授权人。
        raise PosError("pos.approval_denied", 403)
    u = _load_user(cur, tenant_id, approver_user_id)
    if not u:
        raise PosError("pos.approval_denied", 403)
    authz = resolve(u, cur=cur)
    if not (u.get("is_super_admin") or authz.has(APPROVE_CODE)):
        raise PosError("pos.approval_denied", 403)
    return {
        "cashier_id": str(row["id"]),
        "user_id": str(approver_user_id),
        "name": row["display_name"],
    }


def authorize(
    cur,
    *,
    request,
    user: dict,
    tenant_id: str,
    workspace_client_id: int,
    approval: Optional[dict],
) -> Optional[dict]:
    """闸开时授权判定。返回:

      - None            → 操作者本人有权,无需外部授权(不写授权审计)。
      - {cashier_id...} → 店长授权人身份(需写审计留痕「谁授权的」)。

    无权且未带授权块 → PosError pos.approval_required(前台据此弹店长授权窗);
    授权块校验失败 → pos.approval_denied / pos.pin_invalid。
    """
    if _actor_holds_code(request, user):
        return None
    if not approval:
        raise PosError("pos.approval_required", 403)
    return _verify_approver(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        cashier_id=approval.get("cashier_id"),
        pin=approval.get("pin"),
    )


def execute_gated_write(
    request,
    *,
    ws_override: Optional[int],
    approval: Optional[dict],
    write_fn,
    action: str,
    sale_id_of,
    audit_details: Optional[dict] = None,
) -> dict:
    """退货/作废的授权闸 + 审计,挂在共用写事务信封(core.pos_api.pos_write)上。

    信封(鉴权/租户校验/账套归属/模块闸/单事务)不在此自持——只提供两个钩子:写前授权闸
    (与写同事务),写后审计(须 commit 后独立写、不随退货回滚)。闸关时 guard 放行、不留痕。
    """
    state: dict = {}

    def _authorize(cur, ctx):
        state["gated"], state["approver"] = guard(
            cur,
            request=request,
            user=ctx["user"],
            tenant_id=ctx["tenant_id"],
            workspace_client_id=ctx["workspace_client_id"],
            approval=approval,
        )

    def _audit(result, ctx):
        # 仅经店长授权(闸开且有授权人)时写审计;本人有权/闸关都不写。
        if state.get("gated") and state.get("approver"):
            log_approval(
                tenant_id=ctx["tenant_id"],
                action=action,
                sale_id=sale_id_of(result),
                operator=ctx["user"],
                approver=state["approver"],
                details=audit_details,
            )

    return pos_api.pos_write(
        request,
        ws_override=ws_override,
        write_fn=write_fn,
        before_write=_authorize,
        after_commit=_audit,
    )


def guard(
    cur, *, request, user: dict, tenant_id: str, workspace_client_id: int, approval: Optional[dict]
) -> tuple[bool, Optional[dict]]:
    """退货/作废写前授权闸:返回 (gated, approver)。

    闸关 → (False, None),调用方逐字节走历史。闸开 → 跑 authorize,(True, None)=本人有权、
    (True, {..})=店长授权(需审计);无权无授权块或校验失败则由 authorize 抛 PosError。
    """
    if not feature_flags.pos_refund_approval_enabled_for(tenant_id):
        return False, None
    approver = authorize(
        cur,
        request=request,
        user=user,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        approval=approval,
    )
    return True, approver


def log_approval(
    *,
    tenant_id: str,
    action: str,
    sale_id: Optional[str],
    operator: dict,
    approver: dict,
    details: Optional[dict] = None,
) -> None:
    """把店长授权写进 operation_logs(actor = 授权人,即「谁授权的」)。best-effort,不阻塞退货。"""
    from services.audit import store as audit_store

    payload = {
        "approved_by_cashier_id": approver.get("cashier_id"),
        "approved_by_user_id": approver.get("user_id"),
        "approved_by_name": approver.get("name"),
        "operator_cashier_id": operator.get("cashier_id"),
        "operator_name": operator.get("display_name"),
    }
    if details:
        payload.update(details)
    audit_store.insert_operation_log(
        tenant_id=tenant_id,
        actor_user_id=approver.get("user_id"),
        actor_username=approver.get("name"),
        actor_is_super=False,
        action=action,
        target_type="pos_sale",
        target_id=sale_id,
        target_name=None,
        details=payload,
    )
