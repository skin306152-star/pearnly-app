#!/usr/bin/env python3
"""
Pearnly 整顿期进度自动统计脚本

每个接力窗口必跑一次(铁律 #19 接力 protocol):
    python scripts/refactor_progress.py

输出:
- 代码规模(home.js / app.py / db.py / home.css / home.html 行数)
- 模块文件数(static/home/*.js · *_routes.py · services/*.py · 等)
- 测试数(unit / integration / e2e)
- 静默吞错数(catch (_) {} 无注释)
- Google 级达标进度 %

防偷懒:数字没动 → 接力 agent 没干活 · Zihao 一眼看穿。
"""

import io
import re
import sys
from pathlib import Path

# Windows 默认 GBK 控制台 · 强制 stdout UTF-8 以支持 emoji + 中文
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── 目标(Google 级 90%+ 完成定义)──
TARGETS = {
    "home.js": {"target": 200, "label": "home.js"},
    "app.py": {"target": 500, "label": "app.py"},
    "core/db.py": {"target": 500, "label": "db.py"},
    "home.css": {"target": 500, "label": "home.css"},
    "home.html": {"target": 1000, "label": "home.html"},
}

# 2026-05-22 整顿模式立项时的真实基线(本会话开始前的行数)
START_BASELINE = {
    "home.js": 33768,  # 本会话拆 dashboard + billing 前
    "app.py": 10060,  # 阶段 5 完成后
    "core/db.py": 9255,  # 真实测量
    "home.css": 16124,  # 真实测量(比估计大 2 倍)
    "home.html": 6568,  # 真实测量
}


def count_lines(path: Path) -> int:
    """统计文件行数(CRLF 不算)· 文件不存在返 0"""
    if not path.exists():
        return 0
    with path.open("rb") as f:
        data = f.read()
    if not data:
        return 0
    # CRLF 优先
    crlf_count = data.count(b"\r\n")
    lf_count = data.count(b"\n") - crlf_count
    if data and not data.endswith(b"\n"):
        return crlf_count + lf_count + 1
    return crlf_count + lf_count


def progress_bar(current: int, baseline: int, target: int, width: int = 30) -> str:
    """画进度条 · current 从 baseline 走向 target · 越往 target 走越满"""
    if baseline == target:
        return "[" + "=" * width + "] 100% (already at target)"
    # 进度 = (baseline - current) / (baseline - target)
    delta = baseline - current
    total = baseline - target
    pct = max(0, min(100, int(100 * delta / total)))
    filled = int(width * pct / 100)
    bar = "=" * filled + "-" * (width - filled)
    return f"[{bar}] {pct}%"


def count_files_glob(pattern: str, base: Path) -> int:
    """统计匹配 glob 的文件数"""
    return len(list(base.glob(pattern)))


def count_pattern_in_file(path: Path, pattern: str) -> int:
    """文件里 regex 出现次数 · 文件不存在返 0"""
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return len(re.findall(pattern, text))


def count_unit_tests() -> int:
    """统计 tests/unit/ 下 def test_* 总数"""
    test_dir = PROJECT_ROOT / "tests" / "unit"
    if not test_dir.exists():
        return 0
    total = 0
    for py_file in test_dir.rglob("*.py"):
        with py_file.open("r", encoding="utf-8", errors="replace") as f:
            total += len(re.findall(r"^\s*def\s+test_\w+", f.read(), re.MULTILINE))
    return total


def count_integration_tests() -> int:
    """统计 tests/integration/ 下 def test_* 总数 · 目录不存在返 0(诚实)"""
    test_dir = PROJECT_ROOT / "tests" / "integration"
    if not test_dir.exists():
        return 0
    total = 0
    for py_file in test_dir.rglob("*.py"):
        with py_file.open("r", encoding="utf-8", errors="replace") as f:
            total += len(re.findall(r"^\s*def\s+test_\w+", f.read(), re.MULTILINE))
    return total


def count_e2e_tests() -> int:
    """统计 tests/e2e/ 下 test('...' Playwright"""
    e2e_dir = PROJECT_ROOT / "tests" / "e2e"
    if not e2e_dir.exists():
        return 0
    total = 0
    for js_file in e2e_dir.rglob("*.spec.js"):
        with js_file.open("r", encoding="utf-8", errors="replace") as f:
            total += len(re.findall(r"^\s*test\(", f.read(), re.MULTILINE))
    return total


def main():
    print("=" * 70)
    print("🏗️  Pearnly 整顿期进度统计")
    print("=" * 70)
    print()

    # ── 代码规模 ──
    print("📏 代码规模")
    print("-" * 70)
    code_scores = []
    for fname, conf in TARGETS.items():
        path = PROJECT_ROOT / fname
        current = count_lines(path)
        baseline = START_BASELINE[fname]
        target = conf["target"]
        bar = progress_bar(current, baseline, target)
        pct = max(0, min(100, int(100 * (baseline - current) / max(1, baseline - target))))
        code_scores.append(pct)
        delta_from_baseline = baseline - current
        delta_to_target = current - target
        sign = "-" if delta_from_baseline > 0 else "+"
        print(f"  {conf['label']:18s} {current:6d} 行 → 目标 {target:5d}  {bar}")
        print(f"  {'':18s}   (减 {delta_from_baseline} · 还差 {max(0, delta_to_target)})")
    code_avg = sum(code_scores) / len(code_scores) if code_scores else 0
    print(f"\n  代码规模平均进度: {code_avg:.0f}%")
    print()

    # ── 模块文件数 ──
    print("📦 模块文件数(目标 50-100 个前端 + 20-30 个 router + 10+ services)")
    print("-" * 70)
    # REFACTOR-A5 修正:Vite/A1 后新前端模块在 src/home/*(不再是 static/home/*)
    home_modules = count_files_glob("src/home/**/*.js", PROJECT_ROOT)
    routers = count_files_glob("*_routes.py", PROJECT_ROOT)
    services = count_files_glob("services/**/*.py", PROJECT_ROOT)
    component_css = count_files_glob("src/home/**/*.css", PROJECT_ROOT)
    print(f"  src/home/**/*.js    : {home_modules:3d}  (目标 50-100)")
    print(f"  *_routes.py         : {routers:3d}  (目标 20-30)")
    print(f"  services/**/*.py    : {services:3d}  (目标 10+)")
    print(f"  src/home/**/*.css   : {component_css:3d}  (目标 20-30)")
    # REFACTOR-A5:每类按目标封顶 1.0 · 防某类超额(如 services 31/10)掩盖未动的类
    module_score = min(
        100,
        int(
            100
            * (
                min(1.0, home_modules / 50)
                + min(1.0, routers / 20)
                + min(1.0, services / 10)
                + min(1.0, component_css / 20)
            )
            / 4
        ),
    )
    print(f"\n  模块化进度: {module_score}%")
    print()

    # ── 测试数 ──
    print("🧪 测试覆盖(目标 500+ unit · 20+ integration · 10+ E2E · 覆盖率 ≥ 70%)")
    print("-" * 70)
    unit = count_unit_tests()
    e2e = count_e2e_tests()
    # REFACTOR-A5 修正:不再写死 0 · 真数 tests/integration/(目录不存在则诚实返 0)
    integration = count_integration_tests()
    print(f"  Unit tests          : {unit:3d}  (目标 500+)")
    print(f"  Integration tests   : {integration:3d}  (目标 20+)")
    print(f"  E2E tests           : {e2e:3d}  (目标 10+)")
    # REFACTOR-A5:同样每类封顶 1.0 · 防 integration 达标掩盖 e2e 几乎为 0
    test_score = min(
        100,
        int(100 * (min(1.0, unit / 500) + min(1.0, e2e / 10) + min(1.0, integration / 20)) / 3),
    )
    print(f"\n  测试覆盖进度: {test_score}%")
    print()

    # ── 静默吞错 ──
    print("🔇 静默吞错(目标 0 个无注释 catch (_) {})")
    print("-" * 70)
    home_js = PROJECT_ROOT / "home.js"
    silent_unannotated = count_pattern_in_file(home_js, r"catch\s*\(\s*_?\s*\)\s*\{\s*\}")
    silent_annotated = count_pattern_in_file(home_js, r"catch\s*\(\s*_?\s*\)\s*\{\s*/\* silent")
    silent_total = silent_unannotated + silent_annotated
    print(f"  home.js 未注释 silent : {silent_unannotated:3d}  (目标 0)")
    print(f"  home.js 已注释 silent : {silent_annotated:3d}  (无要求)")
    print(f"  合计                  : {silent_total:3d}")
    silent_score = (
        100 if silent_unannotated == 0 else max(0, int(100 * silent_annotated / silent_total))
    )
    print(f"\n  静默吞错清理进度: {silent_score}%")
    print()

    # ── 工程化(检查工具链是否就绪)──
    print("🔧 工程化(目标:Vite / Alembic / lint / 安全扫描 / 依赖锁定 / 监控 全就绪)")
    print("-" * 70)
    checks = [
        (
            "Vite(package.json 有 vite)",
            (PROJECT_ROOT / "package.json").exists()
            and "vite"
            in (PROJECT_ROOT / "package.json").read_text(encoding="utf-8", errors="replace"),
        ),
        ("Alembic(alembic.ini)", (PROJECT_ROOT / "alembic.ini").exists()),
        (
            "Black(pyproject 或 .flake8)",
            any((PROJECT_ROOT / f).exists() for f in ["pyproject.toml", ".flake8"]),
        ),
        (
            "ESLint(.eslintrc 或 eslint.config)",
            any(
                (PROJECT_ROOT / f).exists()
                for f in [
                    ".eslintrc.json",
                    ".eslintrc.js",
                    "eslint.config.js",
                    "eslint.config.mjs",  # REFACTOR-A5 · flat config(ESM)
                ]
            ),
        ),
        (
            "Prettier(.prettierrc)",
            any(
                (PROJECT_ROOT / f).exists()
                for f in [".prettierrc", ".prettierrc.json", ".prettierrc.js", "prettier.config.js"]
            ),
        ),
        ("requirements.lock(pip-tools)", (PROJECT_ROOT / "requirements.lock.txt").exists()),
        (
            "Code coverage(.coveragerc / codecov / pyproject [tool.coverage])",
            any((PROJECT_ROOT / f).exists() for f in [".coveragerc", "codecov.yml", ".codecov.yml"])
            or (
                (PROJECT_ROOT / "pyproject.toml").exists()
                and "[tool.coverage"
                in (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
            ),  # REFACTOR-A8 · 覆盖率配在 pyproject [tool.coverage]
        ),
        (
            "Dependabot(.github/dependabot.yml)",
            (PROJECT_ROOT / ".github" / "dependabot.yml").exists(),
        ),
        (
            "Health endpoint(grep app.py)",
            (
                "/health" in (PROJECT_ROOT / "app.py").read_text(encoding="utf-8", errors="replace")
                if (PROJECT_ROOT / "app.py").exists()
                else False
            ),
        ),
    ]
    ready = sum(1 for _, ok in checks if ok)
    for label, ok in checks:
        print(f"  [{'✅' if ok else '⚪'}] {label}")
    engineering_score = int(100 * ready / len(checks))
    print(f"\n  工程化就绪进度: {engineering_score}% ({ready}/{len(checks)})")
    print()

    # ── 总体进度 ──
    print("=" * 70)
    overall = int((code_avg + module_score + test_score + silent_score + engineering_score) / 5)
    print(f"🎯 Google 级达标综合进度: {overall}%")
    bar = "=" * int(50 * overall / 100) + "-" * (50 - int(50 * overall / 100))
    print(f"   [{bar}] {overall}%")
    print()
    print(f"   代码规模      : {int(code_avg):3d}%")
    print(f"   模块化        : {module_score:3d}%")
    print(f"   测试覆盖      : {test_score:3d}%")
    print(f"   静默吞错清理  : {silent_score:3d}%")
    print(f"   工程化就绪    : {engineering_score:3d}%")
    print()
    print("   目标: 90%+ · 路径 B + 5-8 个月封锁整顿(2026-05-22 起)")
    print()
    print("=" * 70)
    print("用法:")
    print("  - 每窗口收尾跑一次 · 数字没动 = 没干活")
    print("  - 月末统计跑一次 · 出整顿月报")
    print("  - 整顿期结束跑一次 · 验证 ≥ 90% 达标")
    print("=" * 70)

    # 返回非 0 退出码若进度倒退(下次可加)
    return 0


if __name__ == "__main__":
    sys.exit(main())
