#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把生产库的表结构导成一份可读、可重建的 SQL 快照(只读·SELECT-only)。

为什么要有这东西:本仓没有 schema 的单一事实源。
  · prod 的 alembic_version 停在 0020,git-deploy 没有 `alembic upgrade` 钩子 ——
    0021 之后的迁移全是留档,从没在生产跑过(多条迁移自己的 docstring 就写着"留档性质")。
  · 真正建表的是运行期 `ensure_tables()` 里的 `CREATE TABLE IF NOT EXISTS`。
  · 还有 26 张在产表连这个都没有:建表语句在仓库里根本不存在(见
    tests/unit/test_schema_ddl_coverage_gate.py 的 KNOWN_UNCOVERED)。空库重建不出来,
    只能从"谁的开发库还活着"里抄 —— 生产结构没有版本化的事实源。

本脚本先补最便宜的一环:把生产结构落进版本控制当**只读参照**。
产物 docs/db/prod-schema.sql 不被任何代码执行、不是迁移;它的用途是
  ① 空库/灾备重建时有据可依;② 给 DDL 覆盖闸提供"生产到底有哪些表"的事实源;
  ③ 结构变更在 PR diff 里看得见。

⚠️ 只读硬保险:全程只发 SELECT(information_schema / pg_catalog),绝不对生产写。

用法:
    export DATABASE_URL=...            # 生产只读串
    python scripts/dump_prod_schema.py docs/db/prod-schema.sql
"""

from __future__ import annotations

import io
import os
import sys
from typing import Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HEADER = """-- Pearnly · 生产库表结构快照(自动生成 · 只读参照 · 不是迁移)
--
-- 生成:python scripts/dump_prod_schema.py docs/db/prod-schema.sql
-- 事实源说明见该脚本文件头。这份文件不被任何运行期代码读取或执行;
-- 它的读者是①灾备重建 ②DDL 覆盖闸(tests/unit/test_schema_ddl_coverage_gate.py)③ PR reviewer。
--
-- 不含:数据、权限/角色、RLS 策略、触发器、扩展。只有序列/表/列/约束/索引。
-- 生成顺序按表名排序,便于 diff;因此 FOREIGN KEY 单独列在末尾而非表内联。
--
-- 空库重放(扩展得先自己装 · 本文件不建):
--   psql -d <空库> -c 'CREATE EXTENSION IF NOT EXISTS pgcrypto'      -- gen_random_uuid()
--                  -c 'CREATE EXTENSION IF NOT EXISTS vector'
--                  -f prod-schema.sql
"""


def _connect():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise SystemExit("❌ DATABASE_URL 未设置")
    import psycopg2

    conn = psycopg2.connect(url, sslmode=os.environ.get("PGSSLMODE", "require"))
    conn.set_client_encoding("UTF8")
    return conn


def _q(cur, sql: str) -> List[tuple]:
    cur.execute(sql)
    return cur.fetchall()


def _columns(cur) -> Dict[str, List[str]]:
    rows = _q(
        cur,
        """
        SELECT c.relname, a.attname,
               format_type(a.atttypid, a.atttypmod),
               a.attnotnull,
               pg_get_expr(d.adbin, d.adrelid),
               a.attnum
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
        WHERE n.nspname = 'public' AND c.relkind = 'r'
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY c.relname, a.attnum
        """,
    )
    out: Dict[str, List[str]] = {}
    for table, col, typ, notnull, default, _ in rows:
        piece = f'  "{col}" {typ}'
        if default is not None:
            piece += f" DEFAULT {default}"
        if notnull:
            piece += " NOT NULL"
        out.setdefault(table, []).append(piece)
    return out


def _constraints(cur) -> Tuple[Dict[str, List[str]], List[str]]:
    """表内联约束(PK/UNIQUE/CHECK)与外键(单独输出,避开建表顺序依赖)。"""
    rows = _q(
        cur,
        """
        SELECT c.relname, con.conname, con.contype, pg_get_constraintdef(con.oid)
        FROM pg_constraint con
        JOIN pg_class c ON c.oid = con.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind = 'r'
        ORDER BY c.relname, con.contype, con.conname
        """,
    )
    inline: Dict[str, List[str]] = {}
    fks: List[str] = []
    for table, name, ctype, definition in rows:
        if ctype == "f":
            fks.append(f'ALTER TABLE "{table}" ADD CONSTRAINT "{name}" {definition};')
        else:
            inline.setdefault(table, []).append(f'  CONSTRAINT "{name}" {definition}')
    return inline, fks


def _indexes(cur) -> Dict[str, List[str]]:
    """独立索引。约束自带的索引不在内 —— 判据用 pg_constraint.conindid,不用名字里有没有 _pkey:
    UNIQUE 约束的索引名是 <表>_<列>_key,按名字过滤漏掉它们,重放时 20 处 "already exists"。"""
    rows = _q(
        cur,
        """
        SELECT c.relname, pg_get_indexdef(i.indexrelid)
        FROM pg_index i
        JOIN pg_class c ON c.oid = i.indrelid
        JOIN pg_class ic ON ic.oid = i.indexrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind = 'r'
          AND NOT EXISTS (SELECT 1 FROM pg_constraint con WHERE con.conindid = i.indexrelid)
        ORDER BY c.relname, ic.relname
        """,
    )
    out: Dict[str, List[str]] = {}
    for table, definition in rows:
        out.setdefault(table, []).append(definition + ";")
    return out


def _sequences(cur) -> List[str]:
    """serial 列的 DEFAULT nextval('x') 引用的序列。不导出 = 空库重放时这些表一张都建不出来
    (2026-07-31 首版快照 176 张里 54 张卡在这:ERROR relation "x_id_seq" does not exist)。"""
    rows = _q(
        cur,
        """
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind = 'S'
        ORDER BY c.relname
        """,
    )
    return [f'CREATE SEQUENCE IF NOT EXISTS "{name}";' for (name,) in rows]


def render(cols, inline, fks, idx, seqs=()) -> str:
    parts = [HEADER]
    if seqs:
        parts.append("\n-- 序列(先于表:表的 DEFAULT nextval() 直接引用它们)")
        parts.extend(seqs)
    for table in sorted(cols):
        body = cols[table] + inline.get(table, [])
        parts.append(f'\nCREATE TABLE IF NOT EXISTS "{table}" (\n' + ",\n".join(body) + "\n);")
        for line in idx.get(table, []):
            parts.append(line)
    parts.append("\n-- 外键(建表全部完成后再加,避免顺序依赖)")
    parts.extend(fks)
    return "\n".join(parts) + "\n"


def main() -> int:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "docs/db/prod-schema.sql"
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cols = _columns(cur)
            inline, fks = _constraints(cur)
            idx = _indexes(cur)
            seqs = _sequences(cur)
        conn.rollback()
    finally:
        conn.close()
    text = render(cols, inline, fks, idx, seqs)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(
        f"wrote {out_path} · {len(cols)} tables · {len(seqs)} sequences · {len(fks)} foreign keys"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
