# -*- coding: utf-8 -*-
"""智能归档设置(archive_settings)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
归档命名模板 + 文件夹分组策略的读写。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import json as _json
import logging
from typing import Optional, Dict, Any, List

from core import db

logger = logging.getLogger(__name__)


def ensure_archive_settings_table():
    """建归档设置表 + enroll user 维度 RLS · 幂等。

    历史欠债:此表早期 prod 带外建、代码无 CREATE。这里补权威 schema(IF NOT EXISTS·prod
    已存在则只跑 enroll)。per-user 命名偏好(键 user_id)→ apply_user_rls 纯 user 隔离·
    force=False(owner 兜底·owner_users 级联删走 owner 绕过)。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS archive_settings (
                    user_id UUID PRIMARY KEY,
                    tenant_id UUID,
                    name_template JSONB NOT NULL DEFAULT '[]'::jsonb,
                    folder_strategy TEXT NOT NULL DEFAULT 'by_month_seller',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """)
            from core.rls import apply_user_rls

            apply_user_rls(cur, "archive_settings")
        logger.info("✅ archive_settings 表 + user RLS policy 已就绪")
    except Exception as e:
        logger.error(f"ensure_archive_settings_table failed: {e}")


def get_archive_settings(user_id: str) -> Optional[Dict[str, Any]]:
    """读用户的归档设置。没配过就返回 None(调用方用默认)"""
    try:
        with db.get_cursor_rls(user_id=user_id) as cur:
            cur.execute(
                """
                SELECT user_id, name_template, folder_strategy
                FROM archive_settings WHERE user_id = %s
            """,
                (user_id,),
            )
            r = cur.fetchone()
            return dict(r) if r else None
    except Exception as e:
        logger.error(f"get_archive_settings failed: {e}")
        return None


def get_archive_template(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """只读命名模板。给识别流程用的快捷方法"""
    s = get_archive_settings(user_id)
    if not s:
        return None
    tpl = s.get("name_template") or []
    return tpl if isinstance(tpl, list) and tpl else None


def upsert_archive_settings(
    user_id: str, name_template: List[Dict[str, Any]], folder_strategy: str
) -> bool:
    """创建或更新归档设置"""
    if folder_strategy not in ("none", "by_month", "by_seller", "by_month_seller"):
        folder_strategy = "by_month_seller"
    try:
        with db.get_cursor_rls(user_id=user_id, commit=True) as cur:
            cur.execute(
                """
                INSERT INTO archive_settings (user_id, name_template, folder_strategy)
                VALUES (%s, %s::jsonb, %s)
                ON CONFLICT (user_id) DO UPDATE
                  SET name_template = EXCLUDED.name_template,
                      folder_strategy = EXCLUDED.folder_strategy,
                      updated_at = NOW()
            """,
                (user_id, _json.dumps(name_template or []), folder_strategy),
            )
            return True
    except Exception as e:
        logger.error(f"upsert_archive_settings failed: {e}")
        return False
