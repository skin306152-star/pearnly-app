# -*- coding: utf-8 -*-
"""C3 真库 E2E — 设置页模块管理 + 开通状态(POS 项目 · docs/pos/04 §2)。

真账号 pearnly_e2e_3:开通前 onboarded=False → 开通(pharmacy)→ onboarded=True/业态正确 →
关 pos 模块(关=隐藏)→ onboarded=False 但仓/收银员数据仍在(未删)→ 未知 module_key 被拒。

一事务跑 + 结尾 ROLLBACK(零残留)。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_e2e_c3.py
"""

import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.modules import store as modules_store  # noqa: E402
from services.pos import onboarding as onboarding_svc  # noqa: E402

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
        tid, ws = str(a["tid"]), a["ws"]

        st0 = onboarding_svc.get_state(cur, tenant_id=tid, workspace_client_id=ws)
        record("开通前 onboarded=False", st0["onboarded"] is False, str(st0["onboarded"]))

        ob = onboarding_svc.onboard(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            business_type="pharmacy",
            warehouse_name="C3门店",
            first_cashier={"display_name": "C3", "pin": "1357"},
        )
        st1 = onboarding_svc.get_state(cur, tenant_id=tid, workspace_client_id=ws)
        record(
            "开通后 onboarded=True · 业态 pharmacy · 能力块含 track_batch",
            st1["onboarded"]
            and st1["business_type"] == "pharmacy"
            and "track_batch" in st1["capabilities"]
            and st1["cashier_count"] >= 1,
            f"onboarded={st1['onboarded']} biz={st1['business_type']} cashiers={st1['cashier_count']}",
        )
        record("开通返 cashier_id", bool(ob["cashier_id"]))

        # 关 pos 模块(关=隐藏不删数据)
        upd = modules_store.set_module(cur, tenant_id=tid, module_key="pos", enabled=False)
        st2 = onboarding_svc.get_state(cur, tenant_id=tid, workspace_client_id=ws)
        record(
            "关 pos 模块 → onboarded=False 但仓/收银员数据仍在(未删)",
            upd["enabled"] is False
            and st2["onboarded"] is False
            and st2["has_warehouse"] is True
            and st2["cashier_count"] >= 1,
            f"pos_enabled={st2['pos_enabled']} has_wh={st2['has_warehouse']} cashiers={st2['cashier_count']}",
        )

        # config 保留(关开关不动 config):重开 pos 不传 config,业态仍在
        modules_store.set_module(cur, tenant_id=tid, module_key="pos", enabled=True)
        st3 = onboarding_svc.get_state(cur, tenant_id=tid, workspace_client_id=ws)
        record(
            "重开 pos · 业态 config 保留",
            st3["business_type"] == "pharmacy",
            str(st3["business_type"]),
        )

        # 未知 module_key 被拒
        try:
            modules_store.set_module(cur, tenant_id=tid, module_key="hacker", enabled=True)
            record("未知 module_key 被拒", False, "未抛错")
        except ValueError:
            record("未知 module_key 被拒(ValueError→422)", True)

        # 业态预设可读
        record(
            "业态预设含 pharmacy",
            "pharmacy" in onboarding_svc.BUSINESS_PRESETS
            and "prescription" in onboarding_svc.BUSINESS_PRESETS["pharmacy"],
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
