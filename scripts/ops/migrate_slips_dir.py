# -*- coding: utf-8 -*-
"""存量充值截图搬家(ENC-b · 一次性):routes/static/slips/* → 备份覆盖面内的
{SLIPS_STORAGE_ROOT}/slips/*(services.billing.slip_storage 的落点)。

老目录写死在路由文件旁,自 2026-06-03 目录重组起从未进 rsync 备份覆盖面,且 admin 展示
URL 已 404(见 ENC-b 派单书事实底稿)。本脚本只做一次性搬家,不是常驻服务——照
encrypt_storage_backfill.py 同款三道保险(读原文件 → 经 slip_storage.write_slip 落新址,
FILE_ENC_MODE=on 时顺带加密 → 解密回验 sha256 逐字节一致 → 才删源文件),幂等
(新址已存在且回验通过则跳过,不重复搬)。

用法:
    python scripts/ops/migrate_slips_dir.py [--source DIR] [--keep-source] [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from services.billing import slip_storage  # noqa: E402


class MigrateError(Exception):
    """搬家中途不可继续的错误(回验失败),带已处理计数。"""

    def __init__(self, message: str, report: dict):
        super().__init__(message)
        self.report = report


def _default_source() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "routes" / "static" / "slips"


def migrate(source: Path, *, keep_source: bool = False, dry_run: bool = False) -> dict:
    """搬家 source/ 下所有文件到 slip_storage 落点。返回 {moved, skipped, corrupt}。"""
    report = {"moved": 0, "skipped": 0, "corrupt": []}
    if not source.exists():
        return report
    for path in sorted(source.iterdir()):
        if not path.is_file():
            continue
        slip_rel = f"slips/{path.name}"
        dest = slip_storage.abs_path(slip_rel)
        plain = path.read_bytes()
        plain_sha = hashlib.sha256(plain).hexdigest()

        if dest and dest.exists():
            existing = slip_storage.read_slip(slip_rel)
            if existing is not None and hashlib.sha256(existing).hexdigest() == plain_sha:
                report["skipped"] += 1
                if not keep_source and not dry_run:
                    path.unlink()
                continue

        if dry_run:
            report["moved"] += 1
            continue

        slip_storage.write_slip(slip_rel, plain)
        roundtrip = slip_storage.read_slip(slip_rel)
        if roundtrip is None or hashlib.sha256(roundtrip).hexdigest() != plain_sha:
            report["corrupt"].append(str(path))
            continue
        report["moved"] += 1
        if not keep_source:
            path.unlink()

    if report["corrupt"]:
        raise MigrateError(f"发现 {len(report['corrupt'])} 个搬家后回验失败的文件,点名停", report)
    return report


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--source", type=Path, default=None, help="老 slips 目录(默认 routes/static/slips)"
    )
    ap.add_argument("--keep-source", action="store_true", help="搬完不删源文件(留作双份核对)")
    ap.add_argument("--dry-run", action="store_true", help="只报告将搬几个,不实际写")
    args = ap.parse_args(argv)

    source = args.source or _default_source()
    try:
        rep = migrate(source, keep_source=args.keep_source, dry_run=args.dry_run)
    except MigrateError as e:
        print(f"[migrate-slips] 停:{e}")
        for c in e.report.get("corrupt", []):
            print("  回验失败:" + c)
        return 1
    print(f"[migrate-slips] 搬移={rep['moved']} 跳过(已存在且一致)={rep['skipped']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
