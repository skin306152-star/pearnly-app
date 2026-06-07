# -*- coding: utf-8 -*-
"""PO-B2 真库 E2E — 班次 + 小票端到端(POS 项目 · docs/pos/04 §5/§6)。

真 Postgres 验证单测 FakeCursor 测不到的:开班、建小票(FEFO 扣批次 + 终端连号 + totals 价外
VAT)、幂等不双扣、取单/按号取、退货回补原批 + 超退拦、作废回补、交班日结、热敏小票出字节。

一事务跑 + 结尾 ROLLBACK(零残留)。锚已有 workspace_clients + product,改 product 标志 + 造批次
库存全在事务里,随 rollback 消失。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_e2e_po_b2.py
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

# 0024 + 0025 表(IF NOT EXISTS · 事务内建 · 随 rollback 消失;prod 已建则 no-op)。
DDL = (
    """CREATE TABLE IF NOT EXISTS pos_terminals (
        id bigserial PRIMARY KEY, tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL,
        name text NOT NULL DEFAULT 'T', is_active boolean NOT NULL DEFAULT TRUE,
        created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now())""",
    """CREATE TABLE IF NOT EXISTS pos_cashiers (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL, user_id uuid, display_name text NOT NULL,
        pin_hash text NOT NULL, color text, is_active boolean NOT NULL DEFAULT TRUE,
        created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now())""",
    """CREATE TABLE IF NOT EXISTS pos_shifts (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        terminal_id bigint NOT NULL REFERENCES pos_terminals(id) ON DELETE CASCADE,
        cashier_id uuid REFERENCES pos_cashiers(id) ON DELETE CASCADE,
        opened_at timestamptz NOT NULL DEFAULT now(), closed_at timestamptz,
        opening_float numeric(14,2) NOT NULL DEFAULT 0, expected_cash numeric(14,2),
        counted_cash numeric(14,2), cash_diff numeric(14,2), status text NOT NULL DEFAULT 'open',
        created_at timestamptz NOT NULL DEFAULT now())""",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_shift_open "
    "ON pos_shifts (tenant_id, terminal_id) WHERE status = 'open'",
    """CREATE TABLE IF NOT EXISTS pos_sales (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL, client_uuid uuid UNIQUE, shift_id uuid, terminal_id bigint,
        cashier_id uuid, receipt_no text, doc_kind text NOT NULL DEFAULT 'receipt',
        sale_type text NOT NULL DEFAULT 'sale', refund_of_sale_id uuid, member_client_id bigint,
        subtotal numeric(14,2) NOT NULL DEFAULT 0, discount_total numeric(14,2) NOT NULL DEFAULT 0,
        vat_amount numeric(14,2) NOT NULL DEFAULT 0, grand_total numeric(14,2) NOT NULL DEFAULT 0,
        price_includes_vat boolean NOT NULL DEFAULT FALSE, paid_total numeric(14,2) NOT NULL DEFAULT 0,
        change_amount numeric(14,2) NOT NULL DEFAULT 0, full_invoice_id uuid,
        status text NOT NULL DEFAULT 'completed', sold_at timestamptz NOT NULL DEFAULT now(),
        synced_at timestamptz, created_by uuid, created_at timestamptz NOT NULL DEFAULT now())""",
    """CREATE TABLE IF NOT EXISTS pos_sale_lines (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
        sale_id uuid NOT NULL REFERENCES pos_sales(id) ON DELETE CASCADE,
        product_id uuid NOT NULL REFERENCES products(id) ON DELETE RESTRICT, sell_unit text,
        unit_factor numeric(14,3) NOT NULL DEFAULT 1, qty numeric(14,3) NOT NULL,
        qty_base numeric(14,3) NOT NULL, unit_price numeric(14,2) NOT NULL,
        line_discount numeric(14,2) NOT NULL DEFAULT 0, vat_applicable boolean NOT NULL DEFAULT TRUE,
        batch_id uuid, refund_of_line_id uuid REFERENCES pos_sale_lines(id) ON DELETE SET NULL,
        line_total numeric(14,2) NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS pos_payments (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
        sale_id uuid NOT NULL REFERENCES pos_sales(id) ON DELETE CASCADE, method text NOT NULL,
        amount numeric(14,2) NOT NULL, ref text)""",
)

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def _stock_of(cur, tenant_id, batch_id) -> Decimal:
    cur.execute(
        "SELECT qty_on_hand FROM inventory_stock WHERE tenant_id = %s AND batch_id = %s",
        (tenant_id, batch_id),
    )
    r = cur.fetchone()
    return Decimal(str(r["qty_on_hand"])) if r else Decimal("0")


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
        for stmt in DDL:
            cur.execute(stmt)

        cur.execute(
            "SELECT wc.id AS ws, wc.tenant_id AS tid, "
            "(SELECT id FROM products WHERE tenant_id = wc.tenant_id AND is_active = TRUE LIMIT 1) AS pid "
            "FROM workspace_clients wc "
            "WHERE EXISTS (SELECT 1 FROM products WHERE tenant_id = wc.tenant_id AND is_active = TRUE) "
            "ORDER BY wc.id LIMIT 1"
        )
        anchor = cur.fetchone()
        if not anchor or not anchor["pid"]:
            print("缺 同租户的 workspace_clients+products 锚点", file=sys.stderr)
            conn.rollback()
            return 2
        ws, tid, pid = anchor["ws"], str(anchor["tid"]), str(anchor["pid"])

        # 备好商品标志 + 批次库存(NEAR 先效 10 / FAR 后效 10)
        cur.execute(
            "UPDATE products SET track_batch = TRUE, vat_applicable = TRUE WHERE id = %s", (pid,)
        )
        wh = inv_store.get_or_create_default_warehouse(cur, tenant_id=tid, workspace_client_id=ws)
        whid = wh["id"]
        batch = {}
        for name, days in (("NEAR", 5), ("FAR", 60)):
            cur.execute(
                "INSERT INTO inventory_batches (tenant_id, product_id, batch_no, expiry_date) "
                "VALUES (%s,%s,%s, CURRENT_DATE + %s) RETURNING id",
                (tid, pid, f"B2-{name}", days),
            )
            bid = cur.fetchone()["id"]
            batch[name] = bid
            cur.execute(
                "INSERT INTO inventory_stock "
                "(tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, qty_on_hand) "
                "VALUES (%s,%s,%s,%s,%s,10)",
                (tid, ws, pid, whid, bid),
            )

        term = cashier_dal.get_or_create_default_terminal(
            cur, tenant_id=tid, workspace_client_id=ws
        )
        cashier = cashier_dal.create_cashier(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            display_name="B2-E2E",
            pin_hash="x",
        )
        cid = str(cashier["id"])
        sh = shift_svc.open_shift(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            terminal_id=term["id"],
            cashier_id=cid,
            opening_float=500,
        )
        record("开班", bool(sh["id"]), sh["id"])

        # 建小票:3 件 × 10(价外 VAT7%)→ 32.10;FEFO 先扣 NEAR
        payload = {
            "client_uuid": "11111111-1111-1111-1111-111111111111",
            "shift_id": sh["id"],
            "terminal_id": term["id"],
            "cashier_id": cid,
            "price_includes_vat": False,
            "lines": [{"product_id": pid, "qty": 3, "unit_price": 10}],
            "payments": [{"method": "cash", "amount": 50}],
        }
        r1 = sale_svc.create_sale(cur, tenant_id=tid, workspace_client_id=ws, payload=payload)
        record(
            "建小票 totals 价外 VAT",
            r1["sale"]["grand_total"] == "32.10" and r1["sale"]["vat_amount"] == "2.10",
            f"{r1['sale']['grand_total']} / vat {r1['sale']['vat_amount']}",
        )
        record(
            "终端连号 RCP-T<终端>",
            r1["sale"]["receipt_no"].startswith(f"RCP-T{term['id']}-"),
            r1["sale"]["receipt_no"],
        )
        record("找零", r1["sale"]["change_amount"] == "17.90", r1["sale"]["change_amount"])
        record(
            "FEFO 先扣 NEAR(10→7)",
            _stock_of(cur, tid, batch["NEAR"]) == Decimal("7")
            and _stock_of(cur, tid, batch["FAR"]) == Decimal("10"),
            f"NEAR={_stock_of(cur, tid, batch['NEAR'])} FAR={_stock_of(cur, tid, batch['FAR'])}",
        )

        # 幂等:同 client_uuid 重发 → deduped 且不二次扣
        r1b = sale_svc.create_sale(cur, tenant_id=tid, workspace_client_id=ws, payload=payload)
        record(
            "幂等不双扣",
            r1b["deduped"] is True and _stock_of(cur, tid, batch["NEAR"]) == Decimal("7"),
            f"deduped={r1b['deduped']} NEAR={_stock_of(cur, tid, batch['NEAR'])}",
        )

        sale_id = r1["sale"]["id"]
        detail = sale_svc.get_sale_detail(cur, tenant_id=tid, sale_id=sale_id)
        by_no = sale_svc.get_sale_by_receipt(
            cur, tenant_id=tid, receipt_no=r1["sale"]["receipt_no"]
        )
        record(
            "取单 / 按号取单",
            len(detail["lines"]) == 1 and by_no["sale"]["id"] == sale_id,
            f"{len(detail['lines'])} lines",
        )

        # 退货 1 件 → 负额 + NEAR 回补 7→8
        line_id = detail["lines"][0]["id"]
        rf = refund_svc.refund(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            original_sale_id=sale_id,
            lines=[{"sale_line_id": line_id, "qty": 1}],
            refund_method="cash",
        )
        record(
            "退货负额 + 回补原批(NEAR 7→8)",
            rf["refund_sale"]["grand_total"].startswith("-")
            and _stock_of(cur, tid, batch["NEAR"]) == Decimal("8"),
            f"{rf['refund_sale']['grand_total']} NEAR={_stock_of(cur, tid, batch['NEAR'])}",
        )

        # 超退:再退 5(已退1 + 5 > 原3)→ over_refund
        try:
            refund_svc.refund(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                original_sale_id=sale_id,
                lines=[{"sale_line_id": line_id, "qty": 5}],
            )
            record("超退被拦", False, "未抛错")
        except PosError as e:
            record("超退被拦", e.code == "pos.over_refund", e.code)

        # 作废另开的单 → 库存回补
        p2 = dict(
            payload,
            client_uuid="22222222-2222-2222-2222-222222222222",
            payments=[{"method": "cash", "amount": 20}],
        )
        p2["lines"] = [{"product_id": pid, "qty": 1, "unit_price": 10}]
        r2 = sale_svc.create_sale(cur, tenant_id=tid, workspace_client_id=ws, payload=p2)
        before = _stock_of(cur, tid, batch["NEAR"])
        v = sale_svc.void_sale(cur, tenant_id=tid, workspace_client_id=ws, sale_id=r2["sale"]["id"])
        record(
            "作废回补库存",
            v["status"] == "void" and _stock_of(cur, tid, batch["NEAR"]) == before + Decimal("1"),
            f"{before}→{_stock_of(cur, tid, batch['NEAR'])}",
        )

        # 热敏小票出字节
        pdf = sale_svc.build_receipt_pdf(cur, tenant_id=tid, sale_id=sale_id)
        record("热敏小票 PDF 出字节", pdf[:4] == b"%PDF" and len(pdf) > 500, f"{len(pdf)}B")

        # 交班日结
        closed = shift_svc.close_shift(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            shift_id=sh["id"],
            counted_cash=closed_expected(cur, tid, sh["id"]),
        )
        record(
            "交班日结(差异 0)",
            closed["shift"]["cash_diff"] == 0.0 and "by_method" in closed["summary"],
            f"diff={closed['shift']['cash_diff']} expected={closed['shift']['expected_cash']}",
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


def closed_expected(cur, tenant_id, shift_id) -> float:
    """点钞填成应有现金,使差异为 0(验差异计算闭合)。"""
    cur.execute(
        "SELECT opening_float FROM pos_shifts WHERE tenant_id = %s AND id = %s",
        (tenant_id, shift_id),
    )
    opening = Decimal(str(cur.fetchone()["opening_float"]))
    cur.execute(
        "SELECT COALESCE(SUM(p.amount),0) AS c FROM pos_payments p JOIN pos_sales s ON s.id=p.sale_id "
        "WHERE p.tenant_id=%s AND s.shift_id=%s AND s.status='completed' AND p.method='cash'",
        (tenant_id, shift_id),
    )
    cash = Decimal(str(cur.fetchone()["c"]))
    cur.execute(
        "SELECT COALESCE(SUM(change_amount),0) AS chg FROM pos_sales "
        "WHERE tenant_id=%s AND shift_id=%s AND status='completed'",
        (tenant_id, shift_id),
    )
    change = Decimal(str(cur.fetchone()["chg"]))
    return float(opening + cash - change)


if __name__ == "__main__":
    sys.exit(main())
