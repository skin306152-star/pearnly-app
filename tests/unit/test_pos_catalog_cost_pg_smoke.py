# -*- coding: utf-8 -*-
"""POS 商品平均成本查询的真 PostgreSQL 方言与优先级冒烟。"""

from __future__ import annotations

import unittest
import uuid
from decimal import Decimal

from services.inventory import queries
from services.pos import stock
from tests.unit._pg_smoke import connect_or_skip


class PosCatalogCostPgSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        from psycopg2.extras import RealDictCursor

        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        cls.cur.execute(
            "CREATE TEMP TABLE products ("
            "id uuid PRIMARY KEY, tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL, "
            "default_cost numeric)"
        )
        cls.cur.execute(
            "CREATE TEMP TABLE inventory_batches ("
            "product_id uuid NOT NULL, tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL, "
            "unit_cost numeric)"
        )
        cls.cur.execute(
            "CREATE TEMP TABLE inventory_transactions ("
            "product_id uuid NOT NULL, tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL, "
            "warehouse_id bigint, qty_delta numeric, unit_cost numeric, txn_type text, batch_id uuid)"
        )

    @classmethod
    def tearDownClass(cls):
        cls.cur.close()
        cls.conn.rollback()
        cls.conn.close()

    def test_batch_then_loose_wac_then_default_cost(self):
        tenant = str(uuid.uuid4())
        other_tenant = str(uuid.uuid4())
        batch_id = str(uuid.uuid4())
        loose_id = str(uuid.uuid4())
        default_id = str(uuid.uuid4())
        ids = [batch_id, loose_id, default_id]
        self.cur.executemany(
            "INSERT INTO products (id, tenant_id, workspace_client_id, default_cost) "
            "VALUES (%s, %s, 9, %s)",
            [
                (batch_id, tenant, Decimal("99.00")),
                (loose_id, tenant, Decimal("88.00")),
                (default_id, tenant, Decimal("3.25")),
            ],
        )
        self.cur.executemany(
            "INSERT INTO inventory_batches "
            "(product_id, tenant_id, workspace_client_id, unit_cost) VALUES (%s, %s, %s, %s)",
            [
                (batch_id, tenant, 9, Decimal("6.00")),
                (batch_id, tenant, 9, Decimal("8.00")),
                (batch_id, other_tenant, 9, Decimal("900.00")),
                (batch_id, tenant, 10, Decimal("800.00")),
            ],
        )
        self.cur.executemany(
            "INSERT INTO inventory_transactions "
            "(product_id, tenant_id, workspace_client_id, qty_delta, unit_cost, txn_type, batch_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [
                (loose_id, tenant, 9, Decimal("2"), Decimal("4.00"), "purchase_in", None),
                (loose_id, tenant, 9, Decimal("3"), Decimal("10.00"), "purchase_in", None),
                (loose_id, other_tenant, 9, Decimal("1"), Decimal("999.00"), "purchase_in", None),
                (loose_id, tenant, 10, Decimal("1"), Decimal("777.00"), "purchase_in", None),
                (loose_id, tenant, 9, Decimal("1"), Decimal("555.00"), "sale", None),
                (
                    loose_id,
                    tenant,
                    9,
                    Decimal("1"),
                    Decimal("444.00"),
                    "purchase_in",
                    str(uuid.uuid4()),
                ),
            ],
        )

        result = queries.average_costs_by_product(
            self.cur,
            tenant_id=tenant,
            workspace_client_id=9,
            product_ids=ids,
        )

        self.assertEqual(result[batch_id], Decimal("7.00"))
        self.assertEqual(result[loose_id], Decimal("7.6000000000000000"))
        self.assertEqual(result[default_id], Decimal("3.25"))

    def test_sale_cost_uses_reference_only_when_actual_cost_is_missing(self):
        tenant = str(uuid.uuid4())
        product_id = str(uuid.uuid4())
        self.cur.execute(
            "INSERT INTO products (id, tenant_id, workspace_client_id, default_cost) "
            "VALUES (%s, %s, 9, 4.50)",
            (product_id, tenant),
        )

        result = stock.cost_for_moves(
            self.cur,
            tenant_id=tenant,
            workspace_client_id=9,
            warehouse_id=3,
            product_id=product_id,
            moves=[(None, Decimal("2"))],
        )

        self.assertEqual(result, Decimal("9.00"))
        self.cur.execute(
            "SELECT COUNT(*) AS count FROM inventory_transactions "
            "WHERE tenant_id = %s AND product_id = %s",
            (tenant, product_id),
        )
        self.assertEqual(self.cur.fetchone()["count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
