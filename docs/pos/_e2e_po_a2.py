# -*- coding: utf-8 -*-
"""PO-A2 真库 E2E — product_units 在真 Postgres 上验证应用层隔离 + 单一默认 + Decimal 换算。

内联 SQL 与 services/products/units.py 逐字一致(test_product_units_store 已断言 DAL 发出
这些语句)。隔离硬保证 = 应用层 WHERE tenant_id(prod 角色 BYPASSRLS · RLS 仅兜底)。
一事务内建表 + 跑 + ROLLBACK(零残留)。不 ALTER 线上 products(避免锁活表;列由 ensure_schema
部署后建,post-deploy 用 information_schema 复验)。

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


def clear_default(cur, ta, pid):
    cur.execute(
        "UPDATE product_units SET is_default_sell=FALSE, updated_at=now() "
        "WHERE tenant_id=%s AND product_id=%s AND is_default_sell=TRUE",
        (ta, pid),
    )


def create_unit(cur, ta, pid, name, factor, default):
    if default:
        clear_default(cur, ta, pid)
    cur.execute(
        "INSERT INTO product_units (tenant_id, product_id, unit_name, factor_to_base, is_default_sell) "
        "VALUES (%s,%s,%s,%s,%s) RETURNING factor_to_base",
        (ta, pid, name, Decimal(str(factor)), default),
    )
    return cur.fetchone()


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
            print("no products in prod to anchor FK", file=sys.stderr)
            conn.rollback()
            return 2
        pid, ta = prod["id"], prod["tenant_id"]
        tb = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        cur.execute(
            "CREATE TABLE IF NOT EXISTS product_units ("
            " id uuid PRIMARY KEY DEFAULT gen_random_uuid(),"
            " tenant_id uuid NOT NULL,"
            " product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,"
            " unit_name text NOT NULL, factor_to_base numeric(14,3) NOT NULL,"
            " barcode text, price numeric(14,2),"
            " is_default_sell boolean NOT NULL DEFAULT FALSE,"
            " created_at timestamptz NOT NULL DEFAULT now(),"
            " updated_at timestamptz NOT NULL DEFAULT now(),"
            " UNIQUE (tenant_id, product_id, unit_name))"
        )

        r1 = create_unit(cur, ta, pid, "กล่อง", 100, True)
        record(
            "factor_to_base 存为 Decimal(14,3)",
            r1["factor_to_base"] == Decimal("100.000"),
            str(r1["factor_to_base"]),
        )
        create_unit(cur, ta, pid, "ขวด", 1, True)  # 第二个设默认 → 应清掉第一个

        cur.execute(
            "SELECT unit_name, is_default_sell FROM product_units "
            "WHERE tenant_id=%s AND product_id=%s ORDER BY factor_to_base",
            (ta, pid),
        )
        rows = cur.fetchall()
        record("A 看到自己 2 个单位", len(rows) == 2, str([r["unit_name"] for r in rows]))
        defaults = [r["unit_name"] for r in rows if r["is_default_sell"]]
        record("单一默认(只 ขวด)", defaults == ["ขวด"], str(defaults))

        cur.execute(
            "SELECT count(*) AS n FROM product_units WHERE tenant_id=%s AND product_id=%s",
            (tb, pid),
        )
        record("B 看不到 A 的单位(应用层隔离)", cur.fetchone()["n"] == 0)

        # FK:挂到不存在的 product_id 被拒
        try:
            cur.execute("SAVEPOINT sp1")
            cur.execute(
                "INSERT INTO product_units (tenant_id, product_id, unit_name, factor_to_base) "
                "VALUES (%s,%s,'x',1)",
                (ta, "00000000-0000-0000-0000-000000000000"),
            )
            record("FK 拒绝挂到不存在商品", False, "竟插入成功")
        except psycopg2.Error:
            cur.execute("ROLLBACK TO SAVEPOINT sp1")
            record("FK 拒绝挂到不存在商品", True, "被拒(符合预期)")
    finally:
        conn.rollback()
        conn.close()

    print("\n── PO-A2 真库 E2E(product_units · 应用层隔离 · 回滚零残留)──")
    passed = sum(1 for _n, ok, _d in results if ok)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  · {detail}")
    print(f"  → {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
