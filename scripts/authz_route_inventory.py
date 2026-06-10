# -*- coding: utf-8 -*-
"""全量路由 × 守门方式盘点(权限整顿批2 · docs/permissions/06 对照表的数据源)。

用法:PEARNLY_SKIP_HEAVY_INIT=1 python scripts/authz_route_inventory.py [--json]
对每条 FastAPI 路由扫 endpoint 源码,识别它走哪道门(require_perm 系 / 平台层 /
登录态 / 公开),输出 markdown 表或 JSON。check_authz_coverage 闸复用本模块。
"""

from __future__ import annotations

import inspect
import json
import os
import re
import sys

os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
os.environ.setdefault("JWT_SECRET", "inventory-dummy-secret-16chars")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 守门标记 → 识别正则(按优先级,第一个命中算数)。
# helper_gated = 文件内共享 helper 包住门(_read/_write/_run/_owner_ctx/_subject/
# resolve_caller/_require_user/_get_user 等,各文件已验证 helper 内部走门)。
GATE_PATTERNS = [
    ("require_perm", r"\brequire_perm(_pos)?(_tid)?(_pos_tid)?\s*\("),
    ("super_admin", r"\b_require_super_admin\s*\("),
    ("pos_require_tenant", r"\brequire_tenant\s*\("),
    ("auth_member", r"\bauth_(member|owner)\s*\("),
    ("pos_auth", r"\bpos_auth\s*\("),
    ("login_only", r"\bget_current_user_from_request\s*\("),
    (
        "helper_gated",
        r"\b(_read|_write|_run|_owner_ctx|_subject|resolve_caller|_require_user|_get_user"
        r"|_report|_gen_credential|_get_user_safe|_make_note|_require_tenant|_auth)\s*\(",
    ),
]


def collect_routes():
    from app import app

    rows = []
    for route in app.routes:
        methods = sorted(m for m in (getattr(route, "methods", None) or ()) if m != "HEAD")
        endpoint = getattr(route, "endpoint", None)
        if not methods or endpoint is None:
            continue
        try:
            src = inspect.getsource(endpoint)
            srcfile = os.path.relpath(inspect.getsourcefile(endpoint) or "", os.getcwd())
        except (OSError, TypeError):
            src, srcfile = "", ""
        gate = "public"
        for name, pattern in GATE_PATTERNS:
            if re.search(pattern, src):
                gate = name
                break
        rows.append(
            {
                "methods": "/".join(methods),
                "path": route.path,
                "endpoint": endpoint.__name__,
                "file": srcfile.replace("\\", "/"),
                "gate": gate,
            }
        )
    rows.sort(key=lambda r: (r["file"], r["path"], r["methods"]))
    return rows


def main():
    rows = collect_routes()
    if "--json" in sys.argv:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    counts: dict = {}
    for r in rows:
        counts[r["gate"]] = counts.get(r["gate"], 0) + 1
    print(f"total routes: {len(rows)}")
    for gate, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {gate:18} {n}")
    print()
    for r in rows:
        print(f"{r['gate']:18} {r['methods']:10} {r['path']:60} {r['file']}")


if __name__ == "__main__":
    main()
