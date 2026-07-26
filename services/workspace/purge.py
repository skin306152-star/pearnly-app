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
from typing import Any, Dict, Iterator, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 主体行上要留下的列:Zihao 拍板「除了套账名称和税号,其它全部清空」。
# 结构性列(id/tenant_id/user_id/时间戳)与 NOT NULL 列不动,否则行本身就废了。
_KEEP_COLUMNS = frozenset({"id", "tenant_id", "user_id", "name", "tax_id"})


# ⚠️ 表结构一律从 pg_catalog 读,不碰 information_schema。
# 2026-07-26 线上事故:information_schema 的约束视图(constraint_column_usage /
# key_column_usage)【按权限过滤】—— 只对表属主可见。生产业务连接跑在最小权限角色
# pearnly_app 上,这几个视图返回 0 行 → 子表清单为空 → 一张子表没删 → 父表 work_orders
# 被 RESTRICT 外键挡住 → 报「清除完毕」但工单/审核/交付包/报表原样还在。
# 本地验收连的是属主账号,视图正常,所以没照出来。pg_catalog 不挑权限,两边一致。
_SCOPE_TABLES_SQL = """
    SELECT c.relname AS table_name
    FROM pg_attribute a
    JOIN pg_class c ON c.oid = a.attrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind = 'r'
      AND a.attname = 'workspace_client_id' AND a.attnum > 0 AND NOT a.attisdropped
    ORDER BY c.relname
"""


def scope_tables(cur) -> List[str]:
    """所有带 workspace_client_id 的表(= 直接归属某个账套的数据)。"""
    cur.execute(_SCOPE_TABLES_SQL)
    return [r["table_name"] for r in cur.fetchall()]


def child_edges(cur) -> List[Dict[str, str]]:
    """外键指向账套级表、自己却不带 workspace_client_id 的子表(明细行/附件行等)。

    这些表按父表 id 反查删除。CASCADE 的父表删了会自动带走,但 RESTRICT 的会把父表
    的删除整个挡下来(work_order_items / pos_sale_lines 等),所以一律先删子表。
    """
    cur.execute(f"""
        WITH ws AS ({_SCOPE_TABLES_SQL})
        SELECT DISTINCT
               ch.relname AS child,
               ca.attname AS child_col,
               pa.relname AS parent,
               fa.attname AS parent_col
        FROM pg_constraint c
        JOIN pg_class ch ON ch.oid = c.conrelid
        JOIN pg_class pa ON pa.oid = c.confrelid
        JOIN pg_namespace n ON n.oid = ch.relnamespace
        JOIN pg_attribute ca ON ca.attrelid = c.conrelid AND ca.attnum = c.conkey[1]
        JOIN pg_attribute fa ON fa.attrelid = c.confrelid AND fa.attnum = c.confkey[1]
        WHERE c.contype = 'f' AND n.nspname = 'public'
          AND array_length(c.conkey, 1) = 1
          AND pa.relname IN (SELECT table_name FROM ws)
          AND ch.relname NOT IN (SELECT table_name FROM ws)
        ORDER BY child, child_col
        """)
    return [dict(r) for r in cur.fetchall()]


def verify_empty(cur, ws_id: int) -> List[Dict[str, Any]]:
    """删完真回数:哪张表还剩行就报哪张。

    「删了 0 行」和「这张表本来就没数据」在 DELETE 的 rowcount 上长得一模一样 ——
    上一版正是靠 rowcount 报成功,结果一张子表都没删掉还说清完了。这里不看过程看结果。
    """
    left: List[Dict[str, Any]] = []
    for table in scope_tables(cur):
        cur.execute(
            f"SELECT count(*) AS n FROM {table} WHERE workspace_client_id = %s",  # noqa: S608
            (ws_id,),
        )
        n = int((cur.fetchone() or {}).get("n") or 0)
        if n:
            left.append({"table": table, "rows": n})
    for edge in child_edges(cur):
        cur.execute(
            f"SELECT count(*) AS n FROM {edge['child']} WHERE {edge['child_col']} IN "  # noqa: S608
            f"(SELECT {edge['parent_col']} FROM {edge['parent']} WHERE workspace_client_id = %s)",
            (ws_id,),
        )
        n = int((cur.fetchone() or {}).get("n") or 0)
        if n:
            left.append({"table": edge["child"], "rows": n})
    return left


def _has_tenant_column(cur, table: str) -> bool:
    cur.execute(
        "SELECT 1 FROM pg_attribute a "
        "JOIN pg_class c ON c.oid = a.attrelid "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relname = %s "
        "AND a.attname = 'tenant_id' AND a.attnum > 0 AND NOT a.attisdropped",
        (table,),
    )
    return cur.fetchone() is not None


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

    # 子表与账套级表进同一个重试轮:子表原本只跑一轮,顺序不对或一次失败就永久漏掉
    # (2026-07-26 线上正是子表全漏)。子表排前面 —— RESTRICT 外键要求先清子再清父。
    scoped = {t: _has_tenant_column(cur, t) for t in tables}
    pending: List[Tuple[str, str, Any]] = [("child", e["child"], e) for e in edges] + [
        ("table", t, t) for t in tables
    ]

    while pending:
        stuck: List[Tuple[str, str, Any]] = []
        progressed = False
        for kind, label, target in pending:
            if kind == "child":
                ok, n = _try_delete(cur, label, lambda e=target: _delete_child(cur, e, ws_id))
            else:
                ok, n = _try_delete(
                    cur,
                    label,
                    lambda t=target: _delete_scope(cur, t, ws_id, tenant_id, scoped[t]),
                )
            if not ok:
                stuck.append((kind, label, target))
                continue
            progressed = True
            done += 1
            deleted_total += n
            yield {
                "step": kind,
                "label": label,
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
    # 结论以真回数为准,不以 DELETE 的 rowcount 为准。
    left = verify_empty(cur, ws_id)
    yield {
        "step": "finished",
        "deleted_total": deleted_total,
        "done": done,
        "total": total,
        "leftover": [x["table"] for x in left],
        "leftover_detail": left,
    }
