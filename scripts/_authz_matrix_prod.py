# -*- coding: utf-8 -*-
"""权限矩阵真库验证(对 live prod · 窗口① 替 ② 复跑 64 码后的矩阵)。

_authz_e2e.py 的 步骤1-3 核心(owner==64 码 + 角色×路由 200/403/404 矩阵),
去掉 prod 上有锁定风险的所有权转移段;Session+Retry 容忍短暂重启;
try/finally 保证清理(4 个测试号),被部署打断也不留残留。
run:  ssh pearnly 'venv/bin/python -' < scripts/_authz_matrix_prod.py
"""

import sys
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "http://127.0.0.1:7860"
OWNER_USER, OWNER_PASS = "pearnly_e2e_3", "Pe@rnly-E2E-3p4"
WS_A, WS_B = 11, 33
STAMP = str(int(time.time()))[-6:]
PASS_OK, FAIL = 0, []

S = requests.Session()
S.mount("http://", HTTPAdapter(max_retries=Retry(total=4, backoff_factor=1.5,
        status_forcelist=[502, 503, 504], allowed_methods=None)))


def check(name, cond, detail=""):
    global PASS_OK
    if cond:
        PASS_OK += 1
        print(f"  PASS {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL {name} :: {detail}")


def H(tok, ws=None):
    h = {"Authorization": f"Bearer {tok}"}
    if ws is not None:
        h["X-Workspace-Client-Id"] = str(ws)
    return h


def login(u, p):
    return S.post(f"{BASE}/api/login", json={"username": u, "password": p}, timeout=40).json()["token"]


tokens, user_ids = {}, {}
try:
    print("== 1. owner 登录 + 64 码")
    owner = login(OWNER_USER, OWNER_PASS)
    tokens["owner"] = owner
    d = S.get(f"{BASE}/api/me/permissions", headers=H(owner), timeout=40).json()["data"]
    check("owner role_key", d["role_key"] == "owner", d["role_key"])
    check("owner 64 码全集(②加 field.cost/payroll)", len(d["permissions"]) == 64, len(d["permissions"]))
    check("owner scope all", d["scope_mode"] == "all")
    check("含 field.cost.view", "field.cost.view" in d["permissions"], "缺")
    check("含 field.payroll.view", "field.payroll.view" in d["permissions"], "缺")

    print("== 2. 邀请+接受 4 角色")
    for role in ("admin", "accountant", "clerk", "viewer"):
        r = S.post(f"{BASE}/api/team/invitations",
                   json={"channel": "line", "target": f"mx-{role}-{STAMP}", "role_key": role,
                         "scope_mode": "all"}, headers=H(owner), timeout=40)
        check(f"invite {role}", r.status_code == 200, r.text[:120])
        itok = r.json()["invite_url"].rsplit("/", 1)[-1]
        uname = f"e2e_authz_{role}_{STAMP}"
        ra = S.post(f"{BASE}/api/invitations/{itok}/accept",
                    json={"username": uname, "password": f"E2e-{STAMP}-pw1"}, timeout=40)
        check(f"accept {role}", ra.status_code == 200, ra.text[:120])
        tokens[role] = login(uname, f"E2e-{STAMP}-pw1")
        p = S.get(f"{BASE}/api/me/permissions", headers=H(tokens[role]), timeout=40).json()["data"]
        check(f"{role} role_key", p["role_key"] == role, p["role_key"])
        if role == "viewer":
            check("viewer 只 view/export",
                  all(c.rsplit(".", 1)[-1] in ("view", "export") for c in p["permissions"]), "")

    for m in S.get(f"{BASE}/api/team/members", headers=H(owner), timeout=40).json()["members"]:
        user_ids[m["username"]] = m["id"]

    print("== 3. 角色 × 路由矩阵")
    MATRIX = [
        ("team.members", "GET", "/api/team/members", None,
         {"owner": 200, "admin": 200, "accountant": 403, "clerk": 403, "viewer": 403}),
        ("security-events", "GET", "/api/team/security-events", None,
         {"owner": 200, "admin": 200, "accountant": 403, "clerk": 403, "viewer": 403}),
        ("security-events/export", "GET", "/api/team/security-events/export", None,
         {"owner": 200, "admin": 200, "accountant": 403, "clerk": 403, "viewer": 403}),
        ("sales.list", "GET", "/api/sales/documents", None,
         {"owner": 200, "admin": 200, "accountant": 200, "clerk": 200, "viewer": 200}),
        ("workspace.list", "GET", "/api/workspace/clients", None,
         {"owner": 200, "admin": 200, "accountant": 200, "clerk": 200, "viewer": 200}),
        ("modules.toggle", "PUT", "/api/me/modules/knowledge", {"enabled": True},
         {"owner": 200, "admin": 200, "accountant": 403, "clerk": 403, "viewer": 403}),
    ]
    for name, method, path, body, expect in MATRIX:
        st = {}
        for role in ("owner", "admin", "accountant", "clerk", "viewer"):
            st[role] = S.request(method, f"{BASE}{path}", json=body, headers=H(tokens[role]),
                                 timeout=40).status_code
        ok = all(st[r] == e for r, e in expect.items())
        check(f"matrix {name}", ok, str(st))
finally:
    print("== 清理(try/finally 保证执行)")
    if tokens.get("owner"):
        for role in ("admin", "accountant", "clerk", "viewer"):
            uid = user_ids.get(f"e2e_authz_{role}_{STAMP}")
            if uid:
                try:
                    S.delete(f"{BASE}/api/team/members/{uid}", headers=H(tokens["owner"]), timeout=40)
                except Exception as e:
                    print(f"  清理 {role} 失败: {e}")
        rem = [x["username"] for x in S.get(f"{BASE}/api/team/members",
               headers=H(tokens["owner"]), timeout=40).json().get("members", [])]
        print("  剩余成员:", rem)

print(f"\n== 结果 PASS {PASS_OK} · FAIL {len(FAIL)}")
if FAIL:
    print("失败:", FAIL)
    sys.exit(1)
