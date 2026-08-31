#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸:生产在用的每张表,建表 DDL 都得在产品代码里(不是只在测试桩/文档里)。

治的病:本仓 schema 没有版本化的事实源。prod 的 alembic_version 停在 0020,
git-deploy 没有 `alembic upgrade` 钩子 —— 0021 之后 70 多条迁移从没在生产跑过,
真正建表的是运行期 `ensure_tables()` 的 `CREATE TABLE IF NOT EXISTS`。
于是有一批表两头都没有:迁移里只有 ALTER、代码里没有 CREATE,建表语句只存在于
某台开发机的活库里。空库重建不出来 —— 真库测试一碰就炸,只能在测试文件里手抄 DDL,
而手抄的 DDL 又不是事实源(抄错了没人知道)。

历史欠账已于 2026-08-01 还清:迁移 001a_legacy_tables(载荷 alembic/sql/001a_legacy_tables.sql)
把那 26 张表的建表 DDL 逐字从快照补进了迁移史,KNOWN_UNCOVERED 因此清空。
闸从此是硬门:生产在用的表,产品代码里必须有建表 DDL,一张都不许缺。

判据来源:
  · "生产有哪些表" = docs/db/prod-schema.sql(scripts/dump_prod_schema.py 生成的只读快照)
  · "仓库里有没有建表 DDL" = 扫产品代码里的 CREATE TABLE。
    ⚠️ tests/ 与 docs/ 一律不算数 —— 测试桩里的手抄 DDL 正是本闸要抓的东西,
    把它算作覆盖等于闸给自己开后门(快照文件本身就在 docs/,不排除的话全表恒绿)。

用法:
    python scripts/check_schema_ddl_coverage.py [--quiet]
退出码:0 = 覆盖没退步;1 = 有新表没 DDL,或名单有过期条目。
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = PROJECT_ROOT / "docs" / "db" / "prod-schema.sql"

# 扫描范围:产品代码。tests/ docs/ 不在内(见文件头"判据来源")。
_SCAN_DIRS = ("alembic/versions", "alembic/sql", "services", "core", "routes", "scripts/sql")
_SCAN_ROOT_FILES = ("app.py", "db.py")
_SKIP_PARTS = ("node_modules", "__pycache__", ".git", "venv", "dist")

_CREATE_RE = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?[\"']?([a-z0-9_]+)", re.I)

# 历史欠账清单。2026-07-31 建闸时装了 26 张,2026-08-01 由 001a_legacy_tables 全部还清,
# 现在是空的 —— 空 = 生产每张表都有 DDL,新表欠债当场红。留着这个入口是为了下次真需要
# 记债时有个透明位置(条目要写清欠的是什么、谁还),不是为了给人塞新债。
KNOWN_UNCOVERED: Dict[str, str] = {}

# 已从运行时代码断开的旧 Cowork LINE 表。它们暂留生产库只为分批核验后安全删除，
# 不属于“生产在用的表”，因此不要求把已删除的业务 DDL 重新塞回产品代码。
RETIRED_TABLES_PENDING_DROP = {
    "line_client_bind_codes",
    "line_client_contacts",
    "line_client_questions",
    "line_ocr_jobs",
    "line_pending_actions",
    "line_pending_entry",
    "notification_logs",
    "notification_rules",
}


def snapshot_tables(snapshot_text: str) -> Set[str]:
    return {m.group(1).lower() for m in _CREATE_RE.finditer(snapshot_text)}


def _iter_product_files(root: Path):
    for rel in _SCAN_ROOT_FILES:
        p = root / rel
        if p.is_file():
            yield p
    for d in _SCAN_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.suffix not in (".py", ".sql") or not p.is_file():
                continue
            if any(part in _SKIP_PARTS for part in p.parts):
                continue
            yield p


def product_ddl_tables(root: Path = PROJECT_ROOT) -> Set[str]:
    """产品代码里出现过 CREATE TABLE 的表名。"""
    found: Set[str] = set()
    for p in _iter_product_files(root):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        found.update(m.group(1).lower() for m in _CREATE_RE.finditer(text))
    return found


def evaluate(prod: Set[str], covered: Set[str], known: Set[str]) -> List[str]:
    """纯函数,便于用有毒输入做反证。返回违规说明(空 = 通过)。"""
    problems: List[str] = []
    uncovered = {
        t
        for t in prod
        if t not in covered and t != "alembic_version" and t not in RETIRED_TABLES_PENDING_DROP
    }
    for t in sorted(uncovered - known):
        problems.append(f"新增欠账:表 {t} 在生产存在,但产品代码里没有建表 DDL")
    for t in sorted(known & covered):
        problems.append(f"名单过期:表 {t} 已经有 DDL 了,请从 KNOWN_UNCOVERED 删掉")
    for t in sorted(known - prod):
        problems.append(f"名单过期:表 {t} 生产已不存在,请从 KNOWN_UNCOVERED 删掉")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not SNAPSHOT.is_file():
        print(
            f"❌ 找不到 {SNAPSHOT.relative_to(PROJECT_ROOT).as_posix()}(先跑 dump_prod_schema.py)"
        )
        return 1
    prod = snapshot_tables(SNAPSHOT.read_text(encoding="utf-8"))
    covered = product_ddl_tables()
    problems = evaluate(prod, covered, set(KNOWN_UNCOVERED))
    if problems:
        print("❌ schema DDL 覆盖闸不通过:")
        for line in problems:
            print("   ", line)
        return 1
    if not args.quiet:
        print(f"✅ 生产 {len(prod)} 张表 · 历史欠账 {len(KNOWN_UNCOVERED)} 张(未新增)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
