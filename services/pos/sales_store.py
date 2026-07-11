# -*- coding: utf-8 -*-
"""POS 小票 DAL + 双跑迁移(POS 项目 · PO-B2 · docs/pos/03 §4)。

参数化叶子:每条语句 WHERE tenant_id(应用层硬隔离 · RLS 仅兜底)。编排(发号/算价/扣库存/落库)
在 sale.py / refund.py;此层只读写 pos_sales / pos_sale_lines / pos_payments。
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_SALE_COLS = (
    "id, tenant_id, workspace_client_id, client_uuid, shift_id, terminal_id, cashier_id, "
    "receipt_no, doc_kind, sale_type, refund_of_sale_id, member_client_id, subtotal, "
    "discount_total, vat_amount, grand_total, price_includes_vat, paid_total, change_amount, "
    "full_invoice_id, status, sold_at, synced_at, created_by, created_at"
)


def _num(v: Any) -> Any:
    return Decimal(str(v)) if v is not None else None


def ensure_sales_schema() -> None:
    from core import db

    rls_tables = ("pos_sales", "pos_sale_lines", "pos_payments")
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_sales (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    client_uuid uuid UNIQUE,
                    shift_id uuid REFERENCES pos_shifts(id) ON DELETE SET NULL,
                    terminal_id bigint REFERENCES pos_terminals(id) ON DELETE SET NULL,
                    cashier_id uuid REFERENCES pos_cashiers(id) ON DELETE SET NULL,
                    receipt_no text,
                    doc_kind text NOT NULL DEFAULT 'receipt',
                    sale_type text NOT NULL DEFAULT 'sale',
                    refund_of_sale_id uuid REFERENCES pos_sales(id) ON DELETE SET NULL,
                    member_client_id bigint,
                    subtotal numeric(14,2) NOT NULL DEFAULT 0,
                    discount_total numeric(14,2) NOT NULL DEFAULT 0,
                    vat_amount numeric(14,2) NOT NULL DEFAULT 0,
                    grand_total numeric(14,2) NOT NULL DEFAULT 0,
                    price_includes_vat boolean NOT NULL DEFAULT FALSE,
                    paid_total numeric(14,2) NOT NULL DEFAULT 0,
                    change_amount numeric(14,2) NOT NULL DEFAULT 0,
                    full_invoice_id uuid,
                    status text NOT NULL DEFAULT 'completed',
                    sold_at timestamptz NOT NULL DEFAULT now(),
                    synced_at timestamptz,
                    created_by uuid,
                    created_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_sales_shift "
                "ON pos_sales (tenant_id, workspace_client_id, shift_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_sales_receipt "
                "ON pos_sales (tenant_id, receipt_no)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_sales_sold_at "
                "ON pos_sales (tenant_id, workspace_client_id, sold_at)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_sale_lines (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    sale_id uuid NOT NULL REFERENCES pos_sales(id) ON DELETE CASCADE,
                    product_id uuid NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
                    sell_unit text,
                    unit_factor numeric(14,3) NOT NULL DEFAULT 1,
                    qty numeric(14,3) NOT NULL,
                    qty_base numeric(14,3) NOT NULL,
                    unit_price numeric(14,2) NOT NULL,
                    line_discount numeric(14,2) NOT NULL DEFAULT 0,
                    vat_applicable boolean NOT NULL DEFAULT TRUE,
                    batch_id uuid,
                    refund_of_line_id uuid REFERENCES pos_sale_lines(id) ON DELETE SET NULL,
                    line_total numeric(14,2) NOT NULL
                )
                """)
            # 0062:成本快照(卖出扣库存那一刻的 COGS · 报表毛利用);老行/无成本数据保持 NULL。
            cur.execute(
                "ALTER TABLE pos_sale_lines ADD COLUMN IF NOT EXISTS cost_total numeric(14,2)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_sale_lines_sale ON pos_sale_lines (sale_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_sale_lines_refund "
                "ON pos_sale_lines (refund_of_line_id)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_payments (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    sale_id uuid NOT NULL REFERENCES pos_sales(id) ON DELETE CASCADE,
                    method text NOT NULL,
                    amount numeric(14,2) NOT NULL,
                    ref text
                )
                """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_pos_payments_sale ON pos_payments (sale_id)")
            apply_tenant_rls(cur, *rls_tables)
        logger.info("✅ POS 小票 3 表 + RLS 已就绪 (POS PO-B2)")
    except Exception as e:
        logger.warning(f"ensure_sales_schema 失败(跳过 · 等 alembic 0025): {e}")


# ── 商品(售卖时取标志/单位)────────────────────────────────────────────
# 隔离:同一 tenant 下可代多套账(workspace_client_id),取商品/单位/单据必须连 ws 过滤,
# 否则知道 id/票号即可跨套账读取(见 [[workspace-isolation-audit]])。ws 为必填,不许漏。
def get_product_for_sale(cur, *, tenant_id: str, workspace_client_id: int, product_id: str):
    cur.execute(
        "SELECT id, base_unit, track_batch, vat_applicable, name_th, name_en, name_zh, unit_price "
        "FROM products WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s "
        "AND is_active = TRUE",
        (tenant_id, workspace_client_id, product_id),
    )
    return cur.fetchone()


def get_unit_factor(
    cur, *, tenant_id: str, workspace_client_id: int, product_id: str, unit_name: str
):
    cur.execute(
        "SELECT factor_to_base, price FROM product_units "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND product_id = %s AND unit_name = %s",
        (tenant_id, workspace_client_id, product_id, unit_name),
    )
    return cur.fetchone()


# ── sales 头 ──────────────────────────────────────────────────────────
def find_sale_by_client_uuid(cur, *, tenant_id: str, workspace_client_id: int, client_uuid: str):
    cur.execute(
        f"SELECT {_SALE_COLS} FROM pos_sales "
        f"WHERE tenant_id = %s AND workspace_client_id = %s AND client_uuid = %s",
        (tenant_id, workspace_client_id, client_uuid),
    )
    return cur.fetchone()


def get_sale(cur, *, tenant_id: str, workspace_client_id: int, sale_id: str):
    cur.execute(
        f"SELECT {_SALE_COLS} FROM pos_sales "
        f"WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, sale_id),
    )
    return cur.fetchone()


def get_sale_by_receipt(cur, *, tenant_id: str, workspace_client_id: int, receipt_no: str):
    cur.execute(
        f"SELECT {_SALE_COLS} FROM pos_sales "
        f"WHERE tenant_id = %s AND workspace_client_id = %s AND receipt_no = %s "
        f"ORDER BY created_at DESC LIMIT 1",
        (tenant_id, workspace_client_id, receipt_no),
    )
    return cur.fetchone()


def insert_sale(cur, *, tenant_id: str, fields: dict) -> dict:
    cols = [
        "workspace_client_id",
        "client_uuid",
        "shift_id",
        "terminal_id",
        "cashier_id",
        "receipt_no",
        "doc_kind",
        "sale_type",
        "refund_of_sale_id",
        "member_client_id",
        "subtotal",
        "discount_total",
        "vat_amount",
        "grand_total",
        "price_includes_vat",
        "paid_total",
        "change_amount",
        "status",
        "sold_at",
        "created_by",
    ]
    money = {
        "subtotal",
        "discount_total",
        "vat_amount",
        "grand_total",
        "paid_total",
        "change_amount",
    }
    vals = [tenant_id]
    for c in cols:
        v = fields.get(c)
        vals.append(_num(v) if c in money else v)
    placeholders = ", ".join(["%s"] * (len(cols) + 1))
    cur.execute(
        f"INSERT INTO pos_sales (tenant_id, {', '.join(cols)}) VALUES ({placeholders}) "
        f"RETURNING {_SALE_COLS}",
        vals,
    )
    return cur.fetchone()


def insert_line(cur, *, tenant_id: str, sale_id: str, fields: dict) -> dict:
    cols = [
        "product_id",
        "sell_unit",
        "unit_factor",
        "qty",
        "qty_base",
        "unit_price",
        "line_discount",
        "vat_applicable",
        "batch_id",
        "refund_of_line_id",
        "line_total",
        "cost_total",
    ]
    qty = {"unit_factor", "qty", "qty_base"}
    money = {"unit_price", "line_discount", "line_total", "cost_total"}
    vals = [tenant_id, sale_id]
    for c in cols:
        v = fields.get(c)
        vals.append(_num(v) if c in (qty | money) else v)
    placeholders = ", ".join(["%s"] * (len(cols) + 2))
    cur.execute(
        f"INSERT INTO pos_sale_lines (tenant_id, sale_id, {', '.join(cols)}) "
        f"VALUES ({placeholders}) RETURNING id, batch_id, qty_base",
        vals,
    )
    return cur.fetchone()


def insert_payment(cur, *, tenant_id: str, sale_id: str, method: str, amount, ref=None) -> None:
    cur.execute(
        "INSERT INTO pos_payments (tenant_id, sale_id, method, amount, ref) "
        "VALUES (%s, %s, %s, %s, %s)",
        (tenant_id, sale_id, method, _num(amount), ref),
    )


def list_lines(cur, *, tenant_id: str, sale_id: str) -> list:
    cur.execute(
        "SELECT id, product_id, sell_unit, unit_factor, qty, qty_base, unit_price, "
        "line_discount, vat_applicable, batch_id, refund_of_line_id, line_total, cost_total "
        "FROM pos_sale_lines WHERE tenant_id = %s AND sale_id = %s ORDER BY id",
        (tenant_id, sale_id),
    )
    return cur.fetchall()


def list_payments(cur, *, tenant_id: str, sale_id: str) -> list:
    cur.execute(
        "SELECT method, amount, ref FROM pos_payments WHERE tenant_id = %s AND sale_id = %s",
        (tenant_id, sale_id),
    )
    return cur.fetchall()


def refunded_qty_for_line(cur, *, tenant_id: str, line_id: str) -> Decimal:
    """该原始行已退数量合计(退货行的 refund_of_line_id 指向它;退货行 qty 存正)。"""
    cur.execute(
        "SELECT COALESCE(SUM(qty), 0) AS q FROM pos_sale_lines "
        "WHERE tenant_id = %s AND refund_of_line_id = %s",
        (tenant_id, line_id),
    )
    return Decimal(str(cur.fetchone()["q"]))


def set_status(cur, *, tenant_id: str, sale_id: str, status: str) -> None:
    cur.execute(
        "UPDATE pos_sales SET status = %s WHERE tenant_id = %s AND id = %s",
        (status, tenant_id, sale_id),
    )


def set_full_invoice_id(cur, *, tenant_id: str, sale_id: str, doc_id) -> None:
    """升级正式税票后回填:标记该小票被全式票取代(VAT 申报去重锚点 · PO-B4)。"""
    cur.execute(
        "UPDATE pos_sales SET full_invoice_id = %s WHERE tenant_id = %s AND id = %s",
        (doc_id, tenant_id, sale_id),
    )


def has_refunds(cur, *, tenant_id: str, sale_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM pos_sales WHERE tenant_id = %s AND refund_of_sale_id = %s LIMIT 1",
        (tenant_id, sale_id),
    )
    return cur.fetchone() is not None
