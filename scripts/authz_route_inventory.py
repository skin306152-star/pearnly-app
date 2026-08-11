# -*- coding: utf-8 -*-
"""全量路由 × 守门方式盘点(权限整顿批2 · docs/permissions/06 对照表的数据源)。

用法:PEARNLY_SKIP_HEAVY_INIT=1 python scripts/authz_route_inventory.py [--json]
对每条 FastAPI 路由扫 endpoint 源码,识别它走哪道门(require_perm 系 / 平台层 /
登录态 / 公开),输出 markdown 表或 JSON。check_authz_coverage 闸复用本模块。
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import re
import sys
import textwrap

os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
os.environ.setdefault("JWT_SECRET", "inventory-dummy-secret-16chars")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 守门标记 → 门函数名(按优先级,第一个命中算数)。属性调用按属性名与整条点路径两种形态匹配。
# helper_gated = 文件内共享 helper 包住门(_read/_write/_run/_owner_ctx/_subject/
# resolve_caller/_require_user/_get_user 等,各文件已验证 helper 内部走门)。
#
# ⚠️ 加新门必须同步登记在此:2026-07-25 体检发现本表漏了 4 类真门(_authorize /
# authorize_pearnly_ai / POS 写事务信封 / _require_owner),85 条报红里 68 条是本表
# 认不出来的误报 —— 闸自己不准比没有闸更坏(逼人怀疑真报警)。加门的判据 = 那个函数
# 内部真的做"登录 + 权限 + 租户/账套归属",不是名字像。
GATE_NAMES = [
    (
        "require_perm",
        ("require_perm", "require_perm_pos", "require_perm_tid", "require_perm_pos_tid"),
    ),
    ("super_admin", ("_require_super_admin",)),
    ("pos_require_tenant", ("require_tenant",)),
    ("auth_member", ("auth_member", "auth_owner")),
    ("pos_auth", ("pos_auth",)),
    ("login_only", ("get_current_user_from_request",)),
    # core.route_helpers.authorize_pearnly_ai:登录 + M1 闸(关→404 fail-closed)+ require_perm
    ("pearnly_ai_gate", ("authorize_pearnly_ai",)),
    # routes/steward_common.authorize_steward:上面那道 + pearnly_ai_steward 双闸(S1 起
    # steward 三个路由文件共用的跨文件门 —— 跨文件不吃 helper 跟随,按名字登记)
    ("steward_gate", ("authorize_steward",)),
    # core.pos_api 写/读事务信封:内部 require_perm_pos → 模块闸 → 账套归属(单一事实源)
    # services.pos.approval.execute_gated_write 挂在 pos_write 上(退货/作废的授权闸+审计)
    ("pos_envelope", ("pos_write", "pos_read", "execute_gated_write", "pos_api.subject")),
    (
        "helper_gated",
        (
            "_read",
            "_write",
            "_run",
            "_owner_ctx",
            "_subject",
            "resolve_caller",
            "_require_user",
            "_get_user",
            "_report",
            "_gen_credential",
            "_get_user_safe",
            "_make_note",
            "_require_tenant",
            "_auth",
            "_authorize",
            "_require_owner",
        ),
    ),
]

_GATE_SETS = [(label, frozenset(names)) for label, names in GATE_NAMES]

# AST 解析不了时的回落名单,由上表派生 —— 别另立一套正则,两处必漂。
_GATE_FALLBACK = [
    (label, re.compile(r"\b(?:" + "|".join(re.escape(n) for n in names) + r")\s*\("))
    for label, names in GATE_NAMES
]

_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")  # 仅 AST 回落路径用
_MAX_HOPS = 2  # handler → 同文件 helper → 再一层(payroll._load_year_or_404 那类嵌一层的)

# 写库调用 + 字面量 SQL 动词:门写在这行之后 = 先动数据再查权限,不算门。
_WRITE_CALLS = frozenset({"execute", "executemany"})
_WRITE_SQL_RE = re.compile(r"\s*(INSERT|UPDATE|DELETE|TRUNCATE|ALTER|DROP)\b", re.IGNORECASE)


def _func_node(src: str):
    """源码 → 函数节点;语法异常返回 None(调用方回落正则,闸不许崩在解析上)。"""
    try:
        tree = ast.parse(textwrap.dedent(src))
    except (SyntaxError, ValueError) as exc:
        head = (src.strip().splitlines() or [""])[0][:80]
        print(f"[authz-inventory] AST 解析失败回落正则({exc}): {head}", file=sys.stderr)
        return None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node
    return None


def _call_names(call: ast.Call) -> tuple:
    """一个调用的可匹配形态:裸名 foo / 属性名(x.foo 的 foo)/ 整条点路径 pos_api.subject。"""
    func = call.func
    if isinstance(func, ast.Name):
        return (func.id,)
    if not isinstance(func, ast.Attribute):
        return ()
    parts, node = [], func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return (func.attr, ".".join(reversed(parts)))
    return (func.attr,)


def _is_dead_branch(node) -> bool:
    """只认字面量恒假(`if False:` / `if 0:`)。不做数据流分析 —— 够抓"门埋死分支"就行。"""
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if isinstance(test, ast.Constant):
        return not test.value
    return isinstance(test, ast.Name) and test.id == "False"


def _collect_calls(node, out: list) -> None:
    """收 Call;恒假分支的 body 不进(else 照进)。"""
    for child in ast.iter_child_nodes(node):
        if _is_dead_branch(child):
            for stmt in child.orelse:
                _collect_calls(stmt, out)
            continue
        if isinstance(child, ast.Call):
            out.append(child)
        _collect_calls(child, out)


def _is_write_call(call: ast.Call) -> bool:
    """SQL 必须是字面量才判写:变量 SQL 无从判定,保守当读 —— 宁可漏判也不误伤已守门路由。"""
    if not _WRITE_CALLS.intersection(_call_names(call)):
        return False
    arg = call.args[0] if call.args else None
    if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
        return False
    return bool(_WRITE_SQL_RE.match(arg.value))


def _live_calls(fn) -> list:
    """可执行路径上、且发生在第一条写库语句之前的调用 —— 只有这些能算门。"""
    calls: list = []
    _collect_calls(fn, calls)
    calls.sort(key=lambda c: (c.lineno, c.col_offset))
    writes = [(c.lineno, c.col_offset) for c in calls if _is_write_call(c)]
    if writes:
        cutoff = min(writes)
        calls = [c for c in calls if (c.lineno, c.col_offset) <= cutoff]
    return calls


def _direct_gate(calls: list):
    """handler 自己这一层有没有门(输入已按可执行路径 + 写库顺序过滤)。"""
    names: set = set()
    for call in calls:
        names.update(_call_names(call))
    for label, gate in _GATE_SETS:
        if names & gate:
            return label
    return None


def _regex_gate(src: str):
    """回落路径:AST 解析不了时按名字认门,宁可宽松也不让闸整体失灵。"""
    for label, pattern in _GATE_FALLBACK:
        if pattern.search(src):
            return label
    return None


def _gate_of(src: str, module, hops: int = _MAX_HOPS, seen=None):
    """先看 handler 自己,再顺着它调用的【同文件】函数往里看 hops 层。

    2026-07-25:原来只看 handler 一层,于是 payroll 年报(门在 _load_year_or_404 里)、
    bank-sales(门在 _authorize_bank_sales 里)这类被判"无守门" —— 往名单里堆函数名治不
    了根(下次换个名字又漏),改成顺着调用看进去。只跟同文件定义的函数,跨文件 helper 仍
    靠 GATE_NAMES 明确登记,免得无边界地把任何东西都算成有门。

    2026-08-11:判门从"整段源码跑正则"改成走 AST。正则认得出注释掉的门(`# require_perm`)、
    埋在 `if False:` 里的门、写在 db.execute("DELETE ...") 之后的门 —— 三种退化写法一行不
    生效却全被判"已守门"(已复现)。AST 只看可执行路径、且只认改数据之前跑到的调用;被剪掉
    的调用同样不作为往下跟的入口,否则 `DELETE` 之后再调已守门 helper 又能骗过去。
    """
    fn = _func_node(src)
    calls = _live_calls(fn) if fn is not None else None
    hit = _direct_gate(calls) if calls is not None else _regex_gate(src)
    if hit or hops <= 0 or module is None:
        return hit
    seen = seen if seen is not None else set()
    if fn is not None:
        own = fn.name
        callees = [names[0] for names in map(_call_names, calls) if names]
    else:
        matched = re.match(r"\s*(?:async\s+)?def\s+(\w+)", src)
        own = matched.group(1) if matched else None
        callees = _CALL_RE.findall(src)  # `def foo(` 自己也被当成调用 · 靠 own 挡掉
    if own:
        seen.add(own)
    for callee in callees:
        if callee in seen:
            continue
        seen.add(callee)
        fn_callee = getattr(module, callee, None)
        if not inspect.isfunction(fn_callee) or inspect.getmodule(fn_callee) is not module:
            continue
        try:
            sub = inspect.getsource(fn_callee)
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
