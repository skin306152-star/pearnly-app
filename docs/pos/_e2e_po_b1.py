# -*- coding: utf-8 -*-
"""PO-B1 真库 E2E — 收银员体系在真 Postgres 上验证(单测 FakeCursor 测不到的 DB 级保证 +
服务层端到端):onboarding 开模块/建仓/建终端/建收银员、PIN 登录三态、单 open 班次 partial
unique、应用层租户隔离。

一事务内跑 + 结尾 ROLLBACK(零残留)。锚在已有 workspace_clients 行取真 tenant/ws,不造垃圾。
prod 运行:ssh pearnly → cd /opt/mrpilot → source .env → PYTHONPATH=/opt/mrpilot \
  .venv/bin/python docs/pos/_e2e_po_b1.py
"""

import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.auth import decode_access_token  # noqa: E402
from core.pos_api import PosError  # noqa: E402
from services.modules import store as modules_store  # noqa: E402
from services.pos import auth as pos_auth  # noqa: E402
from services.pos import cashier as cashier_dal  # noqa: E402
from services.pos import onboarding as onboarding_svc  # noqa: E402

# 与 services/pos/cashier.ensure_core_schema 同源 DDL(IF NOT EXISTS · 在事务内建 · 随 ROLLBACK
# 消失 → 零残留;prod 已建则为 no-op)。
DDL = (
    """CREATE TABLE IF NOT EXISTS pos_terminals (
        id bigserial PRIMARY KEY, tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL,
        name text NOT NULL DEFAULT 'แคชเชียร์ 1', is_active boolean NOT NULL DEFAULT TRUE,
        created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now())""",
    """CREATE TABLE IF NOT EXISTS pos_cashiers (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL, user_id uuid REFERENCES users(id) ON DELETE SET NULL,
        display_name text NOT NULL, pin_hash text NOT NULL, color text,
        is_active boolean NOT NULL DEFAULT TRUE, created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now())""",
    """CREATE TABLE IF NOT EXISTS pos_shifts (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        terminal_id bigint NOT NULL REFERENCES pos_terminals(id) ON DELETE CASCADE,
        cashier_id uuid NOT NULL REFERENCES pos_cashiers(id) ON DELETE CASCADE,
        opened_at timestamptz NOT NULL DEFAULT now(), closed_at timestamptz,
        opening_float numeric(14,2) NOT NULL DEFAULT 0, expected_cash numeric(14,2),
        counted_cash numeric(14,2), cash_diff numeric(14,2), status text NOT NULL DEFAULT 'open',
        created_at timestamptz NOT NULL DEFAULT now())""",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_shift_open "
    "ON pos_shifts (tenant_id, terminal_id) WHERE status = 'open'",
)

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("✅" if ok else "❌") + f" {name}" + (f" · {detail}" if detail else ""))


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
            cur.execute(stmt)  # 事务内建表(随 rollback 消失 · prod 已建则 no-op)

        cur.execute("SELECT id, tenant_id FROM workspace_clients ORDER BY id LIMIT 1")
        anchor = cur.fetchone()
        if not anchor:
            print("no workspace_clients to anchor", file=sys.stderr)
            conn.rollback()
            return 2
        ws, tid = anchor["id"], str(anchor["tenant_id"])

        # 1) onboarding(药房业态)
        out = onboarding_svc.onboard(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            business_type="pharmacy",
            warehouse_name="ร้านยา E2E",
            first_cashier={"display_name": "E2E-Nok", "pin": "4321"},
        )
        mods = modules_store.get_modules(cur, tenant_id=tid)
        record(
            "onboarding 开 pos+inventory + 能力块",
            mods["pos"]["enabled"]
            and mods["inventory"]["enabled"]
            and mods["pos"]["config"].get("track_batch") is True
            and "track_expiry" in out["capabilities"],
            str(out["capabilities"]),
        )
        cashier_id = out["cashier_id"]
        record("onboarding 建首位收银员", bool(cashier_id), str(cashier_id))

        # 2) PIN 登录正确 → POS token
        login = pos_auth.login(
            cur, tenant_id=tid, workspace_client_id=ws, cashier_id=cashier_id, pin="4321"
        )
        payload = decode_access_token(login["token"])
        record(
            "PIN 登录正确签 POS token",
            payload
            and payload.get("typ") == "pos"
            and payload.get("tenant_id") == tid
            and payload.get("workspace_client_id") == ws
            and payload.get("cashier_id") == cashier_id,
            str(payload and payload.get("typ")),
        )

        # 3) PIN 错误 → pin_invalid
        try:
            pos_auth.login(
                cur, tenant_id=tid, workspace_client_id=ws, cashier_id=cashier_id, pin="0000"
            )
            record("PIN 错误拒登", False, "未抛错")
        except PosError as e:
            record("PIN 错误拒登", e.code == "pos.pin_invalid" and e.http_status == 401, e.code)

        # 4) 停用收银员 → cashier_inactive
        cur.execute("UPDATE pos_cashiers SET is_active = FALSE WHERE id = %s", (cashier_id,))
        try:
            pos_auth.login(
                cur, tenant_id=tid, workspace_client_id=ws, cashier_id=cashier_id, pin="4321"
            )
            record("停用收银员拒登", False, "未抛错")
        except PosError as e:
            record(
                "停用收银员拒登", e.code == "pos.cashier_inactive" and e.http_status == 403, e.code
            )
        cur.execute("UPDATE pos_cashiers SET is_active = TRUE WHERE id = %s", (cashier_id,))

        # 5) 单 open 班次 partial unique(同终端第二个 open 班次必撞)
        term = cashier_dal.get_or_create_default_terminal(
            cur, tenant_id=tid, workspace_client_id=ws
        )
        cur.execute(
            "INSERT INTO pos_shifts (tenant_id, workspace_client_id, terminal_id, cashier_id) "
            "VALUES (%s,%s,%s,%s)",
            (tid, ws, term["id"], cashier_id),
        )
        cur.execute("SAVEPOINT sp_dup")
        try:
            cur.execute(
                "INSERT INTO pos_shifts (tenant_id, workspace_client_id, terminal_id, cashier_id) "
                "VALUES (%s,%s,%s,%s)",
                (tid, ws, term["id"], cashier_id),
            )
            record("同终端第二 open 班次被唯一约束拦", False, "未撞")
            cur.execute("RELEASE SAVEPOINT sp_dup")
        except psycopg2.errors.UniqueViolation:
            cur.execute("ROLLBACK TO SAVEPOINT sp_dup")
            record("同终端第二 open 班次被唯一约束拦", True)

        # 6) 应用层隔离:另一假 tenant 看不到本 tenant 的收银员
        other = cashier_dal.list_cashiers(
            cur, tenant_id="00000000-0000-0000-0000-000000000000", workspace_client_id=ws
        )
        record("应用层隔离:他租户拿不到收银员", other == [], f"{len(other)} rows")

        conn.rollback()
    except Exception as e:
        conn.rollback()
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
