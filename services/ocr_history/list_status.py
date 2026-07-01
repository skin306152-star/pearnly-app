"""识别记录列表的派生状态 SQL + 状态聚合 + 列表过滤(从 queries.list_ocr_history 抽出 · 控行数)。

销项识别记录无 status 列 · 三态由 confidence + 关键字段齐全度派生:
  failed   = 发票号/金额/卖方全空(基本没识别到内容)
  confirmed= 高置信 且 发票号+金额齐全(可直接使用)
  pending  = 其余(缺字段或非高置信 · 需复核)
failed 与 confirmed 互斥(confirmed 要求金额非空 · failed 要求金额空)。
"""

from typing import Dict, List, Optional, Tuple

FAILED_SQL = "(total_amount IS NULL AND invoice_no IS NULL AND seller_name IS NULL)"
CONFIRMED_SQL = "(confidence = 'high' AND total_amount IS NOT NULL AND invoice_no IS NOT NULL)"
STATUS_CASE_SQL = (
    f"CASE WHEN {FAILED_SQL} THEN 'failed' "
    f"WHEN {CONFIRMED_SQL} THEN 'confirmed' ELSE 'pending' END"
)

EMPTY_COUNTS = {"all": 0, "confirmed": 0, "pending": 0, "failed": 0}


def _jsonb_first(field: str) -> str:
    """从 pages jsonb 数组里抽第一条非空 fields.<field>(列表只读买方名/税额 · 省全量 pages 流量)。"""
    return (
        f"(SELECT elem->'fields'->>'{field}' "
        f"FROM jsonb_array_elements("
        f"CASE WHEN jsonb_typeof(pages) = 'array' THEN pages ELSE '[]'::jsonb END) elem "
        f"WHERE COALESCE(elem->'fields'->>'{field}', '') <> '' LIMIT 1)"
    )


BUYER_NAME_SQL = _jsonb_first("buyer_name")
VAT_AMOUNT_SQL = _jsonb_first("vat")


def owner_visibility_where(
    user_id: str,
    tenant_id: Optional[str],
    workspace_client_id: Optional[int],
    restrict_client_ids: Optional[List[int]],
) -> Tuple[List[str], list]:
    """识别记录「谁能看到哪些行」的单一可见性事实源:所有权 + 套账 + 员工分配 + 排除草稿。

    不含时间窗/关键词/状态/客户切换 —— 时间窗由调用方叠加(列表用保留期、月度聚合用本月),
    故这里不含。谓词与 queries.list_ocr_history 内联版一致(月度聚合 agent_overview 复用它防漂)。
    """
    if tenant_id:
        where = ["user_id IN (SELECT id FROM users WHERE tenant_id = %s)"]
        params: list = [tenant_id]
    else:
        where = ["user_id = %s"]
        params = [user_id]
    if workspace_client_id is not None:
        where.append("(workspace_client_id = %s OR workspace_client_id IS NULL)")
        params.append(int(workspace_client_id))
    if restrict_client_ids is not None:
        if len(restrict_client_ids) == 0:
            where.append("(user_id = %s AND client_id IS NULL)")
            params.append(user_id)
        else:
            where.append("(client_id = ANY(%s::bigint[]) OR (user_id = %s AND client_id IS NULL))")
            params.append([int(c) for c in restrict_client_ids])
            params.append(user_id)
    where.append("staged = FALSE")
    return where, params


def apply_list_filters(
    where: List[str],
    params: list,
    source_filter: Optional[str],
    status_filter: Optional[str],
) -> Tuple[str, list]:
    """在 base where 上叠加状态/来源过滤 · 只作用于列表与其分页总数(不影响汇总卡全量分布)。"""
    list_where = list(where)
    list_params = list(params)
    if source_filter:
        list_where.append("source = %s")
        list_params.append("manual" if source_filter == "upload" else source_filter)
    if status_filter == "confirmed":
        list_where.append(CONFIRMED_SQL)
    elif status_filter == "failed":
        list_where.append(FAILED_SQL)
    elif status_filter == "pending":
        list_where.append(f"(NOT {FAILED_SQL} AND NOT {CONFIRMED_SQL})")
    return " AND ".join(list_where), list_params


def status_counts(cur, base_where_sql: str, params: list) -> Dict[str, int]:
    """汇总卡:全量(不含状态/来源过滤)的三态分布。"""
    cur.execute(
        f"""SELECT COUNT(*) AS all_c,
                   COUNT(*) FILTER (WHERE {CONFIRMED_SQL}) AS confirmed_c,
                   COUNT(*) FILTER (WHERE {FAILED_SQL}) AS failed_c
            FROM ocr_history WHERE {base_where_sql}""",
        params,
    )
    crow = cur.fetchone()
    all_c = int(crow["all_c"])
    confirmed_c = int(crow["confirmed_c"])
    failed_c = int(crow["failed_c"])
    return {
        "all": all_c,
        "confirmed": confirmed_c,
        "failed": failed_c,
        "pending": max(0, all_c - confirmed_c - failed_c),
    }
