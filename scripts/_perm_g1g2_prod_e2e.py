# -*- coding: utf-8 -*-
"""权限 G1/G2 真库 E2E(对 live prod · HTTP · 窗口① 验收 V4/V5)。

run:  ssh pearnly 'venv/bin/python -' < scripts/_perm_g1g2_prod_e2e.py
靠 HTTP 打 127.0.0.1:7860(不需 DB/.env)· channel=line 避免真发邮件 · 自清理。
V4 席位:邀请填满 → 422 team.seat_limit → 撤回 → 可再邀。
V5 日志:type 筛选只回该域 / 游标分页不重 / CSV 带 BOM + 表头(泰文安全)。
"""

import sys
import time

import requests

BASE = "http://127.0.0.1:7860"
OWNER_USER = "pearnly_e2e_3"
OWNER_PASS = "Pe@rnly-E2E-3p4"
STAMP = str(int(time.time()))[-6:]
PASS_OK, FAIL = 0, []
created_invites = []


def check(name, cond, detail=""):
    global PASS_OK
    if cond:
        PASS_OK += 1
        print(f"  PASS {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL {name} :: {detail}")


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


def invite(tok, label):
    r = requests.post(
        f"{BASE}/api/team/invitations",
        json={
            "channel": "line",
            "target": f"g1-{label}-{STAMP}",
            "role_key": "viewer",
            "scope_mode": "all",
        },
        headers=H(tok),
        timeout=30,
    )
    body = {}
    try:
        body = r.json()
    except Exception:
        pass
    if r.status_code == 200 and body.get("id"):
        created_invites.append(body["id"])
    return r.status_code, body


tok = requests.post(
    f"{BASE}/api/login", json={"username": OWNER_USER, "password": OWNER_PASS}, timeout=30
).json()["token"]

print("== V4 席位 enforce")
st = requests.get(f"{BASE}/api/team/members", headers=H(tok), timeout=30).json()
seats_max = int(st.get("seats_max") or 0)
used = int(st.get("seats_used") or st.get("total") or 0)
check("members 返 seats_used 字段", "seats_used" in st, list(st.keys()))
print(f"   seats_max={seats_max} seats_used={used}")
available = seats_max - used
if seats_max and seats_max < 999999 and available <= 20:
    for i in range(max(0, available)):
        c, _ = invite(tok, f"fill{i}")
        check(f"填席 {i} 成功", c == 200, c)
    c, b = invite(tok, "over")
    check("满员邀请 422", c == 422, c)
    check("满员错误码 team.seat_limit", b.get("detail") == "team.seat_limit", b)
    if created_invites:
        freed = created_invites.pop()
        dc = requests.delete(f"{BASE}/api/team/invitations/{freed}", headers=H(tok), timeout=30)
        check("撤回 200", dc.status_code == 200, dc.status_code)
        c, b = invite(tok, "reinvite")
        check("撤回后可再邀 200", c == 200, f"{c}:{b}")
else:
    check("席位场景可测", False, f"available={available} seats_max={seats_max}(跳过填席)")

print("== V5 安全日志 筛选/游标/CSV")
invite(tok, "evt")  # 保底造一条 team.invite 事件
data = requests.get(
    f"{BASE}/api/team/security-events?type=team&limit=50", headers=H(tok), timeout=30
).json()
check("返 events + next_cursor", "events" in data and "next_cursor" in data, list(data.keys()))
check(
    "type=team 只回 team. 域",
    all(str(e.get("action") or "").startswith("team.") for e in data.get("events", [])),
    [e.get("action") for e in data.get("events", [])][:8],
)

p1 = requests.get(f"{BASE}/api/team/security-events?limit=1", headers=H(tok), timeout=30).json()
if p1.get("next_cursor") and p1.get("events"):
    p2 = requests.get(
        f"{BASE}/api/team/security-events?limit=1&cursor={p1['next_cursor']}",
        headers=H(tok),
        timeout=30,
    ).json()
    ids1 = {e.get("id") for e in p1["events"]}
    ids2 = {e.get("id") for e in p2.get("events", [])}
    check("游标分页不重", not (ids1 & ids2), f"{ids1} vs {ids2}")
else:
    check("游标分页(事件不足跳过)", True, "events<2")

exp = requests.get(f"{BASE}/api/team/security-events/export?type=team", headers=H(tok), timeout=60)
check("export 200", exp.status_code == 200, exp.status_code)
check(
    "export text/csv",
    "text/csv" in exp.headers.get("content-type", ""),
    exp.headers.get("content-type"),
)
check("CSV 带 UTF-8 BOM", exp.content.startswith(b"\xef\xbb\xbf"), exp.content[:8])
head = exp.content.decode("utf-8-sig").splitlines()[0] if exp.content else ""
check("CSV 表头正确", head.startswith("created_at,action,actor,target,ip,details"), head)

print("== 清理本测试残留邀请")
for iid in created_invites:
    requests.delete(f"{BASE}/api/team/invitations/{iid}", headers=H(tok), timeout=30)
print(f"   撤回 {len(created_invites)} 条")

print(f"\n== 结果 PASS {PASS_OK} · FAIL {len(FAIL)}")
if FAIL:
    print("失败:", FAIL)
    sys.exit(1)
