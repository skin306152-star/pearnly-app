# -*- coding: utf-8 -*-
"""PO-B5 真库 E2E — 离线批量补传 sync(POS 项目 · docs/pos/04 §6 sync)。

真 Postgres 验证 FakeCursor 测不到的:一批混合(有效 / 同 client_uuid 重复 / 坏品)走
sync_sales,逐张 SAVEPOINT 隔离——有效张落库且扣库存、重复张 deduped 不双扣、坏张
line_invalid 被回退且不污染同批其余;批后库存只减一次。

一事务跑 + 结尾 ROLLBACK(零残留)。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_e2e_po_b5.py
"""

import os
import sys
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.inventory import store as inv_store  # noqa: E402
from services.pos import cashier as cashier_dal  # noqa: E402
from services.pos import sale as sale_svc  # noqa: E402
from services.pos import shift as shift_svc  # noqa: E402

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def _stock(cur, tid, ws, pid) -> Decimal:
    cur.execute(
        "SELECT COALESCE(SUM(qty_on_hand),0) AS q FROM inventory_stock "
        "WHERE tenant_id=%s AND workspace_client_id=%s AND product_id=%s",
        (tid, ws, pid),
    )
    return Decimal(str(cur.fetchone()["q"]))


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
            cur, tenant_id=tid, workspace_client_id=ws, display_name="B5-E2E", pin_hash="x"
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

        before = _stock(cur, tid, ws, pid)

        def _item(cu, product_id):
            return {
                "client_uuid": cu,
                "shift_id": sh["id"],
                "terminal_id": term["id"],
                "lines": [{"product_id": product_id, "qty": 1, "unit_price": 10}],
                "payments": [{"method": "cash", "amount": 10}],
            }

        a = "b5000001-0000-0000-0000-000000000001"
        b = "b5000002-0000-0000-0000-000000000002"
        bad_pid = "00000000-0000-0000-0000-0000000000ff"
        batch = [_item(a, pid), _item(a, pid), _item(b, bad_pid)]

        out = sale_svc.sync_sales(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            items=batch,
            cashier_id=cid,
            operator={"cashier_id": cid},
        )
        r = out["results"]
        record("有效张落库", r[0]["ok"] and not r[0]["deduped"], r[0].get("receipt_no"))
        record(
            "重复张 deduped 不双扣",
            r[1]["ok"] and r[1]["deduped"] is True,
            str(r[1].get("deduped")),
        )
        record(
            "坏品张被拦 line_invalid(不卡批)",
            (not r[2]["ok"]) and r[2]["error"]["code"] == "pos.line_invalid",
            r[2].get("error", {}).get("code"),
        )

        after = _stock(cur, tid, ws, pid)
        record("批后库存只减一次(100→99)", after == before - Decimal("1"), f"{before}→{after}")

        # 同 client_uuid 只落一张
        cur.execute(
            "SELECT COUNT(*) AS c FROM pos_sales WHERE tenant_id=%s AND client_uuid=%s", (tid, a)
        )
        record("同 client_uuid 只一张", cur.fetchone()["c"] == 1)

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
