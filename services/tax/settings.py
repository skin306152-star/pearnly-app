# -*- coding: utf-8 -*-
"""报税设置 DAL(一套账一行 · docs/tax-filing/01)。

vat_registered=False → 不生成 PP30(屏4「未登记 VAT」边界);file_zero=True → 0 税额
照常生成(泰国月度强制)。efiling_connected 现恒为 False:RD e-filing 开放度未确认,
接入流程留待对接方案拍板,本期提交走导出手报 + mark-filed(docs/tax-filing/05 §3 注)。

vat_registered 单一事实源 = workspace_clients(2026-08 双事实源收口):公司资料页与
G1 小票合规/画像派生已统一只读该表,这里经 seller_profile.get_seller/set_seller 读写代理
而非另存一份,消掉两处零同步的登记态(见 services/pos/sale.py _receipt_doc_kind 注)。
tax_settings.vat_registered 列保留不迁移(零 schema 变更),代码里不再读写,待后续
schema 清理批一并退役该列。
"""

from __future__ import annotations

from services.sales.seller_profile import get_seller, set_seller

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
        "SELECT branch_type, branch_no, efiling_connected, "
        "remind_days_before, file_zero "
        "FROM tax_settings WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    out = (
        dict(row)
        if row is not None
        else {k: v for k, v in DEFAULTS.items() if k != "vat_registered"}
    )
    seller = get_seller(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    out["vat_registered"] = bool(seller["vat_registered"]) if seller else DEFAULTS["vat_registered"]
    return out


def update_settings(cur, *, tenant_id: str, workspace_client_id: int, data: dict) -> dict:
    current = get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    merged = {k: data.get(k, current.get(k)) for k in _EDITABLE}
    set_seller(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        fields={"vat_registered": bool(merged["vat_registered"])},
    )
    cur.execute(
        "INSERT INTO tax_settings "
        "(tenant_id, workspace_client_id, branch_type, branch_no, "
        " remind_days_before, file_zero) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (tenant_id, workspace_client_id) DO UPDATE SET "
        "branch_type = EXCLUDED.branch_type, "
        "branch_no = EXCLUDED.branch_no, "
        "remind_days_before = EXCLUDED.remind_days_before, "
        "file_zero = EXCLUDED.file_zero, "
        "updated_at = now()",
        (
            tenant_id,
            workspace_client_id,
            merged["branch_type"] or "main",
            merged["branch_no"],
            int(merged["remind_days_before"] or 0),
            bool(merged["file_zero"]),
        ),
    )
    return {**merged, "efiling_connected": False}
