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
#
# ⚠️ 加新门必须同步登记在此:2026-07-25 体检发现本表漏了 4 类真门(_authorize /
# authorize_pearnly_ai / POS 写事务信封 / _require_owner),85 条报红里 68 条是本表
# 认不出来的误报 —— 闸自己不准比没有闸更坏(逼人怀疑真报警)。加门的判据 = 那个函数
# 内部真的做"登录 + 权限 + 租户/账套归属",不是名字像。
GATE_PATTERNS = [
    ("require_perm", r"\brequire_perm(_pos)?(_tid)?(_pos_tid)?\s*\("),
    ("super_admin", r"\b_require_super_admin\s*\("),
    ("pos_require_tenant", r"\brequire_tenant\s*\("),
    ("auth_member", r"\bauth_(member|owner)\s*\("),
    ("pos_auth", r"\bpos_auth\s*\("),
    ("login_only", r"\bget_current_user_from_request\s*\("),
    # core.route_helpers.authorize_pearnly_ai:登录 + M1 闸(关→404 fail-closed)+ require_perm
    ("pearnly_ai_gate", r"\bauthorize_pearnly_ai\s*\("),
    # core.pos_api 写/读事务信封:内部 require_perm_pos → 模块闸 → 账套归属(单一事实源)
    # services.pos.approval.execute_gated_write 挂在 pos_write 上(退货/作废的授权闸+审计)
    ("pos_envelope", r"\b(pos_write|pos_read|execute_gated_write)\s*\(|\bpos_api\.subject\s*\("),
    (
        "helper_gated",
        r"\b(_read|_write|_run|_owner_ctx|_subject|resolve_caller|_require_user|_get_user"
        r"|_report|_gen_credential|_get_user_safe|_make_note|_require_tenant|_auth"
        r"|_authorize|_require_owner)\s*\(",
    ),
]


_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_MAX_HOPS = 2  # handler → 同文件 helper → 再一层(payroll._load_year_or_404 那类嵌一层的)


def _direct_gate(src: str):
    for name, pattern in GATE_PATTERNS:
        if re.search(pattern, src):
            return name
    return None


def _gate_of(src: str, module, hops: int = _MAX_HOPS, seen=None):
    """先看 handler 自己,再顺着它调用的【同文件】函数往里看 hops 层。

    2026-07-25:原来只看 handler 一层,于是 payroll 年报(门在 _load_year_or_404 里)、
    bank-sales(门在 _authorize_bank_sales 里)这类被判"无守门" —— 往名单里堆函数名治不
    了根(下次换个名字又漏),改成顺着调用看进去。只跟同文件定义的函数,跨文件 helper 仍
    靠 GATE_PATTERNS 明确登记,免得无边界地把任何东西都算成有门。
    """
    hit = _direct_gate(src)
    if hit or hops <= 0 or module is None:
        return hit
    seen = seen if seen is not None else set()
    own = re.match(r"\s*(?:async\s+)?def\s+(\w+)", src)
    if own:
        seen.add(own.group(1))  # `def foo(` 自己也被 _CALL_RE 当成调用 · 否则白吃一层
    for callee in _CALL_RE.findall(src):
        if callee in seen:
            continue
        seen.add(callee)
        fn = getattr(module, callee, None)
        if not inspect.isfunction(fn) or inspect.getmodule(fn) is not module:
            continue
        try:
            sub = inspect.getsource(fn)
        except (OSError, TypeError):
            continue
        hit = _gate_of(sub, module, hops - 1, seen)
        if hit:
            return f"{hit}→{callee}"
    return None


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
        gate = _gate_of(src, inspect.getmodule(endpoint)) or "public"
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
