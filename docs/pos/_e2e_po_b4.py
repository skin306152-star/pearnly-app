# -*- coding: utf-8 -*-
"""PO-B4 真库 E2E — 小票升级正式税票(POS 项目 · docs/pos/04 §6)。

真 Postgres 验证:建小票 → 升级全式 ใบกำกับภาษี(落 sales_documents · 取 tax_invoice 连号 ·
status=issued · 冻结快照)→ 回填 pos_sales.full_invoice_id → 票面金额与小票一致 → 重复升级
被 already_upgraded 拦 → 无效税号被 tax_id_invalid 拦。

一事务跑 + 结尾 ROLLBACK(零残留:连号 UPDATE 随 rollback 回退,不占真税票号)。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_e2e_po_b4.py
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
from services.pos import sale as sale_svc  # noqa: E402
from services.pos import sales_store  # noqa: E402
from services.pos import shift as shift_svc  # noqa: E402
from services.pos import upgrade as upgrade_svc  # noqa: E402

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def _make_sale(cur, *, tid, ws, pid, term_id, cashier_id, shift_id, client_uuid):
    payload = {
        "client_uuid": client_uuid,
        "shift_id": shift_id,
        "terminal_id": term_id,
        "cashier_id": cashier_id,
        "price_includes_vat": False,
        "lines": [{"product_id": pid, "qty": 2, "unit_price": 50}],
        "payments": [{"method": "cash", "amount": 200}],
    }
    return sale_svc.create_sale(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        payload=payload,
        operator={"cashier_id": cashier_id},
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
            print("缺 同租户的 workspace_clients+products 锚点", file=sys.stderr)
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
            "VALUES (%s,%s,%s,%s,NULL,100) "
            "ON CONFLICT DO NOTHING",
            (tid, ws, pid, wh["id"]),
        )

        term = cashier_dal.get_or_create_default_terminal(
            cur, tenant_id=tid, workspace_client_id=ws
        )
        cashier = cashier_dal.create_cashier(
            cur, tenant_id=tid, workspace_client_id=ws, display_name="B4-E2E", pin_hash="x"
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

        sale = _make_sale(
            cur,
            tid=tid,
            ws=ws,
            pid=pid,
            term_id=term["id"],
            cashier_id=cid,
            shift_id=sh["id"],
            client_uuid="b4000001-0000-0000-0000-000000000001",
        )
        sale_id = sale["sale"]["id"]
        record("建小票", sale["sale"]["grand_total"] == "107.00", sale["sale"]["grand_total"])

        # 升级:公司买方(13 位税号)
        up = upgrade_svc.upgrade_to_full_tax_invoice(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            sale_id=sale_id,
            buyer={
                "party_type": "company",
                "name": "บริษัท ทดสอบ จำกัด",
                "tax_id": "0105556000001",
                "branch_type": "head",
                "address": "กรุงเทพฯ",
            },
        )
        doc = up["document"]
        record(
            "升级落 tax_invoice + 取连号",
            bool(doc["doc_number"]) and doc["doc_type"] == "tax_invoice",
            doc["doc_number"],
        )

        # 回填 full_invoice_id
        reloaded = sales_store.get_sale(cur, tenant_id=tid, workspace_client_id=ws, sale_id=sale_id)
        record(
            "回填 full_invoice_id",
            str(reloaded["full_invoice_id"]) == doc["id"],
            str(reloaded.get("full_invoice_id")),
        )

        # 票面金额与小票一致(不重复计 VAT:同额)
        cur.execute(
            "SELECT grand_total, vat_amount FROM sales_documents WHERE tenant_id=%s AND id=%s",
            (tid, doc["id"]),
        )
        d = cur.fetchone()
        record(
            "全式票金额=小票(同额不重算)",
            Decimal(str(d["grand_total"])) == Decimal("107.00")
            and Decimal(str(d["vat_amount"])) == Decimal("7.00"),
            f"grand={d['grand_total']} vat={d['vat_amount']}",
        )

        # 重复升级 → already_upgraded
        try:
            upgrade_svc.upgrade_to_full_tax_invoice(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                sale_id=sale_id,
                buyer={
                    "party_type": "company",
                    "name": "X",
                    "tax_id": "0105556000001",
                    "branch_type": "head",
                    "address": "Y",
                },
            )
            record("重复升级被拦", False, "未抛错")
        except PosError as e:
            record("重复升级被拦", e.code == "pos.already_upgraded", e.code)

        # 无效税号 → tax_id_invalid(另开一单)
        sale2 = _make_sale(
            cur,
            tid=tid,
            ws=ws,
            pid=pid,
            term_id=term["id"],
            cashier_id=cid,
            shift_id=sh["id"],
            client_uuid="b4000002-0000-0000-0000-000000000002",
        )
        try:
            upgrade_svc.upgrade_to_full_tax_invoice(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                sale_id=sale2["sale"]["id"],
                buyer={
                    "party_type": "company",
                    "name": "X",
                    "tax_id": "123",
                    "branch_type": "head",
                    "address": "Y",
                },
            )
            record("无效税号被拦", False, "未抛错")
        except PosError as e:
            record("无效税号被拦", e.code == "pos.tax_id_invalid", e.code)

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
