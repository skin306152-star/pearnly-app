# -*- coding: utf-8 -*-
"""C2 性能加固验证 — 批量数据 + EXPLAIN ANALYZE(POS 项目 · docs/pos/04 §4)。

在合成租户下灌大量流水/小票/库存(单事务内 generate_series 服务端生成),ANALYZE 后对热查询
跑 EXPLAIN (ANALYZE, BUFFERS),断言:① 走目标索引(非 Seq Scan)② 执行耗时 < 1000ms(p95 目标)。
覆盖:库存进销存(inventory_transactions ix_txn_product)、销售报表(pos_sales ix_pos_sales_sold_at)、
库存查询(inventory_stock ix_stock_ws_product)。

一事务跑 + 结尾 ROLLBACK(零残留 · 合成租户数据全回退)。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_perf_c2.py
"""

import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.inventory import store as inv_store  # noqa: E402

# 合成租户(不碰真租户;事务内造数 + rollback)。
TID = "ce2e0000-0000-0000-0000-0000000000c2"
WS = 990000001
N_TXN, N_SALES, N_STOCK_WS = 60000, 40000, 400
results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def _plan(cur, sql, params):
    cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql, params)
    plan = cur.fetchone()["QUERY PLAN"][0]
    return plan["Plan"], plan["Execution Time"]


def _uses_index(node, index_name) -> bool:
    if node.get("Index Name") == index_name:
        return True
    return any(_uses_index(c, index_name) for c in node.get("Plans", []))


def _has_seq_scan_on(node, table) -> bool:
    if node.get("Node Type") == "Seq Scan" and node.get("Relation Name") == table:
        return True
    return any(_has_seq_scan_on(c, table) for c in node.get("Plans", []))


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
        wh = inv_store.get_or_create_default_warehouse(cur, tenant_id=TID, workspace_client_id=WS)[
            "id"
        ]

        # 50 个商品(FK 目标)
        cur.execute(
            "INSERT INTO products (tenant_id, name_th, base_unit, vat_applicable, is_active) "
            "SELECT %s, 'PERF'||g, '粒', TRUE, TRUE FROM generate_series(1,50) g RETURNING id",
            (TID,),
        )
        pids = [r["id"] for r in cur.fetchall()]
        print(f"造数:{len(pids)} 商品 · {N_TXN} 流水 · {N_SALES} 小票 · {N_STOCK_WS}ws×50 库存…")

        # 流水:N_TXN 条,轮转商品,半数 sale_out
        cur.execute(
            "INSERT INTO inventory_transactions "
            "(tenant_id, workspace_client_id, product_id, warehouse_id, txn_type, qty_delta, created_at) "
            "SELECT %s, %s, (%s::uuid[])[1 + (g %% 50)], %s, "
            "CASE WHEN g %% 2 = 0 THEN 'sale_out' ELSE 'purchase_in' END, "
            "CASE WHEN g %% 2 = 0 THEN -1 ELSE 2 END, "
            "now() - (g || ' minutes')::interval "
            "FROM generate_series(1, %s) g",
            (TID, WS, pids, wh, N_TXN),
        )
        # 小票:N_SALES 条
        cur.execute(
            "INSERT INTO pos_sales "
            "(tenant_id, workspace_client_id, receipt_no, sale_type, status, grand_total, vat_amount, "
            "paid_total, change_amount, sold_at) "
            "SELECT %s, %s, 'PR'||g, 'sale', 'completed', 100, 7, 100, 0, "
            "now() - (g || ' minutes')::interval FROM generate_series(1, %s) g",
            (TID, WS, N_SALES),
        )
        # 库存:N_STOCK_WS 个 ws,各自独立仓(uq_stock 以 warehouse 区分),每仓 50 商品
        # → 压 ix_stock_ws_product:按单 ws 过滤只取 ~50 行(不全表扫 2 万)。
        cur.execute(
            "INSERT INTO warehouses (tenant_id, workspace_client_id, name) "
            "SELECT %s, w, 'PWH'||w FROM generate_series(1, %s) w RETURNING id, workspace_client_id",
            (TID, N_STOCK_WS),
        )
        whs = cur.fetchall()
        target_ws = whs[0]["workspace_client_id"]  # 拿其中一个 ws 做单 ws 查询
        cur.execute(
            "INSERT INTO inventory_stock "
            "(tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, qty_on_hand) "
            "SELECT %s, wh.workspace_client_id, (%s::uuid[])[p.idx], wh.id, NULL, 10 "
            "FROM unnest(%s::bigint[], %s::bigint[]) AS wh(id, workspace_client_id) "
            "CROSS JOIN generate_series(1,50) p(idx)",
            (TID, pids, [w["id"] for w in whs], [w["workspace_client_id"] for w in whs]),
        )
        cur.execute("ANALYZE inventory_transactions, pos_sales, inventory_stock")

        # 1a) 进销存全量聚合(C1 movement 的真实查询 · 扫全租户流水 seq scan 是最优计划)→ 验性能预算
        _, ms = _plan(
            cur,
            "SELECT product_id, SUM(qty_delta) FROM inventory_transactions "
            "WHERE tenant_id=%s AND workspace_client_id=%s GROUP BY product_id",
            (TID, WS),
        )
        record(f"进销存全量聚合 < 1s · {ms:.0f}ms", ms < 1000, f"{ms:.0f}ms")

        # 1b) 单商品流水(钻取/FEFO 类点查)→ 走 ix_txn_product
        node, ms = _plan(
            cur,
            "SELECT SUM(qty_delta) FROM inventory_transactions "
            "WHERE tenant_id=%s AND workspace_client_id=%s AND product_id=(%s::uuid[])[1]",
            (TID, WS, pids),
        )
        record(
            f"单商品流水走 ix_txn_product · {ms:.0f}ms",
            _uses_index(node, "ix_txn_product")
            and not _has_seq_scan_on(node, "inventory_transactions")
            and ms < 1000,
            f"{ms:.0f}ms",
        )

        # 2) 报表区间 → ix_pos_sales_sold_at
        node, ms = _plan(
            cur,
            "SELECT COALESCE(SUM(grand_total),0), COUNT(*) FROM pos_sales "
            "WHERE tenant_id=%s AND workspace_client_id=%s AND status='completed' "
            "AND sale_type='sale' AND sold_at >= now() - interval '7 days'",
            (TID, WS),
        )
        record(
            f"报表区间走 ix_pos_sales_sold_at · {ms:.0f}ms",
            _uses_index(node, "ix_pos_sales_sold_at")
            and not _has_seq_scan_on(node, "pos_sales")
            and ms < 1000,
            f"{ms:.0f}ms",
        )

        # 3) 库存查询(单 ws)→ ix_stock_ws_product(本 PO 新增)
        node, ms = _plan(
            cur,
            "SELECT product_id, qty_on_hand FROM inventory_stock "
            "WHERE tenant_id=%s AND workspace_client_id=%s",
            (TID, target_ws),
        )
        record(
            f"库存单 ws 查询走 ix_stock_ws_product · {ms:.0f}ms",
            _uses_index(node, "ix_stock_ws_product")
            and not _has_seq_scan_on(node, "inventory_stock")
            and ms < 1000,
            f"{ms:.0f}ms",
        )

        conn.rollback()
    except Exception as e:
        conn.rollback()
        import traceback

        traceback.print_exc()
        print(f"PERF 异常: {e}", file=sys.stderr)
        return 2
    finally:
        cur.close()
        conn.close()

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{'='*52}\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
