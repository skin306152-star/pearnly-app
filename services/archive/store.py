# -*- coding: utf-8 -*-
"""智能归档设置(archive_settings)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
归档命名模板 + 文件夹分组策略的读写。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import json as _json
import logging
from typing import Optional, Dict, Any, List

import db

logger = logging.getLogger(__name__)


def get_archive_settings(user_id: str) -> Optional[Dict[str, Any]]:
    """读用户的归档设置。没配过就返回 None(调用方用默认)"""
    try:
        with db.get_cursor() as cur:
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
        with db.get_cursor(commit=True) as cur:
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
