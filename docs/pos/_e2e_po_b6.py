# -*- coding: utf-8 -*-
"""PO-B6 真库 E2E — 销售报表聚合(POS 项目 · docs/pos/04 §7)。

真 Postgres 验证 FakeCursor 测不到的、且专打笛卡尔积陷阱:建一张「2 行 + 2 支付」的小票
(若 by_method 误 join lines、或 top_products 误 join payments,金额/数量会翻倍)。用建单
前后的报表增量断言:KPI gross +107(非 214)、by_method 合计 +107(非 214)、畅销品该商品
qty +2(非 4)、并验新建收银员名下恰好 1 单 107(by_cashier 隔离干净)。

一事务跑 + 结尾 ROLLBACK(零残留)。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_e2e_po_b6.py
"""

import os
import sys
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.inventory import store as inv_store  # noqa: E402
from services.pos import cashier as cashier_dal  # noqa: E402
from services.pos import report as report_svc  # noqa: E402
from services.pos import sale as sale_svc  # noqa: E402
from services.pos import shift as shift_svc  # noqa: E402

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def _D(v):
    return Decimal(str(v))


def _method_total(rep) -> Decimal:
    return sum((_D(v) for v in rep["by_method"].values()), Decimal("0"))


def _prod_qty(rep, pid) -> Decimal:
    for t in rep["top_products"]:
        if t["product_id"] == pid:
            return _D(t["qty"])
    return Decimal("0")


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL 未设置", file=sys.stderr)
        return 2
    conn = psycopg2.connect(url, sslmode="require")
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SET LOCAL app.bypass_rls = 'on'")
        cur.execute(
            "SELECT wc.id AS ws, wc.tenant_id AS tid, "
            "(SELECT id FROM products WHERE tenant_id = wc.tenant_id AND is_active = TRUE LIMIT 1) AS pid "
            "FROM workspace_clients wc "
            "WHERE EXISTS (SELECT 1 FROM products WHERE tenant_id = wc.tenant_id AND is_active = TRUE) "
            "ORDER BY wc.id LIMIT 1"
        )
        anchor = cur.fetchone()
        if not anchor or not anchor["pid"]:
            print("缺锚点", file=sys.stderr)
            conn.rollback()
            return 2
        ws, tid, pid = anchor["ws"], str(anchor["tid"]), str(anchor["pid"])

        cur.execute(
            "UPDATE products SET track_batch = FALSE, vat_applicable = TRUE WHERE id = %s", (pid,)
        )
        wh = inv_store.get_or_create_default_warehouse(cur, tenant_id=tid, workspace_client_id=ws)
        cur.execute(
            "INSERT INTO inventory_stock "
            "(tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, qty_on_hand) "
            "VALUES (%s,%s,%s,%s,NULL,100) ON CONFLICT DO NOTHING",
            (tid, ws, pid, wh["id"]),
        )
        term = cashier_dal.get_or_create_default_terminal(
            cur, tenant_id=tid, workspace_client_id=ws
        )
        cashier = cashier_dal.create_cashier(
            cur, tenant_id=tid, workspace_client_id=ws, display_name="B6-E2E", pin_hash="x"
        )
        cid = str(cashier["id"])
        sh = shift_svc.open_shift(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            terminal_id=term["id"],
            cashier_id=cid,
            opening_float=0,
        )

        before = report_svc.sales_report(cur, tenant_id=tid, workspace_client_id=ws)

        # 2 行 + 2 支付:行小计 50+50=100,价外 VAT7% → grand 107;支付 cash 50 + promptpay 57
        payload = {
            "client_uuid": "b6000001-0000-0000-0000-000000000001",
            "shift_id": sh["id"],
            "terminal_id": term["id"],
            "cashier_id": cid,
            "lines": [
                {"product_id": pid, "qty": 1, "unit_price": 50},
                {"product_id": pid, "qty": 1, "unit_price": 50},
            ],
            "payments": [
                {"method": "cash", "amount": 50},
                {"method": "promptpay", "amount": 57},
            ],
        }
        sold = sale_svc.create_sale(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            payload=payload,
            operator={"cashier_id": cid},
        )
        record(
            "建 2行2支付小票 grand=107",
            sold["sale"]["grand_total"] == "107.00",
            sold["sale"]["grand_total"],
        )

        after = report_svc.sales_report(cur, tenant_id=tid, workspace_client_id=ws)

        d_gross = _D(after["kpi"]["gross"]) - _D(before["kpi"]["gross"])
        d_count = after["kpi"]["sales_count"] - before["kpi"]["sales_count"]
        record("KPI gross +107(非笛卡尔翻倍)", d_gross == Decimal("107.00"), f"+{d_gross}")
        record("KPI 单数 +1", d_count == 1, f"+{d_count}")

        d_method = _method_total(after) - _method_total(before)
        record(
            "by_method 合计 +107(payments 未误乘 lines)",
            d_method == Decimal("107.00"),
            f"+{d_method}",
        )

        d_qty = _prod_qty(after, pid) - _prod_qty(before, pid)
        record("畅销品 qty +2(lines 未误乘 payments)", d_qty == Decimal("2.000"), f"+{d_qty}")

        # 新建收银员名下恰好 1 单 107(by_cashier 隔离干净)
        mine = [c for c in after["by_cashier"] if c["cashier_id"] == cid]
        record(
            "by_cashier 新收银员 1 单/107",
            len(mine) == 1 and mine[0]["sales_count"] == 1 and mine[0]["gross"] == "107.00",
            str(mine),
        )

        conn.rollback()
    except Exception as e:
        conn.rollback()
        import traceback

        traceback.print_exc()
        print(f"E2E 异常: {e}", file=sys.stderr)
        return 2
    finally:
        cur.close()
        conn.close()

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{'='*50}\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
