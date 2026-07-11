# -*- coding: utf-8 -*-
"""开/交班审计留痕(PC-3 · 喂 PC-2 防内盗页 · docs/pos/04 §5)。

开班/交班各写一条 operation_logs(pos.shift.opened / pos.shift.closed)。交班是钱路,审计必须
best-effort、不阻塞交班 —— 调用点挂在 pos_write 的 after_commit 钩子上(commit 后独立连接写,
审计失败绝不回滚已落库的班次),且 insert_operation_log 本身吞异常。

⚠️ FK 血泪(同 approval.log_void_operator):开/结班常由收银员令牌发起,其 id=cashier_id
(非 users.id · 无绑主账号)。operation_logs.actor_user_id 有 users 外键 → 塞 cashier_id 会
FK 违约被静默吞。故 actor_user_id 只在操作者确是主账号(老板/绑主账号收银员令牌)时填,收银员
令牌一律留 None;操作人身份走 actor_username(display_name)+ details.cashier_id。
"""

from __future__ import annotations

from typing import Optional


def _actor(operator: dict) -> tuple[Optional[str], Optional[str]]:
    """(actor_user_id, actor_username)。收银员令牌 → user_id 留 None(见文件头 FK 血泪)。"""
    username = operator.get("display_name") or operator.get("username")
    if operator.get("role") == "cashier":
        return None, username
    return (str(operator["id"]) if operator.get("id") else None, username)


def _log(*, tenant_id: str, action: str, operator: dict, shift: dict, extra: dict) -> None:
    # 局部导入避 services.audit.store → core.db → dal_reexports 的循环(同 approval.log_void_operator)。
    from services.audit import store as audit_store

    actor_user_id, actor_username = _actor(operator)
    details = {"cashier_id": operator.get("cashier_id"), "shift_seq": shift.get("shift_seq")}
    details.update(extra)
    audit_store.insert_operation_log(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        actor_username=actor_username,
        actor_is_super=bool(operator.get("is_super_admin")),
        action=action,
        target_type="pos_shift",
        target_id=shift.get("id"),
        target_name=None,
        details=details,
    )


def log_shift_opened(*, tenant_id: str, operator: dict, shift: dict) -> None:
    _log(
        tenant_id=tenant_id,
        action="pos.shift.opened",
        operator=operator,
        shift=shift,
        extra={"opening_float": shift.get("opening_float")},
    )


def log_shift_closed(*, tenant_id: str, operator: dict, shift: dict) -> None:
    _log(
        tenant_id=tenant_id,
        action="pos.shift.closed",
        operator=operator,
        shift=shift,
        extra={
            "expected_cash": shift.get("expected_cash"),
            "counted_cash": shift.get("counted_cash"),
            "cash_diff": shift.get("cash_diff"),
        },
    )


# pos_write 的 after_commit 钩子签名 (result, ctx):commit 后独立写,失败不回滚交班。
def after_open(result: dict, ctx: dict) -> None:
    log_shift_opened(tenant_id=ctx["tenant_id"], operator=ctx["user"], shift=result["shift"])


def after_close(result: dict, ctx: dict) -> None:
    log_shift_closed(tenant_id=ctx["tenant_id"], operator=ctx["user"], shift=result["shift"])
