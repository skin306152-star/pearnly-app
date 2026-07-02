"""Agent 能力防漏闸 · 机械核对.

从 routes/*.py 自动扒出每个 API 入口(单一事实源·不靠人记),再和登记表
docs/agent/agent_registry.json 对照.任何"代码里有、登记表没分类"的功能区 → 退出码 1.
新增路由文件忘了登记 → 这里红 → 杜绝"漏接 Agent 最后才发现".

用法:
  python scripts/agent_capability_audit.py          # 核对 + 概览(漏 = exit 1)
  python scripts/agent_capability_audit.py --list    # 同时逐条列出全部入口
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTES_DIR = ROOT / "routes"
REGISTRY = ROOT / "docs" / "agent" / "agent_registry.json"

# 任意路由变量名都认:@router.get / @app.post / @glvat_router.post / @bankv2_router.get ...
# (第一版只认 router/app/bp 等固定名 → 漏了自定义名的真端点 · 防漏闸自己抓出来的)
DECORATOR = re.compile(
    r"""@(\w+)\.(get|post|put|delete|patch|route)\s*\(\s*
        (?:["']([^"']+)["'])?""",
    re.VERBOSE,
)

BUCKET_LABEL = {
    "A": "进·只读",
    "B": "进·要确认",
    "C": "不进·App专属",
    "D": "不进·系统/安全",
}


def extract_endpoints() -> dict[str, list[tuple[str, str]]]:
    """{module_stem: [(METHOD, path), ...]} for every route decorator under routes/."""
    found: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for py in sorted(ROUTES_DIR.glob("*.py")):
        if py.stem == "__init__":
            continue
        text = py.read_text(encoding="utf-8", errors="replace")
        for m in DECORATOR.finditer(text):
            method = m.group(2).upper()
            path = m.group(3) or "(dynamic)"
            found[py.stem].append((method, path))
    return found


def bucket_of(value) -> str:
    """登记值 → 桶。A 档为 {bucket, agent[, why]} 结构,B/C/D 仍为裸字符串。"""
    if isinstance(value, dict):
        return str(value.get("bucket") or "?")
    return str(value)


def agent_annotation_errors(registry: dict) -> list[str]:
    """A 档第二道核对:每个 A 功能区必须显式声明接法(tool:xxx)或豁免(exempt:原因)。
    没这道,'已分 A 但没人接'会静默漂成假覆盖。"""
    errs = []
    for area, value in registry.items():
        if bucket_of(value) != "A":
            continue
        agent = value.get("agent") if isinstance(value, dict) else None
        if not isinstance(agent, str) or not (
            agent.startswith("tool:") or agent.startswith("exempt:")
        ):
            errs.append(area)
        elif len(agent.split(":", 1)[1].strip()) == 0:
            errs.append(area)
    return sorted(errs)


def main() -> int:
    show_list = "--list" in sys.argv
    registry = {
        k: v
        for k, v in json.loads(REGISTRY.read_text(encoding="utf-8")).items()
        if not k.startswith("_")
    }
    code = extract_endpoints()

    total = sum(len(v) for v in code.values())
    unclassified = sorted(f for f in code if f not in registry)
    stale = sorted(f for f in registry if f not in code)

    per_bucket_files: Counter[str] = Counter()
    per_bucket_eps: Counter[str] = Counter()
    for f, eps in code.items():
        b = bucket_of(registry.get(f, "?"))
        per_bucket_files[b] += 1
        per_bucket_eps[b] += len(eps)

    print("== Pearnly Agent 能力核对 ==")
    print(f"功能区(文件) {len(code)} · 入口(端点) {total}\n")
    for b in ("A", "B", "C", "D"):
        print(
            f"  {b} {BUCKET_LABEL[b]:<10} 功能区 {per_bucket_files[b]:>2} · 入口 {per_bucket_eps[b]:>3}"
        )

    if show_list:
        print("\n-- 全部入口 --")
        for f in sorted(code):
            b = bucket_of(registry.get(f, "?"))
            print(f"\n[{b}] {f}")
            for method, path in code[f]:
                print(f"    {method:<6} {path}")

    if stale:
        print(f"\n[warn] 登记表有、代码已无(可清理): {', '.join(stale)}")

    failed = False
    if unclassified:
        failed = True
        print(
            f"\n[FAIL] 代码里有、登记表未分类的功能区 {len(unclassified)} 个 → 请在 "
            f"agent_registry.json 标 A/B/C/D:"
        )
        for f in unclassified:
            print(f"    - {f}  ({len(code[f])} 入口)")

    bad_agents = agent_annotation_errors(registry)
    if bad_agents:
        failed = True
        print(
            f"\n[FAIL] A 档功能区缺 agent 声明 {len(bad_agents)} 个 → "
            f'标 {{"bucket":"A","agent":"tool:<名>|exempt:<原因>"}}:'
        )
        for f in bad_agents:
            print(f"    - {f}")

    if failed:
        return 1
    print("\n[OK] 全部功能区已分类 · A 档全声明接法 · 无遗漏")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
