# -*- coding: utf-8 -*-
"""C1 真库 E2E — 库存报表(进销存/周转/近效期看板)(POS 项目 · docs/pos/04 §4)。

真 Postgres 验证 FilTER 分区聚合的期间边界与笛卡尔积防护:给一个干净商品造受控流水(期初前
入 100 / 期内入 50 / 期内售 30 / 期内调减 5),断言进销存 期初100·入50·出35·售30·期末115 +
周转率;再造三批不同效期库存,断言近效期看板分桶(已过期/≤7天/≤30天)+ 风险货值。

一事务跑 + 结尾 ROLLBACK(零残留)。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_e2e_c1.py
"""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.inventory import reports as report_svc  # noqa: E402
from services.inventory import store as inv_store  # noqa: E402

E2E_USER = "pearnly_e2e_3"
results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def _txn(cur, tid, ws, pid, wh, days_ago, qty_delta, txn_type):
    cur.execute(
        "INSERT INTO inventory_transactions "
        "(tenant_id, workspace_client_id, product_id, warehouse_id, txn_type, qty_delta, created_at) "
        "VALUES (%s,%s,%s,%s,%s,%s, now() - (%s || ' days')::interval)",
        (tid, ws, pid, wh, txn_type, qty_delta, days_ago),
    )


def _batch(cur, tid, ws, pid, wh, expiry_days, qty, cost):
    cur.execute(
        "INSERT INTO inventory_batches (tenant_id, product_id, batch_no, expiry_date, unit_cost) "
        "VALUES (%s,%s,%s, CURRENT_DATE + %s, %s) RETURNING id",
        (tid, pid, f"C1-{expiry_days}", expiry_days, cost),
    )
    bid = cur.fetchone()["id"]
    cur.execute(
        "INSERT INTO inventory_stock "
        "(tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, qty_on_hand) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (tid, ws, pid, wh, bid, qty),
    )


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

        # 干净商品 + 受控流水
        cur.execute(
            "INSERT INTO products (tenant_id, name_th, name_zh, name_en, base_unit, vat_applicable, "
            "track_batch, track_expiry, is_active) "
            "VALUES (%s,'C1','报表品','C1','粒',TRUE,TRUE,TRUE,TRUE) RETURNING id",
            (tid,),
        )
        pid = str(cur.fetchone()["id"])
        _txn(cur, tid, ws, pid, wh, 10, 100, "purchase_in")  # 期初前:+100
        _txn(cur, tid, ws, pid, wh, 3, 50, "purchase_in")  # 期内入:+50
        _txn(cur, tid, ws, pid, wh, 2, -30, "sale_out")  # 期内售:-30
        _txn(cur, tid, ws, pid, wh, 1, -5, "adjust")  # 期内报损:-5(出但非售)

        d_from = date.today() - timedelta(days=5)
        d_to = date.today()
        rpt = report_svc.inventory_report(
            cur, tenant_id=tid, workspace_client_id=ws, date_from=d_from, date_to=d_to
        )
        m = [x for x in rpt["movement"] if x["product_id"] == pid][0]
        record(
            "进销存 期初100·入50·出35·售30·期末115",
            m["opening"] == "100.000"
            and m["in"] == "50.000"
            and m["out"] == "35.000"
            and m["sold"] == "30.000"
            and m["closing"] == "115.000",
            f"开{m['opening']} 入{m['in']} 出{m['out']} 售{m['sold']} 末{m['closing']}",
        )
        # 周转率 = 售30 / 平均((100+115)/2=107.5) = 0.2790... → 0.28
        record("周转率 0.28", m["turnover_ratio"] == "0.28", str(m["turnover_ratio"]))

        # 近效期是 ws 全量聚合(ws 11 有历史残留库存)→ 用插批前后增量断言,隔离残留
        def _ne(rep):
            bk = {b["label"]: b for b in rep["near_expiry"]["buckets"]}
            return bk, Decimal(rep["near_expiry"]["value_at_risk"])

        bk0, val0 = _ne(
            report_svc.inventory_report(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                date_from=d_from,
                date_to=d_to,
                near_expiry_days=30,
            )
        )
        # 三批(过期 -2 / +3天 / +20天),各 qty 5/12/30,cost 10
        _batch(cur, tid, ws, pid, wh, -2, 5, 10)
        _batch(cur, tid, ws, pid, wh, 3, 12, 10)
        _batch(cur, tid, ws, pid, wh, 20, 30, 10)
        bk1, val1 = _ne(
            report_svc.inventory_report(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                date_from=d_from,
                date_to=d_to,
                near_expiry_days=30,
            )
        )

        def _d(label, field):
            return bk1[label][field] - bk0[label][field]

        def _dq(label):
            return Decimal(bk1[label]["qty"]) - Decimal(bk0[label]["qty"])

        record(
            "近效期分桶增量 expired+{1,5} / le_7d+{1,12} / le_30d+{2,42}",
            _d("expired", "batches") == 1
            and _dq("expired") == Decimal("5")
            and _d("le_7d", "batches") == 1
            and _dq("le_7d") == Decimal("12")
            and _d("le_30d", "batches") == 2
            and _dq("le_30d") == Decimal("42"),
            f"expired+{_d('expired','batches')}/{_dq('expired')} "
            f"le_7d+{_d('le_7d','batches')}/{_dq('le_7d')} "
            f"le_30d+{_d('le_30d','batches')}/{_dq('le_30d')}",
        )
        # 风险货值增量 = (5+12+30)*10 = 470(窗口含过期)
        record("风险货值增量 470.00", val1 - val0 == Decimal("470.00"), f"+{val1 - val0}")

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
