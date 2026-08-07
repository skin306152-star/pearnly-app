# -*- coding: utf-8 -*-
"""OCR 确认→正式单据转换桥 schema 双跑入口(启动调一次 · 与 alembic 0098 同源幂等 DDL)。

prod 无自动迁移钩子 → startup 经 ensure_intake_bridge_schema() 幂等加列(与 services/stockcard/
schema.py 同款范式)。DDL 与迁移逐字对齐(改一处必同改两处)。失败仅告警不 raise(不挡主服务)。
"""

from __future__ import annotations

import logging

logger = logging.getLogger("mr-pilot")

_COLUMNS = (
    "ALTER TABLE purchase_docs ADD COLUMN IF NOT EXISTS ocr_history_id uuid",
    "ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS ocr_history_id uuid",
)

_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_purchase_docs_ocr_history "
    "ON purchase_docs (tenant_id, ocr_history_id) WHERE ocr_history_id IS NOT NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_sales_documents_ocr_history "
    "ON sales_documents (tenant_id, ocr_history_id) WHERE ocr_history_id IS NOT NULL",
)


def ensure_intake_bridge_schema() -> None:
    """幂等加列 + 溯源防重索引(startup 调 · 与 alembic 0098 双跑)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        for stmt in _COLUMNS + _INDEXES:
            cur.execute(stmt)
