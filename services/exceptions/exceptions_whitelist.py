# -*- coding: utf-8 -*-
"""异常白名单 DAL(REFACTOR-WA-B1 · 2026-05-29 从 exceptions/store 抽出 · 纯搬家 0 逻辑改)

is_exception_whitelisted(规则命中判定 · insert_exception 调)+ 白名单 CRUD(add/list/delete)+
count_whitelist_rules。组内自洽(只依赖 db)· exceptions/store 顶部 re-import 当 facade · db.X/store.X 单一对象。
"""

import json as _json  # noqa: F401
import logging
from typing import Optional, Dict, Any, List  # noqa: F401

logger = logging.getLogger(__name__)


def is_exception_whitelisted(
    user_id: str, tenant_id: Optional[str], seller_name: Optional[str], rule_code: str
) -> bool:
    """检查 (seller, rule) 是否在白名单 · 命中则跳过该规则"""
    if not seller_name or not seller_name.strip() or not rule_code:
        return False
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT 1 FROM exception_whitelist
                    WHERE tenant_id = %s AND LOWER(seller_name) = LOWER(%s) AND rule_code = %s
                    LIMIT 1
                """,
                    (tenant_id, seller_name.strip(), rule_code),
                )
            else:
                cur.execute(
                    """
                    SELECT 1 FROM exception_whitelist
                    WHERE user_id = %s AND tenant_id IS NULL
                      AND LOWER(seller_name) = LOWER(%s) AND rule_code = %s
                    LIMIT 1
                """,
                    (user_id, seller_name.strip(), rule_code),
                )
            return cur.fetchone() is not None
    except Exception as e:
        logger.warning(f"is_exception_whitelisted failed: {e}")
        return False


def add_exception_whitelist(
    user_id: str, tenant_id: Optional[str], seller_name: Optional[str], rule_code: str
) -> bool:
    """加入「忽略此类」白名单 · 下次同供应商同规则不再拦"""
    if not seller_name or not seller_name.strip() or not rule_code:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO exception_whitelist (user_id, tenant_id, seller_name, rule_code)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """,
                (str(user_id), tenant_id, seller_name.strip(), rule_code),
            )
            return True
    except Exception as e:
        logger.error(f"add_exception_whitelist failed: {e}")
        return False


def list_exception_whitelist(user_id: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出当前 user/tenant 下所有学过的白名单规则"""
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, seller_name, rule_code, created_at
                    FROM exception_whitelist
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                """,
                    (tenant_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, seller_name, rule_code, created_at
                    FROM exception_whitelist
                    WHERE user_id = %s AND tenant_id IS NULL
                    ORDER BY created_at DESC
                """,
                    (str(user_id),),
                )
            items = []
            for r in cur.fetchall():
                items.append(
                    {
                        "id": int(r["id"]),
                        "seller_name": r["seller_name"],
                        "rule_code": r["rule_code"],
                        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    }
                )
            return items
    except Exception as e:
        logger.error(f"list_exception_whitelist failed: {e}")
        return []


def delete_exception_whitelist(user_id: str, wl_id: int, tenant_id: Optional[str] = None) -> bool:
    """删除一条白名单规则 · 同 tenant 内任意成员可删"""
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    """
                    DELETE FROM exception_whitelist
                    WHERE id = %s AND tenant_id = %s
                """,
                    (int(wl_id), tenant_id),
                )
            else:
                cur.execute(
                    """
                    DELETE FROM exception_whitelist
                    WHERE id = %s AND user_id = %s AND tenant_id IS NULL
                """,
                    (int(wl_id), str(user_id)),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_exception_whitelist failed: {e}")
        return False


def count_whitelist_rules(user_id: str, tenant_id: Optional[str] = None) -> int:
    """统计当前已学习的「忽略此类」规则数 · 给 KPI 卡用"""
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM exception_whitelist WHERE tenant_id = %s",
                    (tenant_id,),
                )
            else:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM exception_whitelist WHERE user_id = %s AND tenant_id IS NULL",
                    (user_id,),
                )
            r = cur.fetchone()
            return int(r["n"]) if r else 0
    except Exception:
        return 0


import db  # noqa: E402
