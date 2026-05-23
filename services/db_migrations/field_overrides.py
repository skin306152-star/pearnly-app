# -*- coding: utf-8 -*-
"""
services.db_migrations.field_overrides · P1.1 BUG-FIX-P1.1 v118.35.0.41

跟 alembic/versions/002_field_overrides_4_modules.py 双跑 · prod 启动时幂等跑
4 模块的 task / row 表都加 field_overrides JSONB 列(允许 NULL · 老数据不动):
- M1 ocr_history
- M2 reconciliation_row
- M3 gl_vat_tasks
- M4 bank_recon_v2_tasks

Schema:`field_overrides JSONB`
形态:`{field_name: {"ocr": <value>, "user": <value>, "ts": <iso8601>}, ...}`

铁律 #21 ✅:新 schema 业务函数禁止进 db.py · 独立 service module
docs/audits/2026-05-22-ocr-recon-audit.md §5 Phase 1 P1.1
docs/architecture/db-migration-plan.md §0 双跑灰度策略
"""

import logging

logger = logging.getLogger(__name__)

# 4 模块 task / row 表 · 跟 alembic 002 同源(单一权威源在 audit doc · 改这里也要改 alembic)
TARGET_TABLES = ("ocr_history", "reconciliation_row", "gl_vat_tasks", "bank_recon_v2_tasks")


def ensure_field_overrides_columns() -> None:
    """
    幂等加 field_overrides JSONB 列到 4 模块 task/row 表 · 启动时调
    任一表失败不阻塞其它(独立 try)· 失败仅 logger.warning · 不 raise
    Alembic 跑过 002 后再跑这函数 · ADD COLUMN IF NOT EXISTS 是 no-op
    """
    # 延迟 import 避免循环依赖(db.py 启动时不一定全加载)
    import db as _db

    for table in TARGET_TABLES:
        try:
            with _db.get_cursor(commit=True) as cur:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS field_overrides JSONB")
            logger.info(f"✅ {table}.field_overrides JSONB 已就绪 (P1.1 v118.35.0.41)")
        except Exception as e:
            logger.warning(
                f"ensure_field_overrides_columns: {table} 加 field_overrides 失败 (跳过 · 等 alembic 002): {e}"
            )
