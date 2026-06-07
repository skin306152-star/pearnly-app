# -*- coding: utf-8 -*-
"""餐厅前端 E2E 播种(prod · 测试租户 pearnly_e2e_3 · 持久化 · 幂等)。

把测试租户开成餐厅业态供 /pos 前端真浏览器 E2E:pos 模块(business_type=restaurant)+ 仓 + 终端 +
收银员(PIN 1234)+ 区域 + 3 桌 + 3 菜品。仅测试账号,可重复跑。运行:注入 DATABASE_URL 后执行。
"""

import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from services.pos.auth import hash_pin  # noqa: E402

TID = "152de6e5-29eb-437d-bb2c-5d408695e60e"
WS = 11
PINH = hash_pin("1234")


def main():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("NO DATABASE_URL", file=sys.stderr)
        return 2
    c = psycopg2.connect(url, sslmode="require")
    c.autocommit = False
    cur = c.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "INSERT INTO tenant_modules (tenant_id, module_key, enabled, config) "
        "VALUES (%s,'pos',TRUE,%s::jsonb) "
        "ON CONFLICT (tenant_id, module_key) DO UPDATE SET enabled=TRUE, config=EXCLUDED.config",
        (TID, '{"business_type":"restaurant","tables":true,"kitchen":true}'),
    )
    cur.execute(
        "INSERT INTO tenant_modules (tenant_id, module_key, enabled) VALUES (%s,'inventory',TRUE) "
        "ON CONFLICT (tenant_id, module_key) DO UPDATE SET enabled=TRUE",
        (TID,),
    )
    cur.execute(
        "SELECT id FROM warehouses WHERE tenant_id=%s AND workspace_client_id=%s LIMIT 1", (TID, WS)
    )
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO warehouses (tenant_id, workspace_client_id, name, is_default, is_active) "
            "VALUES (%s,%s,'门店',TRUE,TRUE)",
            (TID, WS),
        )
    cur.execute(
        "SELECT id FROM pos_terminals WHERE tenant_id=%s AND workspace_client_id=%s LIMIT 1",
        (TID, WS),
    )
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO pos_terminals (tenant_id, workspace_client_id, name) VALUES (%s,%s,'T1')",
            (TID, WS),
        )
    cur.execute(
        "SELECT id FROM pos_cashiers WHERE tenant_id=%s AND workspace_client_id=%s AND display_name=%s",
        (TID, WS, "E2E 餐厅"),
    )
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO pos_cashiers (tenant_id, workspace_client_id, display_name, pin_hash, color) "
            "VALUES (%s,%s,'E2E 餐厅',%s,'#2563EB')",
            (TID, WS, PINH),
        )

    cur.execute(
        "SELECT id FROM pos_areas WHERE tenant_id=%s AND workspace_client_id=%s AND name='大厅 A'",
        (TID, WS),
    )
    row = cur.fetchone()
    if row:
        area_id = row["id"]
    else:
        cur.execute(
            "INSERT INTO pos_areas (tenant_id, workspace_client_id, name) VALUES (%s,%s,'大厅 A') RETURNING id",
            (TID, WS),
        )
        area_id = cur.fetchone()["id"]
    for i, name in enumerate(("R1", "R2", "R3"), start=1):
        cur.execute(
            "SELECT 1 FROM pos_tables WHERE tenant_id=%s AND workspace_client_id=%s AND name=%s",
            (TID, WS, name),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO pos_tables (tenant_id, workspace_client_id, area_id, name, seats, sort) "
                "VALUES (%s,%s,%s,%s,4,%s)",
                (TID, WS, area_id, name, i),
            )
    for name_th, price in (
        ("ผัดกะเพรา 打抛猪饭", "120.00"),
        ("โค้ก 可乐", "15.00"),
        ("มะม่วงข้าวเหนียว 芒果糯米", "90.00"),
    ):
        cur.execute(
            "SELECT 1 FROM products WHERE tenant_id=%s AND name_th=%s AND is_active=TRUE",
            (TID, name_th),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO products (tenant_id, name_th, name_en, name_zh, unit_price, base_unit, vat_applicable, is_active) "
                "VALUES (%s,%s,%s,%s,%s,'จาน',TRUE,TRUE)",
                (TID, name_th, name_th, name_th, price),
            )
    c.commit()

    cur.execute(
        "SELECT COUNT(*) AS n FROM pos_tables WHERE tenant_id=%s AND workspace_client_id=%s",
        (TID, WS),
    )
    tables = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM products WHERE tenant_id=%s AND is_active=TRUE", (TID,))
    prods = cur.fetchone()["n"]
    c.close()
    print(f"seeded restaurant tenant: tables={tables} products={prods} cashier=E2E 餐厅/1234")
    return 0


if __name__ == "__main__":
    sys.exit(main())
