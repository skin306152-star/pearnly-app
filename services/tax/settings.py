# -*- coding: utf-8 -*-
"""报税设置 DAL(一套账一行 · docs/tax-filing/01)。

vat_registered=False → 不生成 PP30(屏4「未登记 VAT」边界);file_zero=True → 0 税额
照常生成(泰国月度强制)。efiling_connected 现恒为 False:RD e-filing 开放度未确认,
接入流程留待对接方案拍板,本期提交走导出手报 + mark-filed(docs/tax-filing/05 §3 注)。
"""

from __future__ import annotations

DEFAULTS = {
    "vat_registered": True,
    "branch_type": "main",
    "branch_no": None,
    "efiling_connected": False,
    "remind_days_before": 3,
    "file_zero": True,
}

_EDITABLE = ("vat_registered", "branch_type", "branch_no", "remind_days_before", "file_zero")


def get_settings(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    cur.execute(
        "SELECT vat_registered, branch_type, branch_no, efiling_connected, "
        "remind_days_before, file_zero "
        "FROM tax_settings WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    return dict(row) if row is not None else dict(DEFAULTS)


def update_settings(cur, *, tenant_id: str, workspace_client_id: int, data: dict) -> dict:
    current = get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    merged = {k: data.get(k, current.get(k)) for k in _EDITABLE}
    cur.execute(
        "INSERT INTO tax_settings "
        "(tenant_id, workspace_client_id, vat_registered, branch_type, branch_no, "
        " remind_days_before, file_zero) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (tenant_id, workspace_client_id) DO UPDATE SET "
        "vat_registered = EXCLUDED.vat_registered, "
        "branch_type = EXCLUDED.branch_type, "
        "branch_no = EXCLUDED.branch_no, "
        "remind_days_before = EXCLUDED.remind_days_before, "
        "file_zero = EXCLUDED.file_zero, "
        "updated_at = now()",
        (
            tenant_id,
            workspace_client_id,
            bool(merged["vat_registered"]),
            merged["branch_type"] or "main",
            merged["branch_no"],
            int(merged["remind_days_before"] or 0),
            bool(merged["file_zero"]),
        ),
    )
    return get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
