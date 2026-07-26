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
_TABLES_WITH_COLUMN_SQL = """
    SELECT c.relname AS table_name
    FROM pg_attribute a
    JOIN pg_class c ON c.oid = a.attrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind = 'r'
      AND a.attname = %s AND a.attnum > 0 AND NOT a.attisdropped
    ORDER BY c.relname
"""
_SCOPE_TABLES_SQL = _TABLES_WITH_COLUMN_SQL.replace("%s", "'workspace_client_id'")


def tables_with_column(cur, column: str) -> List[str]:
    """public 下带某列的表。一条查回来 —— 逐表问「有没有这列」是 73 次往返换一张表。"""
    cur.execute(_TABLES_WITH_COLUMN_SQL, (column,))
    return [r["table_name"] for r in cur.fetchall()]


def scope_tables(cur) -> List[str]:
    """所有带 workspace_client_id 的表(= 直接归属某个账套的数据)。"""
    return tables_with_column(cur, "workspace_client_id")


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


# ⚠️ 按期清能碰哪些表,只能白名单,不能按「有没有 period 列」嗅 —— 列名一样不代表
# 说的是同一件事。生产实测:work_orders/client_period_obligations 是佛历(2569-07),
# journal_vouchers/tax_filings 是公历(2026-07),document_number_sequences 是公历年月桶
# 且它是发票号计数器(删了号会跳,泰国税票号不许跳,见 alembic 0006_sales_core)。
# 拿佛历期去删公历表 = 删 0 行还报成功,正是本模块要根治的静默漏删;拿它去删计数器
# 则是踩法律红线。宁可少删并如实说明,不可乱删。
# 新增带 period 的表要进来,先确认它的 period 与 work_orders 同一套词汇。
_PERIOD_TABLES_BE = ("work_orders", "client_period_obligations", "client_payroll_rows")


def _period_tables(cur, tables: List[str]) -> List[str]:
    """按期清覆盖的表:与 work_orders 同一套佛历账期词汇的那几张(白名单,见上注)。"""
    have = set(tables_with_column(cur, "period")) & set(tables)
    return [t for t in _PERIOD_TABLES_BE if t in have]


def periods_with_data(cur, ws_id: int) -> List[Dict[str, Any]]:
    """该账套下真有数据的账期 + 每期的工单数。只列真有的 —— 下拉里摆一堆空账期是假选项。"""
    cur.execute(
        "SELECT period, count(*) AS orders FROM work_orders "
        "WHERE workspace_client_id = %s AND period IS NOT NULL AND period <> '' "
        "GROUP BY period ORDER BY period DESC",
        (ws_id,),
    )
    return [{"period": r["period"], "orders": int(r["orders"] or 0)} for r in cur.fetchall()]


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


def _delete_child(cur, edge: Dict[str, str], ws_id: int) -> int:
    cur.execute(
        f"DELETE FROM {edge['child']} WHERE {edge['child_col']} IN "  # noqa: S608 — 标识符来自 information_schema
        f"(SELECT {edge['parent_col']} FROM {edge['parent']} WHERE workspace_client_id = %s)",
        (ws_id,),
    )
    return cur.rowcount or 0


def _delete_scope(cur, table: str, ws_id: int, tenant_id: Optional[str], scoped: bool) -> int:
    """应用层 WHERE 是主隔离;表上有 tenant_id 就再叠一层(RLS 是第二道)。"""
    where = "workspace_client_id = %s" + (" AND tenant_id = %s" if scoped else "")
    params = (ws_id, tenant_id) if scoped else (ws_id,)
    cur.execute(f"DELETE FROM {table} WHERE {where}", params)  # noqa: S608 — 标识符来自 pg_catalog
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
    # 同顶注:走 pg_catalog 不走 information_schema —— 后者按权限过滤,最小权限角色下
    # 可能返回空,那样这行就「清了个寂寞」还一声不吭。
    cur.execute(
        "SELECT a.attname AS c FROM pg_attribute a "
        "JOIN pg_class t ON t.oid = a.attrelid "
        "JOIN pg_namespace n ON n.oid = t.relnamespace "
        "WHERE n.nspname = 'public' AND t.relname = 'workspace_clients' "
        "AND a.attnum > 0 AND NOT a.attisdropped AND NOT a.attnotnull"
    )
    cols = [r["c"] for r in cur.fetchall() if r["c"] not in _KEEP_COLUMNS]
    if not cols:
        return
    sets = ", ".join(f"{c} = NULL" for c in cols)
    cur.execute(
        f"UPDATE workspace_clients SET {sets}, updated_at = now() "  # noqa: S608 — 列名来自 information_schema
        "WHERE id = %s AND tenant_id = %s",
        (ws_id, tenant_id),
    )


def period_scope(cur, ws_id: int, period: str) -> Dict[str, List[str]]:
    """该账期的工单 id、以及挂在这些工单上的票据 id。

    必须在删任何行【之前】取:票据与账期的唯一联系是 work_order_items.ocr_history_id,
    子行一删这层关系就没了,票据再也认不出属于哪个账期。
    """
    cur.execute(
        "SELECT id::text AS id FROM work_orders WHERE workspace_client_id = %s AND period = %s",
        (ws_id, period),
    )
    wo_ids = [r["id"] for r in cur.fetchall()]
    hist_ids: List[str] = []
    if wo_ids:
        cur.execute(
            "SELECT DISTINCT ocr_history_id::text AS id FROM work_order_items "
            "WHERE work_order_id = ANY(%s::uuid[]) AND ocr_history_id IS NOT NULL",
            (wo_ids,),
        )
        hist_ids = [r["id"] for r in cur.fetchall()]
    return {"work_order_ids": wo_ids, "ocr_history_ids": hist_ids}


def _period_pending(cur, ws_id: int, period: str, scope: Dict[str, List[str]]) -> List[Tuple]:
    """按账期清的工作清单。只碰这一期的东西:该期工单及其名下一切 + 挂上去的票据 +
    带 period 列的那几张表按期过滤。主数据(商品/科目表/供应商/客户档案)与别的账期不动。"""
    wo_ids = scope["work_order_ids"]
    hist_ids = scope["ocr_history_ids"]
    items: List[Tuple] = []

    if wo_ids:
        for edge in child_edges(cur):
            if edge["parent"] != "work_orders":
                continue
            items.append(
                (
                    "child",
                    edge["child"],
                    lambda e=edge: _delete_by_ids(cur, e["child"], e["child_col"], wo_ids, ws_id),
                )
            )
        items.append(
            (
                "table",
                "work_orders",
                lambda: _delete_by_ids(cur, "work_orders", "id", wo_ids, ws_id),
            )
        )
    if hist_ids:
        for edge in child_edges(cur):
            if edge["parent"] != "ocr_history":
                continue
            items.append(
                (
                    "child",
                    edge["child"],
                    lambda e=edge: _delete_by_ids(cur, e["child"], e["child_col"], hist_ids, ws_id),
                )
            )
        items.append(
            (
                "table",
                "ocr_history",
                lambda: _delete_by_ids(cur, "ocr_history", "id", hist_ids, ws_id),
            )
        )
    for table in _period_tables(cur, scope_tables(cur)):
        if table == "work_orders":
            continue
        items.append(
            ("table", table, lambda t=table: _delete_by_period(cur, t, ws_id, period)),
        )
    return items


def _delete_by_ids(cur, table: str, column: str, ids: List[str], ws_id: Optional[int]) -> int:
    """按 id 列表删。表上有 workspace_client_id 就再叠一层 —— 模块的硬规矩是每条 DELETE
    都带账套隔离,不能因为「id 是从受限查询里来的」就省掉(调用序不是隔离)。"""
    if not ids:
        return 0
    where = f"{column} = ANY(%s::uuid[])"
    params: tuple = (ids,)
    if ws_id is not None and column != "workspace_client_id":
        cur.execute(
            "SELECT 1 FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public' "
            "AND c.relname = %s AND a.attname = 'workspace_client_id' "
            "AND a.attnum > 0 AND NOT a.attisdropped",
            (table,),
        )
        if cur.fetchone():
            where += " AND workspace_client_id = %s"
            params = (ids, ws_id)
    cur.execute(f"DELETE FROM {table} WHERE {where}", params)  # noqa: S608 — 标识符来自 pg_catalog
    return cur.rowcount or 0


def _delete_by_period(cur, table: str, ws_id: int, period: str) -> int:
    cur.execute(
        f"DELETE FROM {table} WHERE workspace_client_id = %s AND period = %s",  # noqa: S608
        (ws_id, period),
    )
    return cur.rowcount or 0


def verify_period_empty(cur, ws_id: int, period: str, scope: Dict[str, List[str]]) -> List[Dict]:
    """按账期清完的真回数:该期工单还剩几张、挂上去的票据还剩几条、带期表还剩几行。"""
    left: List[Dict[str, Any]] = []
    cur.execute(
        "SELECT count(*) AS n FROM work_orders WHERE workspace_client_id = %s AND period = %s",
        (ws_id, period),
    )
    n = int((cur.fetchone() or {}).get("n") or 0)
    if n:
        left.append({"table": "work_orders", "rows": n})
    if scope["ocr_history_ids"]:
        cur.execute(
            "SELECT count(*) AS n FROM ocr_history WHERE id = ANY(%s::uuid[])",
            (scope["ocr_history_ids"],),
        )
        n = int((cur.fetchone() or {}).get("n") or 0)
        if n:
            left.append({"table": "ocr_history", "rows": n})
    for table in _period_tables(cur, scope_tables(cur)):
        if table == "work_orders":
            continue
        cur.execute(
            f"SELECT count(*) AS n FROM {table} "  # noqa: S608
            "WHERE workspace_client_id = %s AND period = %s",
            (ws_id, period),
        )
        n = int((cur.fetchone() or {}).get("n") or 0)
        if n:
            left.append({"table": table, "rows": n})
    # 子表也要回数:整套账清那条已经逐张子表数了,按期这条原先一张不数 —— 而"子表全没删"
    # 正是本模块要根治的事故形状,在按期路径上不能是结构性看不见的。
    for edge in child_edges(cur):
        if edge["parent"] not in ("work_orders", "ocr_history"):
            continue
        ids = scope["work_order_ids" if edge["parent"] == "work_orders" else "ocr_history_ids"]
        if not ids:
            continue
        cur.execute(
            f"SELECT count(*) AS n FROM {edge['child']} "  # noqa: S608
            f"WHERE {edge['child_col']} = ANY(%s::uuid[])",
            (ids,),
        )
        n = int((cur.fetchone() or {}).get("n") or 0)
        if n:
            left.append({"table": edge["child"], "rows": n})
    return left


def purge(
    cur, *, tenant_id: Optional[str], ws_id: int, period: Optional[str] = None
) -> Iterator[Dict[str, Any]]:
    """逐表清空并把进度吐出来。调用方负责事务提交/回滚与文件清理。

    period=None → 整个账套清空(主体行只留名称与税号)。
    period 给值 → 只清这一期:该期工单及其名下一切 + 挂上去的票据 + 带期表按期过滤;
    主体行与主数据不动 —— 换一期还要接着用。

    产出:{"step","label","deleted","done","total"};收尾一条 {"leftover","leftover_detail"}。
    """
    if period:
        yield from _purge_period(cur, ws_id=ws_id, period=period)
        return

    edges = child_edges(cur)
    tables = scope_tables(cur)
    total = len(edges) + len(tables) + 1  # +1 = 主体行重置
    done = 0
    deleted_total = 0

    # 子表与账套级表进同一个重试轮:子表原本只跑一轮,顺序不对或一次失败就永久漏掉
    # (2026-07-26 线上正是子表全漏)。子表排前面 —— RESTRICT 外键要求先清子再清父。
    scoped = set(tables_with_column(cur, "tenant_id"))
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
                    lambda t=target: _delete_scope(cur, t, ws_id, tenant_id, t in scoped),
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


def _purge_period(cur, *, ws_id: int, period: str) -> Iterator[Dict[str, Any]]:
    scope = period_scope(cur, ws_id, period)
    pending = _period_pending(cur, ws_id, period, scope)
    total = max(len(pending), 1)
    done = 0
    deleted_total = 0

    while pending:
        stuck: List[Tuple] = []
        progressed = False
        for kind, label, run in pending:
            ok, n = _try_delete(cur, label, run)
            if not ok:
                stuck.append((kind, label, run))
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

    left = verify_period_empty(cur, ws_id, period, scope)
    yield {
        "step": "finished",
        "deleted_total": deleted_total,
        "done": done,
        "total": total,
        "period": period,
        "leftover": [x["table"] for x in left],
        "leftover_detail": left,
    }
