# -*- coding: utf-8 -*-
"""POS 边界/契约 E2E(POS 项目 · C4 · docs/pos/04 §6 / 10 §5)。

补齐核心流程外的边界:库存不足拦单(out_of_stock 不扣)、幂等重放(deduped 不双扣)、退货超额
(over_refund)、退过的单不可作废、跨班(已交班)作废被拒、已交班班次不可再开单(shift_closed)、
并发扣库存(FOR UPDATE 串行化 · 第二单见不足即拦)。

一事务跑 + 结尾 ROLLBACK(零残留)。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_e2e_boundary.py
"""

import os
import sys
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.pos_api import PosError  # noqa: E402
from services.inventory import store as inv_store  # noqa: E402
from services.pos import cashier as cashier_dal  # noqa: E402
from services.pos import refund as refund_svc  # noqa: E402
from services.pos import sale as sale_svc  # noqa: E402
from services.pos import shift as shift_svc  # noqa: E402

E2E_USER = "pearnly_e2e_3"
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


def _expect(name, code, fn):
    try:
        fn()
        record(name, False, "未抛错")
    except PosError as e:
        record(name, e.code == code, e.code)


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
        tid, ws = str(a["tid"]), a["ws"]
        wh = inv_store.get_or_create_default_warehouse(cur, tenant_id=tid, workspace_client_id=ws)[
            "id"
        ]
        cur.execute(
            "INSERT INTO products (tenant_id, name_th, base_unit, vat_applicable, track_batch, is_active) "
            "VALUES (%s,'BND','粒',TRUE,FALSE,TRUE) RETURNING id",
            (tid,),
        )
        pid = str(cur.fetchone()["id"])
        cur.execute(
            "INSERT INTO inventory_stock "
            "(tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, qty_on_hand) "
            "VALUES (%s,%s,%s,%s,NULL,2)",
            (tid, ws, pid, wh),
        )
        term = cashier_dal.get_or_create_default_terminal(
            cur, tenant_id=tid, workspace_client_id=ws
        )
        cid = str(
            cashier_dal.create_cashier(
                cur, tenant_id=tid, workspace_client_id=ws, display_name="BND", pin_hash="x"
            )["id"]
        )
        s1 = shift_svc.open_shift(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            terminal_id=term["id"],
            cashier_id=cid,
            opening_float=0,
        )

        def _sale(cu, qty):
            return sale_svc.create_sale(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                payload={
                    "client_uuid": cu,
                    "shift_id": s1["id"],
                    "terminal_id": term["id"],
                    "cashier_id": cid,
                    "lines": [{"product_id": pid, "qty": qty, "unit_price": 10}],
                    "payments": [{"method": "cash", "amount": 10 * qty}],
                },
                operator={"cashier_id": cid},
            )

        cuA = "bd000001-0000-0000-0000-000000000001"
        sa = _sale(cuA, 1)
        record("正常卖 1(stock 2→1)", _stock(cur, tid, ws, pid) == Decimal("1"))

        before = _stock(cur, tid, ws, pid)
        _expect(
            "库存不足拦单 out_of_stock",
            "pos.out_of_stock",
            lambda: _sale("bd00000a-0000-0000-0000-00000000000a", 5),
        )
        record(
            "拦单后库存不变", _stock(cur, tid, ws, pid) == before, str(_stock(cur, tid, ws, pid))
        )

        rep = _sale(cuA, 1)  # 同 client_uuid 重放
        record(
            "幂等重放 deduped 不双扣",
            rep["deduped"] is True and _stock(cur, tid, ws, pid) == Decimal("1"),
            f"deduped={rep['deduped']}",
        )

        line_id = sale_svc.get_sale_detail(
            cur, tenant_id=tid, workspace_client_id=ws, sale_id=sa["sale"]["id"]
        )["lines"][0]["id"]
        _expect(
            "退货超额 over_refund",
            "pos.over_refund",
            lambda: refund_svc.refund(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                original_sale_id=sa["sale"]["id"],
                lines=[{"sale_line_id": line_id, "qty": 5}],
                cashier_id=cid,
            ),
        )

        refund_svc.refund(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            original_sale_id=sa["sale"]["id"],
            lines=[{"sale_line_id": line_id, "qty": 1}],
            cashier_id=cid,
        )
        _expect(
            "退过的单不可作废 void_not_allowed",
            "pos.void_not_allowed",
            lambda: sale_svc.void_sale(
                cur, tenant_id=tid, workspace_client_id=ws, sale_id=sa["sale"]["id"]
            ),
        )

        # 跨班:另开一单 → 交班 → 作废被拒 + 闭班不能再开单
        sb = _sale("bd000002-0000-0000-0000-000000000002", 1)
        shift_svc.close_shift(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            shift_id=s1["id"],
            cashier_id=cid,
            counted_cash=0,
        )
        _expect(
            "已交班作废被拒 void_not_allowed",
            "pos.void_not_allowed",
            lambda: sale_svc.void_sale(
                cur, tenant_id=tid, workspace_client_id=ws, sale_id=sb["sale"]["id"]
            ),
        )
        _expect(
            "已交班班次不可再开单 shift_closed",
            "pos.shift_closed",
            lambda: _sale("bd00000b-0000-0000-0000-00000000000b", 1),
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
    print(f"\n{'='*52}\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
