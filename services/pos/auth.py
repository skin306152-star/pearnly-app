# -*- coding: utf-8 -*-
"""收银员 PIN 鉴权(POS 项目 · PO-B1 · docs/pos/04 §1)。

PIN 绝不存明文:bcrypt 加盐哈希(同主登录密码栈)。登录 = 按 (tenant, workspace, cashier_id)
取行 → 校 is_active → bcrypt 校 PIN → 签 POS token(core.auth.create_pos_token · 自含
tenant/workspace/cashier 声明 · 离线可用 · 不查 users 表)。失败抛 PosError 走信封。
"""

from __future__ import annotations

import bcrypt

from core.auth import create_pos_token
from core.pos_api import PosError
from services.pos import cashier as cashier_dal


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(str(pin).encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_pin(pin: str, pin_hash: str) -> bool:
    try:
        return bcrypt.checkpw(str(pin).encode("utf-8"), pin_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def login(cur, *, tenant_id: str, workspace_client_id: int, cashier_id: str, pin: str) -> dict:
    """PIN 登录:校 cashier 归属/启用/PIN → 返回 {token, ttl_hours, cashier, shift}。

    pin_invalid(401):找不到 cashier 或 PIN 不符(不区分,防枚举)。
    cashier_inactive(403):账号停用。
    """
    row = cashier_dal.get_cashier(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, cashier_id=cashier_id
    )
    if not row:
        raise PosError("pos.pin_invalid", 401)
    if not row.get("is_active", True):
        raise PosError("pos.cashier_inactive", 403)
    if not verify_pin(pin, row["pin_hash"]):
        raise PosError("pos.pin_invalid", 401)

    token, ttl_hours = create_pos_token(
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        cashier_id=str(row["id"]),
        display_name=row["display_name"],
    )
    # 共享钱箱:返回本收银台当前未结班次(与开班人无关),任何收银员登录都接续同一班。
    shift = cashier_dal.get_open_shift_for_workspace(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    return {
        "token": token,
        "offline_ttl_hours": ttl_hours,
        "cashier": {"id": str(row["id"]), "display_name": row["display_name"]},
        "shift": _shift_view(shift),
    }


def _shift_view(shift) -> dict | None:
    if not shift:
        return None
    return {
        "id": str(shift["id"]),
        "terminal_id": shift["terminal_id"],
        "opened_at": shift["opened_at"].isoformat() if shift.get("opened_at") else None,
        "opening_float": (
            float(shift["opening_float"]) if shift.get("opening_float") is not None else None
        ),
    }
