# -*- coding: utf-8 -*-
"""每端点真实 SQL 往返条数计数(诊断 · 临时)。

包一层计数游标 patch core.db.get_cursor/get_cursor_rls,用 e2e_3 假 Request 直接
调路由 handler,数 execute() 次数 = 跨区往返次数(每次 ×69ms)。区分真 N+1 vs 慢单查。

run: ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONPATH=/opt/mrpilot venv/bin/python scripts/_perf_sqlcount.py
"""

import asyncio
import inspect
from contextlib import contextmanager

from starlette.requests import Request

from core import auth, db

COUNT = {"n": 0}
_orig = db.get_cursor
_orig_rls = db.get_cursor_rls


class _Counting:
    def __init__(self, real):
        object.__setattr__(self, "_r", real)

    def execute(self, *a, **k):
        COUNT["n"] += 1
        return self._r.execute(*a, **k)

    def __getattr__(self, name):
        return getattr(self._r, name)

    def __iter__(self):
        return iter(self._r)


@contextmanager
def _cnt(commit=False):
    with _orig(commit=commit) as cur:
        yield _Counting(cur)


@contextmanager
def _cnt_rls(tenant_id=None, bypass=False, commit=False):
    with _orig_rls(tenant_id=tenant_id, bypass=bypass, commit=commit) as cur:
        yield _Counting(cur)


db.get_cursor = _cnt
db.get_cursor_rls = _cnt_rls


def _token():
    with _orig() as cur:
        cur.execute(
            "SELECT id, username, plan, tenant_id, role, is_super_admin "
            "FROM users WHERE username='pearnly_e2e_3'"
        )
        u = cur.fetchone()
    return auth.create_access_token(
        str(u["id"]),
        u["username"],
        u["plan"] or "free",
        tenant_id=str(u["tenant_id"]),
        role=u["role"] or "owner",
        is_super_admin=bool(u["is_super_admin"]),
    )


def _req(token):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [(b"authorization", b"Bearer " + token.encode())],
        "client": ("127.0.0.1", 0),
        "server": ("127.0.0.1", 7860),
    }
    return Request(scope)


def _run(label, fn, **kw):
    COUNT["n"] = 0
    try:
        r = fn(**kw)
        if inspect.iscoroutine(r):
            asyncio.run(r)
        print(f"  {COUNT['n']:>3} SQL   {label}")
    except Exception as e:
        print(f"  {COUNT['n']:>3} SQL   {label}  [err {type(e).__name__}: {str(e)[:50]}]")


def main():
    token = _token()
    req = _req(token)

    from routes import (
        auth_me_routes,
        billing_credits_routes,
        clients_routes,
        erp_endpoints_routes,
        exceptions_routes,
        history_routes,
        knowledge_routes,
        me_routes,
        recon_routes_bankv2,
        tenant_routes,
        vat_excel_tasks_routes,
        workspace_routes,
    )

    print("real SQL round-trips per boot endpoint (e2e_3):")
    _run("/api/me", me_routes.get_me, request=req)
    _run("/api/me/plan", auth_me_routes.get_my_plan, request=req)
    _run("/api/me/credits", billing_credits_routes.get_my_credits, request=req, response=_Resp())
    _run("/api/me/tenant-usage", tenant_routes.get_my_tenant_usage, request=req)
    _run("/api/clients", clients_routes.api_list_clients, request=req)
    _run("/api/workspace/clients", workspace_routes.list_workspace_clients, request=req)
    _run("/api/exceptions/stats", exceptions_routes.api_exceptions_stats, request=req)
    _run("/api/erp/endpoints", erp_endpoints_routes.erp_endpoints_list, request=req)
    _run("/api/history?limit=20", history_routes.history_list, request=req, limit=20)
    _run("/api/recon/bank-v2/tasks", recon_routes_bankv2.bank_v2_list_tasks, request=req)
    _run(
        "/api/vat_excel/tasks",
        vat_excel_tasks_routes.list_tasks,
        request=req,
        page=1,
        page_size=20,
        status=None,
        period=None,
    )
    _run("/api/knowledge/bases", knowledge_routes.list_bases, request=req)


class _Resp:
    headers = {}

    def __setitem__(self, k, v):
        pass


if __name__ == "__main__":
    main()
