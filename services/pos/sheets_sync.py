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
from services.pos import sheets_labels

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
                header_lang text NOT NULL DEFAULT 'th',
                enabled boolean NOT NULL DEFAULT FALSE,
                updated_at timestamptz NOT NULL DEFAULT now(),
                PRIMARY KEY (tenant_id, workspace_client_id)
            )
            """)
        cur.execute(
            "ALTER TABLE pos_sheets_settings ADD COLUMN IF NOT EXISTS "
            "header_lang text NOT NULL DEFAULT 'th'"
        )
        apply_tenant_rls(cur, "pos_sheets_settings")


def extract_spreadsheet_id(raw: str) -> str:
    """接受完整 Google Sheet URL 或纯 ID,统一抽出纯 ID。"""
    raw = (raw or "").strip()
    m = _SHEET_URL_RE.search(raw)
    return m.group(1) if m else raw


def get_settings(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    cur.execute(
        "SELECT spreadsheet_id, tab_name, enabled, header_lang FROM pos_sheets_settings "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if not row:
        return {
            "spreadsheet_id": "",
            "tab_name": _DEFAULT_TAB,
            "enabled": False,
            "header_lang": "th",
        }
    return {
        "spreadsheet_id": row["spreadsheet_id"] or "",
        "tab_name": row["tab_name"] or _DEFAULT_TAB,
        "enabled": bool(row["enabled"]),
        "header_lang": sheets_labels.norm_lang(row.get("header_lang") or "th"),
    }


def save_settings(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    spreadsheet_id: str,
    enabled: bool,
    header_lang: str = "th",
) -> dict:
    sid = extract_spreadsheet_id(spreadsheet_id)
    cur.execute(
        """
        INSERT INTO pos_sheets_settings (tenant_id, workspace_client_id, spreadsheet_id, enabled, header_lang)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (tenant_id, workspace_client_id)
        DO UPDATE SET spreadsheet_id = EXCLUDED.spreadsheet_id,
                      enabled = EXCLUDED.enabled,
                      header_lang = EXCLUDED.header_lang,
                      updated_at = now()
        """,
        (
            tenant_id,
            workspace_client_id,
            sid or None,
            bool(enabled),
            sheets_labels.norm_lang(header_lang),
        ),
    )
    return get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)


def sheet_url(spreadsheet_id: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit" if spreadsheet_id else ""


def set_enabled(cur, *, tenant_id: str, workspace_client_id: int, enabled: bool) -> dict:
    """只切开关,不动已存的目标表/表头语言(关闭留档不等于丢表)。"""
    current = get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    return save_settings(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        spreadsheet_id=current["spreadsheet_id"],
        enabled=enabled,
        header_lang=current["header_lang"],
    )


def ensure_target_sheet(cur, *, tenant_id: str, workspace_client_id: int, lang: str = "th") -> dict:
    """开启留档且还没有目标表 → 自动在老板自己的 Drive 建一张,表头跟随建表当下的界面语言。

    不需要手动找表贴链接。表头语言随 header_lang 落库固定,后续每笔追加沿用同一语言。
    """
    settings = get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    if settings["spreadsheet_id"]:
        return save_settings(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            spreadsheet_id=settings["spreadsheet_id"],
            enabled=True,
            header_lang=settings["header_lang"],
        )

    from core.pos_api import PosError
    from services.export import google_oauth

    token = google_oauth.valid_access_token(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    if not token:
        raise PosError("pos.google_not_connected", 400)

    cur.execute(
        "SELECT name FROM workspace_clients WHERE tenant_id = %s AND id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    store_name = (row["name"] if row else "") or "Pearnly"
    header_lang = sheets_labels.norm_lang(lang)

    from services.export.sheets import SheetsClient

    client = SheetsClient(token)
    ssid = client.find_or_create_spreadsheet("root", f"{store_name} · POS")
    client.ensure_tab(ssid, _DEFAULT_TAB)
    client.overwrite_tab(ssid, _DEFAULT_TAB, [sheets_labels.header_row(header_lang)])
    return save_settings(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        spreadsheet_id=ssid,
        enabled=True,
        header_lang=header_lang,
    )


def _sale_row(cur, *, tenant_id: str, sale: dict, lang: str) -> list:
    from services.pos import sales_store

    cur.execute(
        "SELECT l.qty, p.name_th, p.name_en FROM pos_sale_lines l "
        "JOIN products p ON p.id = l.product_id "
        "WHERE l.tenant_id = %s AND l.sale_id = %s ORDER BY l.id",
        (tenant_id, sale["id"]),
    )
    lines = cur.fetchall()
    items = ", ".join(f"{r['name_th'] or r['name_en']} x{r['qty']}" for r in lines)
    qty_total = sum(r["qty"] or 0 for r in lines)

    cashier_name = ""
    if sale.get("cashier_id"):
        cur.execute(
            "SELECT display_name FROM pos_cashiers WHERE tenant_id = %s AND id = %s",
            (tenant_id, sale["cashier_id"]),
        )
        crow = cur.fetchone()
        cashier_name = (crow["display_name"] if crow else "") or ""

    payments = sales_store.list_payments(cur, tenant_id=tenant_id, sale_id=sale["id"])
    method = payments[0]["method"] if payments else ""
    sold_at = sale.get("sold_at")
    date_s = sold_at.strftime("%Y-%m-%d") if sold_at else ""
    time_s = sold_at.strftime("%H:%M:%S") if sold_at else ""

    return [
        sale["receipt_no"],
        date_s,
        time_s,
        cashier_name,
        items,
        qty_total,
        str(sale.get("subtotal", 0)),
        str(sale.get("discount_total", 0)),
        str(sale.get("vat_amount", 0)),
        str(sale.get("grand_total", 0)),
        sheets_labels.method_label(method, lang),
        str(sale.get("paid_total", 0)),
        str(sale.get("change_amount", 0)),
    ]


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
        row = _sale_row(cur, tenant_id=tenant_id, sale=sale, lang=settings["header_lang"])

        from services.export.sheets import SheetsClient

        SheetsClient(token).append_row(settings["spreadsheet_id"], settings["tab_name"], row)
    except Exception as e:  # noqa: BLE001 — 后台留档失败绝不影响收银主路径
        logger.warning("pos_sheets sync_sale failed (sale_id=%s): %s", sale_id, e)
