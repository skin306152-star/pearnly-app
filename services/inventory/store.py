# -*- coding: utf-8 -*-
"""库存 DAL + 双跑迁移(POS 项目 · PO-A3 · docs/pos/03 §3)。

参数化叶子:每个函数收 cursor + tenant_id,每条语句 WHERE tenant_id(应用层硬隔离)。
库存唯一真理=inventory_transactions(immutable);inventory_stock 是物化值,与流水同事务更新。
stock 行的 upsert 用 SELECT ... FOR UPDATE + IS NOT DISTINCT FROM(正确处理 NULL batch +
锁行防多终端并发双扣),不用 ON CONFLICT(NULL batch 在普通唯一约束里互不相等)。
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")


class InsufficientStockError(Exception):
    pass


_TXN_COLS = (
    "id, tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, "
    "txn_type, qty_delta, unit_cost, ref_type, ref_id, client_uuid, reason, "
    "created_by, created_at"
)


def _num(v: Any) -> Any:
    return Decimal(str(v)) if v is not None else None


# ── schema 双跑(与 alembic 0023 同源幂等 DDL)─────────────────────────
def ensure_schema() -> None:
    from core import db

    rls_tables = ("warehouses", "inventory_batches", "inventory_stock", "inventory_transactions")
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS warehouses (
                    id bigserial PRIMARY KEY,
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    name text NOT NULL DEFAULT 'ร้าน',
                    is_default boolean NOT NULL DEFAULT FALSE,
                    is_active boolean NOT NULL DEFAULT TRUE,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_warehouses_ws "
                "ON warehouses (tenant_id, workspace_client_id)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS inventory_batches (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint,
                    product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    batch_no text NOT NULL,
                    expiry_date date,
                    received_at date NOT NULL DEFAULT CURRENT_DATE,
                    unit_cost numeric(14,2),
                    created_at timestamptz NOT NULL DEFAULT now(),
                    UNIQUE (tenant_id, product_id, batch_no)
                )
                """)
            # PO-5 套账隔离:批次归主体。列在 PO-1 回填已加,这里幂等补(新库/未回填库)。
            # 仍可空(rollout):写侧 get_or_create_batch 写入当前套账,收 NOT NULL 留 PO-8。
            cur.execute(
                "ALTER TABLE inventory_batches ADD COLUMN IF NOT EXISTS workspace_client_id bigint"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_batches_fefo "
                "ON inventory_batches (tenant_id, product_id, expiry_date)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_batches_ws "
                "ON inventory_batches (tenant_id, workspace_client_id, product_id)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS inventory_stock (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    warehouse_id bigint NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
                    batch_id uuid REFERENCES inventory_batches(id) ON DELETE CASCADE,
                    qty_on_hand numeric(14,3) NOT NULL DEFAULT 0,
                    qty_reserved numeric(14,3) NOT NULL DEFAULT 0,
                    updated_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_batched "
                "ON inventory_stock (tenant_id, product_id, warehouse_id, batch_id) "
                "WHERE batch_id IS NOT NULL"
            )
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_nobatch "
                "ON inventory_stock (tenant_id, product_id, warehouse_id) "
                "WHERE batch_id IS NULL"
            )
            # stock_overview / 近效期 / 库存报表按 (tenant, workspace) 过滤再聚合;uq_* 以 product
            # 打头不含 workspace,这条补 (tenant, workspace) 前缀避免大库全租户扫(C2 性能 · 04 §4)。
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_stock_ws_product "
                "ON inventory_stock (tenant_id, workspace_client_id, product_id)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS inventory_transactions (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    warehouse_id bigint NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
                    batch_id uuid REFERENCES inventory_batches(id) ON DELETE SET NULL,
                    txn_type text NOT NULL,
                    qty_delta numeric(14,3) NOT NULL,
                    unit_cost numeric(14,2),
                    ref_type text,
                    ref_id uuid,
                    client_uuid uuid UNIQUE,
                    reason text,
                    created_by uuid,
                    created_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_txn_product ON inventory_transactions "
                "(tenant_id, workspace_client_id, product_id, created_at)"
            )
            apply_tenant_rls(cur, *rls_tables)
        logger.info("✅ 库存 4 表 + RLS 已就绪 (POS PO-A3)")
    except Exception as e:
        logger.warning(f"ensure_schema inventory 失败(跳过 · 等 alembic 0023): {e}")


# ── warehouses ────────────────────────────────────────────────────────
def list_warehouses(cur, *, tenant_id: str, workspace_client_id: int) -> list:
    cur.execute(
        "SELECT id, name, is_default, is_active FROM warehouses "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND is_active = TRUE "
        "ORDER BY is_default DESC, id",
        (tenant_id, workspace_client_id),
    )
    return cur.fetchall()


def get_warehouse(cur, *, tenant_id: str, workspace_client_id: int, warehouse_id: int):
    cur.execute(
        "SELECT id, name, is_default, is_active FROM warehouses "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, warehouse_id),
    )
    return cur.fetchone()


def get_or_create_default_warehouse(
    cur, *, tenant_id: str, workspace_client_id: int, name: Optional[str] = None
) -> dict:
    """每个账套至少一个默认仓;无则建(入库/盘点首次自动有仓)。name 仅在新建时生效(已有仓不改名)。"""
    cur.execute(
        "SELECT id, name, is_default, is_active FROM warehouses "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND is_default = TRUE "
        "AND is_active = TRUE LIMIT 1",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if row:
        return row
    if name:
        cur.execute(
            "INSERT INTO warehouses (tenant_id, workspace_client_id, is_default, name) "
            "VALUES (%s, %s, TRUE, %s) RETURNING id, name, is_default, is_active",
            (tenant_id, workspace_client_id, name),
        )
    else:
        cur.execute(
            "INSERT INTO warehouses (tenant_id, workspace_client_id, is_default) "
            "VALUES (%s, %s, TRUE) RETURNING id, name, is_default, is_active",
            (tenant_id, workspace_client_id),
        )
    return cur.fetchone()


# ── batches ───────────────────────────────────────────────────────────
def product_tracks_batch(cur, *, tenant_id: str, product_id: str) -> bool:
    """商品是否勾了「批次管理」(products.track_batch)。非批次品收货时忽略批号 → 货入散装行,
    避免货被锁进批次行、而非批次卖出查散装行够不着(= 库存看得见卖不出)。"""
    cur.execute(
        "SELECT track_batch FROM products WHERE tenant_id = %s AND id = %s",
        (tenant_id, product_id),
    )
    row = cur.fetchone()
    return bool(row and row["track_batch"])


def get_or_create_batch(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    product_id: str,
    batch_no: str,
    expiry_date=None,
    unit_cost=None,
) -> dict:
    """按 (product, batch_no) 取批次;无则建(归当前套账)。已存在则补回 expiry/cost(首次为准)。

    PO-5:自然唯一键 (tenant, product, batch_no) 不含套账(product 已按套账隔离 → 批次随之归属),
    故 SELECT 仍按自然键,避免 NULL 套账行与新插入撞唯一约束;INSERT 写入 workspace_client_id。
    命中旧行若套账为空(回填遗漏)→ 顺手回填到当前套账(自愈)。
    """
    cur.execute(
        "SELECT id, batch_no, expiry_date, unit_cost, workspace_client_id FROM inventory_batches "
        "WHERE tenant_id = %s AND product_id = %s AND batch_no = %s",
        (tenant_id, product_id, batch_no),
    )
    row = cur.fetchone()
    if row:
        if row.get("workspace_client_id") is None and workspace_client_id is not None:
            cur.execute(
                "UPDATE inventory_batches SET workspace_client_id = %s "
                "WHERE id = %s AND tenant_id = %s",
                (workspace_client_id, row["id"], tenant_id),
            )
        return row
    cur.execute(
        "INSERT INTO inventory_batches "
        "(tenant_id, workspace_client_id, product_id, batch_no, expiry_date, unit_cost) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, batch_no, expiry_date, unit_cost",
        (tenant_id, workspace_client_id, product_id, batch_no, expiry_date, _num(unit_cost)),
    )
    return cur.fetchone()


def get_batch(cur, *, tenant_id: str, workspace_client_id: int, product_id: str, batch_id: str):
    # PO-5:读 batch 带套账过滤(rollout-safe:含 IS NULL,回填遗漏行仍可读)。
    cur.execute(
        "SELECT id, batch_no, expiry_date, unit_cost FROM inventory_batches "
        "WHERE tenant_id = %s AND product_id = %s AND id = %s "
        "AND (workspace_client_id = %s OR workspace_client_id IS NULL)",
        (tenant_id, product_id, batch_id, workspace_client_id),
    )
    return cur.fetchone()


# ── stock(物化结果 · upsert 走 SELECT FOR UPDATE)──────────────────────
def get_stock_for_update(
    cur, *, tenant_id: str, product_id: str, warehouse_id: int, batch_id: Optional[str]
):
    cur.execute(
        "SELECT id, qty_on_hand FROM inventory_stock "
        "WHERE tenant_id = %s AND product_id = %s AND warehouse_id = %s "
        "AND batch_id IS NOT DISTINCT FROM %s FOR UPDATE",
        (tenant_id, product_id, warehouse_id, batch_id),
    )
    return cur.fetchone()


def sum_on_hand_for_update(cur, *, tenant_id: str, product_id: str, warehouse_id: int) -> Decimal:
    """锁定并汇总某 (product,warehouse) 跨所有批次的在库总量。

    盘点按总数对账用:显示端 stock_overview 是 SUM(所有批次),盘点也须拿同口径总数算差异,
    否则只对 batch=None 单行 → 差异全错(见 ledger.count)。先 FOR UPDATE 锁全部批次行防并发,
    再 Python 求和(聚合本身不能 FOR UPDATE)。
    """
    cur.execute(
        "SELECT COALESCE(qty_on_hand, 0) AS q FROM inventory_stock "
        "WHERE tenant_id = %s AND product_id = %s AND warehouse_id = %s FOR UPDATE",
        (tenant_id, product_id, warehouse_id),
    )
    return sum((Decimal(str(r["q"])) for r in cur.fetchall()), Decimal("0"))


def apply_stock_delta(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    product_id: str,
    warehouse_id: int,
    batch_id: Optional[str],
    qty_delta,
    reject_negative: bool = False,
) -> Decimal:
    """加减某 (product,warehouse,batch) 行的在库量,返回新 qty_on_hand。

    锁行后 UPDATE(防多终端并发双扣);无行则 INSERT。允许转负(超卖告警在上层 · 见 08 ADR)。
    """
    delta = _num(qty_delta)
    existing = get_stock_for_update(
        cur,
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        batch_id=batch_id,
    )
    if existing:
        if reject_negative and Decimal(str(existing["qty_on_hand"])) + delta < 0:
            raise InsufficientStockError
        # id 来自上面 tenant 限定的 get_stock_for_update(且 FOR UPDATE 锁行);UPDATE 再带
        # tenant_id 是纵深防御——RLS 被 BYPASSRLS 架空,应用层每句自证隔离不依赖调用方纪律。
        cur.execute(
            "UPDATE inventory_stock SET qty_on_hand = qty_on_hand + %s, updated_at = now() "
            "WHERE id = %s AND tenant_id = %s RETURNING qty_on_hand",
            (delta, existing["id"], tenant_id),
        )
        return cur.fetchone()["qty_on_hand"]
    if reject_negative and delta < 0:
        raise InsufficientStockError
    cur.execute(
        "INSERT INTO inventory_stock "
        "(tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, qty_on_hand) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING qty_on_hand",
        (tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, delta),
    )
    return cur.fetchone()["qty_on_hand"]


# ── transactions(immutable 流水)──────────────────────────────────────
def find_txn_by_client_uuid(cur, *, tenant_id: str, client_uuid: str):
    cur.execute(
        f"SELECT {_TXN_COLS} FROM inventory_transactions "
        f"WHERE tenant_id = %s AND client_uuid = %s",
        (tenant_id, client_uuid),
    )
    return cur.fetchone()


def insert_txn(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    product_id: str,
    warehouse_id: int,
    batch_id: Optional[str],
    txn_type: str,
    qty_delta,
    unit_cost=None,
    ref_type=None,
    ref_id=None,
    client_uuid=None,
    reason=None,
    created_by=None,
) -> dict:
    cur.execute(
        f"INSERT INTO inventory_transactions "
        f"(tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, txn_type, "
        f" qty_delta, unit_cost, ref_type, ref_id, client_uuid, reason, created_by) "
        f"VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING {_TXN_COLS}",
        (
            tenant_id,
            workspace_client_id,
            product_id,
            warehouse_id,
            batch_id,
            txn_type,
            _num(qty_delta),
            _num(unit_cost),
            ref_type,
            ref_id,
            client_uuid,
            reason,
            created_by,
        ),
    )
    return cur.fetchone()


def weighted_avg_purchase_cost_loose(
    cur, *, tenant_id: str, workspace_client_id: int, product_id: str, warehouse_id: int
) -> Optional[Decimal]:
    """散装(无批次)库存的加权平均进货成本(POS 报表 COGS · 非批次品成本口径)。

    批次品有批次自带 unit_cost 可精确对账;散装货多次进价不同、无批次分摊,只能退而求其次用
    加权平均成本(WAC,零售通行口径):对该 (product, warehouse) 全部 purchase_in 且 batch_id
    IS NULL 的流水按数量加权。无任何带成本的进货记录 → None(诚实未知,不当 0)。
    """
    cur.execute(
        "SELECT SUM(qty_delta * unit_cost) AS cost_sum, SUM(qty_delta) AS qty_sum "
        "FROM inventory_transactions "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND product_id = %s "
        "AND warehouse_id = %s AND batch_id IS NULL AND txn_type = 'purchase_in' "
        "AND unit_cost IS NOT NULL AND qty_delta > 0",
        (tenant_id, workspace_client_id, product_id, warehouse_id),
    )
    row = cur.fetchone() or {}
    qty_sum = row.get("qty_sum")
    if not qty_sum or Decimal(str(qty_sum)) == 0:
        return None
    return Decimal(str(row["cost_sum"])) / Decimal(str(qty_sum))
