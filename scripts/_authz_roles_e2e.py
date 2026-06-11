# -*- coding: utf-8 -*-
"""自定义角色 + 成本遮蔽 真库 E2E(G3/G4 · 窗口② 自检 · 不入库)。

本地 uvicorn(127.0.0.1:7965)× 真 Supabase。覆盖 07 §五 V1/V2/V3/V6 后端面:
  1. owner perms 含 field.cost.view + 全集 64 码
  2. 建自定义角色(店长:能看库存报表但【不勾】field.cost.view)→ 列表可见
  3. 邀请一名成员 → 用 /role-assign 分配自定义角色 → 下个请求即生效(V1)
  4. 成本遮蔽(V6):该成员读 /api/inventory/stock、/report 的 avg_cost/stock_value/
     value_at_risk 全为 null;owner 读同接口为真值;API 不返回明文
  5. 提权码禁入(billing.manage/ownership.transfer 被剥离)
  6. 乐观锁:PATCH 旧 version → 409
  7. 删在用角色 → 422 team.role_in_use(V3);改回系统角色后可删
  8. 重启种子不覆盖(V2):直连库插自定义行 → 跑 _seed_roles → 行权限/名不变
  9. 清理:删成员 + 删自定义角色

DB 段需 DATABASE_URL(从 prod .env 取);WS_A 须为 owner 名下已开 inventory 的套账。
"""

import sys
import time

import requests

BASE = "http://127.0.0.1:7965"
OWNER_USER = "pearnly_e2e_3"
OWNER_PASS = "Pe@rnly-E2E-3p4"
WS_A = 11

STAMP = str(int(time.time()))[-6:]
PASS_OK, FAIL = 0, []


def check(name, cond, detail=""):
    global PASS_OK
    if cond:
        PASS_OK += 1
        print(f"  PASS {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL {name} {detail}")


def login(u, p):
    r = requests.post(f"{BASE}/api/login", json={"username": u, "password": p})
    assert r.status_code == 200, f"login {u}: {r.status_code} {r.text[:200]}"
    return r.json()["token"]


def H(tok, ws=None):
    h = {"Authorization": f"Bearer {tok}"}
    if ws is not None:
        h["X-Workspace-Client-Id"] = str(ws)
    return h


print("== 1. owner perms 含成本码 + 64 全集")
owner = login(OWNER_USER, OWNER_PASS)
d = requests.get(f"{BASE}/api/me/permissions", headers=H(owner)).json()["data"]
check("owner 64 码", len(d["permissions"]) == 64, len(d["permissions"]))
check("owner 含 field.cost.view", "field.cost.view" in d["permissions"])

print("== 2. 建自定义角色(店长 · 不勾成本码)")
LIMITED = ["inv.view", "inv.report.view", "purchase.doc.view", "sales.doc.view"]
r = requests.post(
    f"{BASE}/api/team/roles",
    json={"name": f"店长{STAMP}", "permissions": LIMITED},
    headers=H(owner),
)
check("建角色 200", r.status_code == 200, r.text[:160])
role = r.json()["role"]
role_id = role["id"]
role_key = role["key"]
check("key 走 custom: 命名空间", role_key.startswith("custom:"), role_key)
check("不含成本码", "field.cost.view" not in role["permissions"])
roles = requests.get(f"{BASE}/api/team/roles/custom", headers=H(owner)).json()["roles"]
check("列表含新角色", any(x["id"] == role_id for x in roles))

print("== 3. 邀请成员 + 分配自定义角色 + 即时生效(V1)")
r = requests.post(
    f"{BASE}/api/team/invitations",
    json={
        "channel": "line",
        "target": f"e2e-role-{STAMP}",
        "role_key": "viewer",
        "scope_mode": "all",
    },
    headers=H(owner),
)
inv_tok = r.json()["invite_url"].rsplit("/", 1)[-1]
uname = f"e2e_role_member_{STAMP}"
pw = f"E2e-{STAMP}-pw1"
requests.post(f"{BASE}/api/invitations/{inv_tok}/accept", json={"username": uname, "password": pw})
member = login(uname, pw)
members = requests.get(f"{BASE}/api/team/members", headers=H(owner)).json()["members"]
member_uid = next(m["id"] for m in members if m["username"] == uname)
r = requests.put(
    f"{BASE}/api/team/members/{member_uid}/role-assign",
    json={"role_key": role_key},
    headers=H(owner),
)
check("分配自定义角色 200", r.status_code == 200, r.text[:160])
p = requests.get(f"{BASE}/api/me/permissions", headers=H(member)).json()["data"]
check("下个请求即生效", p["role_key"] == role_key, p["role_key"])
check("成员无成本码", "field.cost.view" not in p["permissions"])

print("== 4. 成本遮蔽(V6)")
ms = requests.get(f"{BASE}/api/inventory/stock?workspace_client_id={WS_A}", headers=H(member, WS_A))
os_ = requests.get(f"{BASE}/api/inventory/stock?workspace_client_id={WS_A}", headers=H(owner, WS_A))
if ms.status_code == 200 and os_.status_code == 200:
    md, od = ms.json().get("data", {}), os_.json().get("data", {})
    check(
        "成员 stock_value=null", md.get("summary", {}).get("stock_value") is None, md.get("summary")
    )
    check("owner stock_value 非null", od.get("summary", {}).get("stock_value") is not None)
    check(
        "成员每行 avg_cost=null",
        all(it.get("avg_cost") is None for it in md.get("items", [])),
    )
    mr = (
        requests.get(
            f"{BASE}/api/inventory/report?workspace_client_id={WS_A}", headers=H(member, WS_A)
        )
        .json()
        .get("data", {})
    )
    check("成员 value_at_risk=null", mr.get("near_expiry", {}).get("value_at_risk") is None)
else:
    check("库存接口可达(跳过遮蔽断言)", False, f"member={ms.status_code} owner={os_.status_code}")

print("== 5. 提权码禁入")
r = requests.post(
    f"{BASE}/api/team/roles",
    json={
        "name": f"越权{STAMP}",
        "permissions": ["sales.doc.view", "ownership.transfer", "billing.manage"],
    },
    headers=H(owner),
)
esc = r.json()["role"]
check(
    "提权码被剥离",
    "ownership.transfer" not in esc["permissions"] and "billing.manage" not in esc["permissions"],
)
requests.delete(f"{BASE}/api/team/roles/{esc['id']}", headers=H(owner))

print("== 6. 乐观锁冲突")
r = requests.patch(
    f"{BASE}/api/team/roles/{role_id}",
    json={"name": f"店长改{STAMP}", "version": 999},
    headers=H(owner),
)
check("旧 version → 409", r.status_code == 409, r.status_code)

print("== 7. 删在用角色被拦(V3)")
r = requests.delete(f"{BASE}/api/team/roles/{role_id}", headers=H(owner))
check("在用删 422", r.status_code == 422, r.status_code)
detail = r.json().get("detail", {})
check("拦截带在用人数", isinstance(detail, dict) and detail.get("member_count", 0) >= 1, detail)
requests.put(
    f"{BASE}/api/team/members/{member_uid}/role-assign",
    json={"role_key": "viewer"},
    headers=H(owner),
)
r = requests.delete(f"{BASE}/api/team/roles/{role_id}", headers=H(owner))
check("转走后可删 200", r.status_code == 200, r.text[:120])

print("== 8. 重启种子不覆盖(V2 · 直连库)")
try:
    from core import db
    import services.db_migrations.authz_schema as mig

    # 经 API 造一行真 tenant 维度的 custom 行,再原地跑种子,验证它不被刷掉
    rr = requests.post(
        f"{BASE}/api/team/roles",
        json={"name": f"种子探针{STAMP}", "permissions": ["sales.doc.view"]},
        headers=H(owner),
    ).json()["role"]
    probe_id = rr["id"]
    with db.get_cursor(commit=True) as cur:
        mig._seed_roles(cur)
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT display_name, permissions, is_active FROM roles WHERE id = %s", (probe_id,)
        )
        after = cur.fetchone()
    perms = after["permissions"]
    if isinstance(perms, str):
        import json as _j

        perms = _j.loads(perms)
    check(
        "种子后自定义名不变",
        (after["display_name"] or "").startswith("种子探针"),
        after["display_name"],
    )
    check("种子后码集不变", perms == ["sales.doc.view"], perms)
    requests.delete(f"{BASE}/api/team/roles/{probe_id}", headers=H(owner))
except Exception as e:  # noqa: BLE001
    check("种子不覆盖(DB 段)", False, f"需 DATABASE_URL: {e}")

print("== 9. 清理")
r = requests.delete(f"{BASE}/api/team/members/{member_uid}", headers=H(owner))
check("删成员", r.status_code == 200, r.text[:80])

print(f"\n== 结果: PASS {PASS_OK} · FAIL {len(FAIL)}")
if FAIL:
    print("失败项:", FAIL)
    sys.exit(1)
