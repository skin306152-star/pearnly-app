#!/usr/bin/env python3
"""Plan the smallest safe local verification set for a git diff.

The planner is intentionally fail-safe: Python production changes keep the
full unit suite unless the diff is limited to explicit unit-test files. E2E
targets are selected from the ledger so a missing coverage declaration is
visible instead of silently becoming an omitted test.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = PROJECT_ROOT / "tests" / "e2e" / "e2e_ledger.json"
FRONTEND_SUFFIXES = {".css", ".html", ".js", ".mjs", ".ts"}
FRONTEND_CONFIGS = {
    "eslint.config.js",
    "package-lock.json",
    "package.json",
    "tsconfig.json",
}
PRODUCT_PYTHON_PREFIXES = ("app.py", "db.py", "routes/", "core/", "services/")
UNIT_ROOT = "tests/unit/"


def _path(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def default_base() -> str:
    """Use the same merge-base rule as the pre-push hook."""
    try:
        _run_git("rev-parse", "--verify", "--quiet", "origin/master")
    except subprocess.CalledProcessError:
        return "HEAD~1"
    try:
        return _run_git("merge-base", "origin/master", "HEAD").strip()
    except subprocess.CalledProcessError:
        return "origin/master"


def changed_paths(base: str, head: str) -> list[str]:
    raw = _run_git("diff", "--name-only", "-z", base, head, "--")
    return sorted({_path(item) for item in raw.split("\0") if item})


def load_ledger() -> dict[str, Any]:
    with LEDGER_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _target_path(kind: str, name: str) -> str:
    root = "scripts" if kind == "cjs" else "tests/e2e"
    return f"{root}/{name}"


def ledger_targets(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for name, spec in ledger.get("scripts", {}).items():
        targets.append(
            {
                "kind": "cjs",
                "name": name,
                "path": _target_path("cjs", name),
                "covers": [_path(item) for item in spec.get("covers", [])],
            }
        )
    for name, spec in ledger.get("specs", {}).items():
        targets.append(
            {
                "kind": "spec",
                "name": name,
                "path": _target_path("spec", name),
                "covers": [_path(item) for item in spec.get("covers", [])],
            }
        )
    return targets


def _matches(path: str, pattern: str) -> bool:
    pattern = _path(pattern)
    return fnmatch.fnmatchcase(path, pattern) or fnmatch.fnmatchcase(
        path, pattern.removeprefix("**/")
    )


def _target_hit(target: dict[str, Any], paths: set[str]) -> bool:
    if target["path"] in paths or target["name"] in paths:
        return True
    return any(_matches(path, pattern) for path in paths for pattern in target["covers"])


def _is_frontend_path(path: str) -> bool:
    name = Path(path).name
    return (
        path.startswith(("src/", "static/"))
        or Path(path).suffix in FRONTEND_SUFFIXES
        or name in FRONTEND_CONFIGS
        or name.startswith(("eslint.config.", "vite.config."))
    )


def _is_product_python(path: str) -> bool:
    return path.endswith(".py") and path.startswith(PRODUCT_PYTHON_PREFIXES)


def _unit_plan(paths: list[str]) -> dict[str, Any]:
    unit_files = sorted(path for path in paths if path.startswith(UNIT_ROOT))
    python_files = [path for path in paths if path.endswith(".py")]
    production_python = [path for path in python_files if not path.startswith("tests/")]

    if production_python:
        return {
            "mode": "full",
            "tests": unit_files,
            "reason": "production Python dependencies are not safely reverse-mapped",
            "command": "PYTHONUTF8=1 python scripts/run_unit_sharded.py --quiet",
        }
    if unit_files:
        commands = []
        for path in unit_files:
            module = path[:-3].replace("/", ".")
            commands.append(f"python -m unittest {module}")
        return {
            "mode": "targeted",
            "tests": unit_files,
            "reason": "diff is limited to explicit unit-test modules",
            "command": " && ".join(commands),
        }
    return {"mode": "skip", "tests": [], "reason": "no Python files changed", "command": None}


def _gate_plan(paths: list[str]) -> list[dict[str, str]]:
    changed = set(paths)
    has_python = any(path.endswith(".py") for path in paths)
    has_product_python = any(_is_product_python(path) for path in paths)
    has_frontend = any(_is_frontend_path(path) for path in paths)
    has_typescript = any(path.endswith(".ts") for path in paths)
    has_e2e_change = any(
        path.startswith(("tests/e2e/", "scripts/_"))
        and path.endswith((".spec.js", ".cjs"))
        or path in {"tests/e2e/e2e_ledger.json", "tests/unit/test_e2e_ledger_gate.py"}
        for path in paths
    )

    gates = [
        ("check_test_git_writes", "python scripts/check_test_git_writes.py --quiet"),
        ("check_destructive_db_tests", "python scripts/check_destructive_db_tests.py --quiet"),
        ("check_file_size", "python scripts/check_file_size.py --quiet"),
        ("check_line_ratchet", "python scripts/check_line_ratchet.py --quiet"),
    ]
    if has_python:
        gates.extend(
            [
                ("ruff", "ruff check <changed-python-files>"),
                ("black", "black --check <changed-python-files>"),
                ("import_app", 'python -c "import app"'),
                ("check_imports", "python scripts/check_imports.py --quiet"),
                ("check_tracked_imports", "python scripts/check_tracked_imports.py --quiet"),
                ("check_i18n", "python scripts/check_i18n.py --strict --quiet"),
                ("check_i18n_refs", "python scripts/check_i18n_refs.py"),
                ("unit", "<unit-plan>"),
                ("check_new_debt", "python scripts/check_new_debt.py"),
            ]
        )
    if has_frontend:
        gates.extend(
            [
                ("check_ui_consistency", "python scripts/check_ui_consistency.py --quiet"),
                (
                    "check_theme_responsive",
                    "python scripts/check_theme_responsive.py --gate --quiet",
                ),
                ("prettier", "npx prettier --check <changed-frontend-files>"),
                ("eslint", "npm run lint"),
                ("check_ai_smell", "python scripts/check_ai_smell.py <changed-frontend-files>"),
                ("check_ai_i18n_refs", "python scripts/check_ai_i18n_refs.py"),
                ("check_home_i18n_refs", "python scripts/check_home_i18n_refs.py"),
                ("build", "npm run build"),
                ("check_asset_bundling", "python scripts/check_asset_bundling.py"),
                ("ui_design_lint", "node scripts/ui_design_lint.mjs --gate"),
            ]
        )
    if has_typescript:
        gates.append(("typecheck", "npm run typecheck"))
    if has_product_python:
        gates.extend(
            [
                ("check_e2e_stub_contracts", "python scripts/check_e2e_stub_contracts.py --quiet"),
                (
                    "check_authz_coverage",
                    "PEARNLY_SKIP_HEAVY_INIT=1 python scripts/check_authz_coverage.py --quiet",
                ),
            ]
        )
    elif has_e2e_change:
        gates.append(
            ("check_e2e_stub_contracts", "python scripts/check_e2e_stub_contracts.py --quiet")
        )
    if any(path.startswith("tests/visual/design/") for path in paths):
        gates.append(("design_fidelity", "node tests/visual/test_design_fidelity.spec.js"))
    if has_e2e_change:
        gates.append(("e2e_ledger", "python -m unittest tests.unit.test_e2e_ledger_gate"))
    if changed and not has_python and not has_frontend and not has_e2e_change:
        gates.append(("docs_only", "no runtime-specific gate"))
    return [{"name": name, "command": command} for name, command in gates]


def plan(paths: list[str], ledger: dict[str, Any]) -> dict[str, Any]:
    normalized = sorted({_path(path) for path in paths})
    targets = ledger_targets(ledger)
    selected = [target for target in targets if _target_hit(target, set(normalized))]
    selected_specs = sorted(target["path"] for target in selected if target["kind"] == "spec")
    selected_cjs = sorted(target["path"] for target in selected if target["kind"] == "cjs")

    for path in normalized:
        if path.startswith("tests/e2e/") and path.endswith(".spec.js"):
            if path not in selected_specs:
                selected_specs.append(path)
    selected_specs = sorted(set(selected_specs))

    declared_specs = {target["name"] for target in targets if target["kind"] == "spec"}
    changed_specs = {
        Path(path).name
        for path in normalized
        if path.startswith("tests/e2e/") and path.endswith(".spec.js")
    }
    ledger_gaps = sorted(changed_specs - declared_specs)

    return {
        "changed": normalized,
        "unit": _unit_plan(normalized),
        "specs": selected_specs,
        "cjs": selected_cjs,
        "spec_command": (
            "npx playwright test " + " ".join(selected_specs) if selected_specs else None
        ),
        "cjs_commands": [f"node {path}" for path in selected_cjs],
        "ledger_gaps": ledger_gaps,
        "gates": _gate_plan(normalized),
    }


def _text(plan_data: dict[str, Any]) -> str:
    lines = ["Impact plan", "===========", "Changed:"]
    lines.extend(f"  - {path}" for path in plan_data["changed"])
    unit = plan_data["unit"]
    lines.append(f"Unit tests: {unit['mode']}")
    if unit["reason"]:
        lines.append(f"  {unit['reason']}")
    if unit["command"]:
        lines.append(f"  {unit['command']}")
    lines.append("Playwright specs:")
    lines.extend(f"  - {path}" for path in plan_data["specs"])
    if plan_data["spec_command"]:
        lines.append(f"  run: {plan_data['spec_command']}")
    lines.append("Browser scripts:")
    lines.extend(f"  - {path}" for path in plan_data["cjs"])
    lines.extend(f"  run: {command}" for command in plan_data["cjs_commands"])
    if plan_data["ledger_gaps"]:
        lines.append("Ledger gaps:")
        lines.extend(
            f"  - {name} is not declared in e2e_ledger.json" for name in plan_data["ledger_gaps"]
        )
    lines.append("Gates:")
    lines.extend(f"  - {gate['name']}: {gate['command']}" for gate in plan_data["gates"])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="git revision at the start of the diff")
    parser.add_argument("--head", default="HEAD", help="git revision at the end of the diff")
    parser.add_argument("--path", action="append", help="use a path instead of reading git diff")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--run-unit",
        action="store_true",
        help="execute the planned unit-test subset; production Python falls back to full",
    )
    parser.add_argument(
        "--check-ledger",
        action="store_true",
        help="fail when changed Playwright specs are not declared in the ledger",
    )
    return parser.parse_args()


def _unit_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_WORK_TREE",
        "GIT_PREFIX",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_QUARANTINE_PATH",
    ):
        env.pop(name, None)
    return env


def run_unit_tests(unit: dict[str, Any]) -> int:
    if unit["mode"] == "skip":
        print("impact: no Python changes, unit tests skipped")
        return 0
    if unit["mode"] == "full":
        command = [sys.executable, "scripts/run_unit_sharded.py", "--quiet"]
        return subprocess.run(command, cwd=PROJECT_ROOT, env=_unit_env()).returncode
    result = 0
    for path in unit["tests"]:
        module = path[:-3].replace("/", ".")
        code = subprocess.run(
            [sys.executable, "-m", "unittest", module],
            cwd=PROJECT_ROOT,
            env=_unit_env(),
        ).returncode
        result = result or code
    return result


def main() -> int:
    args = parse_args()
    paths = args.path or changed_paths(args.base or default_base(), args.head)
    report = plan(paths, load_ledger())
    if args.run_unit:
        return run_unit_tests(report["unit"])
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_text(report))
    if args.check_ledger and report["ledger_gaps"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
