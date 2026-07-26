# -*- coding: utf-8 -*-
"""按账套主体清空数据(保留主体本身的名称与税号)。

表清单不写死:运行期从 information_schema 找出所有带 workspace_client_id 的表,再把
外键指向它们、但自己不带该列的子表一并纳入。写死 70+ 张表必然随 schema 漂移,漏一张
就是「报告清空成功、数据还在」。

删除顺序靠每张表一个 SAVEPOINT + 多轮重试解决:某张表因外键删不掉就回滚到该表的
savepoint、下一轮再试,直到某一轮一张也删不动为止。不需要预先算拓扑序,新增外键
也不用回来改这里。仍删不掉的表如实报出去,不假装干净。

隔离:每条 DELETE 都带 workspace_client_id;表上有 tenant_id 的再叠一层 —— 应用层
WHERE 是主隔离,RLS 是第二道(core/rls.py)。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

logger = logging.getLogger(__name__)

_STORAGE_ROOT = os.environ.get("PEARNLY_STORAGE_ROOT", "/opt/mrpilot/storage")

# 主体行上要留下的列:Zihao 拍板「除了套账名称和税号,其它全部清空」。
# 结构性列(id/tenant_id/user_id/时间戳)与 NOT NULL 列不动,否则行本身就废了。
_KEEP_COLUMNS = frozenset({"id", "tenant_id", "user_id", "name", "tax_id"})

# 存本地磁盘路径的列(删行前先把路径抠出来,删完再清文件 —— 同
# services/purchase/attachment_files.py 的 collect→delete→purge 三段式)。
# 只列真正指向本机文件的;外部链接(drive_url/receipt_url)不在此列,删不着也不该删。
_FILE_COLUMNS: Tuple[Tuple[str, str], ...] = (
    ("ocr_history", "storage_path"),
    ("ocr_history", "pdf_storage_path"),
    ("knowledge_documents", "storage_path"),
    ("vat_recon_tasks", "excel_path"),
)


def scope_tables(cur) -> List[str]:
    """所有带 workspace_client_id 的表(= 直接归属某个账套的数据)。"""
    cur.execute(
        "SELECT table_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND column_name = 'workspace_client_id' "
        "ORDER BY table_name"
    )
    return [r["table_name"] for r in cur.fetchall()]


def child_edges(cur) -> List[Dict[str, str]]:
    """外键指向账套级表、自己却不带 workspace_client_id 的子表(明细行/附件行等)。

    这些表按父表 id 反查删除。CASCADE 的父表删了会自动带走,但 RESTRICT 的会把父表
    的删除整个挡下来(work_order_items / pos_sale_lines 等),所以一律先删子表。
    """
    cur.execute("""
        WITH ws AS (
            SELECT table_name FROM information_schema.columns
            WHERE table_schema = 'public' AND column_name = 'workspace_client_id'
        )
        SELECT DISTINCT tc.table_name AS child, kcu.column_name AS child_col,
               ccu.table_name AS parent, ccu.column_name AS parent_col
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
             ON kcu.constraint_name = tc.constraint_name AND kcu.table_schema = tc.table_schema
        JOIN information_schema.constraint_column_usage ccu
             ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
          AND ccu.table_name IN (SELECT table_name FROM ws)
          AND tc.table_name NOT IN (SELECT table_name FROM ws)
        ORDER BY child, child_col
        """)
    return [dict(r) for r in cur.fetchall()]


def _has_tenant_column(cur, table: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s AND column_name = 'tenant_id'",
        (table,),
    )
    return cur.fetchone() is not None


def collect_file_paths(cur, ws_id: int) -> List[str]:
    """删行【之前】把本地文件路径抠出来 —— 行没了就再也定位不到这些文件。"""
    paths: List[str] = []
    tables = set(scope_tables(cur))
    for table, column in _FILE_COLUMNS:
        if table not in tables:
            continue
        cur.execute(
            f"SELECT {column} AS p FROM {table} "  # noqa: S608 — 表名/列名来自本模块常量,非外部输入
            f"WHERE workspace_client_id = %s AND {column} IS NOT NULL AND {column} <> ''",
            (ws_id,),
        )
        paths.extend(str(r["p"]) for r in cur.fetchall())
    return paths


def purge_files(paths: List[str]) -> int:
    """事务提交后 best-effort 删盘上文件,返回真删掉的个数。

    失败只记日志不抛:行已经删了,留个孤儿文件不影响正确性,把整个清除报成失败反而更糟。
    只动 storage 根目录之下的路径 —— 库里存的字符串不该当可信输入,越界的一律跳过。
    """
    root = Path(_STORAGE_ROOT).resolve()
    removed = 0
    for raw in paths:
        try:
            p = (root / raw).resolve() if not os.path.isabs(raw) else Path(raw).resolve()
            if root not in p.parents:
                logger.warning(f"[purge] 路径越界,跳过: {raw}")
                continue
            if p.is_file():
                p.unlink()
                removed += 1
        except Exception:  # noqa: BLE001
            logger.warning(f"[purge] 删文件失败: {raw}", exc_info=True)
    return removed


def _delete_child(cur, edge: Dict[str, str], ws_id: int) -> int:
    cur.execute(
        f"DELETE FROM {edge['child']} WHERE {edge['child_col']} IN "  # noqa: S608 — 标识符来自 information_schema
        f"(SELECT {edge['parent_col']} FROM {edge['parent']} WHERE workspace_client_id = %s)",
        (ws_id,),
    )
    return cur.rowcount or 0


def _delete_scope(cur, table: str, ws_id: int, tenant_id: Optional[str], scoped: bool) -> int:
    if scoped:
        cur.execute(
            f"DELETE FROM {table} WHERE workspace_client_id = %s AND tenant_id = %s",  # noqa: S608
            (ws_id, tenant_id),
        )
    else:
        cur.execute(
            f"DELETE FROM {table} WHERE workspace_client_id = %s",  # noqa: S608
            (ws_id,),
        )
    return cur.rowcount or 0


def _try_delete(cur, key: str, run) -> Tuple[bool, int]:
    """一张表一个 SAVEPOINT:删失败(多半是外键)只回滚这张表,不炸整个事务。"""
    sp = "sp_purge"
    cur.execute(f"SAVEPOINT {sp}")
    try:
        n = run()
    except Exception as e:  # noqa: BLE001 — 失败原因不重要,下一轮重试;轮完仍败会如实报出
        cur.execute(f"ROLLBACK TO SAVEPOINT {sp}")
        logger.info(f"[purge] {key} 本轮删不掉,留待下一轮: {e}")
        return False, 0
    cur.execute(f"RELEASE SAVEPOINT {sp}")
    return True, n


def _reset_subject_row(cur, ws_id: int, tenant_id: Optional[str]) -> None:
    """主体行只留名称与税号,其余可空业务列清掉(结构列与 NOT NULL 列不动)。"""
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = 'workspace_clients' "
        "AND is_nullable = 'YES'"
    )
    cols = [r["column_name"] for r in cur.fetchall() if r["column_name"] not in _KEEP_COLUMNS]
    if not cols:
        return
    sets = ", ".join(f"{c} = NULL" for c in cols)
    cur.execute(
        f"UPDATE workspace_clients SET {sets}, updated_at = now() "  # noqa: S608 — 列名来自 information_schema
        "WHERE id = %s AND tenant_id = %s",
        (ws_id, tenant_id),
    )


def purge(cur, *, tenant_id: Optional[str], ws_id: int) -> Iterator[Dict[str, Any]]:
    """逐表清空并把进度吐出来。调用方负责事务提交/回滚与文件清理。

    产出:{"step","label","deleted","done","total"};收尾一条 {"done": total, "leftover": [...]}。
    """
    edges = child_edges(cur)
    tables = scope_tables(cur)
    total = len(edges) + len(tables) + 1  # +1 = 主体行重置
    done = 0
    deleted_total = 0

    for edge in edges:
        ok, n = _try_delete(cur, edge["child"], lambda e=edge: _delete_child(cur, e, ws_id))
        done += 1
        deleted_total += n
        yield {
            "step": "child",
            "label": edge["child"],
            "deleted": n,
            "done": done,
            "total": total,
            "ok": ok,
        }

    pending = list(tables)
    scoped = {t: _has_tenant_column(cur, t) for t in pending}
    while pending:
        stuck: List[str] = []
        progressed = False
        for table in pending:
            ok, n = _try_delete(
                cur, table, lambda t=table: _delete_scope(cur, t, ws_id, tenant_id, scoped[t])
            )
            if not ok:
                stuck.append(table)
                continue
            progressed = True
            done += 1
            deleted_total += n
            yield {
                "step": "table",
                "label": table,
                "deleted": n,
                "done": done,
                "total": total,
                "ok": True,
            }
        if not progressed:
            break
        pending = stuck

    _reset_subject_row(cur, ws_id, tenant_id)
    done += 1
    yield {
        "step": "subject",
        "label": "workspace_clients",
        "deleted": 0,
        "done": done,
        "total": total,
        "ok": True,
    }
    yield {
        "step": "finished",
        "deleted_total": deleted_total,
        "done": done,
        "total": total,
        "leftover": pending,
    }
