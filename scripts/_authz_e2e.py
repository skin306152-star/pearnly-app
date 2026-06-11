# -*- coding: utf-8 -*-
"""权限整顿真库 E2E(本窗口自检用 · 不入库)。

本地 uvicorn(127.0.0.1:7965)× 真 Supabase。流程:
  1. owner(pearnly_e2e_3)登录 → /api/me/permissions 形状
  2. 邀请 admin/accountant/clerk/viewer 四角色 → 接受 → 各自登录
  3. 5 角色 × 代表性路由 200/403/404 矩阵
  4. 作用域:accountant 切 assigned=[11] → 套账 33 探针 404 · 切换器只列 11
  5. 邀请边界:owner 角色 422 / 撤回后接受 / 重复接受 / 坏 token
  6. 改角色边界:改自己 422 / 动 owner 422;转移边界:目标非 admin 422
  7. 所有权转移全流:e2e3 → admin → 回转 e2e3(净零)
  8. 清理:删 4 个新号 + 撤回余留邀请
"""

import sys
import time
import requests

BASE = "http://127.0.0.1:7965"
OWNER_USER = "pearnly_e2e_3"
OWNER_PASS = "Pe@rnly-E2E-3p4"
WS_A, WS_B = 11, 33

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


def login(username, password):
    r = requests.post(f"{BASE}/api/login", json={"username": username, "password": password})
    assert r.status_code == 200, f"login {username}: {r.status_code} {r.text[:200]}"
    return r.json()["token"]


def H(tok, ws=None):
    h = {"Authorization": f"Bearer {tok}"}
    if ws is not None:
        h["X-Workspace-Client-Id"] = str(ws)
    return h


print("== 1. owner 登录 + permissions 形状")
owner_tok = login(OWNER_USER, OWNER_PASS)
r = requests.get(f"{BASE}/api/me/permissions", headers=H(owner_tok)).json()
d = r["data"]
check("owner role_key", d["role_key"] == "owner", d["role_key"])
check("owner 64 码全集", len(d["permissions"]) == 64, len(d["permissions"]))
check("owner scope all", d["scope_mode"] == "all")

print("== 2. 邀请 4 角色 + 接受 + 登录")
tokens = {"owner": owner_tok}
user_ids = {}
for role in ("admin", "accountant", "clerk", "viewer"):
    r = requests.post(
        f"{BASE}/api/team/invitations",
        json={"channel": "line", "target": f"e2e-{role}", "role_key": role, "scope_mode": "all"},
        headers=H(owner_tok),
    )
    check(f"invite {role} created", r.status_code == 200, r.text[:120])
    inv_token = r.json()["invite_url"].rsplit("/", 1)[-1]
    uname = f"e2e_authz_{role}_{STAMP}"
    r = requests.post(
        f"{BASE}/api/invitations/{inv_token}/accept",
        json={"username": uname, "password": f"E2e-{STAMP}-pw1"},
    )
    check(f"accept {role}", r.status_code == 200, r.text[:120])
    tokens[role] = login(uname, f"E2e-{STAMP}-pw1")
    p = requests.get(f"{BASE}/api/me/permissions", headers=H(tokens[role])).json()["data"]
    check(f"{role} role_key", p["role_key"] == role, p["role_key"])
    if role == "clerk":
        check("clerk 无任何 approve", all(not c.endswith(".approve") for c in p["permissions"]))
    if role == "viewer":
        check(
            "viewer 只 view/export",
            all(c.rsplit(".", 1)[-1] in ("view", "export") for c in p["permissions"]),
            p["permissions"],
        )

members = requests.get(f"{BASE}/api/team/members", headers=H(owner_tok)).json()["members"]
for m in members:
    user_ids[m["username"]] = m["id"]
    if m["role_key"] == "owner":
        owner_uid = m["id"]

print("== 3. 角色 × 路由矩阵(200/403/404)")
MATRIX = [
    # (name, method, path, json, ws, {role: expected_status})
    (
        "team.members",
        "GET",
        "/api/team/members",
        None,
        None,
        {"owner": 200, "admin": 200, "accountant": 403, "clerk": 403, "viewer": 403},
    ),
    (
        "security-events",
        "GET",
        "/api/team/security-events",
        None,
        None,
        {"owner": 200, "admin": 200, "accountant": 403, "clerk": 403, "viewer": 403},
    ),
    (
        "sales.list",
        "GET",
        "/api/sales/documents",
        None,
        None,
        {"owner": 200, "admin": 200, "accountant": 200, "clerk": 200, "viewer": 200},
    ),
    (
        "sales.settings GET",
        "GET",
        "/api/sales/settings",
        None,
        None,
        {"owner": 200, "admin": 200, "accountant": 200, "clerk": 200, "viewer": 200},
    ),
    (
        "products.list",
        "GET",
        "/api/sales/products",
        None,
        None,
        {"owner": 200, "admin": 200, "accountant": 200, "clerk": 200, "viewer": 200},
    ),
    (
        "purchase.list",
        "GET",
        "/api/purchase/docs",
        None,
        WS_A,
        {"owner": 200, "admin": 200, "accountant": 200, "clerk": 200, "viewer": 200},
    ),
    (
        "recon.tasks",
        "GET",
        "/api/recon/tasks",
        None,
        None,
        {"owner": 200, "admin": 200, "accountant": 200, "clerk": 200, "viewer": 200},
    ),
    (
        "workspace.list",
        "GET",
        "/api/workspace/clients",
        None,
        None,
        {"owner": 200, "admin": 200, "accountant": 200, "clerk": 200, "viewer": 200},
    ),
    (
        "pos.admin.cashiers",
        "GET",
        f"/api/pos/admin/cashiers?workspace_client_id={WS_A}",
        None,
        None,
        {"owner": None, "admin": None, "accountant": 403, "clerk": 403, "viewer": 403},
    ),
    (
        "modules.toggle(403面)",
        "PUT",
        "/api/me/modules/knowledge",
        {"enabled": True},
        None,
        {"owner": 200, "admin": 200, "accountant": 403, "clerk": 403, "viewer": 403},
    ),
]
for name, method, path, body, ws, expect in MATRIX:
    statuses = {}
    for role in ("owner", "admin", "accountant", "clerk", "viewer"):
        r = requests.request(method, f"{BASE}{path}", json=body, headers=H(tokens[role], ws))
        statuses[role] = r.status_code
    ok = True
    for role, exp in expect.items():
        if exp is None:
            continue
        if statuses[role] != exp:
            ok = False
    # pos admin:owner 与 admin 同状态(模块开关决定 200 或 403,但绝不和低角色同权)
    if name.startswith("pos.admin"):
        ok = ok and statuses["owner"] == statuses["admin"]
    check(f"matrix {name}", ok, str(statuses))

print("== 4. 作用域 assigned → 404 防枚举")
acct_uid = user_ids[f"e2e_authz_accountant_{STAMP}"]
r = requests.put(
    f"{BASE}/api/team/members/{acct_uid}/scope",
    json={"scope_mode": "assigned", "workspace_ids": [WS_A]},
    headers=H(owner_tok),
)
check("set scope assigned [11]", r.status_code == 200, r.text[:120])
r = requests.get(f"{BASE}/api/purchase/docs", headers=H(tokens["accountant"], WS_A))
check("assigned 套账A 200", r.status_code == 200, r.status_code)
r = requests.get(f"{BASE}/api/purchase/docs", headers=H(tokens["accountant"], WS_B))
check("assigned 套账B 404", r.status_code == 404, r.status_code)
r = requests.get(f"{BASE}/api/workspace/clients", headers=H(tokens["accountant"])).json()
ids = [c["id"] for c in r["clients"]]
check("切换器只列已分配", ids == [WS_A], ids)
r = requests.put(
    f"{BASE}/api/team/members/{acct_uid}/scope",
    json={"scope_mode": "all", "workspace_ids": []},
    headers=H(owner_tok),
)
check("scope 还原 all", r.status_code == 200)

# G1 席位 enforce 上线后 owner+4 角色已占满 seats_max=5;先删 viewer 腾一席,
# 否则下面的 revoke-me 邀请会被 422 team.seat_limit 拦(并致脚本中断不清理)。
viewer_key = f"e2e_authz_viewer_{STAMP}"
viewer_uid = user_ids.get(viewer_key)
if viewer_uid:
    rv = requests.delete(f"{BASE}/api/team/members/{viewer_uid}", headers=H(owner_tok))
    check("腾席:删 viewer 成员", rv.status_code == 200, rv.status_code)
    user_ids.pop(viewer_key, None)

print("== 5. 邀请边界")
r = requests.post(
    f"{BASE}/api/team/invitations",
    json={"channel": "line", "target": "x", "role_key": "owner", "scope_mode": "all"},
    headers=H(owner_tok),
)
check("邀请 owner 422", r.status_code == 422, r.status_code)
r = requests.post(
    f"{BASE}/api/team/invitations",
    json={"channel": "line", "target": "revoke-me", "role_key": "viewer", "scope_mode": "all"},
    headers=H(owner_tok),
)
inv_id = r.json()["id"]
inv_tok2 = r.json()["invite_url"].rsplit("/", 1)[-1]
r = requests.delete(f"{BASE}/api/team/invitations/{inv_id}", headers=H(owner_tok))
check("撤回 200", r.status_code == 200)
r = requests.post(
    f"{BASE}/api/invitations/{inv_tok2}/accept",
    json={"username": f"e2e_authz_rv_{STAMP}", "password": f"E2e-{STAMP}-pw1"},
)
check("撤回后接受 422", r.status_code == 422 and "revoked" in r.text, r.text[:100])
r = requests.get(f"{BASE}/api/invitations/not-a-real-token/preview")
check("坏 token preview=invalid", r.json().get("status") == "invalid")
check(
    "重复接受拦截",
    requests.post(
        f"{BASE}/api/invitations/{inv_tok2}/accept",
        json={"username": f"e2e_authz_rv2_{STAMP}", "password": f"E2e-{STAMP}-pw1"},
    ).status_code
    == 422,
)

print("== 6. 改角色 / 转移边界")
r = requests.put(
    f"{BASE}/api/team/members/{owner_uid}/role", json={"role_key": "admin"}, headers=H(owner_tok)
)
check("改自己(owner)422", r.status_code == 422, r.status_code)
clerk_uid = user_ids[f"e2e_authz_clerk_{STAMP}"]
r = requests.post(
    f"{BASE}/api/ownership/transfer", json={"target_user_id": clerk_uid}, headers=H(owner_tok)
)
check("转移给非 admin 422", r.status_code == 422 and "not_admin" in r.text, r.text[:100])
r = requests.put(
    f"{BASE}/api/team/members/{clerk_uid}/role", json={"role_key": "viewer"}, headers=H(owner_tok)
)
check("clerk→viewer 改角色 200", r.status_code == 200, r.text[:100])
p = requests.get(f"{BASE}/api/me/permissions", headers=H(tokens["clerk"])).json()["data"]
check("降档即时生效(下个请求)", p["role_key"] == "viewer", p["role_key"])

print("== 7. 所有权转移全流(去 + 回)")
admin_uid = user_ids[f"e2e_authz_admin_{STAMP}"]
r = requests.post(
    f"{BASE}/api/ownership/transfer", json={"target_user_id": admin_uid}, headers=H(owner_tok)
)
check("发起转移 200", r.status_code == 200, r.text[:120])
t_tok = r.json()["token"]
r = requests.post(
    f"{BASE}/api/ownership/transfer/accept", json={"token": t_tok}, headers=H(tokens["clerk"])
)
check("非接收方确认 422", r.status_code == 422)
r = requests.post(
    f"{BASE}/api/ownership/transfer/accept", json={"token": t_tok}, headers=H(tokens["admin"])
)
check("接收方确认 200", r.status_code == 200, r.text[:120])
p = requests.get(f"{BASE}/api/me/permissions", headers=H(tokens["admin"])).json()["data"]
check("新 owner 生效", p["role_key"] == "owner", p["role_key"])
p = requests.get(f"{BASE}/api/me/permissions", headers=H(owner_tok)).json()["data"]
check("旧 owner 降 admin", p["role_key"] == "admin", p["role_key"])
r = requests.post(
    f"{BASE}/api/ownership/transfer", json={"target_user_id": owner_uid}, headers=H(tokens["admin"])
)
check("回转发起 200", r.status_code == 200, r.text[:120])
r = requests.post(
    f"{BASE}/api/ownership/transfer/accept",
    json={"token": r.json()["token"]},
    headers=H(owner_tok),
)
check("回转确认 200", r.status_code == 200, r.text[:120])
p = requests.get(f"{BASE}/api/me/permissions", headers=H(owner_tok)).json()["data"]
check("e2e3 还原 owner", p["role_key"] == "owner", p["role_key"])

print("== 8. 清理")
for role in ("admin", "accountant", "clerk", "viewer"):
    uid = user_ids.get(f"e2e_authz_{role}_{STAMP}")
    if uid:
        r = requests.delete(f"{BASE}/api/team/members/{uid}", headers=H(owner_tok))
        check(f"删 {role}", r.status_code == 200, r.text[:80])
m = requests.get(f"{BASE}/api/team/members", headers=H(owner_tok)).json()
check(
    "清理后只剩 owner 行内无残留",
    all(not x["username"].startswith("e2e_authz_") for x in m["members"]),
)

print(f"\n== 结果: PASS {PASS_OK} · FAIL {len(FAIL)}")
if FAIL:
    print("失败项:", FAIL)
    sys.exit(1)
