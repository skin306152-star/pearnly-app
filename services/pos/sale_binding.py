from __future__ import annotations

from typing import Optional

from core.pos_api import PosError


def resolve(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    shift_id: Optional[str],
    terminal_id: Optional[int],
    cashier_id: Optional[str],
) -> dict:
    if not shift_id:
        raise PosError("pos.shift_closed", 409, detail="shift_required")
    if not cashier_id:
        raise PosError("pos.forbidden", 403)
    cur.execute(
        "SELECT s.id, s.terminal_id, s.cashier_id, t.is_active AS terminal_active, "
        "c.is_active AS cashier_active FROM pos_shifts s "
        "JOIN pos_terminals t ON t.tenant_id = s.tenant_id "
        "AND t.workspace_client_id = s.workspace_client_id AND t.id = s.terminal_id "
        "JOIN pos_cashiers c ON c.tenant_id = s.tenant_id "
        "AND c.workspace_client_id = s.workspace_client_id AND c.id = s.cashier_id "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s "
        "AND s.id = %s AND s.status = 'open' FOR UPDATE OF s",
        (tenant_id, workspace_client_id, shift_id),
    )
    shift = cur.fetchone()
    if not shift:
        raise PosError("pos.shift_closed", 409)
    if not shift["terminal_active"]:
        raise PosError("pos.shift_closed", 409, detail="terminal_inactive")
    if terminal_id is not None and int(terminal_id) != int(shift["terminal_id"]):
        raise PosError("pos.shift_closed", 409, detail="terminal_mismatch")
    if str(cashier_id) != str(shift["cashier_id"]):
        raise PosError("pos.shift_closed", 409, detail="cashier_mismatch")
    if not shift["cashier_active"]:
        raise PosError("pos.cashier_inactive", 403)
    return {"terminal_id": shift["terminal_id"], "cashier_id": str(shift["cashier_id"])}
