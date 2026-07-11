#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_blob_size.py · 防屎山闸 #3 · 大文件 / sourcemap 闸

铁律 #27 延伸:禁止把大二进制(未压缩图 / 误提交的 sourcemap / 数据 dump)提进 git。
git 历史一旦收下大 blob 就永久驻留(即使后来删掉,历史里那份还在,clone/CI 永远背着),
且保护分支禁 force-push,回收要全员停工重写历史。故只能在"进门"这一刻挡住。

判据(只看本次 diff 新增/改动的文件 · 不追溯存量):
  * 任一 static/dist 下的 *.map(sourcemap 永不该进库·vite 已 sourcemap:false)→ fail
  * 任一新增/改动 blob 在 HEAD 处 > MAX_BLOB_MB → fail
存量大文件(如既有 landing PNG)不动它,不 re-commit 就不触发。

逃生门(与 RATCHET-EXEMPT 同范式·铁律 #21 透明记录):
  commit message 写 `BLOB-EXEMPT: <path>` 即跳过该文件本次检查(真需要的大资产)。

退出码:0 = 干净或全豁免;1 = 至少一个未豁免违规。零依赖(仅标准库 + git)。

用法:
  python scripts/check_blob_size.py                       # 默认 HEAD~1..HEAD
  python scripts/check_blob_size.py --base origin/master --head HEAD
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# main.js 现 ~1.33MB(每次 build re-commit)· 旧 sourcemap 3.2MB · landing PNG 4~5.5MB。
# 2.5MB:放过 minified bundle,挡住 map 与未压缩大图;bundle 真涨破须显式 BLOB-EXEMPT。
MAX_BLOB_MB = 2.5
MAX_BLOB_BYTES = int(MAX_BLOB_MB * 1024 * 1024)

_SOURCEMAP_RE = re.compile(r"^static/dist/.*\.map$")


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败 · exit {result.returncode}\n{result.stderr}")
    return result.stdout


def blob_size(head: str, path: str) -> int | None:
    """path 在 head 处的字节数;已删除/取不到返回 None。"""
    try:
        return int(git("cat-file", "-s", f"{head}:{path}").strip())
    except RuntimeError:
        return None


def collect_exempt(commit_range: str) -> set[str]:
    log = git("log", "--format=%B", commit_range)
    return {m.group(1).replace("\\", "/") for m in re.finditer(r"BLOB-EXEMPT:\s*(\S+)", log)}


def main() -> int:
    ap = argparse.ArgumentParser(description="防屎山闸 #3 · 大文件 / sourcemap 闸")
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    try:
        git("rev-parse", "--git-dir")
        git("rev-parse", "--verify", args.base)
    except (RuntimeError, FileNotFoundError) as e:
        print(f"⚠️  git 不可用或 base `{args.base}` 不存在(首 commit?)· 跳过:{e}")
        return 0

    commit_range = f"{args.base}..{args.head}"
    changed = [
        p
        for p in git("diff", "--name-only", "--diff-filter=AM", commit_range).splitlines()
        if p.strip()
    ]
    exempt = collect_exempt(commit_range)

    fails: list[tuple[str, int, str]] = []
    for path in changed:
        rp = path.replace("\\", "/")
        if rp in exempt:
            continue
        if _SOURCEMAP_RE.match(rp):
            fails.append((rp, blob_size(args.head, path) or 0, "sourcemap 禁入库"))
            continue
        size = blob_size(args.head, path)
        if size is not None and size > MAX_BLOB_BYTES:
            fails.append((rp, size, f"> {MAX_BLOB_MB}MB"))

    if args.quiet and not fails:
        return 0

    print("=" * 72)
    print(f"📦 Pearnly 防屎山闸 #3 · 大文件/sourcemap({commit_range})")
    print("=" * 72)
    if not fails:
        print("结果:✅ PASS · 本次 diff 无未豁免大 blob / sourcemap")
        return 0

    print("🔴 违规(新增/改动的大 blob · git 历史会永久背上):")
    for rp, size, why in fails:
        print(f"  [FAIL] {size / 1048576:6.2f} MB  {rp}  ({why})")
    print()
    print("解法:")
    print("  1) 压缩 / 移出 git(sourcemap 本就该 gitignore · 图片先压)")
    print("  2) 真需要 → commit message 加:BLOB-EXEMPT: <path> · <理由>")
    print("=" * 72)
    return 1


if __name__ == "__main__":
    sys.exit(main())
