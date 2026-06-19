# -*- coding: utf-8 -*-
"""LINE 来源进项单查询(批量撤销用)。

只读最近 / 今天该套账 source='line' 的可撤单(posted/draft)。隔离=每句 WHERE tenant_id +
workspace_client_id(应用层唯一防线·见 test_purchase_sql_isolation);调用方传 RLS cursor。
今天按泰国时区(与卡片/连号同口径)。
"""

from __future__ import annotations

_COLS = "d.id, d.grand_total, d.doc_date, d.status, d.doc_no, s.name AS supplier_name"
_FROM = (
    "FROM purchase_docs d "
    "LEFT JOIN suppliers s ON s.id = d.supplier_id AND s.tenant_id = d.tenant_id"
)


def find_recent_line_docs(cur, *, tenant_id, workspace_client_id, limit) -> list:
    """最近 limit 笔 LINE 进项单(posted/draft·created_at 倒序)。"""
    cur.execute(
        f"SELECT {_COLS} {_FROM} "
        "WHERE d.tenant_id = %s AND d.workspace_client_id = %s "
        "AND d.source = 'line' AND d.status IN ('posted', 'draft') "
        "ORDER BY d.created_at DESC LIMIT %s",
        (tenant_id, workspace_client_id, int(limit)),
    )
    return list(cur.fetchall())


def find_today_line_docs(cur, *, tenant_id, workspace_client_id) -> list:
    """今天(泰国时区)该套账全部 LINE 进项单(posted/draft·created_at 倒序)。"""
    cur.execute(
        f"SELECT {_COLS} {_FROM} "
        "WHERE d.tenant_id = %s AND d.workspace_client_id = %s "
        "AND d.source = 'line' AND d.status IN ('posted', 'draft') "
        "AND (d.created_at AT TIME ZONE 'Asia/Bangkok')::date "
        "= (now() AT TIME ZONE 'Asia/Bangkok')::date "
        "ORDER BY d.created_at DESC",
        (tenant_id, workspace_client_id),
    )
    return list(cur.fetchall())
