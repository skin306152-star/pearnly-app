"""POS 商品名称快照的真实 PostgreSQL 冒烟。"""

import unittest
import uuid

from services.pos import sales_store
from services.products.names import display_product_name
from tests.unit._pg_smoke import connect_or_skip


class ProductNameSnapshotPgSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        from psycopg2.extras import RealDictCursor

        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        cls.cur.execute(
            "CREATE TEMP TABLE products ("
            "id uuid PRIMARY KEY, name_th text, name_en text, name_zh text)"
        )
        cls.cur.execute(
            "CREATE TEMP TABLE pos_sale_lines ("
            "id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid, sale_id uuid, "
            "product_id uuid, product_name_snapshot text, sell_unit text, unit_factor numeric, "
            "qty numeric, qty_base numeric, unit_price numeric, line_discount numeric, "
            "vat_applicable boolean, batch_id uuid, refund_of_line_id uuid, line_total numeric, "
            "cost_total numeric)"
        )

    @classmethod
    def tearDownClass(cls):
        cls.cur.close()
        cls.conn.rollback()
        cls.conn.close()

    def test_product_edit_does_not_change_the_sale_line_name(self):
        tenant_id = str(uuid.uuid4())
        sale_id = str(uuid.uuid4())
        product_id = str(uuid.uuid4())
        self.cur.execute(
            "INSERT INTO products (id, name_th, name_en, name_zh) VALUES (%s, %s, %s, %s) "
            "RETURNING name_th, name_en, name_zh",
            (product_id, "น้ำ", "Water", "水"),
        )
        snapshot = display_product_name(self.cur.fetchone())
        sales_store.insert_line(
            self.cur,
            tenant_id=tenant_id,
            sale_id=sale_id,
            fields={
                "product_id": product_id,
                "product_name_snapshot": snapshot,
                "sell_unit": "ขวด",
                "unit_factor": 1,
                "qty": 1,
                "qty_base": 1,
                "unit_price": 10,
                "line_discount": 0,
                "vat_applicable": True,
                "batch_id": None,
                "refund_of_line_id": None,
                "line_total": 10,
                "cost_total": 5,
            },
        )
        self.cur.execute(
            "UPDATE products SET name_th = %s, name_en = %s, name_zh = %s WHERE id = %s",
            ("ชื่อใหม่", "New name", "新名称", product_id),
        )

        line = sales_store.list_lines(self.cur, tenant_id=tenant_id, sale_id=sale_id)[0]
        self.assertEqual(line["product_name_snapshot"], "น้ำ / Water / 水")


if __name__ == "__main__":
    unittest.main()
