# -*- coding: utf-8 -*-
"""PO-A1 真库 E2E — tenant_modules 在真 Postgres 上验证应用层隔离 + 默认回落 + upsert + jsonb。

为什么内联 SQL 而非 import store:本脚本在 push 前跑,prod 还没有 services.modules 代码。
这里的 SQL 与 services/modules/store.py 逐字一致(test_modules_store 单测已断言 store 发出
这些语句),故真库验证内联 SQL == 验证 store。

真正生效的隔离 = 应用层 WHERE tenant_id(prod 角色 postgres 带 BYPASSRLS · Postgres RLS
对本连接不强制 · RLS policy 是给未来最小权限角色的兜底)。一事务内建表 + 跑 + ROLLBACK(零残留)。
"""

import json
import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

TA = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TB = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

KNOWN = ("inventory", "pos", "sales", "expense", "recon", "knowledge")
DEFAULT_ENABLED = {
    "sales": True,
    "expense": True,
    "recon": True,
    "knowledge": True,
    "inventory": False,
    "pos": False,
}

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))


def get_modules(cur, tid):
    cur.execute(
        "SELECT module_key, enabled, config FROM tenant_modules WHERE tenant_id = %s", (tid,)
    )
    rows = {r["module_key"]: r for r in cur.fetchall()}
    out = {}
    for key in KNOWN:
        row = rows.get(key)
        if row is not None:
            out[key] = {"enabled": bool(row["enabled"]), "config": row["config"] or {}}
        else:
            out[key] = {"enabled": DEFAULT_ENABLED.get(key, False), "config": {}}
    return out


def is_enabled(cur, tid, key):
    cur.execute(
        "SELECT enabled FROM tenant_modules WHERE tenant_id = %s AND module_key = %s", (tid, key)
    )
    row = cur.fetchone()
    return bool(row["enabled"]) if row else DEFAULT_ENABLED.get(key, False)


def set_toggle(cur, tid, key, enabled):
    cur.execute(
        "INSERT INTO tenant_modules (tenant_id, module_key, enabled) VALUES (%s,%s,%s) "
        "ON CONFLICT (tenant_id, module_key) DO UPDATE SET enabled=EXCLUDED.enabled, updated_at=now()",
        (tid, key, enabled),
    )


def set_with_config(cur, tid, key, enabled, config):
    cur.execute(
        "INSERT INTO tenant_modules (tenant_id, module_key, enabled, config) VALUES (%s,%s,%s,%s::jsonb) "
        "ON CONFLICT (tenant_id, module_key) DO UPDATE SET enabled=EXCLUDED.enabled, "
        "config=EXCLUDED.config, updated_at=now()",
        (tid, key, enabled, json.dumps(config)),
    )


def main():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("NO DATABASE_URL", file=sys.stderr)
        return 2
    conn = psycopg2.connect(url, sslmode="require")
    try:
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "CREATE TABLE IF NOT EXISTS tenant_modules ("
            " id uuid PRIMARY KEY DEFAULT gen_random_uuid(),"
            " tenant_id uuid NOT NULL, module_key text NOT NULL,"
            " enabled boolean NOT NULL DEFAULT FALSE,"
            " config jsonb NOT NULL DEFAULT '{}'::jsonb,"
            " created_at timestamptz NOT NULL DEFAULT now(),"
            " updated_at timestamptz NOT NULL DEFAULT now(),"
            " UNIQUE (tenant_id, module_key))"
        )

        set_with_config(cur, TA, "pos", True, {"tables": True})
        a = get_modules(cur, TA)
        record(
            "A 的 pos 已开 + config 回放",
            a["pos"] == {"enabled": True, "config": {"tables": True}},
            str(a["pos"]),
        )
        record("A 的 inventory 仍默认关", a["inventory"]["enabled"] is False)
        record("A 的 sales 默认开(既有功能不破)", a["sales"]["enabled"] is True)
        record("is_enabled(A,pos)=True", is_enabled(cur, TA, "pos") is True)

        b = get_modules(cur, TB)
        record(
            "B 的 pos 回落默认关(看不到 A 的开关 · 应用层隔离)",
            b["pos"]["enabled"] is False,
            str(b["pos"]),
        )
        record("is_enabled(B,pos)=False", is_enabled(cur, TB, "pos") is False)

        set_toggle(cur, TA, "pos", False)
        a2 = get_modules(cur, TA)
        record(
            "仅翻开关后 config 保留",
            a2["pos"] == {"enabled": False, "config": {"tables": True}},
            str(a2["pos"]),
        )

        cur.execute("SELECT count(*) AS n FROM tenant_modules WHERE tenant_id=%s", (TA,))
        record("A 只 1 行(upsert 未重复插)", cur.fetchone()["n"] == 1)
    finally:
        conn.rollback()
        conn.close()

    print("\n── PO-A1 真库 E2E(应用层隔离 · 回滚零残留)──")
    passed = sum(1 for _n, ok, _d in results if ok)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  · {detail}")
    print(f"  → {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
