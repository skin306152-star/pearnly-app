#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸:生产在用的每张表,建表 DDL 都得在产品代码里(不是只在测试桩/文档里)。

治的病:本仓 schema 没有版本化的事实源。prod 的 alembic_version 停在 0020,
git-deploy 没有 `alembic upgrade` 钩子 —— 0021 之后 70 多条迁移从没在生产跑过,
真正建表的是运行期 `ensure_tables()` 的 `CREATE TABLE IF NOT EXISTS`。
于是有一批表两头都没有:迁移里只有 ALTER、代码里没有 CREATE,建表语句只存在于
某台开发机的活库里。空库重建不出来 —— 真库测试一碰就炸,只能在测试文件里手抄 DDL,
而手抄的 DDL 又不是事实源(抄错了没人知道)。

本闸不解决历史欠账(那需要一条 baseline 迁移,风险另议),只钉住两件事:
  ① 新表不许再以这种状态出生 —— 建表 DDL 必须落在产品代码里;
  ② 历史欠账只准变少:KNOWN_UNCOVERED 里的表一旦补上 DDL,必须同步从名单删掉。

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
_SCAN_DIRS = ("alembic/versions", "services", "core", "routes", "scripts/sql")
_SCAN_ROOT_FILES = ("app.py", "db.py")
_SKIP_PARTS = ("node_modules", "__pycache__", ".git", "venv", "dist")

_CREATE_RE = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?[\"']?([a-z0-9_]+)", re.I)

# 历史欠账(2026-07-31 盘点 · 176 张在产表里的 26 张):建表 DDL 在产品代码里根本不存在。
# 前 11 张全仓只有 tests/integration 的手抄桩,后 15 张连桩都没有。
# 修的方向是一条 baseline 迁移把它们补进迁移史;在那之前本名单只准变短。
KNOWN_UNCOVERED: Dict[str, str] = {
    # 只在 tests/integration 的 RLS 真库测试里手抄过 DDL
    "automation_rules": "tests/integration/test_automation_rls_real_tables.py 手抄",
    "bank_reconcile_candidates": "tests/integration/test_bank_recon_rls_real_tables.py 手抄",
    "bank_reconcile_sessions": "tests/integration/test_bank_recon_rls_real_tables.py 手抄",
    "bank_reconcile_transactions": "tests/integration/test_bank_recon_rls_real_tables.py 手抄",
    "email_ingest_accounts": "tests/integration/test_email_ingest_rls_real_tables.py 手抄",
    "email_ingest_logs": "tests/integration/test_email_ingest_rls_real_tables.py 手抄",
    "email_ingest_seen_uids": "tests/integration/test_email_ingest_rls_real_tables.py 手抄",
    "erp_endpoints": "tests/integration/test_erp_push_rls_real_tables.py 手抄",
    "erp_push_logs": "tests/integration/test_erp_push_rls_real_tables.py 手抄",
    "ocr_history": "tests/integration/test_clients_ocr_history_rls_real_tables.py 手抄(被 16 条迁移 ALTER 过)",
    "users": "tests/integration/test_clients_ocr_history_rls_real_tables.py 手抄",
    # 全仓无任何建表语句
    "api_keys": "全仓无 CREATE",
    "erp_oauth_states": "全仓无 CREATE",
    "erp_oauth_tokens": "全仓无 CREATE",
    "excel_templates": "全仓无 CREATE",
    "expense_draft": "全仓无 CREATE",
    "ip_usage": "全仓无 CREATE",
    "line_binding_codes": "全仓无 CREATE",
    "line_bindings": "全仓无 CREATE",
    "mrerp_credentials": "全仓无 CREATE",
    "operation_logs": "全仓无 CREATE",
    "rd_cache": "全仓无 CREATE",
    "rd_daily_usage": "全仓无 CREATE",
    "supplier_client_mapping": "全仓无 CREATE",
    "tenants": "全仓无 CREATE",
    "user_settings": "全仓无 CREATE",
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
    uncovered = {t for t in prod if t not in covered and t != "alembic_version"}
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
