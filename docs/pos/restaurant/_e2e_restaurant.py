# -*- coding: utf-8 -*-
"""餐厅 POS 真账号 E2E(prod 库 · 一事务建表+跑+ROLLBACK 零残留)。餐厅 POS · PO-R。

驱动真服务代码(services/pos/restaurant/*)走完整流程:开台 → 点单 → 送厨房 KOT → 状态流转 → 加菜
(第二张 KOT)→ 请结 → 按项分单 → 整桌结清 → 桌转空闲。验:状态机派生(seat/cook/bill/free)、
服务费 + VAT 算价对齐定稿稿、复用 pos_sales 落账连号、**菜品=成品不扣库存**、client_uuid 幂等、跨租户隔离。

prod 角色 BYPASSRLS,真隔离=应用层 WHERE tenant_id(见 pos-rls-bypass 记忆)。schema 与 0027/schema.py
逐字一致(test_restaurant_core_migration 已断言迁移==双跑),在同一事务内建表/加列再 ROLLBACK,prod 不留任何
表/列/数据(真部署经 startup 双跑建正式表)。运行:注入 DATABASE_URL 后 `python docs/pos/restaurant/_e2e_restaurant.py`。
"""

import os
import sys
import uuid
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from services.pos.restaurant import checkout as checkout_svc  # noqa: E402
from services.pos.restaurant import kitchen as kitchen_svc  # noqa: E402
from services.pos.restaurant import sessions as sessions_svc  # noqa: E402
from services.pos.restaurant import tables as tables_svc  # noqa: E402

TID = "152de6e5-29eb-437d-bb2c-5d408695e60e"  # pearnly_e2e_3
WS = 11
TB = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"  # 别的租户(隔离对照)

results = []


def record(name, ok, detail=""):
    results.append((name, bool(ok), str(detail)))


# 与 alembic 0027 / services/pos/restaurant/schema.py 逐字一致(迁移测试已锁等价)。
DDL = """
CREATE TABLE IF NOT EXISTS pos_areas (
  id bigserial PRIMARY KEY, tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL,
  name text NOT NULL, sort int NOT NULL DEFAULT 0, is_active boolean NOT NULL DEFAULT TRUE,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS pos_tables (
  id bigserial PRIMARY KEY, tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL,
  area_id bigint REFERENCES pos_areas(id) ON DELETE SET NULL, name text NOT NULL,
  seats int NOT NULL DEFAULT 4, sort int NOT NULL DEFAULT 0, is_active boolean NOT NULL DEFAULT TRUE,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());
CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_tables_name ON pos_tables (tenant_id, workspace_client_id, name);
CREATE TABLE IF NOT EXISTS pos_table_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
  workspace_client_id bigint NOT NULL, table_id bigint NOT NULL REFERENCES pos_tables(id) ON DELETE RESTRICT,
  service_type text NOT NULL DEFAULT 'dine_in', party_size int NOT NULL DEFAULT 1,
  status text NOT NULL DEFAULT 'open', opened_at timestamptz NOT NULL DEFAULT now(), closed_at timestamptz,
  cashier_id uuid REFERENCES pos_cashiers(id) ON DELETE SET NULL, note text, created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now());
CREATE UNIQUE INDEX IF NOT EXISTS uq_table_open ON pos_table_sessions (tenant_id, table_id) WHERE status <> 'closed';
CREATE TABLE IF NOT EXISTS pos_kot (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL,
  session_id uuid NOT NULL REFERENCES pos_table_sessions(id) ON DELETE CASCADE, ticket_no int NOT NULL,
  sent_at timestamptz NOT NULL DEFAULT now(), started_at timestamptz, done_at timestamptz, created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS pos_session_lines (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
  session_id uuid NOT NULL REFERENCES pos_table_sessions(id) ON DELETE CASCADE,
  kot_id uuid REFERENCES pos_kot(id) ON DELETE SET NULL,
  product_id uuid NOT NULL REFERENCES products(id) ON DELETE RESTRICT, sell_unit text,
  unit_factor numeric(14,3) NOT NULL DEFAULT 1, qty numeric(14,3) NOT NULL, unit_price numeric(14,2) NOT NULL,
  line_discount numeric(14,2) NOT NULL DEFAULT 0, vat_applicable boolean NOT NULL DEFAULT TRUE, note text,
  kitchen_status text NOT NULL DEFAULT 'pending',
  settled_sale_id uuid REFERENCES pos_sales(id) ON DELETE SET NULL, created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now());
ALTER TABLE pos_sales ADD COLUMN IF NOT EXISTS service_charge numeric(14,2) NOT NULL DEFAULT 0;
"""


def _mk_product(cur, name_th, price, base_unit="จาน"):
    cur.execute(
        "INSERT INTO products (tenant_id, name_th, name_en, name_zh, unit_price, base_unit, "
        "vat_applicable, is_active) VALUES (%s,%s,%s,%s,%s,%s,TRUE,TRUE) RETURNING id",
        (TID, name_th, name_th, name_th, Decimal(str(price)), base_unit),
    )
    return str(cur.fetchone()["id"])


def main():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("NO DATABASE_URL", file=sys.stderr)
        return 2
    conn = psycopg2.connect(url, sslmode="require")
    try:
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(DDL)

        kaprao = _mk_product(cur, "ผัดกะเพรา", "120.00")
        coke = _mk_product(cur, "โค้ก", "15.00")
        mango = _mk_product(cur, "มะม่วงข้าวเหนียว", "90.00")

        # 1) 建区域 + 桌台 ----------------------------------------------------
        area = tables_svc.create_area(
            cur, tenant_id=TID, workspace_client_id=WS, name="大厅 A", sort=0
        )["area"]
        table = tables_svc.create_table(
            cur, tenant_id=TID, workspace_client_id=WS, name="R-E2E-1", area_id=area["id"], seats=4
        )["table"]
        record("建区域+桌台", area["id"] and table["id"], f"table={table['id']}")

        # 2) 开台 ------------------------------------------------------------
        sess = sessions_svc.open_session(
            cur, tenant_id=TID, workspace_client_id=WS, table_id=table["id"], party_size=4
        )["session"]
        sid = sess["id"]
        record("开台 session=open", sess["status"] == "open", sid)
        # 重复开台 → table_occupied
        try:
            sessions_svc.open_session(
                cur, tenant_id=TID, workspace_client_id=WS, table_id=table["id"], party_size=2
            )
            record("重复开台被拒", False, "未抛错")
        except Exception as e:
            record(
                "重复开台被拒(table_occupied)",
                getattr(e, "detail", "") == "table_occupied",
                getattr(e, "code", e),
            )

        # 3) 点单(草稿)----------------------------------------------------
        sessions_svc.add_lines(
            cur,
            tenant_id=TID,
            workspace_client_id=WS,
            session_id=sid,
            lines=[
                {"product_id": kaprao, "qty": 1, "note": "加辣"},
                {"product_id": coke, "qty": 2},
            ],
        )
        ov = _find_table(
            tables_svc.overview(cur, tenant_id=TID, workspace_client_id=WS), table["id"]
        )
        record(
            "草稿未送厨 → 总览 seat + 金额 0", ov["status"] == "seat" and ov["amount"] == "0.00", ov
        )

        # 4) 送厨房 → KOT,总览转 cook --------------------------------------
        kot1 = sessions_svc.send_kitchen(
            cur, tenant_id=TID, workspace_client_id=WS, session_id=sid
        )["kot"]
        record(
            "送厨房生成 KOT(2 项 pending)", len(kot1["items"]) == 2, f"ticket={kot1['ticket_no']}"
        )
        ov = _find_table(
            tables_svc.overview(cur, tenant_id=TID, workspace_client_id=WS), table["id"]
        )
        record(
            "送厨后 → 总览 cook + 金额 150", ov["status"] == "cook" and ov["amount"] == "150.00", ov
        )

        # 5) 后厨状态机:开始制作 → cooking ---------------------------------
        board = kitchen_svc.board(cur, tenant_id=TID, workspace_client_id=WS)
        record("后厨板:1 单待制作", board["stat"]["pending"] == 1, board["stat"])
        kitchen_svc.set_kot_status(
            cur, tenant_id=TID, workspace_client_id=WS, kot_id=kot1["id"], status="cooking"
        )
        board = kitchen_svc.board(cur, tenant_id=TID, workspace_client_id=WS)
        record("开始制作 → 制作中 1", board["stat"]["cooking"] == 1, board["stat"])

        # 6) 加菜(第二张 KOT)+ 首单完成 ----------------------------------
        sessions_svc.add_lines(
            cur,
            tenant_id=TID,
            workspace_client_id=WS,
            session_id=sid,
            lines=[{"product_id": mango, "qty": 1}],
        )
        kot2 = sessions_svc.send_kitchen(
            cur, tenant_id=TID, workspace_client_id=WS, session_id=sid
        )["kot"]
        record(
            "加菜=同桌再送一张 KOT", kot2["ticket_no"] == kot1["ticket_no"] + 1, kot2["ticket_no"]
        )
        kitchen_svc.set_kot_status(
            cur, tenant_id=TID, workspace_client_id=WS, kot_id=kot1["id"], status="done"
        )
        board = kitchen_svc.board(cur, tenant_id=TID, workspace_client_id=WS)
        record("首单完成后只剩第二单在板", len(board["tickets"]) == 1, len(board["tickets"]))

        # 7) 请结 → 总览 bill ----------------------------------------------
        checkout_svc.request_bill(cur, tenant_id=TID, session_id=sid)
        ov = _find_table(
            tables_svc.overview(cur, tenant_id=TID, workspace_client_id=WS), table["id"]
        )
        record("请结 → 总览 bill", ov["status"] == "bill", ov["status"])

        # 8) 按项分单:只结可乐(×2=30)------------------------------------
        detail = sessions_svc.session_detail(cur, tenant_id=TID, session_id=sid)
        coke_line = next(line["id"] for line in detail["sent_lines"] if line["product_id"] == coke)
        prev = checkout_svc.bill_preview(
            cur,
            tenant_id=TID,
            session_id=sid,
            mode="by_item",
            line_ids=[coke_line],
            service_rate="10",
        )
        # 可乐 30 → 服务费 3 → 应收 33 · 含 VAT 33×7/107=2.16
        record(
            "分单预览算价(可乐 30→服务费 3→应收 33)",
            prev["subtotal"] == "30.00"
            and prev["service_charge"] == "3.00"
            and prev["grand_total"] == "33.00",
            prev,
        )
        r1 = checkout_svc.checkout(
            cur,
            tenant_id=TID,
            workspace_client_id=WS,
            session_id=sid,
            payload={
                "mode": "by_item",
                "line_ids": [coke_line],
                "service_rate": "10",
                "price_includes_vat": True,
                "payments": [{"method": "cash", "amount": "33.00"}],
                "client_uuid": str(uuid.uuid4()),
            },
        )
        record(
            "分单落 pos_sale(连号 RCP)",
            r1["sale"]["receipt_no"].startswith("RCP-"),
            r1["sale"]["receipt_no"],
        )
        # 已请结(billing)后做部分结算:余行留台,session 不关闭(仍 billing 待结账)。
        record(
            "分单后 session 未关闭(余行留台)",
            r1["session"]["status"] != "closed",
            r1["session"]["status"],
        )
        record(
            "分单服务费写入 pos_sales",
            r1["sale"]["service_charge"] == "3.00",
            r1["sale"]["service_charge"],
        )

        # 9) 整桌结清剩余(打抛猪 120 + 芒果 90 = 210)----------------------
        prev2 = checkout_svc.bill_preview(
            cur, tenant_id=TID, session_id=sid, mode="whole", service_rate="10"
        )
        # 210 → 服务费 21 → 应收 231 · VAT 231×7/107=15.11
        record(
            "整桌预览(210→服务费 21→应收 231)",
            prev2["subtotal"] == "210.00" and prev2["grand_total"] == "231.00",
            prev2,
        )
        cu_final = str(uuid.uuid4())
        r2 = checkout_svc.checkout(
            cur,
            tenant_id=TID,
            workspace_client_id=WS,
            session_id=sid,
            payload={
                "mode": "whole",
                "service_rate": "10",
                "price_includes_vat": True,
                "payments": [{"method": "promptpay", "amount": "231.00"}],
                "client_uuid": cu_final,
            },
        )
        record(
            "整桌结清 → session closed",
            r2["session"]["status"] == "closed",
            r2["session"]["status"],
        )

        # 10) 结清 → 桌转空闲 ----------------------------------------------
        ov = _find_table(
            tables_svc.overview(cur, tenant_id=TID, workspace_client_id=WS), table["id"]
        )
        record("结清后 → 总览 free", ov["status"] == "free", ov["status"])

        # 11) 幂等:同 client_uuid 再结 → deduped,不双开票 -----------------
        r2b = checkout_svc.checkout(
            cur,
            tenant_id=TID,
            workspace_client_id=WS,
            session_id=sid,
            payload={
                "mode": "whole",
                "payments": [{"method": "promptpay", "amount": "231.00"}],
                "client_uuid": cu_final,
            },
        )
        record(
            "幂等补传 deduped=true 不双扣",
            r2b["deduped"] is True and r2b["sale"]["id"] == r2["sale"]["id"],
            r2b["deduped"],
        )

        # 12) 菜品=成品,埋单不扣库存 --------------------------------------
        cur.execute(
            "SELECT count(*) AS n FROM inventory_transactions WHERE tenant_id=%s AND ref_id = ANY(%s::uuid[])",
            (TID, [r1["sale"]["id"], r2["sale"]["id"]]),
        )
        record("埋单不扣库存(0 条 inventory_transactions)", cur.fetchone()["n"] == 0)

        # 13) 跨租户隔离:别的租户取不到本桌 session --------------------------
        from services.pos.restaurant import store as rstore

        leak = rstore.get_session(cur, tenant_id=TB, session_id=sid)
        record("跨租户隔离:B 取不到 A 的 session", leak is None)

        # 14) 报表口径:两张 sale 进 pos_sales 统一表 ------------------------
        cur.execute(
            "SELECT count(*) AS n, COALESCE(SUM(grand_total),0) AS g FROM pos_sales "
            "WHERE tenant_id=%s AND id = ANY(%s::uuid[])",
            (TID, [r1["sale"]["id"], r2["sale"]["id"]]),
        )
        row = cur.fetchone()
        record(
            "两张餐厅小票进统一报表表(33+231=264)",
            row["n"] == 2 and Decimal(str(row["g"])) == Decimal("264.00"),
            row["g"],
        )
    finally:
        conn.rollback()
        conn.close()

    print("\n── 餐厅 POS 真账号 E2E(prod · 回滚零残留)──")
    passed = sum(1 for _n, ok, _d in results if ok)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  · {detail}")
    print(f"  → {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


def _find_table(overview: dict, table_id: int) -> dict:
    return next(t for t in overview["tables"] if t["id"] == table_id)


if __name__ == "__main__":
    sys.exit(main())
