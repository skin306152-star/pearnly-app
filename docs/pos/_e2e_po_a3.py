# -*- coding: utf-8 -*-
"""PO-A3 真库 E2E — 库存 4 表在真 Postgres 上验证 DB 级保证(单测的 FakeCursor 测不到的部分):
FEFO ORDER BY 真排序、NULL batch 的 partial unique、client_uuid 幂等唯一、FK、应用层隔离。

DDL 与 services/inventory/store.ensure_schema 同源;一事务建表 + 跑 + ROLLBACK(零残留)。
prod 运行:ssh pearnly → cd /opt/mrpilot → source .env → venv python 本文件。
"""

import os
import sys
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))


DDL = [
    """CREATE TABLE IF NOT EXISTS warehouses (
        id bigserial PRIMARY KEY, tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL,
        name text NOT NULL DEFAULT 'ร้าน', is_default boolean NOT NULL DEFAULT FALSE,
        is_active boolean NOT NULL DEFAULT TRUE, created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now())""",
    """CREATE TABLE IF NOT EXISTS inventory_batches (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
        product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE, batch_no text NOT NULL,
        expiry_date date, received_at date NOT NULL DEFAULT CURRENT_DATE, unit_cost numeric(14,2),
        created_at timestamptz NOT NULL DEFAULT now(), UNIQUE (tenant_id, product_id, batch_no))""",
    """CREATE TABLE IF NOT EXISTS inventory_stock (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        warehouse_id bigint NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
        batch_id uuid REFERENCES inventory_batches(id) ON DELETE CASCADE,
        qty_on_hand numeric(14,3) NOT NULL DEFAULT 0, qty_reserved numeric(14,3) NOT NULL DEFAULT 0,
        updated_at timestamptz NOT NULL DEFAULT now())""",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_nobatch ON inventory_stock "
    "(tenant_id, product_id, warehouse_id) WHERE batch_id IS NULL",
    """CREATE TABLE IF NOT EXISTS inventory_transactions (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        warehouse_id bigint NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
        batch_id uuid REFERENCES inventory_batches(id) ON DELETE SET NULL, txn_type text NOT NULL,
        qty_delta numeric(14,3) NOT NULL, unit_cost numeric(14,2), ref_type text, ref_id uuid,
        client_uuid uuid UNIQUE, reason text, created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now())""",
]


def main():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("NO DATABASE_URL", file=sys.stderr)
        return 2
    conn = psycopg2.connect(url, sslmode="require")
    try:
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, tenant_id FROM products LIMIT 1")
        prod = cur.fetchone()
        if not prod:
            print("no products to anchor FK", file=sys.stderr)
            conn.rollback()
            return 2
        pid, ta = prod["id"], prod["tenant_id"]
        tb = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        ws = 999999

        for stmt in DDL:
            cur.execute(stmt)

        cur.execute(
            "INSERT INTO warehouses (tenant_id, workspace_client_id, is_default) "
            "VALUES (%s,%s,TRUE) RETURNING id",
            (ta, ws),
        )
        wh = cur.fetchone()["id"]

        # 两批不同效期 + 各自库存
        for batch_no, days, qty in (("NEAR", 5, 3), ("FAR", 60, 10)):
            cur.execute(
                "INSERT INTO inventory_batches (tenant_id, product_id, batch_no, expiry_date) "
                "VALUES (%s,%s,%s, CURRENT_DATE + %s) RETURNING id",
                (ta, pid, batch_no, days),
            )
            bid = cur.fetchone()["id"]
            cur.execute(
                "INSERT INTO inventory_stock "
                "(tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, qty_on_hand) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (ta, ws, pid, wh, bid, Decimal(str(qty))),
            )

        # FEFO ORDER BY 真排序:近效期 NEAR 在前
        cur.execute(
            "SELECT b.batch_no FROM inventory_stock s JOIN inventory_batches b ON b.id=s.batch_id "
            "WHERE s.tenant_id=%s AND s.workspace_client_id=%s AND s.product_id=%s "
            "AND s.batch_id IS NOT NULL AND s.qty_on_hand>0 "
            "ORDER BY b.expiry_date ASC NULLS LAST, b.received_at ASC",
            (ta, ws, pid),
        )
        order = [r["batch_no"] for r in cur.fetchall()]
        record("FEFO 近效期批在前", order == ["NEAR", "FAR"], str(order))

        # 近效期查询(days=30 → 只 NEAR)
        cur.execute(
            "SELECT b.batch_no FROM inventory_stock s JOIN inventory_batches b ON b.id=s.batch_id "
            "WHERE s.tenant_id=%s AND s.workspace_client_id=%s AND s.batch_id IS NOT NULL "
            "AND b.expiry_date IS NOT NULL AND b.expiry_date <= CURRENT_DATE + 30 AND s.qty_on_hand>0",
            (ta, ws),
        )
        ne = [r["batch_no"] for r in cur.fetchall()]
        record("近效期(30天)只含 NEAR", ne == ["NEAR"], str(ne))

        # stock_overview 聚合不被批次数翻倍(预聚合子查询 join · 实测 bug 回归)
        cur.execute(
            "SELECT COALESCE(SUM(s.qty_on_hand),0) AS qty, COALESCE(MAX(b.avg_cost), p.default_cost) AS avg "
            "FROM products p "
            "LEFT JOIN inventory_stock s ON s.product_id=p.id AND s.tenant_id=p.tenant_id "
            "  AND s.workspace_client_id=%s "
            "LEFT JOIN (SELECT product_id, AVG(unit_cost) AS avg_cost FROM inventory_batches "
            "           WHERE tenant_id=%s GROUP BY product_id) b ON b.product_id=p.id "
            "WHERE p.tenant_id=%s AND p.id=%s GROUP BY p.id, p.default_cost",
            (ws, ta, ta, pid),
        )
        agg = cur.fetchone()
        record("库存汇总不被批次数翻倍(=13 非 26)", agg["qty"] == Decimal("13"), str(agg["qty"]))

        # NULL batch 的 partial unique:同 (product,wh,NULL) 第二行被拒
        cur.execute(
            "INSERT INTO inventory_stock (tenant_id, workspace_client_id, product_id, warehouse_id, qty_on_hand) "
            "VALUES (%s,%s,%s,%s,1)",
            (ta, ws, pid, wh),
        )
        try:
            cur.execute("SAVEPOINT s1")
            cur.execute(
                "INSERT INTO inventory_stock (tenant_id, workspace_client_id, product_id, warehouse_id, qty_on_hand) "
                "VALUES (%s,%s,%s,%s,1)",
                (ta, ws, pid, wh),
            )
            record("NULL batch partial unique 拦重复", False, "竟插入成功")
        except psycopg2.Error:
            cur.execute("ROLLBACK TO SAVEPOINT s1")
            record("NULL batch partial unique 拦重复", True, "被拒")

        # client_uuid 幂等唯一:同 client_uuid 第二笔流水被拒
        cur.execute(
            "INSERT INTO inventory_transactions "
            "(tenant_id, workspace_client_id, product_id, warehouse_id, txn_type, qty_delta, client_uuid) "
            "VALUES (%s,%s,%s,%s,'purchase_in',5,'11111111-1111-1111-1111-111111111111')",
            (ta, ws, pid, wh),
        )
        try:
            cur.execute("SAVEPOINT s2")
            cur.execute(
                "INSERT INTO inventory_transactions "
                "(tenant_id, workspace_client_id, product_id, warehouse_id, txn_type, qty_delta, client_uuid) "
                "VALUES (%s,%s,%s,%s,'purchase_in',5,'11111111-1111-1111-1111-111111111111')",
                (ta, ws, pid, wh),
            )
            record("client_uuid 幂等唯一拦重复补传", False, "竟插入成功")
        except psycopg2.Error:
            cur.execute("ROLLBACK TO SAVEPOINT s2")
            record("client_uuid 幂等唯一拦重复补传", True, "被拒")

        # 应用层隔离:租户 B 看不到 A 的库存
        cur.execute(
            "SELECT count(*) AS n FROM inventory_stock WHERE tenant_id=%s AND product_id=%s",
            (tb, pid),
        )
        record("B 看不到 A 的库存(应用层隔离)", cur.fetchone()["n"] == 0)
    finally:
        conn.rollback()
        conn.close()

    print("\n── PO-A3 真库 E2E(库存 DB 级保证 · 回滚零残留)──")
    passed = sum(1 for _n, ok, _d in results if ok)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  · {detail}")
    print(f"  → {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
