# -*- coding: utf-8 -*-
"""存储收口静态闸(ENC-a 守门):storage 树下的文件禁止绕过 file_crypto 裸 open。

背景:落盘客户资料统一走 core.file_crypto(maybe_seal/unseal)加解密。任何新代码若直接对
storage 目录 open('wb')/read_bytes() 会把明文写盘(泄密)或把密文喂给消费者(炸)。本闸机械
拦这类回归:凡引用了 storage 目录信号(base 目录 env / 版本段目录构造)的文件,不得再出现裸
文件 IO——写读一律经各 store 模块的 helper。

判定=信号 + 裸 IO 双命中:
  - 信号:引用了 storage base env 或 deliverables_dir/versioned_dir/order_dir 构造。
  - 裸 IO:.write_bytes( / .write_text( / 无参 .read_bytes() / open(..., 二进制模式)。
收口 helper 模块(本身就是唯一 sanctioned 落盘点,内部已过 maybe_seal/unseal)进白名单;单行可用
`# storage-io-ok` 显式豁免(如已知明文/兼容路径;不用 `# noqa:` 前缀,避免撞 ruff 解析)。

用法:python scripts/storage_io_guard.py  → 有违规打印并 exit 1。
测试直接 import scan_source/scan_tree(assert 断言)。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCAN_DIRS = ("services", "routes")

# storage 目录信号:命中任一即认为该文件在碰 storage 树落盘布局。
_SIGNALS = (
    "WORKORDER_STORAGE_DIR",
    "PDF_STORAGE_DIR",
    "PDF_STORAGE_BASE",
    "LINE_INTAKE_STORAGE_DIR",
    "EXCEL_STORE_DIR",
    "deliverables_dir",
    "versioned_dir(",
    "order_dir(",
)

# 裸文件 IO:Path.write_bytes/write_text、无参 Path.read_bytes()、二进制 open。
# 各 store 的 helper 形如 storage.read_bytes(path) / write_artifact_bytes(...) 带参且异名,不误伤。
_RAW_IO = (
    re.compile(r"\.write_bytes\s*\("),
    re.compile(r"\.write_text\s*\("),
    re.compile(r"\.read_bytes\s*\(\s*\)"),
)
# 二进制 open:open(...) 与二进制模式字面量分开判(嵌套 os.path.join(...) 会让单正则夭折)。
_OPEN = re.compile(r"\bopen\s*\(")
_BINARY_MODE = re.compile(r"['\"][rwax]\+?b['\"]")


def _has_raw_io(line: str) -> bool:
    if any(pat.search(line) for pat in _RAW_IO):
        return True
    return bool(_OPEN.search(line) and _BINARY_MODE.search(line))


# 收口 helper(sanctioned 落盘点,内部已过 file_crypto)+ 迁移脚本 + 加密层自身。
_ALLOWLIST = {
    "core/file_crypto.py",
    "services/workorder/storage.py",
    "services/ocr/pdf_storage.py",
    "services/knowledge/host_provider.py",
    "services/line_binding/line_intake_staging.py",
    "routes/vat_excel_routes.py",
    "scripts/ops/encrypt_storage_backfill.py",
}

_NOQA = "# storage-io-ok"


def scan_source(text: str, relpath: str) -> list[str]:
    """一份源码 → 违规行清单(relpath:lineno)。白名单/无信号 → 空。"""
    rel = relpath.replace("\\", "/")
    if rel in _ALLOWLIST:
        return []
    if not any(sig in text for sig in _SIGNALS):
        return []
    violations = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _NOQA in line:
            continue
        if _has_raw_io(line):
            violations.append(f"{rel}:{lineno}: 裸文件 IO 绕过 file_crypto —— 改走 store helper")
    return violations


def scan_tree(root: Path = _ROOT) -> list[str]:
    violations: list[str] = []
    for d in _SCAN_DIRS:
        for py in (root / d).rglob("*.py"):
            rel = py.relative_to(root).as_posix()
            violations.extend(scan_source(py.read_text(encoding="utf-8"), rel))
    return violations


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows cp874 控制台打中文不崩
    except (AttributeError, ValueError):
        pass
    violations = scan_tree()
    if violations:
        print("storage_io_guard: 发现绕过 file_crypto 的裸落盘/取盘:")
        for v in violations:
            print("  " + v)
        return 1
    print("storage_io_guard: OK · storage 树落盘全部经 file_crypto 收口")
    return 0


if __name__ == "__main__":
    sys.exit(main())
