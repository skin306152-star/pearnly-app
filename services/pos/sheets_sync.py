# -*- coding: utf-8 -*-
"""POS 售出留档到客户自己的 Google Sheet(POS 项目 · 老板后台 · docs/pos UI 14-Google Sheet)。

复用 services/export/(google_oauth + google_store + sheets)现成的 OAuth 凭据 + SheetsClient
——一个租户一套账只有一份 Google 凭据(export_google_credentials),POS 只加"目标表"配置
(pos_sheets_settings)+ 追加一行写法(SheetsClient.append_row)。同步在售出后台异步跑,不阻塞
收银(见 routes/pos_sales_routes.py 挂钩);任何环节失败只记日志,不重试队列(先上最小可用版本)。
"""

from __future__ import annotations

import logging
import re

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_DEFAULT_TAB = "POS"
_SHEET_URL_RE = re.compile(r"/d/([a-zA-Z0-9_-]+)")


def ensure_schema() -> None:
    """幂等建表 + RLS(startup 经 bootstrap_pos_schema 调)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pos_sheets_settings (
                tenant_id uuid NOT NULL,
                workspace_client_id bigint NOT NULL,
                spreadsheet_id text,
                tab_name text NOT NULL DEFAULT 'POS',
                enabled boolean NOT NULL DEFAULT FALSE,
                updated_at timestamptz NOT NULL DEFAULT now(),
                PRIMARY KEY (tenant_id, workspace_client_id)
            )
            """)
        apply_tenant_rls(cur, "pos_sheets_settings")


def extract_spreadsheet_id(raw: str) -> str:
    """接受完整 Google Sheet URL 或纯 ID,统一抽出纯 ID。"""
    raw = (raw or "").strip()
    m = _SHEET_URL_RE.search(raw)
    return m.group(1) if m else raw


def get_settings(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    cur.execute(
        "SELECT spreadsheet_id, tab_name, enabled FROM pos_sheets_settings "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if not row:
        return {"spreadsheet_id": "", "tab_name": _DEFAULT_TAB, "enabled": False}
    return {
        "spreadsheet_id": row["spreadsheet_id"] or "",
        "tab_name": row["tab_name"] or _DEFAULT_TAB,
        "enabled": bool(row["enabled"]),
    }


def save_settings(
    cur, *, tenant_id: str, workspace_client_id: int, spreadsheet_id: str, enabled: bool
) -> dict:
    sid = extract_spreadsheet_id(spreadsheet_id)
    cur.execute(
        """
        INSERT INTO pos_sheets_settings (tenant_id, workspace_client_id, spreadsheet_id, enabled)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (tenant_id, workspace_client_id)
        DO UPDATE SET spreadsheet_id = EXCLUDED.spreadsheet_id,
                      enabled = EXCLUDED.enabled,
                      updated_at = now()
        """,
        (tenant_id, workspace_client_id, sid or None, bool(enabled)),
    )
    return get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)


def _sale_row(cur, *, tenant_id: str, sale: dict) -> list:
    from services.pos import sales_store

    cur.execute(
        "SELECT l.qty, p.name_th, p.name_en FROM pos_sale_lines l "
        "JOIN products p ON p.id = l.product_id "
        "WHERE l.tenant_id = %s AND l.sale_id = %s ORDER BY l.id",
        (tenant_id, sale["id"]),
    )
    items = ", ".join(
        f"{r['name_th'] or r['name_en']} x{r['qty']}" for r in cur.fetchall()
    )
    payments = sales_store.list_payments(cur, tenant_id=tenant_id, sale_id=sale["id"])
    method = payments[0]["method"] if payments else ""
    sold_at = sale["sold_at"].isoformat() if sale.get("sold_at") else ""
    return [sale["receipt_no"], sold_at, items, str(sale["grand_total"]), method]


def sync_sale(cur, *, tenant_id: str, workspace_client_id: int, sale_id: str) -> None:
    """售出后台追加一行留档。未连接 Google / 未配目标表 / 未开 → no-op。任何失败只记警告。"""
    try:
        settings = get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
        if not settings["enabled"] or not settings["spreadsheet_id"]:
            return
        from services.export import google_oauth

        token = google_oauth.valid_access_token(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        if not token:
            return  # 没连 Google / 凭据被删 → 安静跳过,不是错误

        from services.pos import sales_store

        sale = sales_store.get_sale(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, sale_id=sale_id
        )
        if not sale:
            return
        row = _sale_row(cur, tenant_id=tenant_id, sale=sale)

        from services.export.sheets import SheetsClient

        SheetsClient(token).append_row(settings["spreadsheet_id"], settings["tab_name"], row)
    except Exception as e:  # noqa: BLE001 — 后台留档失败绝不影响收银主路径
        logger.warning("pos_sheets sync_sale failed (sale_id=%s): %s", sale_id, e)
