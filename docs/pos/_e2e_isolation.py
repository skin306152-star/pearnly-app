# -*- coding: utf-8 -*-
"""POS/库存跨租户隔离 E2E(POS 项目 · 安全审计 · docs/pos/10 §5.3)。

RLS 被架空(pos-rls-bypass),应用层每句 WHERE tenant_id 是唯一防线。本脚本在租户 A
(pearnly_e2e_3)真造一张小票 + 库存,再以另一真实租户 B 的 id 走同一套读接口,断言:
A 的小票/库存对 B 不可见(get_sale/find_by_client_uuid/库存查询全空)、跨租户账套归属校验
被拒(require_workspace)。正向对照:以 A 自己读得到。

一事务跑 + 结尾 ROLLBACK(零残留)。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_e2e_isolation.py
"""

import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.pos_api import PosError, require_workspace  # noqa: E402
from services.inventory import store as inv_store  # noqa: E402
from services.pos import cashier as cashier_dal  # noqa: E402
from services.pos import sale as sale_svc  # noqa: E402
from services.pos import sales_store  # noqa: E402
from services.pos import shift as shift_svc  # noqa: E402

E2E_USER = "pearnly_e2e_3"
results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL 未设置", file=sys.stderr)
        return 2
    conn = psycopg2.connect(url, sslmode="require")
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SET LOCAL app.bypass_rls='on'")
        cur.execute(
            "SELECT u.tenant_id AS tid, "
            "(SELECT id FROM workspace_clients WHERE tenant_id=u.tenant_id ORDER BY id LIMIT 1) AS ws "
            "FROM users u WHERE u.username=%s",
            (E2E_USER,),
        )
        a = cur.fetchone()
        if not a or not a["ws"]:
            print(f"缺 {E2E_USER} 锚点", file=sys.stderr)
            conn.rollback()
            return 2
        tid_a, ws_a = str(a["tid"]), a["ws"]

        # 另一真实租户 B(与 A 不同 · 有自己的 workspace)
        cur.execute(
            "SELECT DISTINCT wc.tenant_id AS tid, wc.id AS ws FROM workspace_clients wc "
            "WHERE wc.tenant_id <> %s ORDER BY wc.tenant_id LIMIT 1",
            (tid_a,),
        )
        b = cur.fetchone()
        if not b:
            print("找不到第二个租户做隔离对照", file=sys.stderr)
            conn.rollback()
            return 2
        tid_b, ws_b = str(b["tid"]), b["ws"]
        record("锚定两个真实租户 A/B", tid_a != tid_b, f"A={tid_a[:8]} B={tid_b[:8]}")
        # 同租户内不存在的套账 id,用于跨套账(同 tenant 不同 workspace)隔离断言(POS-RO-003)。
        ws_a_other = int(ws_a) + 999_000

        # 租户 A 造小票 + 库存
        cur.execute(
            "INSERT INTO products (tenant_id, name_th, base_unit, vat_applicable, is_active) "
            "VALUES (%s,'ISO-A','ชิ้น',TRUE,TRUE) RETURNING id",
            (tid_a,),
        )
        pid = str(cur.fetchone()["id"])
        wh = inv_store.get_or_create_default_warehouse(
            cur, tenant_id=tid_a, workspace_client_id=ws_a
        )
        cur.execute(
            "INSERT INTO inventory_stock "
            "(tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, qty_on_hand) "
            "VALUES (%s,%s,%s,%s,NULL,30)",
            (tid_a, ws_a, pid, wh["id"]),
        )
        term = cashier_dal.get_or_create_default_terminal(
            cur, tenant_id=tid_a, workspace_client_id=ws_a
        )
        c = cashier_dal.create_cashier(
            cur, tenant_id=tid_a, workspace_client_id=ws_a, display_name="ISO", pin_hash="x"
        )
        sh = shift_svc.open_shift(
            cur,
            tenant_id=tid_a,
            workspace_client_id=ws_a,
            terminal_id=term["id"],
            cashier_id=str(c["id"]),
            opening_float=0,
        )
        cu = "f0150001-0000-0000-0000-000000000001"
        sale = sale_svc.create_sale(
            cur,
            tenant_id=tid_a,
            workspace_client_id=ws_a,
            payload={
                "client_uuid": cu,
                "shift_id": sh["id"],
                "terminal_id": term["id"],
                "cashier_id": str(c["id"]),
                "price_includes_vat": False,
                "lines": [{"product_id": pid, "qty": 1, "unit_price": 10}],
                "payments": [{"method": "cash", "amount": 10}],
            },
        )
        sale_id = sale["sale"]["id"]

        # 正向对照:A 用自己的套账读得到
        record(
            "A 读自己的小票(正向对照)",
            sales_store.get_sale(cur, tenant_id=tid_a, workspace_client_id=ws_a, sale_id=sale_id)
            is not None,
        )

        # 隔离(跨套账 · 同租户不同 workspace · POS-RO-003):A 换个套账读不到自己的小票
        record(
            "同租户跨套账取不到小票(get_sale)",
            sales_store.get_sale(
                cur, tenant_id=tid_a, workspace_client_id=ws_a_other, sale_id=sale_id
            )
            is None,
        )
        record(
            "同租户跨套账取不到小票(by client_uuid)",
            sales_store.find_sale_by_client_uuid(
                cur, tenant_id=tid_a, workspace_client_id=ws_a_other, client_uuid=cu
            )
            is None,
        )

        # 隔离(跨租户):B 读不到 A 的小票
        record(
            "B 取不到 A 的小票(get_sale)",
            sales_store.get_sale(cur, tenant_id=tid_b, workspace_client_id=ws_b, sale_id=sale_id)
            is None,
        )
        record(
            "B 取不到 A 的小票(by client_uuid)",
            sales_store.find_sale_by_client_uuid(
                cur, tenant_id=tid_b, workspace_client_id=ws_b, client_uuid=cu
            )
            is None,
        )

        # 隔离:B 看不到 A 的库存(按 tenant_id + product 直查)
        cur.execute(
            "SELECT COUNT(*) AS c FROM inventory_stock WHERE tenant_id=%s AND product_id=%s",
            (tid_b, pid),
        )
        record("B 看不到 A 的库存行", cur.fetchone()["c"] == 0)

        # 跨租户账套归属:B 拿 A 的 workspace → 拒;A 拿自己 → 过
        try:
            require_workspace(cur, tid_b, ws_a)
            record("跨租户账套归属被拒", False, "未拒")
        except PosError as e:
            record("跨租户账套归属被拒(forbidden)", e.code == "pos.forbidden", e.code)
        try:
            require_workspace(cur, tid_a, ws_a)
            record("A 自己账套归属通过(正向对照)", True)
        except PosError as e:
            record("A 自己账套归属通过(正向对照)", False, e.code)

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
    print(f"\n{'='*52}\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
